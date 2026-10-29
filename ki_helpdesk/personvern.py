"""Maskerer personopplysninger før en sak sendes til en KI-modell.

Bare det som trengs for å løse saken skal forlate egen maskin (dataminimering, GDPR art. 5).
"""
from __future__ import annotations

import re

MONSTRE = [
    ("FØDSELSNUMMER", re.compile(r"\b[0-3]\d[01]\d\d{2}\s?\d{5}\b")),
    ("KORTNUMMER", re.compile(r"\b(?:\d[ -]?){15,16}\b")),
    ("KONTONUMMER", re.compile(r"\b\d{4}[ .]?\d{2}[ .]?\d{5}\b")),
    ("PASSORD", re.compile(r"(?i)(passord(?:et)?(?: mitt)?\s*(?:er|:|=)\s*)(\S+)")),
    ("E-POST", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("TELEFON", re.compile(r"(?<!\d)(?:\+47\s?)?[49]\d(?:\s?\d){6}(?!\d)")),
]


def masker(tekst: str) -> tuple[str, dict[str, int]]:
    """Returnerer (maskert tekst, antall treff per type)."""
    antall: dict[str, int] = {}
    for navn, monster in MONSTRE:
        if navn == "PASSORD":
            tekst, n = monster.subn(lambda m: m.group(1) + "[PASSORD]", tekst)
        else:
            tekst, n = monster.subn(f"[{navn}]", tekst)
        if n:
            antall[navn] = n
    return tekst, antall
