from sqlalchemy import Column, String, Text, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from backend.database import Base


class EscalationStatus(str, enum.Enum):
    """Escalation ticket status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class EscalationTicket(Base):
    """Escalation ticket for human-in-the-loop workflow"""
    __tablename__ = "escalation_tickets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_clinician_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    reason = Column(Text, nullable=False)
    risk_level = Column(String, nullable=False)
    clinical_summary = Column(Text, nullable=False)  # SBAR format summary
    
    status = Column(SQLEnum(EscalationStatus), default=EscalationStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<EscalationTicket(id={self.id}, risk={self.risk_level}, status={self.status})>"
