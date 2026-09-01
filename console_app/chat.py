"""Conversation construction and context-size management."""

from __future__ import annotations

from datetime import date

from config import SYSTEM_PROMPT

from .constants import MAX_CONTEXT_MESSAGES, MAX_MESSAGE_CHARS, WEEKDAYS_UA


def build_system_prompt() -> str:
    """Add the current local date to make relative dates less ambiguous."""
    today = date.today()
    current_date = today.strftime("%d.%m.%Y")
    weekday = WEEKDAYS_UA[today.weekday()]

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Поточна дата: {current_date}, {weekday}. "
        "Інтерпретуй неповні дати (наприклад, '16-08') відносно цієї "
        "дати. Для прогнозів і новин перевіряй актуальні дані веб-пошуком."
    )


def truncate_text(text: str, limit: int = MAX_MESSAGE_CHARS) -> str:
    """Preserve both ends of an oversized message within a safe limit."""
    if len(text) <= limit:
        return text

    marker = "\n...[повідомлення скорочено]...\n"
    remaining = limit - len(marker)
    start_length = remaining // 2
    end_length = remaining - start_length

    return f"{text[:start_length]}{marker}{text[-end_length:]}"


def build_request_messages(
    messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Build a bounded payload with a freshly generated system prompt."""
    dialogue = messages[1:][-MAX_CONTEXT_MESSAGES:]

    return [
        {"role": "system", "content": truncate_text(build_system_prompt())},
        *[
            {
                "role": message["role"],
                "content": truncate_text(message["content"]),
            }
            for message in dialogue
        ],
    ]


def new_conversation() -> list[dict[str, str]]:
    """Create a fresh dialogue with its initial system instruction."""
    return [{"role": "system", "content": build_system_prompt()}]
