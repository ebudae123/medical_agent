from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from backend.database import Base


class PatientProfile(Base):
    """Living patient profile with provenance tracking"""
    __tablename__ = "patient_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Structured medical information with provenance
    # Each entry format: {"name": "...", "status": "ACTIVE/STOPPED", "provenance_message_id": "uuid", "added_at": "timestamp"}
    medications = Column(JSONB, default=list, nullable=False)
    symptoms = Column(JSONB, default=list, nullable=False)
    allergies = Column(JSONB, default=list, nullable=False)
    conditions = Column(JSONB, default=list, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PatientProfile(patient_id={self.patient_id}, meds={len(self.medications)})>"
