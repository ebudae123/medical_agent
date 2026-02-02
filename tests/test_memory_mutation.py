import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from backend.agent.nodes.memory_nodes import memory_update_node
from backend.models.patient_profile import PatientProfile

@pytest.mark.asyncio
async def test_memory_mutation_flow():
    """
    Test 2: Memory mutation with provenance
    - Turn 1: Add Advil -> Profile meds: Advil (active)
    - Turn 2: Stop Advil -> Profile meds: Advil (stopped)
    - Assert provenance links exist
    """
    patient_id = uuid.uuid4()
    msg_id_1 = uuid.uuid4()
    
    # Mock DB Session
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    
    # ---------------------------------------------------------
    # Turn 1: "I take Advil"
    # ---------------------------------------------------------
    
    # Setup: No existing profile
    mock_result_1 = MagicMock()
    mock_result_1.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result_1
    
    state_turn_1 = {
        "patient_id": str(patient_id),
        "extracted_facts": {
            "medications": [{"name": "Advil", "action": "ADD", "status": "ACTIVE"}]
        }
    }
    
    # Run node
    await memory_update_node(state_turn_1, mock_db, msg_id_1)
    
    # Verify Turn 1
    # Check that a new profile was added
    assert mock_db.add.called
    added_profile = mock_db.add.call_args[0][0]
    
    assert isinstance(added_profile, PatientProfile)
    assert len(added_profile.medications) == 1
    med_entry = added_profile.medications[0]
    
    assert med_entry["name"] == "Advil"
    assert med_entry["status"] == "ACTIVE"
    assert med_entry["provenance_message_id"] == str(msg_id_1)
    
    # ---------------------------------------------------------
    # Turn 2: "Actually I stopped last week"
    # ---------------------------------------------------------
    msg_id_2 = uuid.uuid4()
    
    # Setup: DB returns the profile we created in Turn 1
    mock_result_2 = MagicMock()
    mock_result_2.scalar_one_or_none.return_value = added_profile
    mock_db.execute.return_value = mock_result_2
    
    state_turn_2 = {
        "patient_id": str(patient_id),
        "extracted_facts": {
            "medications": [{"name": "Advil", "action": "STOP"}]
        }
    }
    
    # Run node
    await memory_update_node(state_turn_2, mock_db, msg_id_2)
    
    # Verify Turn 2
    # The profile object should be mutated in place
    assert len(added_profile.medications) == 1
    med_entry_updated = added_profile.medications[0]
    
    assert med_entry_updated["name"] == "Advil"
    assert med_entry_updated["status"] == "STOPPED", "Medication status should be updated to STOPPED"
    assert med_entry_updated["provenance_message_id"] == str(msg_id_2), "Provenance should link to the NEW message"
