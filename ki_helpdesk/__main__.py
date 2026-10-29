"""Kommandolinje: python -m ki_helpdesk eksempler/saker.json [--uten-ki] [--sak ID]"""
from __future__ import annotations

import argparse
import os

from .innlesing import les_saker
from .regler import ko

FARGER = {"kritisk": "\033[41;97m", "høy": "\033[31m", "middels": "\033[33m", "lav": "\033[32m"}
NULL = "\033[0m"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ki_helpdesk", description="Sorter supportsaker og lag svarforslag.")
    p.add_argument("fil", help="JSON- eller CSV-fil med saker.")
    p.add_argument("--uten-ki", action="store_true", help="Bare regelsortering, ingen API-kall.")
    p.add_argument("--sak", help="Behandle bare saken med denne id-en.")
    a = p.parse_args(argv)

    saker = les_saker(a.fil)
    if a.sak:
        saker = [s for s in saker if s.id == a.sak]
    koen = ko(saker)

    print(f"{len(koen)} saker i køen (viktigste først):\n")
    for sak, sort in koen:
        flagg = f"  ⚠ {', '.join(sort.sikkerhetsflagg)}" if sort.sikkerhetsflagg else ""
        print(f"[{FARGER[sort.prioritet]}{sort.prioritet.upper():^8}{NULL}] #{sak.id} {sak.emne}  ({sort.kategori}){flagg}")

    if a.uten_ki:
        return 0
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n(Ingen ANTHROPIC_API_KEY satt – hopper over svarforslag. Se README.)")
        return 0

    from .ki import behandle

    for sak, sort in koen:
        r = behandle(sak, sort)
        print(f"\n— #{sak.id} {sak.emne} —")
        print(f"Sammendrag: {r['sammendrag']}")
        if r["maskert"]:
            print(f"Maskert før sending: {', '.join(f'{k} ×{v}' for k, v in r['maskert'].items())}")
        print(f"Sikkerhet: {r['sikkerhetsvurdering']}")
        print(f"Trenger tekniker: {'ja' if r['trenger_menneske'] else 'nei'}")
        print(f"Svarforslag:\n{r['svarforslag']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
