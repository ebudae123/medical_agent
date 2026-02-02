from sqlalchemy import Column, String, Text, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from backend.database import Base


class SenderType(str, enum.Enum):
    """Message sender type"""
    PATIENT = "PATIENT"
    AI = "AI"
    CLINICIAN = "CLINICIAN"


class RiskLevel(str, enum.Enum):
    """Risk level assessment"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class Message(Base):
    """Message model with voice-ready fields"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    sender_type = Column(SQLEnum(SenderType), nullable=False)
    content = Column(Text, nullable=False)  # Redacted content
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.UNKNOWN)
    
    # Voice-ready fields for future expansion
    audio_url = Column(String, nullable=True)  # S3 path for audio
    transcription_id = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender_type}, risk={self.risk_level})>"
