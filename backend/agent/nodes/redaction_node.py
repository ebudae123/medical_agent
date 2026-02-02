from backend.agent.state import AgentState
from backend.services.redaction import redaction_service


def redaction_node(state: AgentState) -> AgentState:
    """
    Node 1: Redact PHI from patient message
    """
    raw_message = state["raw_message"]
    
    # Redact PHI
    redacted_message, entities = redaction_service.redact_text(raw_message)
    
    # Update state
    state["redacted_message"] = redacted_message
    state["phi_detected"] = len(entities) > 0
    
    return state
