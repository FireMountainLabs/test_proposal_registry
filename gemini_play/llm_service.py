# Gemini LLM Service

import os
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv
from models import KeywordExtractionResult, RiskRankingResult, Risk
from prompts import format_keyword_extraction_prompt, format_risk_ranking_prompt, format_candidate_risks
import config

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiLLMService:
    """Gemini LLM integration with anti-hallucination"""
    
    def __init__(self, api_key: str = None, model: str = None, temperature: float = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = model or config.LLM_MODEL
        self.temperature = temperature or config.LLM_TEMPERATURE
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Create model instance
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini LLM service with model: {self.model_name}")
    
    def extract_keywords(self, proposal: Dict[str, Any]) -> KeywordExtractionResult:
        """
        Stage 1: Extract risk themes from proposal
        
        Args:
            proposal: Proposal dictionary with description and other fields
            
        Returns:
            KeywordExtractionResult with extracted keywords
        """
        try:
            # Convert proposal to text
            proposal_text = self._format_proposal_text(proposal)
            
            # Create prompt
            prompt = format_keyword_extraction_prompt(proposal_text)
            
            logger.info("Extracting keywords from proposal")
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=config.LLM_MAX_TOKENS,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            result_data = json.loads(response.text)
            
            # Validate response structure
            if "keywords" not in result_data or "confidence" not in result_data:
                raise ValueError("Invalid response format from LLM")
            
            keywords = result_data["keywords"]
            confidence = float(result_data["confidence"])
            
            # Validate keywords
            if not isinstance(keywords, list) or len(keywords) == 0:
                raise ValueError("No keywords extracted")
            
            logger.info(f"Extracted keywords: {keywords} (confidence: {confidence})")
            
            return KeywordExtractionResult(
                keywords=keywords,
                confidence=confidence
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response.text}")
            raise Exception("Invalid JSON response from LLM")
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            raise
    
    def rank_and_select(self, proposal: Dict[str, Any], risks: List[Risk]) -> RiskRankingResult:
        """
        Stage 2: Rank filtered risks and select top 3
        
        Args:
            proposal: Proposal dictionary
            risks: List of candidate risks (should be ~20-30)
            
        Returns:
            RiskRankingResult with top 3 risks and reasoning
        """
        try:
            # Limit candidate risks to prevent context overflow
            if len(risks) > config.MAX_CANDIDATE_RISKS:
                risks = risks[:config.MAX_CANDIDATE_RISKS]
                logger.warning(f"Limited candidate risks to {config.MAX_CANDIDATE_RISKS}")
            
            # Format proposal text
            proposal_text = self._format_proposal_text(proposal)
            
            # Format candidate risks
            candidate_risks_text = format_candidate_risks([
                {
                    "risk_id": r.risk_id,
                    "risk_title": r.risk_title,
                    "risk_description": r.risk_description
                }
                for r in risks
            ])
            
            # Create prompt
            prompt = format_risk_ranking_prompt(proposal_text, candidate_risks_text)
            
            logger.info(f"Ranking {len(risks)} candidate risks")
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=config.LLM_MAX_TOKENS,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            result_data = json.loads(response.text)
            
            # Validate response structure
            if "risks" not in result_data:
                raise ValueError("Invalid response format from LLM")
            
            ranked_risks = result_data["risks"]
            
            # Validate we got exactly 3 risks
            if len(ranked_risks) != config.TOP_N_RISKS:
                raise ValueError(f"Expected {config.TOP_N_RISKS} risks, got {len(ranked_risks)}")
            
            # Validate each risk has required fields
            for risk in ranked_risks:
                if "risk_id" not in risk or "reasoning" not in risk:
                    raise ValueError("Invalid risk format in LLM response")
                
                # Validate risk_id exists in candidate risks
                risk_id = risk["risk_id"]
                if not any(r.risk_id == risk_id for r in risks):
                    raise ValueError(f"LLM selected invalid risk_id: {risk_id}")
            
            logger.info(f"Successfully ranked risks: {[r['risk_id'] for r in ranked_risks]}")
            
            return RiskRankingResult(risks=ranked_risks)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response.text}")
            raise Exception("Invalid JSON response from LLM")
        except Exception as e:
            logger.error(f"Error ranking risks: {e}")
            raise
    
    def _format_proposal_text(self, proposal: Dict[str, Any]) -> str:
        """Format proposal dictionary into readable text"""
        parts = []
        
        if proposal.get("proposal_title"):
            parts.append(f"Title: {proposal['proposal_title']}")
        
        if proposal.get("description"):
            parts.append(f"Description: {proposal['description']}")
        
        if proposal.get("technical_approach"):
            parts.append(f"Technical Approach: {proposal['technical_approach']}")
        
        if proposal.get("data_sources"):
            sources = proposal["data_sources"]
            if isinstance(sources, list):
                parts.append(f"Data Sources: {', '.join(sources)}")
            else:
                parts.append(f"Data Sources: {sources}")
        
        if proposal.get("deployment"):
            parts.append(f"Deployment: {proposal['deployment']}")
        
        if proposal.get("data_governance"):
            parts.append(f"Data Governance: {proposal['data_governance']}")
        
        if proposal.get("model_governance"):
            parts.append(f"Model Governance: {proposal['model_governance']}")
        
        if proposal.get("security_measures"):
            parts.append(f"Security Measures: {proposal['security_measures']}")
        
        # Add any additional fields
        if proposal.get("additional_fields"):
            for key, value in proposal["additional_fields"].items():
                parts.append(f"{key}: {value}")
        
        return "\n\n".join(parts)
    
    def health_check(self) -> bool:
        """Check if Gemini API is accessible"""
        try:
            # Simple test request
            response = self.model.generate_content(
                "Say 'OK' if you can respond",
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=10
                )
            )
            return "OK" in response.text
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False
