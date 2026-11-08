"""
Application configuration and environment variable management.

Loads environment variables from the project's .env file and
provides configuration values to application components.
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")