import hashlib
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.audit_log import AuditLog
import uuid


class AuditService:
    """Audit logging service - metadata only, NO PHI"""
    
    @staticmethod
    def _hash_content(content: str) -> str:
        """Create SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        content: Optional[str] = None
    ) -> AuditLog:
        """
        Log an action to audit trail
        
        Args:
            db: Database session
            user_id: User performing the action
            action: Action type (e.g., "MESSAGE_SENT", "PROFILE_UPDATED")
            resource_type: Type of resource (e.g., "Message", "PatientProfile")
            resource_id: ID of the resource
            content: Optional content to hash (NOT stored, only hash)
            
        Returns:
            Created AuditLog entry
        """
        metadata_hash = AuditService._hash_content(content) if content else ""
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_hash=metadata_hash,
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_log)
        await db.flush()
        
        return audit_log
    
    @staticmethod
    async def verify_content(content: str, stored_hash: str) -> bool:
        """Verify content matches stored hash"""
        return AuditService._hash_content(content) == stored_hash


# Singleton instance
audit_service = AuditService()
