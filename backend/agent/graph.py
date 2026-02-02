from langgraph.graph import StateGraph, END
from backend.agent.state import AgentState
from backend.agent.nodes.redaction_node import redaction_node
from backend.agent.nodes.risk_gating_node import risk_gating_node
from backend.agent.nodes.memory_nodes import (
    memory_retrieval_node,
    fact_extraction_node,
    memory_update_node
)
from backend.agent.nodes.response_node import response_node
from backend.agent.nodes.escalation_node import escalation_node
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


def should_escalate(state: AgentState) -> str:
    """Router: Determine if we should escalate or continue"""
    if state.get("should_escalate", False):
        return "escalate"
    return "continue"


class MedicalAgentGraph:
    """LangGraph workflow for medical agent"""
    
    def __init__(self, db: AsyncSession, message_id: uuid.UUID):
        self.db = db
        self.message_id = message_id
        self.graph = self._build_graph()
    
    async def _memory_retrieval_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for memory retrieval node with db dependency"""
        return await memory_retrieval_node(state, self.db)
    
    async def _memory_update_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for memory update node with db and message_id dependencies"""
        return await memory_update_node(state, self.db, self.message_id)
    
    async def _escalation_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for escalation node with db dependency"""
        return await escalation_node(state, self.db)
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("redaction", redaction_node)
        workflow.add_node("risk_gating", risk_gating_node)
        workflow.add_node("memory_retrieval", self._memory_retrieval_wrapper)
        workflow.add_node("fact_extraction", fact_extraction_node)
        workflow.add_node("memory_update", self._memory_update_wrapper)
        workflow.add_node("response_generation", response_node)
        workflow.add_node("escalation", self._escalation_wrapper)
        
        # Define flow
        workflow.set_entry_point("redaction")
        
        workflow.add_edge("redaction", "risk_gating")
        
        # Conditional routing after risk assessment
        workflow.add_conditional_edges(
            "risk_gating",
            should_escalate,
            {
                "escalate": "escalation",
                "continue": "memory_retrieval"
            }
        )
        
        # Low-risk flow
        workflow.add_edge("memory_retrieval", "fact_extraction")
        workflow.add_edge("fact_extraction", "memory_update")
        workflow.add_edge("memory_update", "response_generation")
        workflow.add_edge("response_generation", END)
        
        # High-risk flow
        workflow.add_edge("escalation", END)
        
        return workflow.compile()
    
    async def run(self, initial_state: AgentState) -> AgentState:
        """Run the agent workflow"""
        # LangGraph's invoke method
        result = await self.graph.ainvoke(initial_state)
        return result
