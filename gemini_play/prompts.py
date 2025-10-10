# Risk Assessment Prompt Templates

KEYWORD_EXTRACTION_PROMPT = """
You are an AI/ML security risk assessor. Your task is to analyze a proposal and extract key risk themes that would be relevant for AI/ML security assessment.

PROPOSAL:
{proposal_text}

INSTRUCTIONS:
1. Read the proposal carefully
2. Identify the main AI/ML use case described
3. Extract 3-5 key risk themes that would be relevant for this type of AI/ML system
4. Focus on security, privacy, governance, and operational risks
5. Use specific, searchable terms

RISK THEMES TO CONSIDER:
- data privacy
- model deployment
- training data
- supply chain
- model governance
- access control
- data poisoning
- model bias
- compliance
- third party

Return ONLY a JSON object with this exact format:
{{
  "keywords": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "confidence": 0.85
}}

CRITICAL: Return ONLY valid JSON. No additional text or explanation.
"""

RISK_RANKING_PROMPT = """
You are an AI/ML security risk assessor. Your task is to analyze a proposal and select the top 3 most relevant risks from a list of candidate risks.

PROPOSAL:
{proposal_text}

CANDIDATE RISKS:
{candidate_risks}

INSTRUCTIONS:
1. Analyze the proposal's AI/ML use case, data sources, deployment approach, and security measures
2. For each candidate risk, assess how relevant it is to this specific proposal
3. Consider the likelihood and impact of each risk for this use case
4. Select the TOP 3 most relevant risks
5. For each selected risk, provide a clear explanation of why it applies

CRITICAL CONSTRAINTS:
- You MUST select exactly 3 risks
- You MUST only select from the candidate risks list above
- Risk IDs must match exactly (e.g., "R.AIR.001")
- Provide substantive explanations (at least 2 sentences each)

Return ONLY a JSON object with this exact format:
{{
  "risks": [
    {{
      "risk_id": "R.AIR.XXX",
      "reasoning": "Detailed explanation of why this risk applies to the proposal..."
    }},
    {{
      "risk_id": "R.AIR.YYY", 
      "reasoning": "Detailed explanation of why this risk applies to the proposal..."
    }},
    {{
      "risk_id": "R.AIR.ZZZ",
      "reasoning": "Detailed explanation of why this risk applies to the proposal..."
    }}
  ]
}}

CRITICAL: Return ONLY valid JSON. No additional text or explanation.
"""

def format_keyword_extraction_prompt(proposal_text: str) -> str:
    """Format the keyword extraction prompt with proposal text"""
    return KEYWORD_EXTRACTION_PROMPT.format(proposal_text=proposal_text)

def format_risk_ranking_prompt(proposal_text: str, candidate_risks: str) -> str:
    """Format the risk ranking prompt with proposal text and candidate risks"""
    return RISK_RANKING_PROMPT.format(
        proposal_text=proposal_text,
        candidate_risks=candidate_risks
    )

def format_candidate_risks(risks: list) -> str:
    """Format candidate risks for the prompt"""
    formatted_risks = []
    for risk in risks:
        formatted_risks.append(
            f"ID: {risk['risk_id']}\n"
            f"Title: {risk['risk_title']}\n"
            f"Description: {risk['risk_description']}\n"
        )
    return "\n".join(formatted_risks)
