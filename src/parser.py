from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


CONV_RE = re.compile(
    r"^\s*(?P<amount>[\d_.,]+)\s*(?P<base>[A-Za-z]{2,6})\s*(to|в|->)\s*(?P<quote>[A-Za-z]{2,6})\s*$",
    re.IGNORECASE,
)

ALERT_RE = re.compile(
    r"^\s*(?:уведоми|alert|notify)\s*,?\s*(?:если|когда|when)\s+(?P<base>[A-Za-z]{2,6})\s*(?P<op>[<>]=?|==)\s*(?P<value>[\d_.,]+)\s*(?:to|в|->)\s*(?P<quote>[A-Za-z]{2,6})\s*$",
    re.IGNORECASE,
)


@dataclass
class ConvertQuery:
    amount: float
    base: str
    quote: str


@dataclass
class AlertQuery:
    base: str
    quote: str
    operator: str
    value: float


def _normalize_amount(s: str) -> float:
    s = s.replace("_", "").replace(" ", "")
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    return float(s)


def parse_convert(text: str) -> Optional[ConvertQuery]:
    m = CONV_RE.match(text)
    if not m:
        return None
    amount = _normalize_amount(m.group("amount"))
    base = m.group("base").upper()
    quote = m.group("quote").upper()
    return ConvertQuery(amount=amount, base=base, quote=quote)


def parse_alert(text: str) -> Optional[AlertQuery]:
    m = ALERT_RE.match(text)
    if not m:
        return None
    base = m.group("base").upper()
    quote = m.group("quote").upper()
    op = m.group("op")
    value = _normalize_amount(m.group("value"))
    return AlertQuery(base=base, quote=quote, operator=op, value=value)


