import google.generativeai as genai
from backend.agent.state import AgentState
from backend.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.escalation import EscalationTicket, EscalationStatus
from backend.models.conversation import Conversation, ConversationStatus
import uuid
import json

settings = get_settings()
genai.configure(api_key=settings.google_api_key)


async def escalation_node(state: AgentState, db: AsyncSession) -> AgentState:
    """
    Node 7: Create escalation ticket with SBAR clinical summary
    """
    if not state.get("should_escalate", False):
        return state
    
    conversation_id = uuid.UUID(state["conversation_id"])
    patient_id = uuid.UUID(state["patient_id"])
    risk_assessment = state.get("risk_assessment", {})
    profile = state.get("patient_profile")
    message = state["redacted_message"]
    
    # If profile is None (escalation happened before memory retrieval), load it now
    if profile is None:
        from sqlalchemy import select
        from backend.models.patient_profile import PatientProfile
        
        result = await db.execute(
            select(PatientProfile).where(PatientProfile.patient_id == patient_id)
        )
        profile_obj = result.scalar_one_or_none()
        
        if profile_obj:
            profile = {
                "medications": profile_obj.medications or [],
                "symptoms": profile_obj.symptoms or [],
                "allergies": profile_obj.allergies or [],
                "conditions": profile_obj.conditions or []
            }
        else:
            # No profile exists yet, use empty profile
            profile = {
                "medications": [],
                "symptoms": [],
                "allergies": [],
                "conditions": []
            }
    
    # Generate SBAR clinical summary
    model = genai.GenerativeModel(settings.gemini_model)
    
    prompt = f"""Generate a clinical summary in SBAR format for this escalation.

Patient Message: "{message}"
Risk Level: {risk_assessment.get('risk_level', 'UNKNOWN')}
Risk Reason: {risk_assessment.get('reason', 'Unknown')}

Patient Profile:
- Medications: {json.dumps(profile.get('medications', []))}
- Symptoms: {json.dumps(profile.get('symptoms', []))}
- Allergies: {json.dumps(profile.get('allergies', []))}
- Conditions: {json.dumps(profile.get('conditions', []))}

Generate SBAR format:
**Situation**: What is happening with the patient right now?
**Background**: Relevant medical history and context
**Assessment**: Your clinical assessment of the situation
**Recommendation**: What should the clinician do?

Keep it concise and professional.
"""
    
    try:
        response = model.generate_content(prompt)
        clinical_summary = response.text.strip()
    except Exception as e:
        print(f"Error generating SBAR: {e}")
        clinical_summary = f"Patient reports: {message}\nRisk Level: {risk_assessment.get('risk_level')}\nReason: {risk_assessment.get('reason')}"
    
    # Create escalation ticket
    ticket = EscalationTicket(
        conversation_id=conversation_id,
        patient_id=patient_id,
        reason=risk_assessment.get("reason", "High risk detected"),
        risk_level=risk_assessment.get("risk_level", "UNKNOWN"),
        clinical_summary=clinical_summary,
        status=EscalationStatus.PENDING
    )
    
    db.add(ticket)
    await db.flush()
    
    # Update conversation status
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        conversation.status = ConversationStatus.ESCALATED
    
    state["escalation_ticket_id"] = str(ticket.id)
    state["response"] = f"Your message has been escalated to a healthcare professional. A clinician will respond shortly."
    
    return state
