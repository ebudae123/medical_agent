# AI Medical Assistant

A safety-first medical AI assistant with risk gating, living memory, and human-in-the-loop escalation.

## Features

✅ **Safety-First Architecture**
- PHI redaction (phone, email, SSN)
- Risk assessment with automatic escalation
- Audit logging (metadata only, no PHI)

✅ **LangGraph Agent Workflow**
- Redaction → Risk Gating → Memory Update → Response/Escalation
- Conditional routing based on risk level
- Gemini 2.5 Pro for medical reasoning

✅ **Living Patient Profile**
- Automatic fact extraction from conversations
- Provenance tracking (every fact links to source message in memory)
- Incremental updates for medications, symptoms, allergies, conditions

✅ **Human-in-the-Loop**
- High/medium risk cases escalate to clinicians
- SBAR format clinical summaries
- Clinician dashboard for triage

✅ **Progressive Web App**
- Installable on mobile/desktop
- Messenger-style chat interface
- Real-time updates

## Quick Start

### 1. Install PostgreSQL 16
Download from: https://www.postgresql.org/download/windows/

During installation:
- Port: `5432`
- Password: Choose a password (e.g., `postgres123`)

Create database:
```bash
psql -U postgres
CREATE DATABASE nightingale;
\q
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example
copy .env.example .env

# Edit .env and add:
# - Your PostgreSQL password
# - Your Gemini API key from https://aistudio.google.com/app/apikey
```

### 4. Start the Application
```bash
python start.py
```

This will start:
- Backend API: http://localhost:8000
- Frontend PWA: http://localhost:3000

## How Redaction Happens
Privacy is enforced at the very first step of message processing.

**Location:** `backend/services/redaction.py` and `backend/agent/nodes/redaction_node.py`

1. **Detection**: Regex patterns identify PII (Phone, Email, SSN).
2. **Replacement**: PII is replaced with placeholders (e.g., `[REDACTED_PHONE]`) **before** sending to the LLM or storing in the `content` field of the DB.
3. **Audit**: The raw PII is never logged. Only a SHA-256 hash of the content is stored in the audit trail for integrity verification (`backend/services/audit.py`).

## Access Control (RBAC)
Role-Based Access Control is designed to isolate patient data.

**Enforcement:**
- **Roles**: defined in `backend/models/user.py` (`PATIENT`, `CLINICIAN`, `ADMIN`).
- **Authentication**: `backend/api/v1/auth.py` handles login and token generation.
- **Authorization**: API endpoints should verify `current_user` matches the requested resource.
    - *Note*: Currently, stricter ownership checks are being implemented in API endpoints (e.g., preventing Patient A from accessing Patient B's history).

## Testing

The project includes a suite of micro-tests to verify safety mechanics.

**How to run tests:**
```bash
# Run the full suite
pytest tests/ -v

# Run specific tests
pytest tests/test_risk_escalation.py  # Verify risk logic
pytest tests/test_redaction.py        # Verify PII removal
pytest tests/test_access_control.py   # Verify permission enforcement
```

Note: test_access_control.py expects authentication logic that may not yet be fully implemented in the API, so failures there are expected until RBAC is enforced


