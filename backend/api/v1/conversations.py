from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.conversation import Conversation, ConversationStatus
from backend.models.message import Message, SenderType, RiskLevel
from backend.models.user import User
from backend.agent.graph import MedicalAgentGraph
from backend.agent.state import AgentState
from backend.services.audit import audit_service
from typing import List
import uuid

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class CreateConversationRequest(BaseModel):
    patient_id: str


class SendMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    sender_type: str
    content: str
    risk_level: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    patient_id: str
    status: str
    messages: List[MessageResponse]


@router.get("/patient/{patient_id}/latest", response_model=dict)
async def get_latest_conversation(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get patient's most recent active or escalated conversation"""
    patient_uuid = uuid.UUID(patient_id)
    
    # Get most recent conversation that's not closed
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.patient_id == patient_uuid,
            Conversation.status.in_([ConversationStatus.ACTIVE, ConversationStatus.ESCALATED])
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)  # Only get the most recent one
    )
    conversation = result.scalars().first()
    
    if conversation:
        return {
            "id": str(conversation.id),
            "patient_id": str(conversation.patient_id),
            "status": conversation.status.value,
            "exists": True
        }
    else:
        return {"exists": False}


@router.post("", response_model=dict)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    patient_id = uuid.UUID(request.patient_id)
    
    # Verify patient exists
    result = await db.execute(
        select(User).where(User.id == patient_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Create conversation
    conversation = Conversation(patient_id=patient_id)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return {
        "id": str(conversation.id),
        "patient_id": str(conversation.patient_id),
        "status": conversation.status.value
    }


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with all messages"""
    conv_id = uuid.UUID(conversation_id)
    
    # Get conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return ConversationResponse(
        id=str(conversation.id),
        patient_id=str(conversation.patient_id),
        status=conversation.status.value,
        messages=[
            MessageResponse(
                id=str(msg.id),
                sender_type=msg.sender_type.value,
                content=msg.content,
                risk_level=msg.risk_level.value,
                created_at=msg.created_at.isoformat()
            )
            for msg in messages
        ]
    )


@router.post("/{conversation_id}/messages", response_model=dict)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and trigger the agent workflow
    This is the main entry point for patient interactions
    """
    conv_id = uuid.UUID(conversation_id)
    
    # Get conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create patient message
    patient_message = Message(
        conversation_id=conv_id,
        sender_type=SenderType.PATIENT,
        content=request.content,  # Will be redacted by agent
        risk_level=RiskLevel.UNKNOWN
    )
    db.add(patient_message)
    await db.flush()
    
    # Audit log
    await audit_service.log_action(
        db=db,
        user_id=conversation.patient_id,
        action="MESSAGE_SENT",
        resource_type="Message",
        resource_id=patient_message.id,
        content=request.content
    )
    
    # COMMIT USER MESSAGE FIRST -> ensures visibility even if agent crashes
    await db.commit()
    
    # Run agent workflow
    initial_state: AgentState = {
        "conversation_id": str(conv_id),
        "patient_id": str(conversation.patient_id),
        "raw_message": request.content,
        "redacted_message": "",
        "phi_detected": False,
        "risk_assessment": None,
        "patient_profile": None,
        "extracted_facts": None,
        "response": None,
        "should_escalate": False,
        "escalation_ticket_id": None,
        "error": None
    }
    
    try:
        agent = MedicalAgentGraph(db=db, message_id=patient_message.id)
        final_state = await agent.run(initial_state)
        
        # We need to re-fetch or merge patient_message because session was committed
        # But actually in asyncpg/SQLAlchemy it might be detached.
        # Let's just query it or update it directly.
        # However, since we are in the SAME session context, we can just use `db.merge(patient_message)` if needed,
        # but typically we can just update the object if it's still attached.
        # After commit, objects expire. We need to refresh/merge.
        # But easier to just update via execute or re-fetch.
        
        # Re-fetch for safety
        result = await db.execute(select(Message).where(Message.id == patient_message.id))
        patient_message = result.scalar_one()

        # Update patient message with redacted content and risk level
        patient_message.content = final_state.get("redacted_message", request.content)
        
        if final_state.get("risk_assessment"):
            risk_level_str = final_state["risk_assessment"].get("risk_level", "UNKNOWN").upper()
            if risk_level_str in RiskLevel.__members__:
                patient_message.risk_level = RiskLevel[risk_level_str]
            else:
                patient_message.risk_level = RiskLevel.UNKNOWN
        
        # Create AI response message
        if final_state.get("response"):
            ai_message = Message(
                conversation_id=conv_id,
                sender_type=SenderType.AI,
                content=final_state["response"],
                risk_level=RiskLevel.LOW
            )
            db.add(ai_message)
            
        await db.commit()
        
        return {
            "patient_message_id": str(patient_message.id),
            "response": final_state.get("response"),
            "escalated": final_state.get("should_escalate", False),
            "escalation_ticket_id": final_state.get("escalation_ticket_id"),
            "risk_level": final_state.get("risk_assessment", {}).get("risk_level", "UNKNOWN")
        }
        
    except Exception as e:
        import traceback
        import logging
        error_msg = f"Error in send_message: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Print to stderr for immediate visibility
        logging.error(error_msg)
        
        # Try to rollback
        try:
            await db.rollback()
        except Exception:
            pass
            
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
