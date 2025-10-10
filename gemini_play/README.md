# Risk Assessment Engine

A prototype implementation of the AI/ML Risk Assessment Microservice for dashboard_zero.

## Overview

This implementation provides a two-stage LLM approach to assess AI/ML proposals and identify the top 3 relevant risks with corresponding controls.

## Architecture

- **Stage 1**: Gemini LLM extracts risk keywords from proposal
- **Stage 2**: Database service queries risks, LLM ranks and selects top 3
- **Enrichment**: Controls are fetched and mapped to each risk

## Files Created

- `config.py` - Configuration management
- `models.py` - Pydantic data models
- `prompts.py` - LLM prompt templates
- `db_service.py` - Database service client
- `llm_service.py` - Gemini LLM integration
- `risk_engine.py` - Core assessment logic
- `app.py` - FastAPI application
- `cli.py` - Command-line interface
- `test_engine.py` - Test script
- `sample_proposals/` - Test proposal files

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set Gemini API key:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Usage

### CLI Tool

```bash
# Check health
python cli.py health

# Assess a proposal file
python cli.py assess --proposal-file sample_proposals/medium_proposal.json

# Assess proposal text directly
python cli.py assess --proposal-text "We want to build a chatbot"

# Test with sample proposals
python cli.py test

# Create sample proposals
python cli.py create-samples
```

### API Server

```bash
# Start the API server
python app.py

# Or with uvicorn
uvicorn app:app --host 0.0.0.0 --port 5005
```

### API Endpoints

- `GET /api/health` - Health check
- `POST /api/v1/assess-risks` - Full assessment
- `POST /api/v1/assess-risks-simple` - Simplified assessment
- `GET /api/models` - List available Gemini models

### Testing

```bash
# Run test suite
python test_engine.py
```

## Sample Proposals

Three sample proposals are included:

1. **Weak Proposal** - Minimal detail, vague description
2. **Medium Proposal** - Moderate detail with some technical specifics
3. **Strong Proposal** - Comprehensive with governance and security measures

## Security Features

- **No Direct DB Access**: LLM never accesses database directly
- **Input Sanitization**: Keywords are sanitized before database queries
- **Risk ID Validation**: All risk IDs are validated against known format
- **Structured Output**: JSON schema enforcement prevents hallucinations

## Next Steps

1. Test with real database service
2. Migrate to dashboard_zero microservice
3. Add Docker configuration
4. Implement functional tests
5. Add OpenSearch integration

## Configuration

Key configuration options in `config.py`:

- `SERVICE_PORT = 5005` - API server port
- `LLM_MODEL = "gemini-2.0-flash"` - Gemini model
- `LLM_TEMPERATURE = 0` - Deterministic output
- `TOP_N_RISKS = 3` - Number of risks to return
- `MAX_CANDIDATE_RISKS = 30` - Max risks for LLM ranking

## Dependencies

- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `google-generativeai` - Gemini LLM
- `python-dotenv` - Environment variables
- `requests` - HTTP client