import google.generativeai as genai
from backend.agent.state import AgentState
from backend.config import get_settings
import json

settings = get_settings()
genai.configure(api_key=settings.google_api_key)


async def response_node(state: AgentState) -> AgentState:
    """
    Node 6: Generate AI response using Gemini
    """
    # If already escalated, don't generate response
    if state.get("should_escalate", False):
        return state
    
    message = state["redacted_message"]
    profile = state.get("patient_profile")
    risk_assessment = state.get("risk_assessment", {})
    
    # Build context from patient profile
    context_parts = []
    if profile:
        if profile.get("medications"):
            meds_list = [m["name"] for m in profile["medications"] if isinstance(m, dict) and "name" in m]
            if meds_list:
                context_parts.append(f"Current medications: {', '.join(meds_list)}")
                
        if profile.get("conditions"):
             # Conditions might be strings or dicts depending on implementation, handle both
            conds_list = []
            for c in profile["conditions"]:
                if isinstance(c, dict) and "name" in c:
                    conds_list.append(c["name"])
                elif isinstance(c, str):
                    conds_list.append(c)
            if conds_list:
                context_parts.append(f"Known conditions: {', '.join(conds_list)}")
                
        if profile.get("allergies"):
            allg_list = []
            for a in profile["allergies"]:
                if isinstance(a, dict) and "name" in a:
                    allg_list.append(a["name"])
                elif isinstance(a, str):
                    allg_list.append(a)
            if allg_list:
                context_parts.append(f"Allergies: {', '.join(allg_list)}")
    
    context = "\n".join(context_parts) if context_parts else "No prior medical history available."
    
    # Build prompt
    prompt = f"""You are a helpful medical AI assistant. Provide clear, empathetic guidance.

Patient Context:
{context}

Patient Message: "{message}"

Risk Assessment: {risk_assessment.get('risk_level', 'UNKNOWN')} risk

Guidelines:
1. Be empathetic and supportive
2. Provide clear, actionable advice
3. Never diagnose - suggest when to see a doctor
4. If symptoms are concerning, recommend professional consultation
5. Keep responses concise and easy to understand

Provide your response:"""
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        # Add disclaimer for medium risk
        if risk_assessment.get("risk_level") == "MEDIUM":
            ai_response += "\n\n⚠️ Note: Given the nature of your symptoms, I recommend consulting with a healthcare professional for a proper evaluation."
        
        state["response"] = ai_response
        
    except Exception as e:
        print(f"Error generating response: {e}")
        state["response"] = "I apologize, but I'm having trouble generating a response right now. Please try again or consult with a healthcare professional if your concern is urgent."
    
    return state
