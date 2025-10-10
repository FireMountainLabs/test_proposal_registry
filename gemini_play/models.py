# Risk Assessment Engine Models

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Control(BaseModel):
    """Control model"""
    control_id: str = Field(..., description="Control ID (e.g., C.AIIM.1)")
    control_title: str = Field(..., description="Control title")
    control_description: Optional[str] = Field(None, description="Control description")

class Risk(BaseModel):
    """Risk model"""
    risk_id: str = Field(..., description="Risk ID (e.g., R.AIR.001)")
    risk_title: str = Field(..., description="Risk title")
    risk_description: str = Field(..., description="Risk description")

class RiskAssessment(BaseModel):
    """Individual risk assessment result"""
    risk_id: str = Field(..., description="Risk ID")
    risk_title: str = Field(..., description="Risk title")
    risk_description: str = Field(..., description="Risk description")
    explanation: str = Field(..., description="Why this risk applies to the proposal")
    controls: List[Control] = Field(default_factory=list, description="Mapped controls")

class RiskAssessmentResult(BaseModel):
    """Complete risk assessment result"""
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique assessment ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Assessment timestamp")
    risks: List[RiskAssessment] = Field(..., description="Top 3 identified risks")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProposalSchema(BaseModel):
    """Proposal input schema"""
    cfp_id: Optional[str] = Field(None, description="CFP ID")
    proposal_title: Optional[str] = Field(None, description="Proposal title")
    description: str = Field(..., description="Proposal description")
    technical_approach: Optional[str] = Field(None, description="Technical approach")
    data_sources: Optional[List[str]] = Field(None, description="Data sources")
    deployment: Optional[str] = Field(None, description="Deployment approach")
    data_governance: Optional[str] = Field(None, description="Data governance")
    model_governance: Optional[str] = Field(None, description="Model governance")
    security_measures: Optional[str] = Field(None, description="Security measures")
    
    # Additional fields for flexibility
    additional_fields: Optional[Dict[str, Any]] = Field(None, description="Additional proposal fields")

class AssessmentRequest(BaseModel):
    """Assessment request schema"""
    proposal: ProposalSchema = Field(..., description="Proposal to assess")
    cfp: Optional[Dict[str, Any]] = Field(None, description="Optional CFP context")

class KeywordExtractionResult(BaseModel):
    """Result from keyword extraction stage"""
    keywords: List[str] = Field(..., description="Extracted risk keywords")
    confidence: float = Field(..., description="Confidence score (0-1)")

class RiskRankingResult(BaseModel):
    """Result from risk ranking stage"""
    risks: List[Dict[str, str]] = Field(..., description="Ranked risks with reasoning")
    # Format: [{"risk_id": "R.AIR.001", "reasoning": "..."}, ...]
