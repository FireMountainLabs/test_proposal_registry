#!/usr/bin/env python3
# Risk Assessment CLI Tool

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from risk_engine import RiskAssessmentEngine
from db_service import DatabaseServiceClient
from llm_service import GeminiLLMService
from models import ProposalSchema

def load_proposal_from_file(file_path: str) -> Dict[str, Any]:
    """Load proposal from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {file_path}: {e}")
        sys.exit(1)

def load_proposal_from_text(text: str) -> Dict[str, Any]:
    """Create proposal from text input"""
    return {
        "description": text,
        "proposal_title": "CLI Input Proposal"
    }

def print_assessment_result(result):
    """Print assessment result in a readable format"""
    print("\n" + "="*80)
    print(f"RISK ASSESSMENT RESULT")
    print("="*80)
    print(f"Assessment ID: {result.assessment_id}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Risks Identified: {len(result.risks)}")
    
    for i, risk in enumerate(result.risks, 1):
        print(f"\n{i}. RISK: {risk.risk_title}")
        print(f"   ID: {risk.risk_id}")
        print(f"   Description: {risk.risk_description}")
        print(f"   Explanation: {risk.explanation}")
        
        if risk.controls:
            print(f"   Controls ({len(risk.controls)}):")
            for control in risk.controls:
                print(f"     - {control.control_id}: {control.control_title}")
        else:
            print(f"   Controls: None identified")
    
    print("\n" + "="*80)

def assess_command(args):
    """Handle assess command"""
    try:
        # Load proposal
        if args.proposal_file:
            proposal_data = load_proposal_from_file(args.proposal_file)
        elif args.proposal_text:
            proposal_data = load_proposal_from_text(args.proposal_text)
        else:
            print("Error: Must provide either --proposal-file or --proposal-text")
            sys.exit(1)
        
        # Initialize services
        print("Initializing risk assessment engine...")
        db_client = DatabaseServiceClient()
        llm_service = GeminiLLMService()
        engine = RiskAssessmentEngine(db_client, llm_service)
        
        # Perform assessment
        print("Performing risk assessment...")
        result = engine.assess_proposal(proposal_data)
        
        # Output result
        if args.output_format == "json":
            print(json.dumps(result.dict(), indent=2, default=str))
        else:
            print_assessment_result(result)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def health_command(args):
    """Handle health command"""
    try:
        db_client = DatabaseServiceClient()
        llm_service = GeminiLLMService()
        engine = RiskAssessmentEngine(db_client, llm_service)
        
        health_status = engine.health_check()
        
        print("Health Check Results:")
        print("-" * 40)
        for service, status in health_status.items():
            status_str = "✓ Healthy" if status else "✗ Unhealthy"
            print(f"{service}: {status_str}")
        
        if all(health_status.values()):
            print("\nOverall Status: ✓ All services healthy")
        else:
            print("\nOverall Status: ✗ Some services unhealthy")
            sys.exit(1)
        
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

def test_command(args):
    """Handle test command"""
    try:
        # Load test proposals
        test_dir = Path("sample_proposals")
        if not test_dir.exists():
            print(f"Error: Test directory not found: {test_dir}")
            print("Run 'python cli.py create-samples' first")
            sys.exit(1)
        
        proposal_files = list(test_dir.glob("*.json"))
        if not proposal_files:
            print(f"Error: No proposal files found in {test_dir}")
            sys.exit(1)
        
        # Initialize services
        print("Initializing risk assessment engine...")
        db_client = DatabaseServiceClient()
        llm_service = GeminiLLMService()
        engine = RiskAssessmentEngine(db_client, llm_service)
        
        # Test each proposal
        results = []
        for proposal_file in proposal_files:
            print(f"\nTesting: {proposal_file.name}")
            proposal_data = load_proposal_from_file(str(proposal_file))
            
            result = engine.assess_proposal(proposal_data)
            results.append({
                "file": proposal_file.name,
                "assessment_id": result.assessment_id,
                "risks_count": len(result.risks),
                "risk_ids": [r.risk_id for r in result.risks]
            })
            
            if args.verbose:
                print_assessment_result(result)
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for result in results:
            print(f"{result['file']}: {result['risks_count']} risks - {result['risk_ids']}")
        
        print(f"\nTotal tests: {len(results)}")
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

def create_samples_command(args):
    """Handle create-samples command"""
    try:
        # Create sample proposals directory
        sample_dir = Path("sample_proposals")
        sample_dir.mkdir(exist_ok=True)
        
        # Sample proposals
        samples = {
            "weak_proposal.json": {
                "cfp_id": "CFP-003",
                "proposal_title": "AI for Everything",
                "description": "We want to use AI to improve our business operations.",
                "technical_approach": "We'll use machine learning models."
            },
            "medium_proposal.json": {
                "cfp_id": "CFP-002",
                "proposal_title": "Customer Support Chatbot",
                "description": "Deploy an AI chatbot using RAG to answer customer questions based on our documentation.",
                "technical_approach": "Fine-tune GPT-4 on our support tickets, use vector database for retrieval.",
                "data_sources": ["customer_tickets", "product_docs"],
                "deployment": "Cloud-hosted API"
            },
            "strong_proposal.json": {
                "cfp_id": "CFP-001",
                "proposal_title": "Secure AI-Powered Fraud Detection System",
                "description": "Build a real-time fraud detection system using ensemble ML models with explainability.",
                "technical_approach": "Ensemble of XGBoost and neural networks, SHAP for explainability, A/B testing framework.",
                "data_sources": ["transaction_history", "user_behavior", "third_party_risk_scores"],
                "data_governance": "PII anonymization, data retention policies, audit logging",
                "model_governance": "Model versioning, performance monitoring, bias testing",
                "deployment": "Kubernetes cluster with canary deployments",
                "security_measures": "Input validation, rate limiting, encrypted data at rest and in transit"
            }
        }
        
        # Write sample files
        for filename, data in samples.items():
            filepath = sample_dir / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Created: {filepath}")
        
        print(f"\nCreated {len(samples)} sample proposals in {sample_dir}")
        print("Run 'python cli.py test' to test them")
        
    except Exception as e:
        print(f"Error creating samples: {e}")
        sys.exit(1)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Risk Assessment CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py assess --proposal-file sample_proposals/medium_proposal.json
  python cli.py assess --proposal-text "We want to build a chatbot"
  python cli.py health
  python cli.py test
  python cli.py create-samples
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Assess command
    assess_parser = subparsers.add_parser('assess', help='Assess a proposal')
    assess_group = assess_parser.add_mutually_exclusive_group(required=True)
    assess_group.add_argument('--proposal-file', help='Path to proposal JSON file')
    assess_group.add_argument('--proposal-text', help='Proposal text directly')
    assess_parser.add_argument('--output-format', choices=['text', 'json'], default='text',
                              help='Output format (default: text)')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check service health')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test with sample proposals')
    test_parser.add_argument('--verbose', action='store_true', help='Show detailed results')
    
    # Create samples command
    samples_parser = subparsers.add_parser('create-samples', help='Create sample proposals')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check for required environment variable
    if not os.getenv('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is required")
        print("Set it with: export GEMINI_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    # Route to appropriate command handler
    if args.command == 'assess':
        assess_command(args)
    elif args.command == 'health':
        health_command(args)
    elif args.command == 'test':
        test_command(args)
    elif args.command == 'create-samples':
        create_samples_command(args)

if __name__ == "__main__":
    main()
