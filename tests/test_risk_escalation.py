import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from backend.services.risk_assessment import RiskAssessmentService
from backend.agent.nodes.escalation_node import escalation_node
from backend.agent.state import AgentState

@pytest.mark.asyncio
async def test_risk_escalation_flow():
    """
    Test 1: Verify risk escalation logic
    - Input: "I have crushing chest pain."
    - Assert: risk_level == high
    - Assert: AI does not provide advice
    - Assert: escalation_required == true
    """
    # 1. Test Input
    input_text = "I have crushing chest pain."
    conversation_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    
    # 2. Assessment
    risk_service = RiskAssessmentService()
    # Use real service logic (keyword "chest pain" -> HIGH)
    assessment = await risk_service.assess_risk(input_text)
    
    # Assert Risk Level
    assert assessment["risk_level"] == "HIGH", "Should be HIGH risk for chest pain"
    assert assessment["requires_escalation"] is True, "Should require escalation"

    # 3. Escalation Node Logic
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    
    # Setup DB execute result (needs to be MagicMock for sync scalar_one_or_none)
    mock_result = MagicMock()
    mock_conversation = MagicMock()
    mock_conversation.status = "ACTIVE"
    mock_result.scalar_one_or_none.return_value = mock_conversation
    mock_db.execute.return_value = mock_result
    
    # Prepare State
    state = AgentState(
        conversation_id=conversation_id,
        patient_id=patient_id,
        raw_message=input_text,
        redacted_message=input_text, # Assuming no PII in this specific string
        phi_detected=False,
        risk_assessment=assessment,
        should_escalate=True,
        patient_profile={
            "medications": [],
            "symptoms": [],
            "allergies": [],
            "conditions": []
        },
        extracted_facts=[],
        response=None,
        escalation_ticket_id=None,
        error=None
    )
    
    # Run node
    # The node creates a ticket in DB and updates conversation status
    new_state = await escalation_node(state, mock_db)
    
    # Assert Escalation Ticket Created
    assert new_state["escalation_ticket_id"] is not None, "Ticket ID should be set"
    
    # Assert AI Response (Canned response, no advice)
    response = new_state["response"]
    assert response is not None
    assert "escalated" in response.lower(), "Response should mention escalation"
    assert "take" not in response.lower() and "dose" not in response.lower(), "Response should NOT give medical advice"
    
    # Verify DB interactions
    assert mock_db.add.called, "Should add ticket to DB session"
    assert mock_db.flush.called, "Should flush DB session"
