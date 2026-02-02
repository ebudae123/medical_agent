from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.escalation import EscalationTicket, EscalationStatus
from backend.models.message import Message, SenderType, RiskLevel
from backend.models.user import User
from typing import List, Optional
import uuid

router = APIRouter(prefix="/escalations", tags=["Escalations"])


class EscalationResponse(BaseModel):
    id: str
    conversation_id: str
    patient_id: str
    patient_name: str
    reason: str
    risk_level: str
    clinical_summary: str
    status: str
    created_at: str
    assigned_clinician_id: Optional[str]


class ClinicianResponseRequest(BaseModel):
    clinician_id: str
    response_text: str


@router.get("", response_model=List[EscalationResponse])
async def list_escalations(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List escalation tickets (for clinician dashboard)"""
    query = select(EscalationTicket)
    
    if status:
        query = query.where(EscalationTicket.status == EscalationStatus[status.upper()])
    else:
        # Default: show pending and in-progress
        query = query.where(
            EscalationTicket.status.in_([EscalationStatus.PENDING, EscalationStatus.IN_PROGRESS])
        )
    
    query = query.order_by(EscalationTicket.created_at.desc())
    
    result = await db.execute(query)
    tickets = result.scalars().all()
    
    # Get patient names
    responses = []
    for ticket in tickets:
        patient_result = await db.execute(
            select(User).where(User.id == ticket.patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        responses.append(EscalationResponse(
            id=str(ticket.id),
            conversation_id=str(ticket.conversation_id),
            patient_id=str(ticket.patient_id),
            patient_name=patient.name if patient else "Unknown",
            reason=ticket.reason,
            risk_level=ticket.risk_level,
            clinical_summary=ticket.clinical_summary,
            status=ticket.status.value,
            created_at=ticket.created_at.isoformat(),
            assigned_clinician_id=str(ticket.assigned_clinician_id) if ticket.assigned_clinician_id else None
        ))
    
    return responses


@router.get("/{ticket_id}", response_model=EscalationResponse)
async def get_escalation(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific escalation ticket"""
    result = await db.execute(
        select(EscalationTicket).where(EscalationTicket.id == uuid.UUID(ticket_id))
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Escalation ticket not found")
    
    # Get patient name
    patient_result = await db.execute(
        select(User).where(User.id == ticket.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    
    return EscalationResponse(
        id=str(ticket.id),
        conversation_id=str(ticket.conversation_id),
        patient_id=str(ticket.patient_id),
        patient_name=patient.name if patient else "Unknown",
        reason=ticket.reason,
        risk_level=ticket.risk_level,
        clinical_summary=ticket.clinical_summary,
        status=ticket.status.value,
        created_at=ticket.created_at.isoformat(),
        assigned_clinician_id=str(ticket.assigned_clinician_id) if ticket.assigned_clinician_id else None
    )


@router.post("/{ticket_id}/respond", response_model=dict)
async def respond_to_escalation(
    ticket_id: str,
    request: ClinicianResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """Clinician responds to escalation ticket"""
    ticket_uuid = uuid.UUID(ticket_id)
    clinician_uuid = uuid.UUID(request.clinician_id)
    
    # Get ticket
    result = await db.execute(
        select(EscalationTicket).where(EscalationTicket.id == ticket_uuid)
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Escalation ticket not found")
    
    # Verify clinician exists
    clinician_result = await db.execute(
        select(User).where(User.id == clinician_uuid)
    )
    clinician = clinician_result.scalar_one_or_none()
    if not clinician:
        raise HTTPException(status_code=404, detail="Clinician not found")
    
    # Update ticket
    ticket.assigned_clinician_id = clinician_uuid
    ticket.status = EscalationStatus.IN_PROGRESS
    
    # Create clinician message in conversation
    clinician_message = Message(
        conversation_id=ticket.conversation_id,
        sender_type=SenderType.CLINICIAN,
        content=request.response_text,
        risk_level=RiskLevel.LOW
    )
    db.add(clinician_message)
    
    await db.commit()
    
    return {
        "message": "Response sent successfully",
        "message_id": str(clinician_message.id)
    }


@router.patch("/{ticket_id}/status", response_model=dict)
async def update_escalation_status(
    ticket_id: str,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Update escalation ticket status"""
    result = await db.execute(
        select(EscalationTicket).where(EscalationTicket.id == uuid.UUID(ticket_id))
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Escalation ticket not found")
    
    ticket.status = EscalationStatus[status.upper()]
    
    if status.upper() == "RESOLVED":
        from datetime import datetime
        ticket.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Status updated successfully"}
