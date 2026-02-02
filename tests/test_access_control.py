import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from backend.main import app
from backend.database import get_db
from backend.models.conversation import Conversation
from backend.models.user import User, UserRole

# How to run:
# pytest tests/test_access_control.py

def test_patient_access_isolation():
    """
    Test 4a: Patient A cannot fetch Patient B chat history
    """
    client = TestClient(app)
    
    patient_a_id = uuid.uuid4()
    patient_b_id = uuid.uuid4()
    conversation_b_id = uuid.uuid4()
    
    # Mock DB
    mock_session = AsyncMock()
    
    # Setup conversation mock
    mock_conversation = MagicMock()
    mock_conversation.id = conversation_b_id
    mock_conversation.patient_id = patient_b_id
    # status needs to be an object with .value
    mock_status = MagicMock()
    mock_status.value = "ACTIVE"
    mock_conversation.status = mock_status
    # Also need sender_type.value, risk_level.value for messages if they are accessed?
    # No, get_conversation only accesses conversation.status.value lines 125-128
    
    # Return conversation when queried
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conversation
    # Mock messages result
    # The code calls scalars().all() on the messages result
    mock_messages_result = MagicMock()
    mock_messages_result.scalars.return_value.all.return_value = []
    
    # execute is called twice. First for conversation, second for messages.
    # We can use side_effect to return different results
    mock_session.execute.side_effect = [mock_result, mock_messages_result]
    
    # Override DB dependency
    async def override_get_db():
        yield mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # ---------------------------------------------------------
    # Attempt Access
    # ---------------------------------------------------------
    # Simulate User A (e.g. via hypothetical Auth header or token)
    headers = {"X-User-ID": str(patient_a_id), "X-Role": "PATIENT"}
    
    response = client.get(f"/api/v1/conversations/{conversation_b_id}", headers=headers)
    
    # Assert
    # Test failure condition logic requires checking the implementation gap
    # If the endpoint doesn't check ownership, it might return 200.
    
    if response.status_code == 200:
        pytest.fail("Security Vulnerability: Patient A could access Patient B's conversation")
    
    assert response.status_code in [403, 404]


def test_patient_cannot_fetch_triage_queue():
    """
    Test 4b: Patient cannot fetch clinician triage queue
    """
    client = TestClient(app)
    patient_id = uuid.uuid4()
    
    # Mock DB
    mock_session = AsyncMock()
    
    # Configure execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    async def override_get_db():
        yield mock_session
    app.dependency_overrides[get_db] = override_get_db
    
    # Attempt to access escalations endpoint (Clinician only)
    headers = {"X-User-ID": str(patient_id), "X-Role": "PATIENT"}
    
    response = client.get("/api/v1/escalations", headers=headers)
    
    # Check basic protection
    if response.status_code == 200:
         pytest.fail("Security Vulnerability: Patient could access triage queue")
    
    assert response.status_code == 403
