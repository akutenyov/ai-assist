"""Application coordinator: commands, state, and user-facing control flow."""

from __future__ import annotations

from pathlib import Path

from groq import APIConnectionError, APIStatusError, RateLimitError
from rich.text import Text

from config import GROQ_API_KEY, GROQ_MODEL

from .chat import new_conversation, truncate_text
from .constants import MAX_FILE_PROMPT_CHARS, MAX_MESSAGE_CHARS
from .files import build_file_request, prepare_file_attachment
from .groq_client import create_client, request_response
from .history import create_chat_history_path, list_saved_chats, save_chat_history
from .logging_setup import LOGGER
from .ui import (
    CONSOLE,
    print_assistant_reply,
    print_banner,
    print_error,
    print_file_capabilities,
    print_help,
    print_rate_limits,
    print_saved_chats,
    print_sources,
)


def validate_configuration() -> None:
    """Stop before any API request when the required credential is missing."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY не заданий. Додайте ключ до файлу .env.")


def discard_failed_prompt(messages: list[dict[str, str]]) -> None:
    """Remove only an unsent user prompt after a request error.

    Keeping the role check makes cleanup safe if future code changes alter the
    message sequence or an exception happens before a prompt is appended.
    """
    if messages and messages[-1]["role"] == "user":
        messages.pop()


def read_file_command(prompt: str) -> str | None:
    """Confirm and prepare a local file, returning its pending text attachment."""
    print_file_capabilities()
    raw_path = prompt[6:].strip().strip('"').strip("'")

    if not raw_path:
        print_error("Вкажіть шлях після команди /file.", "Шлях не вказано")
        return None

    confirmation = CONSOLE.input(
        "[bold yellow]Прочитати цей файл і підготувати його для Groq?[/] "
        "\\[y/N] "
    ).strip().lower()
    if confirmation not in {"y", "yes", "т", "так"}:
        CONSOLE.print("[dim]Додавання файла скасовано.[/]")
        return None

    try:
        attachment = prepare_file_attachment(Path(raw_path))
    except (OSError, ValueError) as error:
        print_error(str(error), "Файл не додано")
        LOGGER.warning("File attachment rejected: %s", error)
        return None
    except Exception as error:
        print_error(f"Не вдалося обробити файл: {error}", "Помилка обробки файла")
        LOGGER.exception("Unable to prepare file attachment")
        return None

    CONSOLE.print(
        "[bold green](OK) Файл підготовлено.[/] Введіть наступний запит: "
        "наприклад, «Стисло підсумуй документ»."
    )
    LOGGER.info("File attachment prepared; suffix=%s", Path(raw_path).suffix.lower())
    return attachment


def run_chat() -> None:
    """Run the terminal chat loop until the user exits."""
    validate_configuration()
    client = create_client()
    messages = new_conversation()
    history_path = create_chat_history_path()
    pending_attachment: str | None = None

    print_banner(history_path)
    LOGGER.info("Application started; model=%s", GROQ_MODEL)

    while True:
        try:
            prompt = CONSOLE.input("\n[bold cyan]Ви[/] [dim]>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            CONSOLE.print("\n[bold cyan]До побачення![/]")
            LOGGER.info("Application stopped by keyboard or input end")
            return

        if not prompt:
            continue

        command = prompt.lower()
        if command in {"/exit", "/quit", "/q"}:
            CONSOLE.print("[bold cyan]До побачення![/]")
            LOGGER.info("Application stopped by user command")
            return
        if command in {"/help", "help"}:
            print_help()
            continue
        if command in {"/clear", "clear"}:
            messages = new_conversation()
            history_path = create_chat_history_path()
            pending_attachment = None
            CONSOLE.print(
                "[bold green](OK) Почато новий діалог.[/] "
                f"[dim]Історія: chats\\{history_path.name}[/]"
            )
            LOGGER.info("Conversation context cleared; new chat history started")
            continue
        if command in {"/history", "history"}:
            print_saved_chats(list_saved_chats())
            continue
        if command in {"/file", "file"}:
            print_file_capabilities()
            CONSOLE.print("[dim]Приклад: /file D:\\Документи\\звіт.pdf[/]")
            continue
        if command.startswith("/file "):
            attachment = read_file_command(prompt)
            if attachment is not None:
                pending_attachment = attachment
            continue
        if command in {"/remove-file", "remove-file"}:
            if pending_attachment is None:
                CONSOLE.print("[dim]Немає підготовленого файла.[/]")
            else:
                pending_attachment = None
                CONSOLE.print("[bold green](OK) Файл прибрано з наступного запиту.[/]")
                LOGGER.info("Pending file attachment removed")
            continue

        prompt_for_context = (
            build_file_request(prompt, pending_attachment)
            if pending_attachment
            else truncate_text(prompt)
        )
        if pending_attachment and len(prompt) > MAX_FILE_PROMPT_CHARS:
            CONSOLE.print(
                f"[yellow]Текст завдання скорочено до {MAX_FILE_PROMPT_CHARS} "
                "символів, щоб додати файл.[/]"
            )
            LOGGER.info("User task was truncated for file attachment")
        elif not pending_attachment and prompt_for_context != prompt:
            CONSOLE.print(
                f"[yellow]Запит скорочено до {MAX_MESSAGE_CHARS} символів "
                "для безпечного надсилання.[/]"
            )
            LOGGER.info("User prompt was truncated to context limit")

        messages.append({"role": "user", "content": prompt_for_context})
        try:
            with CONSOLE.status("[bold yellow]Groq думає...[/]", spinner="dots"):
                reply, web_search_used, sources, rate_limits = request_response(
                    client, messages
                )
        except RateLimitError as error:
            discard_failed_prompt(messages)
            print_error(f"Перевищено ліміт Groq: {error}", "Ліміт Groq")
            LOGGER.warning("Groq rate limit: %s", error)
            continue
        except APIConnectionError:
            discard_failed_prompt(messages)
            print_error("Немає з’єднання з Groq. Перевірте інтернет.", "З’єднання відсутнє")
            LOGGER.warning("Groq connection error")
            continue
        except APIStatusError as error:
            discard_failed_prompt(messages)
            print_error(
                f"Помилка Groq ({error.status_code}): {error.message}", "Помилка Groq"
            )
            LOGGER.warning("Groq API status error; status=%s", error.status_code)
            continue
        except Exception as error:
            discard_failed_prompt(messages)
            print_error(f"Неочікувана помилка: {error}", "Неочікувана помилка")
            LOGGER.exception("Unexpected application error")
            continue

        messages.append({"role": "assistant", "content": truncate_text(reply)})
        pending_attachment = None
        try:
            save_chat_history(history_path, messages)
        except OSError as error:
            print_error(f"Не вдалося зберегти історію: {error}")
            LOGGER.exception("Unable to save chat history")

        print_assistant_reply(reply)
        if web_search_used:
            CONSOLE.print(Text("[Використано веб-пошук]", style="bold cyan"))
        if sources:
            print_sources(sources)
        print_rate_limits(rate_limits)
        LOGGER.info(
            "Response received; web_search_used=%s; sources=%s; rate_limits_received=%s",
            web_search_used,
            len(sources),
            bool(rate_limits),
        )
