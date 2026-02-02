from typing import Dict, List
import google.generativeai as genai
from backend.agent.state import AgentState
from backend.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.patient_profile import PatientProfile
import uuid
import json

settings = get_settings()
genai.configure(api_key=settings.google_api_key)


async def memory_retrieval_node(state: AgentState, db: AsyncSession) -> AgentState:
    """
    Node 3: Retrieve current patient profile from database
    """
    patient_id = uuid.UUID(state["patient_id"])
    
    # Fetch patient profile
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    
    if profile:
        state["patient_profile"] = {
            "medications": profile.medications or [],
            "symptoms": profile.symptoms or [],
            "allergies": profile.allergies or [],
            "conditions": profile.conditions or []
        }
    else:
        # Create empty profile if doesn't exist
        state["patient_profile"] = {
            "medications": [],
            "symptoms": [],
            "allergies": [],
            "conditions": []
        }
    
    return state


async def fact_extraction_node(state: AgentState) -> AgentState:
    """
    Node 4: Extract medical facts from patient message using LLM
    """
    message = state["redacted_message"]
    current_profile = state.get("patient_profile", {})
    
    model = genai.GenerativeModel(settings.gemini_model)
    
    prompt = f"""Extract structured medical facts from this patient message.

Patient Message: "{message}"

Current Profile:
- Medications: {json.dumps(current_profile.get('medications', []))}
- Symptoms: {json.dumps(current_profile.get('symptoms', []))}
- Allergies: {json.dumps(current_profile.get('allergies', []))}
- Conditions: {json.dumps(current_profile.get('conditions', []))}

Extract any NEW or UPDATED information about:
1. Medications (name, status: ACTIVE/STOPPED/CHANGED)
2. Symptoms (description, severity, duration)
3. Allergies (allergen, reaction)
4. Conditions (diagnosis, status)

Respond in JSON format:
{{
    "medications": [{{"name": "...", "action": "ADD|STOP|UPDATE", "status": "ACTIVE|STOPPED"}}],
    "symptoms": [{{"description": "...", "severity": "MILD|MODERATE|SEVERE", "action": "ADD|REMOVE"}}],
    "allergies": [{{"allergen": "...", "reaction": "...", "action": "ADD|REMOVE"}}],
    "conditions": [{{"name": "...", "status": "...", "action": "ADD|UPDATE"}}]
}}

If no new facts, return empty arrays.
"""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        extracted_facts = json.loads(result_text)
        if not isinstance(extracted_facts, dict):
             extracted_facts = {}
        state["extracted_facts"] = extracted_facts
        
    except Exception as e:
        print(f"Error extracting facts: {e}")
        state["extracted_facts"] = {}
    
    return state


async def memory_update_node(state: AgentState, db: AsyncSession, message_id: uuid.UUID) -> AgentState:
    """
    Node 5: Update patient profile with extracted facts (with provenance)
    """
    patient_id = uuid.UUID(state["patient_id"])
    
    # Get or create profile
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = PatientProfile(
            patient_id=patient_id,
            medications=[],
            symptoms=[],
            allergies=[],
            conditions=[]
        )
        db.add(profile)
        
    # Ensure fields are lists (in case of DB corruption or None values)
    if profile.medications is None: profile.medications = []
    if profile.symptoms is None: profile.symptoms = []
    if profile.allergies is None: profile.allergies = []
    if profile.conditions is None: profile.conditions = []
    
    extracted_facts = state.get("extracted_facts", {})
    if not isinstance(extracted_facts, dict):
        extracted_facts = {}
    
    # Update medications
    for med_update in extracted_facts.get("medications", []):
        action = med_update.get("action")
        med_name = med_update.get("name")
        
        if action == "ADD":
            profile.medications.append({
                "name": med_name,
                "status": med_update.get("status", "ACTIVE"),
                "provenance_message_id": str(message_id),
                "added_at": str(uuid.uuid4())  # Timestamp placeholder
            })
        elif action == "STOP":
            # Find and update existing medication
            for med in profile.medications:
                if med["name"].lower() == med_name.lower():
                    med["status"] = "STOPPED"
                    med["provenance_message_id"] = str(message_id)
    
    # Update symptoms
    for symptom_update in extracted_facts.get("symptoms", []):
        if symptom_update.get("action") == "ADD":
            profile.symptoms.append({
                "description": symptom_update.get("description"),
                "severity": symptom_update.get("severity", "MODERATE"),
                "provenance_message_id": str(message_id)
            })
    
    # Update allergies
    for allergy_update in extracted_facts.get("allergies", []):
        if allergy_update.get("action") == "ADD":
            profile.allergies.append({
                "allergen": allergy_update.get("allergen"),
                "reaction": allergy_update.get("reaction", "Unknown"),
                "provenance_message_id": str(message_id)
            })
    
    # Update conditions
    for condition_update in extracted_facts.get("conditions", []):
        if condition_update.get("action") == "ADD":
            profile.conditions.append({
                "name": condition_update.get("name"),
                "status": condition_update.get("status", "Active"),
                "provenance_message_id": str(message_id)
            })
    
    # Mark as modified for SQLAlchemy
    from sqlalchemy.orm import attributes
    attributes.flag_modified(profile, "medications")
    attributes.flag_modified(profile, "symptoms")
    attributes.flag_modified(profile, "allergies")
    attributes.flag_modified(profile, "conditions")
    
    await db.flush()
    
    return state
