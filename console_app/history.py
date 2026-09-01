"""Local JSON chat-history persistence and discovery."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from config import GROQ_MODEL

from .constants import CHAT_HISTORY_DIRECTORY
from .logging_setup import PROJECT_DIRECTORY


def create_chat_history_path() -> Path:
    """Return a unique JSON destination for one chat session."""
    directory = PROJECT_DIRECTORY / CHAT_HISTORY_DIRECTORY
    directory.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")

    return directory / f"chat_{timestamp}.json"


def save_chat_history(history_path: Path, messages: list[dict[str, str]]) -> None:
    """Atomically write local chat history without API credentials."""
    payload = {
        "format_version": 1,
        "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": GROQ_MODEL,
        "messages": messages,
    }
    temporary_path = history_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_path.replace(history_path)


def list_saved_chats(limit: int = 10) -> list[tuple[Path, datetime]]:
    """Return the newest saved chats without reading their private content."""
    directory = PROJECT_DIRECTORY / CHAT_HISTORY_DIRECTORY
    chat_files = sorted(
        directory.glob("chat_*.json") if directory.exists() else [],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return [
        (path, datetime.fromtimestamp(path.stat().st_mtime))
        for path in chat_files[:limit]
    ]
