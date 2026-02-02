from typing import Dict, Optional
import google.generativeai as genai
from backend.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.google_api_key)


class RiskAssessmentService:
    """Risk assessment using Gemini 2.5 Pro for structured output"""
    
    # High-risk keywords and patterns
    HIGH_RISK_KEYWORDS = [
        "chest pain", "crushing pain", "heart attack", "stroke",
        "suicide", "kill myself", "end my life", "suicidal",
        "severe bleeding", "heavy bleeding", "can't breathe", "difficulty breathing",
        "unconscious", "passed out", "seizure", "convulsion",
        "severe headache", "worst headache", "sudden weakness",
        "severe abdominal pain", "vomiting blood", "blood in stool"
    ]
    
    MEDIUM_RISK_KEYWORDS = [
        "high fever", "persistent fever", "severe pain",
        "can't sleep", "extreme fatigue", "dizziness",
        "confusion", "disoriented", "severe nausea"
    ]
    
    def __init__(self):
        self.model = genai.GenerativeModel(settings.gemini_model)
    
    def _quick_keyword_check(self, message: str) -> Optional[str]:
        """Quick keyword-based risk check before LLM call"""
        message_lower = message.lower()
        
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in message_lower:
                return "HIGH"
        
        for keyword in self.MEDIUM_RISK_KEYWORDS:
            if keyword in message_lower:
                return "MEDIUM"
        
        return None
    
    async def assess_risk(self, message: str, conversation_context: Optional[str] = None) -> Dict:
        """
        Assess risk level of patient message
        
        Args:
            message: Patient's message
            conversation_context: Optional previous conversation context
            
        Returns:
            Dict with risk_level, reason, confidence, requires_escalation
        """
        # Quick keyword check first
        quick_risk = self._quick_keyword_check(message)
        
        # Build prompt for LLM
        prompt = f"""You are a medical triage AI. Analyze this patient message and determine the risk level.

Patient Message: "{message}"

{f'Previous Context: {conversation_context}' if conversation_context else ''}

Classify the risk level as:
- HIGH: Life-threatening emergency (chest pain, suicide ideation, severe bleeding, stroke symptoms, etc.)
- MEDIUM: Urgent but not immediately life-threatening (high fever, severe pain, persistent symptoms)
- LOW: General health questions, mild symptoms, medication questions

Respond in JSON format:
{{
    "risk_level": "HIGH|MEDIUM|LOW",
    "reason": "Brief explanation of why this risk level",
    "confidence": "HIGH|MEDIUM|LOW",
    "requires_escalation": true/false
}}

HIGH and MEDIUM risk ALWAYS require escalation (requires_escalation: true).
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            import json
            result = json.loads(result_text)
            
            # Override with keyword check if it found HIGH risk
            if quick_risk == "HIGH":
                result["risk_level"] = "HIGH"
                result["requires_escalation"] = True
            
            return result
            
        except Exception as e:
            # Fallback to keyword-based assessment
            print(f"Error in LLM risk assessment: {e}")
            if quick_risk:
                return {
                    "risk_level": quick_risk,
                    "reason": "Keyword-based detection",
                    "confidence": "MEDIUM",
                    "requires_escalation": quick_risk in ["HIGH", "MEDIUM"]
                }
            else:
                return {
                    "risk_level": "LOW",
                    "reason": "No concerning keywords detected",
                    "confidence": "LOW",
                    "requires_escalation": False
                }


# Singleton instance
risk_assessment_service = RiskAssessmentService()
