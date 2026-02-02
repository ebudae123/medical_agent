from backend.agent.state import AgentState
from backend.services.risk_assessment import risk_assessment_service


async def risk_gating_node(state: AgentState) -> AgentState:
    """
    Node 2: Assess risk level of patient message
    """
    redacted_message = state["redacted_message"]
    
    # Assess risk
    risk_assessment = await risk_assessment_service.assess_risk(redacted_message)
    
    # Update state
    state["risk_assessment"] = risk_assessment
    state["should_escalate"] = risk_assessment.get("requires_escalation", False)
    
    return state
