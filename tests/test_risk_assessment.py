import pytest
from backend.services.risk_assessment import RiskAssessmentService


@pytest.mark.asyncio
async def test_high_risk_chest_pain():
    """Test that chest pain is flagged as high risk"""
    service = RiskAssessmentService()
    result = await service.assess_risk("I have severe chest pain")
    
    assert result["risk_level"] == "HIGH"
    assert result["requires_escalation"] == True


@pytest.mark.asyncio
async def test_high_risk_suicide():
    """Test that suicidal ideation is flagged as high risk"""
    service = RiskAssessmentService()
    result = await service.assess_risk("I want to kill myself")
    
    assert result["risk_level"] == "HIGH"
    assert result["requires_escalation"] == True


@pytest.mark.asyncio
async def test_medium_risk_fever():
    """Test that high fever is flagged as medium risk"""
    service = RiskAssessmentService()
    result = await service.assess_risk("I have a high fever for 3 days")
    
    assert result["risk_level"] in ["MEDIUM", "HIGH"]
    assert result["requires_escalation"] == True


@pytest.mark.asyncio
async def test_low_risk_headache():
    """Test that mild symptoms are low risk"""
    service = RiskAssessmentService()
    result = await service.assess_risk("I have a mild headache")
    
    assert result["risk_level"] == "LOW"
    assert result["requires_escalation"] == False


def test_keyword_detection():
    """Test quick keyword-based risk check"""
    service = RiskAssessmentService()
    
    assert service._quick_keyword_check("chest pain") == "HIGH"
    assert service._quick_keyword_check("suicide") == "HIGH"
    assert service._quick_keyword_check("high fever") == "MEDIUM"
    assert service._quick_keyword_check("headache") is None
