"""Offline tests for the AI Assist utility functions."""

from __future__ import annotations

import json

import ai_assist


def test_truncate_text_keeps_both_ends() -> None:
    text = "A" * 40 + "MIDDLE" + "Z" * 40

    result = ai_assist.truncate_text(text, limit=50)

    assert len(result) == 50
    assert result.startswith("A")
    assert result.endswith("Z")
    assert "[повідомлення скорочено]" in result


def test_build_request_messages_has_current_system_prompt_and_bounded_history() -> None:
    messages = [{"role": "system", "content": "old prompt"}]
    messages.extend(
        {"role": "user", "content": f"message {number}"}
        for number in range(ai_assist.MAX_CONTEXT_MESSAGES + 3)
    )

    request_messages = ai_assist.build_request_messages(messages)

    assert request_messages[0]["role"] == "system"
    assert "Поточна дата:" in request_messages[0]["content"]
    assert len(request_messages) == ai_assist.MAX_CONTEXT_MESSAGES + 1
    assert request_messages[1]["content"] == "message 3"


def test_prepare_text_file_attachment_is_bounded(tmp_path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Початок\n" + "x" * 6_000 + "\nКінець", encoding="utf-8")

    attachment = ai_assist.prepare_file_attachment(file_path)

    assert "Прикріплений файл: notes.txt" in attachment
    assert "Початок" in attachment
    assert "Кінець" in attachment
    assert "[повідомлення скорочено]" in attachment


def test_build_file_request_stays_within_message_limit() -> None:
    attachment = "file text\n" + "x" * ai_assist.MAX_FILE_TEXT_CHARS
    request = ai_assist.build_file_request("task" * 1_000, attachment)

    assert len(request) <= ai_assist.MAX_MESSAGE_CHARS
    assert "Завдання користувача" in request
    assert "file text" in request


def test_extract_rate_limits_reads_response_headers() -> None:
    headers = {
        "x-ratelimit-remaining-requests": "249",
        "x-ratelimit-limit-requests": "250",
        "x-ratelimit-reset-requests": "5m",
        "x-ratelimit-remaining-tokens": "69000",
    }

    limits = ai_assist.extract_rate_limits(headers)

    assert limits == [
        "Запити: залишилось 249 з 250; оновлення через 5m",
        "Токени: залишилось 69000",
    ]


def test_save_chat_history_writes_readable_json(tmp_path) -> None:
    history_path = tmp_path / "chat.json"
    messages = [{"role": "user", "content": "Привіт"}]

    ai_assist.save_chat_history(history_path, messages)

    payload = json.loads(history_path.read_text(encoding="utf-8"))
    assert payload["format_version"] == 1
    assert payload["model"] == ai_assist.GROQ_MODEL
    assert payload["messages"] == messages
