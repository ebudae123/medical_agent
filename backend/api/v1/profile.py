from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.patient_profile import PatientProfile
from backend.models.user import User
from typing import List, Dict
import uuid

router = APIRouter(prefix="/profile", tags=["Patient Profile"])


class ProfileResponse(BaseModel):
    patient_id: str
    patient_name: str
    medications: List[Dict]
    symptoms: List[Dict]
    allergies: List[Dict]
    conditions: List[Dict]
    last_updated: str


@router.get("/{patient_id}", response_model=ProfileResponse)
async def get_patient_profile(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get patient's living profile"""
    patient_uuid = uuid.UUID(patient_id)
    
    # Get patient
    patient_result = await db.execute(
        select(User).where(User.id == patient_uuid)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get profile
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_uuid)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # Return empty profile
        return ProfileResponse(
            patient_id=str(patient_uuid),
            patient_name=patient.name,
            medications=[],
            symptoms=[],
            allergies=[],
            conditions=[],
            last_updated=""
        )
    
    return ProfileResponse(
        patient_id=str(patient_uuid),
        patient_name=patient.name,
        medications=profile.medications or [],
        symptoms=profile.symptoms or [],
        allergies=profile.allergies or [],
        conditions=profile.conditions or [],
        last_updated=profile.last_updated.isoformat()
    )
