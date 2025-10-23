"""
Configuration module for LinkedIn Outreach Automation
Contains all settings, constants, and API configurations
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Rate Limiting Configuration
REQUEST_DELAY_SECONDS = 2  # Delay between web requests for ethical scraping
MAX_RETRIES = 3  # Maximum retries for failed requests
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff multiplier

# Quality Thresholds
MIN_CONFIDENCE_SCORE = 60  # Minimum confidence score to generate message
MIN_MESSAGE_WORDS = 150  # Minimum message length
MAX_MESSAGE_WORDS = 200  # Maximum message length
MIN_SUBJECT_WORDS = 6  # Minimum subject line length
MAX_SUBJECT_WORDS = 10  # Maximum subject line length

# Confidence Score Weights
CONFIDENCE_WEIGHTS = {
    "company_website_found": 30,
    "competitive_intel_gathered": 20,
    "technical_audit_completed": 20,
    "executive_context_found": 15,
    "strategic_signals_found": 15
}

# CSV Configuration
REQUIRED_INPUT_COLUMNS = [
    "linkedin_url",
    "first_name",
    "last_name",
    "title",
    "company_name"
]

OPTIONAL_INPUT_COLUMNS = [
    "notes",
    "company_url",
    "industry",
    "company_size"
]

OUTPUT_COLUMNS = [
    "first_name",
    "last_name",
    "linkedin_url",
    "company_name",
    "company_url",
    "title",
    "industry",
    "subject_line",
    "message_body",
    "hook_type",
    "key_insights",
    "competitive_intel",
    "technical_gaps",
    "geo_readiness_score",
    "confidence_score",
    "audit_date",
    "processing_time_seconds"
]

# Web Scraping Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 10  # Seconds

# Hook Types
HOOK_TYPES = [
    "Competitive Intelligence",
    "Market Shift Observation",
    "Strategic Question",
    "Technical Gap Revelation",
    "Peer Intelligence"
]

# Excluded Domains (not company websites)
EXCLUDED_DOMAINS = [
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "indeed.com",
    "glassdoor.com",
    "crunchbase.com",
    "wikipedia.org"
]

# AI Crawler Bots to Check
AI_CRAWLERS = [
    "GPTBot",
    "ClaudeBot",
    "CCBot",
    "anthropic-ai",
    "ChatGPT-User"
]
