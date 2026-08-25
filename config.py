"""Configuration loaded from environment variables and a local .env file."""

import os
from pathlib import Path


def load_dotenv() -> None:
    """Load simple KEY=VALUE values from the adjacent local .env file.

    Existing system environment variables are preserved and take priority.
    This makes it possible to configure a deployed app without editing .env.
    """
    dotenv_path = Path(__file__).with_name(".env")

    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq/compound-mini")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Ти корисний та точний асистент.",
)
