# Risk Assessment Engine Configuration

# Service Configuration
SERVICE_NAME = "risk-assessment-service"
SERVICE_PORT = 5005
SERVICE_HOST = "0.0.0.0"

# LLM Configuration
LLM_PROVIDER = "gemini"
LLM_MODEL = "gemini-2.0-flash"
LLM_TEMPERATURE = 0
LLM_MAX_TOKENS = 2048

# Database Configuration
DATABASE_SERVICE_URL = "http://localhost:5001"
DATABASE_TIMEOUT = 30

# Assessment Configuration
TOP_N_RISKS = 3
MAX_CANDIDATE_RISKS = 30

# Logging Configuration
LOG_LEVEL = "INFO"
