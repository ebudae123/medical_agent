from sqlalchemy import Column, String, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from backend.database import Base


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "ACTIVE"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class Conversation(Base):
    """Conversation model tracking patient conversations"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, patient_id={self.patient_id}, status={self.status})>"
