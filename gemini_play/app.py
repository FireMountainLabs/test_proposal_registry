# FastAPI Risk Assessment Service

import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import AssessmentRequest, RiskAssessmentResult, ProposalSchema
from risk_engine import RiskAssessmentEngine
from db_service import DatabaseServiceClient
from llm_service import GeminiLLMService
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global engine instance
risk_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global risk_engine
    
    # Startup
    logger.info("Starting Risk Assessment Service")
    
    try:
        # Initialize services
        db_client = DatabaseServiceClient()
        llm_service = GeminiLLMService()
        risk_engine = RiskAssessmentEngine(db_client, llm_service)
        
        # Health check
        health_status = risk_engine.health_check()
        logger.info(f"Service health: {health_status}")
        
        if not all(health_status.values()):
            logger.warning("Some services are not healthy")
        
        logger.info("Risk Assessment Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Risk Assessment Service")

# Create FastAPI app
app = FastAPI(
    title="Risk Assessment Service",
    description="AI/ML Proposal Risk Assessment Microservice",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_risk_engine() -> RiskAssessmentEngine:
    """Dependency to get risk engine instance"""
    if risk_engine is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return risk_engine

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        if risk_engine is None:
            return {"status": "unhealthy", "message": "Service not initialized"}
        
        health_status = risk_engine.health_check()
        
        if all(health_status.values()):
            return {
                "status": "healthy",
                "service": config.SERVICE_NAME,
                "version": "1.0.0",
                "dependencies": health_status
            }
        else:
            return {
                "status": "degraded",
                "service": config.SERVICE_NAME,
                "version": "1.0.0",
                "dependencies": health_status
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/api/v1/assess-risks", response_model=RiskAssessmentResult)
async def assess_risks(
    request: AssessmentRequest,
    engine: RiskAssessmentEngine = Depends(get_risk_engine)
):
    """
    Analyze proposal and return top 3 risks
    
    Request:
    {
      "proposal": {
        "description": "Proposal description",
        "technical_approach": "Technical approach",
        ...
      },
      "cfp": {...}  // optional context
    }
    
    Response:
    {
      "assessment_id": "uuid",
      "timestamp": "...",
      "risks": [
        {
          "risk_id": "R.AIR.XXX",
          "risk_title": "...",
          "risk_description": "...",
          "explanation": "Why this applies...",
          "controls": [
            {"control_id": "C.AIIM.X", "control_title": "..."}
          ]
        }
      ]
    }
    """
    try:
        logger.info(f"Received assessment request for proposal: {request.proposal.proposal_title or 'Untitled'}")
        
        # Convert proposal to dict for processing
        proposal_dict = request.proposal.dict()
        
        # Add CFP context if provided
        if request.cfp:
            proposal_dict["cfp_context"] = request.cfp
        
        # Perform assessment
        result = engine.assess_proposal(proposal_dict)
        
        logger.info(f"Assessment completed: {result.assessment_id}")
        return result
        
    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

@app.post("/api/v1/assess-risks-simple", response_model=RiskAssessmentResult)
async def assess_risks_simple(
    proposal: ProposalSchema,
    engine: RiskAssessmentEngine = Depends(get_risk_engine)
):
    """
    Simplified endpoint that takes proposal directly
    """
    try:
        logger.info(f"Received simple assessment request for proposal: {proposal.proposal_title or 'Untitled'}")
        
        # Convert proposal to dict for processing
        proposal_dict = proposal.dict()
        
        # Perform assessment
        result = engine.assess_proposal(proposal_dict)
        
        logger.info(f"Simple assessment completed: {result.assessment_id}")
        return result
        
    except Exception as e:
        logger.error(f"Simple assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

@app.get("/api/models")
async def list_models():
    """List available Gemini models"""
    try:
        import google.generativeai as genai
        
        models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description
                })
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": config.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "assess": "/api/v1/assess-risks",
            "assess_simple": "/api/v1/assess-risks-simple",
            "models": "/api/models"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=False
    )
