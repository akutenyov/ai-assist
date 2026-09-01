"""Centralized limits and static labels used by the application."""

from __future__ import annotations

from typing import Final


MAX_CONTEXT_MESSAGES: Final = 12
MAX_MESSAGE_CHARS: Final = 6_000
MAX_SEARCH_SOURCES: Final = 5
CHAT_HISTORY_DIRECTORY: Final = "chats"
MAX_FILE_BYTES: Final = 5 * 1024 * 1024
MAX_FILE_TEXT_CHARS: Final = 4_500
MAX_FILE_PROMPT_CHARS: Final = 800
MAX_SPREADSHEET_ROWS: Final = 200
SUPPORTED_FILE_TYPES: Final = {
    ".txt": "текстовий файл",
    ".md": "Markdown",
    ".py": "Python-код",
    ".json": "JSON",
    ".csv": "CSV-таблиця",
    ".log": "журнал",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".html": "HTML",
    ".pdf": "PDF із текстовим шаром",
    ".docx": "Word DOCX",
    ".xlsx": "Excel XLSX",
}
WEEKDAYS_UA: Final = (
    "понеділок",
    "вівторок",
    "середа",
    "четвер",
    "п’ятниця",
    "субота",
    "неділя",
)
