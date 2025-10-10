# Database Service Client

import requests
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import Risk, Control
import config

logger = logging.getLogger(__name__)

class DatabaseServiceClient:
    """
    Client for existing database-service API
    
    SECURITY: LLM never touches this. Only risk engine uses it.
    All database access via REST API with proper input validation.
    """
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or config.DATABASE_SERVICE_URL
        self.timeout = timeout or config.DATABASE_TIMEOUT
        self.session = requests.Session()
        
    def search_risks(self, keywords: List[str]) -> List[Risk]:
        """
        Search risks via database-service REST API
        GET /api/search?q=keywords
        
        Keywords are sanitized strings from LLM output,
        never raw SQL or database commands.
        """
        try:
            # Sanitize keywords - remove any potential SQL injection
            sanitized_keywords = [self._sanitize_keyword(k) for k in keywords]
            
            # Search with individual keywords and combine results
            all_risks = {}
            for keyword in sanitized_keywords[:3]:  # Limit to first 3 keywords
                logger.info(f"Searching risks with keyword: {keyword}")
                
                response = self.session.get(
                    f"{self.base_url}/api/search",
                    params={"q": keyword},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Convert to Risk objects
                for item in data.get("results", []):
                    # Only process risk type results
                    if item.get("type") == "risk":
                        risk_id = item["id"]
                        if risk_id not in all_risks:  # Avoid duplicates
                            all_risks[risk_id] = Risk(
                                risk_id=item["id"],
                                risk_title=item["title"],
                                risk_description=item["description"]
                            )
            
            risks = list(all_risks.values())
            logger.info(f"Found {len(risks)} unique risks for keywords: {sanitized_keywords}")
            return risks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search risks: {e}")
            raise Exception(f"Database service unavailable: {e}")
        except Exception as e:
            logger.error(f"Error searching risks: {e}")
            raise
    
    def get_controls_for_risks(self, risk_ids: List[str]) -> Dict[str, List[Control]]:
        """
        Fetch controls via database-service REST API
        GET /api/relationships?risk_ids=R.AIR.001,R.AIR.002
        
        Risk IDs are validated against known format (R.AIR.XXX)
        before making API call.
        """
        try:
            # Validate risk IDs
            validated_ids = [self._validate_risk_id(rid) for rid in risk_ids]
            
            logger.info(f"Fetching controls for risks: {validated_ids}")
            
            response = self.session.get(
                f"{self.base_url}/api/relationships",
                params={"risk_ids": ",".join(validated_ids)},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to Control objects organized by risk_id
            controls_by_risk = {}
            for risk_id in validated_ids:
                controls_by_risk[risk_id] = []
                
                # Find controls for this risk from the relationships list
                for relationship in data:
                    if (relationship.get("source_id") == risk_id and 
                        relationship.get("relationship_type") == "risk_control"):
                        control_id = relationship.get("target_id")
                        if control_id:
                            # Create a basic control object (we don't have full control details)
                            controls_by_risk[risk_id].append(Control(
                                control_id=control_id,
                                control_title=f"Control {control_id}",
                                control_description=f"Control for risk {risk_id}"
                            ))
            
            logger.info(f"Found controls for {len(controls_by_risk)} risks")
            return controls_by_risk
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch controls: {e}")
            raise Exception(f"Database service unavailable: {e}")
        except Exception as e:
            logger.error(f"Error fetching controls: {e}")
            raise
    
    def get_risk_by_id(self, risk_id: str) -> Optional[Risk]:
        """Get a specific risk by ID"""
        try:
            validated_id = self._validate_risk_id(risk_id)
            
            response = self.session.get(
                f"{self.base_url}/api/risks/{validated_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            
            return Risk(
                risk_id=data["id"],
                risk_title=data["title"],
                risk_description=data["description"]
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get risk {risk_id}: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if database service is healthy"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _sanitize_keyword(self, keyword: str) -> str:
        """Sanitize keyword to prevent injection attacks"""
        # Remove any characters that could be used for SQL injection
        import re
        # Keep only alphanumeric, spaces, hyphens, underscores
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', keyword)
        # Limit length
        return sanitized[:100]
    
    def _validate_risk_id(self, risk_id: str) -> str:
        """Validate risk ID format"""
        import re
        # Risk IDs should match pattern R.AIR.XXX or similar
        if not re.match(r'^R\.[A-Z]+\.[0-9]+$', risk_id):
            raise ValueError(f"Invalid risk ID format: {risk_id}")
        return risk_id
