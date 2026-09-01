"""Groq request construction and response metadata extraction."""

from __future__ import annotations

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL

from .chat import build_request_messages
from .constants import MAX_SEARCH_SOURCES


def create_client() -> Groq:
    """Create the configured Groq client with stable Compound web search."""
    return Groq(
        api_key=GROQ_API_KEY,
        default_headers={"Groq-Model-Version": "2025-07-23"},
    )


def read_field(value: object, field: str) -> object | None:
    """Read a field from either an SDK object or a dictionary."""
    if isinstance(value, dict):
        return value.get(field)

    return getattr(value, field, None)


def extract_search_sources(executed_tools: list[object]) -> list[tuple[str, str]]:
    """Return up to five unique titles and URLs from Groq web search."""
    sources: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    for tool in executed_tools:
        if read_field(tool, "type") not in {"search", "web_search"}:
            continue

        results = read_field(tool, "search_results") or []
        if isinstance(results, dict):
            results = results.get("results", [])

        for result in results:
            url = str(read_field(result, "url") or "").strip()
            if not url or url in seen_urls:
                continue

            title = str(read_field(result, "title") or url)
            sources.append((" ".join(title.split())[:160], url))
            seen_urls.add(url)

            if len(sources) == MAX_SEARCH_SOURCES:
                return sources

    return sources


def get_header(headers: object, name: str) -> str | None:
    """Read a response header without depending on one SDK header type."""
    getter = getattr(headers, "get", None)
    if callable(getter):
        value = getter(name)
        if value is not None:
            return str(value)

    items = getattr(headers, "items", None)
    if callable(items):
        for header_name, value in items():
            if str(header_name).lower() == name.lower():
                return str(value)

    return None


def extract_rate_limits(headers: object) -> list[str]:
    """Format the exact request and token limits reported by Groq."""
    limits: list[str] = []

    for label, suffix in (("Запити", "requests"), ("Токени", "tokens")):
        remaining = get_header(headers, f"x-ratelimit-remaining-{suffix}")
        limit = get_header(headers, f"x-ratelimit-limit-{suffix}")
        reset_after = get_header(headers, f"x-ratelimit-reset-{suffix}")

        if remaining is None:
            continue

        line = f"{label}: залишилось {remaining}"
        if limit:
            line += f" з {limit}"
        if reset_after:
            line += f"; оновлення через {reset_after}"
        limits.append(line)

    return limits


def request_response(
    client: Groq,
    messages: list[dict[str, str]],
) -> tuple[str, bool, list[tuple[str, str]], list[str]]:
    """Request Groq and return text, search state, sources, and quota details."""
    raw_response = client.chat.completions.with_raw_response.create(
        model=GROQ_MODEL,
        messages=build_request_messages(messages),
    )
    response = raw_response.parse()
    message = response.choices[0].message
    text = (message.content or "").strip() or "Groq не повернув текстової відповіді."

    executed_tools = getattr(message, "executed_tools", None) or []
    web_search_used = any(
        read_field(tool, "type") in {"search", "web_search"}
        for tool in executed_tools
    )

    return (
        text,
        web_search_used,
        extract_search_sources(executed_tools),
        extract_rate_limits(raw_response.headers),
    )
