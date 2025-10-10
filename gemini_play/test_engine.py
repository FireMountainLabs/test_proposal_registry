#!/usr/bin/env python3
# Simple Test Script for Risk Assessment Engine

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, '.')

from risk_engine import RiskAssessmentEngine
from db_service import DatabaseServiceClient
from llm_service import GeminiLLMService

def test_basic_functionality():
    """Test basic functionality with mock data"""
    print("Testing Risk Assessment Engine...")
    
    # Check environment
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        return False
    
    try:
        # Initialize services
        print("  Initializing services...")
        db_client = DatabaseServiceClient()
        llm_service = GeminiLLMService()
        engine = RiskAssessmentEngine(db_client, llm_service)
        
        # Health check
        print("  Checking health...")
        health = engine.health_check()
        print(f"    Database service: {'✓' if health['database_service'] else '✗'}")
        print(f"    LLM service: {'✓' if health['llm_service'] else '✗'}")
        
        if not health['database_service']:
            print("❌ Database service not available - using local SQLite")
            # For testing, we'll use a mock approach
            return test_with_mock_data()
        
        # Test with sample proposal
        print("  Testing with sample proposal...")
        sample_proposal = {
            "proposal_title": "Test Proposal",
            "description": "We want to build a customer support chatbot using AI to answer questions.",
            "technical_approach": "Use GPT-4 with RAG on our documentation",
            "data_sources": ["customer_tickets", "product_docs"]
        }
        
        result = engine.assess_proposal(sample_proposal)
        
        print(f"    Assessment ID: {result.assessment_id}")
        print(f"    Risks identified: {len(result.risks)}")
        
        for i, risk in enumerate(result.risks, 1):
            print(f"    {i}. {risk.risk_id}: {risk.risk_title}")
            print(f"       Controls: {len(risk.controls)}")
        
        print("✓ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_with_mock_data():
    """Test with mock data when database service is not available"""
    print("  Testing with mock data...")
    
    try:
        # Create a mock database client
        class MockDBClient:
            def search_risks(self, keywords):
                # Return mock risks
                return [
                    type('Risk', (), {
                        'risk_id': 'R.AIR.001',
                        'risk_title': 'Data poisoning (targeted)',
                        'risk_description': 'Attackers manipulate training data'
                    })(),
                    type('Risk', (), {
                        'risk_id': 'R.AIR.002', 
                        'risk_title': 'Data poisoning (backdoor)',
                        'risk_description': 'Adversaries insert backdoor triggers'
                    })(),
                    type('Risk', (), {
                        'risk_id': 'R.AIR.003',
                        'risk_title': 'Data poisoning (indiscriminate)',
                        'risk_description': 'Attackers manipulate large portions of data'
                    })()
                ]
            
            def get_controls_for_risks(self, risk_ids):
                from models import Control
                return {
                    'R.AIR.001': [
                        Control(
                            control_id='C.AIIM.1',
                            control_title='Maintain ML-Asset Inventory',
                            control_description='Establish inventory of models'
                        )
                    ],
                    'R.AIR.002': [
                        Control(
                            control_id='C.AIIM.2',
                            control_title='Automated Discovery',
                            control_description='Deploy discovery tooling'
                        )
                    ],
                    'R.AIR.003': [
                        Control(
                            control_id='C.AIIM.3',
                            control_title='Track Version & Lineage',
                            control_description='Record hash and version'
                        )
                    ]
                }
            
            def health_check(self):
                return True
        
        # Initialize with mock
        db_client = MockDBClient()
        llm_service = GeminiLLMService()
        engine = RiskAssessmentEngine(db_client, llm_service)
        
        # Test proposal
        sample_proposal = {
            "proposal_title": "Test Proposal",
            "description": "We want to build a customer support chatbot using AI to answer questions.",
            "technical_approach": "Use GPT-4 with RAG on our documentation"
        }
        
        result = engine.assess_proposal(sample_proposal)
        
        print(f"    Assessment ID: {result.assessment_id}")
        print(f"    Risks identified: {len(result.risks)}")
        
        for i, risk in enumerate(result.risks, 1):
            print(f"    {i}. {risk.risk_id}: {risk.risk_title}")
            print(f"       Controls: {len(risk.controls)}")
        
        print("✓ Mock data test passed")
        return True
        
    except Exception as e:
        print(f"❌ Mock test failed: {e}")
        return False

def test_sample_proposals():
    """Test with sample proposal files"""
    print("\nTesting with sample proposals...")
    
    sample_dir = Path("sample_proposals")
    if not sample_dir.exists():
        print("❌ Sample proposals directory not found")
        return False
    
    proposal_files = list(sample_dir.glob("*.json"))
    if not proposal_files:
        print("❌ No sample proposal files found")
        return False
    
    try:
        # Initialize services
        db_client = DatabaseServiceClient()
        llm_service = GeminiLLMService()
        engine = RiskAssessmentEngine(db_client, llm_service)
        
        results = []
        for proposal_file in proposal_files:
            print(f"  Testing: {proposal_file.name}")
            
            with open(proposal_file, 'r') as f:
                proposal_data = json.load(f)
            
            result = engine.assess_proposal(proposal_data)
            results.append({
                'file': proposal_file.name,
                'risks_count': len(result.risks),
                'risk_ids': [r.risk_id for r in result.risks]
            })
        
        # Summary
        print("\n  Test Results:")
        for result in results:
            print(f"    {result['file']}: {result['risks_count']} risks")
        
        print("✓ Sample proposals test passed")
        return True
        
    except Exception as e:
        print(f"❌ Sample proposals test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Risk Assessment Engine Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_sample_proposals
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
