"""Leser supportsaker fra JSON eller CSV (kolonner/nøkler: id, avsender, emne, tekst)."""
from __future__ import annotations

import csv
import json
import pathlib

from .regler import Sak


def les_saker(sti: str | pathlib.Path) -> list[Sak]:
    sti = pathlib.Path(sti)
    if sti.suffix.lower() == ".csv":
        with sti.open(encoding="utf-8-sig", newline="") as f:
            rader = list(csv.DictReader(f))
    else:
        rader = json.loads(sti.read_text(encoding="utf-8"))
    return [Sak(str(r.get("id", i + 1)), r.get("avsender", ""), r.get("emne", ""), r.get("tekst", ""))
            for i, r in enumerate(rader)]
