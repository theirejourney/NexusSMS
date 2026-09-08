"""Message pipeline: parse -> persist -> notify. Pluggable via callbacks."""

from __future__ import annotations

import logging
from typing import Callable, Optional

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _NoColor:
        def __getattr__(self, _): return ""
    Fore = Style = _NoColor()

from core.database import log_message
from core.extractor import ExtractionResult, parse_message

logger = logging.getLogger("nexussms")

Callback = Callable[[ExtractionResult, bool], None]


class MessageHandler:
    def __init__(self, db_path: str = "nexus_sms.db",
                 callbacks: Optional[list[Callback]] = None,
                 print_output: bool = True):
        self.db_path = db_path
        self.callbacks: list[Callback] = list(callbacks or [])
        self.print_output = print_output
        self.processed = 0
        self.duplicates = 0

    def add_callback(self, fn: Callback) -> None:
        self.callbacks.append(fn)

    def handle(self, sender: str, body: str,
               message_sid: Optional[str] = None) -> ExtractionResult:
        """Full pipeline for one incoming message. Never raises."""
        result = parse_message(sender, body)
        try:
            inserted = log_message(
                sender=result.sender,
                category=result.category,
                extracted_code=result.extracted_code,
                raw_body=result.raw_body,
                message_sid=message_sid,
                db_path=self.db_path,
            )
        except Exception:
            logger.exception("database write failed for sid=%s", message_sid)
            inserted = False

        self.processed += 1
        if not inserted:
            self.duplicates += 1

        if self.print_output:
            code = (f"{Fore.GREEN}{result.extracted_code}{Style.RESET_ALL}"
                    if result.extracted_code
                    else f"{Fore.RED}None{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[+]{Style.RESET_ALL} Captured | "
                  f"SID: {message_sid or '-'} | Sender: {sender} | "
                  f"Category: {result.category} | Code: {code}"
                  + (f"{Fore.YELLOW} (duplicate, skipped){Style.RESET_ALL}"
                     if not inserted else ""))

        self.notify(result, inserted)
        return result

    def notify(self, result: ExtractionResult, inserted: bool) -> None:
        """Trigger all registered callbacks."""
        for cb in self.callbacks:
            try:
                cb(result, inserted)
            except Exception:
                logger.exception("callback %r failed", cb)


_default_handler: Optional[MessageHandler] = None


def handle_incoming_sms(sender: str, body: str,
                        message_sid: Optional[str] = None,
                        db_path: str = "nexus_sms.db") -> ExtractionResult:
    global _default_handler
    if _default_handler is None:
        _default_handler = MessageHandler(db_path=db_path)
    return _default_handler.handle(sender, body, message_sid)
