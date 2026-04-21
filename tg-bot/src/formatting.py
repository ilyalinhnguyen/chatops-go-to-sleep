"""Telegram-safe formatting helpers."""

from html import escape


def json_pre_html(json_text: str, max_len: int = 3500) -> str:
    """Render JSON in a fixed-width block (use with ParseMode.HTML)."""
    return f"<pre>{escape(json_text[:max_len])}</pre>"
