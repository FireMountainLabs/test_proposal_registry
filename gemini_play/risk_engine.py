# Risk Assessment Engine

import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import RiskAssessmentResult, RiskAssessment, Control, ProposalSchema
from db_service import DatabaseServiceClient
from llm_service import GeminiLLMService
import config

logger = logging.getLogger(__name__)

class RiskAssessmentEngine:
    """Orchestrates two-stage assessment"""
    
    def __init__(self, db_client: DatabaseServiceClient = None, llm_service: GeminiLLMService = None):
        self.db_client = db_client or DatabaseServiceClient()
        self.llm_service = llm_service or GeminiLLMService()
        
        logger.info("Risk Assessment Engine initialized")
    
    def assess_proposal(self, proposal: Dict[str, Any]) -> RiskAssessmentResult:
        """
        Complete risk assessment workflow
        
        Args:
            proposal: Proposal dictionary with description and other fields
            
        Returns:
            RiskAssessmentResult with top 3 risks, explanations, and controls
        """
        try:
            logger.info("Starting risk assessment")
            
            # Stage 1: Extract keywords via LLM
            logger.info("Stage 1: Extracting keywords")
            keyword_result = self.llm_service.extract_keywords(proposal)
            keywords = keyword_result.keywords
            
            # Stage 2: Query database-service with keywords
            logger.info("Stage 2: Querying database for relevant risks")
            candidate_risks = self.db_client.search_risks(keywords)
            
            if not candidate_risks:
                logger.warning("No risks found for keywords, using fallback")
                # Fallback: get some general risks
                candidate_risks = self._get_fallback_risks()
            
            # Stage 3: Rank via LLM
            logger.info("Stage 3: Ranking risks with LLM")
            ranking_result = self.llm_service.rank_and_select(proposal, candidate_risks)
            
            # Stage 4: Enrich with controls
            logger.info("Stage 4: Enriching with controls")
            risk_ids = [r["risk_id"] for r in ranking_result.risks]
            controls_by_risk = self.db_client.get_controls_for_risks(risk_ids)
            
            # Stage 5: Build final result
            logger.info("Stage 5: Building assessment result")
            assessments = []
            
            for ranked_risk in ranking_result.risks:
                risk_id = ranked_risk["risk_id"]
                reasoning = ranked_risk["reasoning"]
                
                # Find the full risk details
                risk_details = None
                for risk in candidate_risks:
                    if risk.risk_id == risk_id:
                        risk_details = risk
                        break
                
                if not risk_details:
                    logger.error(f"Could not find details for risk {risk_id}")
                    continue
                
                # Get controls for this risk
                controls = controls_by_risk.get(risk_id, [])
                
                # Create assessment
                assessment = RiskAssessment(
                    risk_id=risk_id,
                    risk_title=risk_details.risk_title,
                    risk_description=risk_details.risk_description,
                    explanation=reasoning,
                    controls=controls
                )
                
                assessments.append(assessment)
            
            # Ensure we have exactly 3 assessments
            if len(assessments) != config.TOP_N_RISKS:
                logger.warning(f"Expected {config.TOP_N_RISKS} assessments, got {len(assessments)}")
                # Pad with empty assessments if needed
                while len(assessments) < config.TOP_N_RISKS:
                    assessments.append(RiskAssessment(
                        risk_id="N/A",
                        risk_title="Assessment Error",
                        risk_description="Could not assess this risk",
                        explanation="Assessment failed",
                        controls=[]
                    ))
            
            result = RiskAssessmentResult(risks=assessments)
            
            logger.info(f"Risk assessment completed: {len(assessments)} risks identified")
            return result
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            # Return error result
            error_assessments = [
                RiskAssessment(
                    risk_id="ERROR",
                    risk_title="Assessment Error",
                    risk_description="An error occurred during risk assessment",
                    explanation=f"Error: {str(e)}",
                    controls=[]
                )
                for _ in range(config.TOP_N_RISKS)
            ]
            return RiskAssessmentResult(risks=error_assessments)
    
    def _get_fallback_risks(self) -> List:
        """Get fallback risks when keyword search fails"""
        try:
            # Try to get some general risks from the database
            fallback_keywords = ["data", "model", "security", "privacy", "governance"]
            return self.db_client.search_risks(fallback_keywords)
        except Exception as e:
            logger.error(f"Fallback risk search failed: {e}")
            # Return empty list - will be handled by caller
            return []
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all dependencies"""
        return {
            "database_service": self.db_client.health_check(),
            "llm_service": self.llm_service.health_check()
        }
