from typing import TypedDict, List, Dict, Optional


class AgentState(TypedDict):
    """State schema for the medical agent workflow"""
    
    # Input
    conversation_id: str
    patient_id: str
    raw_message: str
    
    # Redaction
    redacted_message: str
    phi_detected: bool
    
    # Risk Assessment
    risk_assessment: Optional[Dict]  # {risk_level, reason, confidence, requires_escalation}
    
    # Patient Profile
    patient_profile: Optional[Dict]  # Current patient profile
    extracted_facts: Optional[List[Dict]]  # New facts extracted from message
    
    # Response
    response: Optional[str]  # AI response to patient
    should_escalate: bool
    escalation_ticket_id: Optional[str]
    
    # Metadata
    error: Optional[str]
