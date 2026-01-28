"""
Research paper configuration and constants
"""

# ================== CONSTANTS ==================

DEFAULT_LOAD_MAX_DOCS = 8
DEFAULT_PER_TOPIC = 5
DEFAULT_TOP_K = 10

DEFAULT_TOPICS = [
    "machine learning",
    "deep learning",
    "generative ai",
    "transformers",
    "computer vision",
    "natural language processing",
    "reinforcement learning",
    "retrieval-augmented generation",
    "agentic AI",
    "model context protocol (MCP)",
]

# LLM Configuration
DEFAULT_LLM_MODEL = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE = 0.2

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
