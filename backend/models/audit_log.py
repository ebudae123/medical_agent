from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from backend.database import Base


class AuditLog(Base):
    """Audit log for compliance - metadata only, NO PHI"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    action = Column(String, nullable=False)  # e.g., "MESSAGE_SENT", "PROFILE_UPDATED"
    resource_type = Column(String, nullable=False)  # e.g., "Message", "PatientProfile"
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    
    metadata_hash = Column(String, nullable=False)  # SHA-256 hash of content
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, user_id={self.user_id}, timestamp={self.timestamp})>"
