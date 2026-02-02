import re
from typing import Dict, List, Tuple


class RedactionService:
    """Simple regex-based PHI redaction for development/testing"""
    
    # Regex patterns for common PHI
    PATTERNS = {
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "date": r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Simple date pattern
    }
    
    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PATTERNS.items()
        }
    
    def redact_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Redact PHI from text
        
        Args:
            text: Original text containing potential PHI
            
        Returns:
            Tuple of (redacted_text, entities_found)
        """
        redacted = text
        entities_found = []
        
        for entity_type, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                entities_found.append({
                    "type": entity_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
                redacted = redacted.replace(match.group(), f"[REDACTED_{entity_type.upper()}]")
        
        return redacted, entities_found
    
    def has_phi(self, text: str) -> bool:
        """Check if text contains any PHI"""
        for pattern in self.compiled_patterns.values():
            if pattern.search(text):
                return True
        return False


# Singleton instance
redaction_service = RedactionService()
