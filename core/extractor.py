"""SMS parsing engine: detects institution category and extracts OTP codes.

Fully pluggable — register your own institution rules at runtime:

    from core.extractor import register_rule, parse_message

    register_rule("crypto", senders=["Coinbase", "Binance"],
                  regex=r"(?:code|verify)[^0-9]{0,10}([0-9]{4,8})")
    result = parse_message(sender, body)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ExtractionResult:
    sender: str
    category: str
    extracted_code: Optional[str]
    raw_body: str
    matched_rule: str
    all_candidates: tuple = field(default_factory=tuple)


_RULES: dict[str, dict] = {
    "banking": {
        "senders": ["Chase", "PayPal", "Revolut", "BofA", "WellsFargo", "Venmo", "Bank of America"],
        "regex": r"(?:code|password|pin|token|otp)\s*(?:is|:|-)?\s*([0-9]{4,8})",
    },
    "tech": {
        "senders": ["AWS", "GitHub", "Google", "Cloudflare", "Microsoft", "Apple", "Facebook", "Meta", "Amazon"],
        "regex": r"(?:verification|security|auth(?:entication)?)\s*(?:code)?\s*(?:is|:|-)?\s*([0-9A-Za-z]{4,10})",
    },
    "general": {
        "senders": ["*"],
        "regex": r"(?<![0-9])([0-9]{4,8})(?![0-9])",
    },
}


def register_rule(category: str, senders: list[str], regex: str) -> None:
    re.compile(regex)
    _RULES[category] = {"senders": senders, "regex": regex}


def remove_rule(category: str) -> None:
    if category == "general":
        raise ValueError("cannot remove the 'general' fallback rule")
    _RULES.pop(category, None)


def list_rules() -> dict:
    return {k: dict(v) for k, v in _RULES.items()}


def _detect_category(sender: str) -> str:
    s = sender.lower()
    for cat, rule in _RULES.items():
        if cat == "general":
            continue
        if any(p.lower() in s for p in rule["senders"]):
            return cat
    return "general"


def parse_message(sender: str, body: str, general_fallback: bool = True) -> ExtractionResult:
    category = _detect_category(sender)
    rule = _RULES[category]

    match = re.search(rule["regex"], body, re.IGNORECASE)
    if not match and category == "general" and not general_fallback:
        return ExtractionResult(sender, category, None, body, rule["regex"])

    code = match.group(1) if match else None
    candidates = tuple(m.group(1) for m in re.finditer(rule["regex"], body, re.IGNORECASE))
    return ExtractionResult(sender, category, code, body, rule["regex"], candidates)


parse_institution_message = parse_message
