import asyncio
import uuid
from backend.database import AsyncSessionLocal, init_db
from backend.agent.graph import MedicalAgentGraph
from backend.agent.state import AgentState
from backend.models.message import Message, SenderType, RiskLevel

async def main():
    message_content = "I want to eat some fruit. Please recommend what kind of fruits are suitable for me."
    patient_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    message_id = uuid.uuid4()
    
    print(f"Testing message: {message_content}")
    
    initial_state: AgentState = {
        "conversation_id": conversation_id,
        "patient_id": patient_id,
        "raw_message": message_content,
        "redacted_message": "",
        "phi_detected": False,
        "risk_assessment": None,
        "patient_profile": None,
        "extracted_facts": None,
        "response": None,
        "should_escalate": False,
        "pending_escalation": False,
        "escalation_ticket_id": None,
        "error": None
    }
    
    # Needs DB session
    await init_db()
    async with AsyncSessionLocal() as db:
        agent = MedicalAgentGraph(db=db, message_id=message_id)
        
        try:
            print("Running agent...")
            final_state = await agent.run(initial_state)
            
            print("\n----- RESULT -----")
            print(f"Response: {final_state.get('response')}")
            print(f"Should Escalate: {final_state.get('should_escalate')}")
            print(f"Risk Assessment: {final_state.get('risk_assessment')}")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
