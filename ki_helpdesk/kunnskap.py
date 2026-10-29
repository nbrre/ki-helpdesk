"""Henter standardløsninger fra kunnskapsbasen (mappen kunnskap/) for en kategori."""
from __future__ import annotations

import pathlib

MAPPE = pathlib.Path(__file__).resolve().parent.parent / "kunnskap"


def for_kategori(kategori: str, mappe: pathlib.Path = MAPPE) -> str:
    fil = mappe / f"{kategori.replace(' ', '_')}.md"
    return fil.read_text(encoding="utf-8") if fil.exists() else ""
