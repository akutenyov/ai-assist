"""All Rich-based terminal rendering and input helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import GROQ_MODEL

from .constants import (
    CHAT_HISTORY_DIRECTORY,
    MAX_FILE_BYTES,
    MAX_FILE_TEXT_CHARS,
    MAX_SPREADSHEET_ROWS,
)


CONSOLE = Console(emoji=False)


def print_help() -> None:
    """Render the supported commands in a compact table."""
    table = Table(
        title="[bold cyan]Команди[/]",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("Команда", style="bold yellow")
    table.add_column("Дія")
    table.add_row("/help", "Показати цю довідку.")
    table.add_row("/clear", "Почати новий діалог без попереднього контексту.")
    table.add_row("/history", "Показати десять останніх збережених чатів.")
    table.add_row("/file", "Показати формати й обмеження завантаження.")
    table.add_row("/file <шлях>", "Додати текст із локального файла до наступного запиту.")
    table.add_row("/remove-file", "Прибрати підготовлений файл із наступного запиту.")
    table.add_row("/exit", "Завершити програму.")
    CONSOLE.print(table)
    CONSOLE.print("[dim]Модель застосовує веб-пошук, коли потрібні актуальні дані.[/]")


def print_banner(history_path: Path) -> None:
    """Render startup information and the active history destination."""
    content = Text()
    content.append("Модель: ", style="bold")
    content.append(GROQ_MODEL, style="cyan")
    content.append("\nВеб-пошук: ", style="bold")
    content.append("автоматично", style="green")
    content.append("\nІсторія: ", style="bold")
    content.append(f"{CHAT_HISTORY_DIRECTORY}\\{history_path.name}", style="dim")
    content.append("\n/help — список команд", style="dim")
    CONSOLE.print(
        Panel(
            content,
            title="[bold bright_cyan]AI Assist[/]",
            border_style="bright_cyan",
            padding=(1, 2),
        )
    )


def print_saved_chats(chats: list[tuple[Path, datetime]]) -> None:
    """Render saved-chat metadata without opening private chat files."""
    if not chats:
        CONSOLE.print("[dim]Збережених чатів ще немає.[/]")
        return

    table = Table(
        title="[bold cyan]Збережені чати[/]",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("Файл", style="white")
    table.add_column("Останнє збереження", style="dim")

    for path, saved_at in chats:
        table.add_row(path.name, saved_at.strftime("%d.%m.%Y %H:%M"))

    CONSOLE.print(table)


def print_file_capabilities() -> None:
    """Explain supported file formats before local content is read."""
    table = Table(
        title="[bold cyan]Обробка файлів[/]",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("Формат", style="bold yellow")
    table.add_column("Що буде опрацьовано")
    table.add_row("TXT, MD, PY, JSON, CSV, LOG, YAML, XML, HTML", "Текст і код")
    table.add_row("PDF", "Текстовий шар; скановані PDF без OCR не підтримуються")
    table.add_row("DOCX", "Текст документа")
    table.add_row("XLSX", f"Значення комірок, до {MAX_SPREADSHEET_ROWS} рядків")
    CONSOLE.print(table)
    CONSOLE.print(
        Panel(
            Text.from_markup(
                f"[bold yellow]Обмеження:[/] файл до {MAX_FILE_BYTES // 1024 // 1024} МБ; "
                f"до {MAX_FILE_TEXT_CHARS:,} символів тексту передається моделі.\n"
                "Фото, аудіо й відео не підтримуються поточною текстовою моделлю "
                f"[cyan]{GROQ_MODEL}[/].\n"
                "Вміст вибраного файла буде надіслано до Groq разом із вашим наступним "
                "запитом і збережено у локальній історії чату. Не додавайте секретні дані."
            ),
            title="[bold yellow]Перед додаванням файла[/]",
            border_style="yellow",
            padding=(1, 2),
        )
    )


def print_assistant_reply(reply: str) -> None:
    """Render a model response as Markdown in its own panel."""
    CONSOLE.print(
        Panel(
            Markdown(reply),
            title="[bold green]Groq[/]",
            border_style="green",
            padding=(1, 2),
        )
    )


def print_sources(sources: list[tuple[str, str]]) -> None:
    """Render web-search sources as a compact table of clickable links."""
    table = Table(
        title="[bold cyan]Джерела веб-пошуку[/]",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Джерело", style="white")
    table.add_column("URL", style="cyan")

    for number, (title, url) in enumerate(sources, start=1):
        table.add_row(str(number), Text(title), Text(url, style=f"link {url} underline cyan"))

    CONSOLE.print(table)


def print_rate_limits(rate_limits: list[str]) -> None:
    """Render the last quota values returned by the Groq API."""
    if not rate_limits:
        CONSOLE.print("[dim]Квота Groq: API не передав ці дані.[/]")
        return

    table = Table.grid(padding=(0, 1))
    for rate_limit in rate_limits:
        table.add_row("[bold magenta]-[/]", Text(rate_limit))

    CONSOLE.print(
        Panel(
            table,
            title="[bold magenta]Залишок квоти Groq[/]",
            border_style="magenta",
            padding=(0, 1),
        )
    )


def print_error(message: str, title: str = "Помилка") -> None:
    """Render external error text safely instead of treating it as markup."""
    CONSOLE.print(
        Panel(
            Text(message),
            title=f"[bold red]{title}[/]",
            border_style="red",
            padding=(0, 1),
        )
    )
