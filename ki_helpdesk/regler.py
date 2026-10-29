"""Regelbasert sortering av supportsaker (virker uten internett og uten API-nøkkel).

Gir kategori, prioritet og sikkerhetsflagg. Resultatet brukes alene, eller sendes med
til Claude som ekstra kontekst.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

KATEGORIER: dict[str, list[str]] = {
    "sikkerhet": ["phishing", "svindel", "mistenkelig", "virus", "løsepenge", "ransomware", "kryptert",
                  "hacket", "klikket på", "klikka på", "ukjent innlogging", "skadevare", "lekket"],
    "passord og innlogging": ["passord", "logge inn", "logge på", "innlogging", "låst ute", "mfa",
                              "authenticator", "tofaktor", "bankid", "konto er låst", "kontoen er låst"],
    "tilgang": ["tilgang", "rettigheter", "mappe", "sharepoint", "teams-kanal", "delt mappe", "ny ansatt"],
    "e-post": ["outlook", "e-post", "epost", "innboks", "kalender", "videresending"],
    "nettverk og vpn": ["vpn", "nettverk", "wifi", "wi-fi", "internett", "tregt nett", "ingen forbindelse"],
    "maskinvare": ["pc", "skjerm", "tastatur", "mus", "skriver", "printer", "lader", "dokkingstasjon", "batteri"],
    "programvare og lisens": ["installere", "lisens", "excel", "word", "office", "oppdatering", "program", "app"],
}

KRITISK = ["alle", "hele kontoret", "ingen får", "løsepenge", "ransomware", "kryptert", "nede", "server"]
HOY = ["haster", "akutt", "kan ikke jobbe", "får ikke jobbet", "kunde venter", "møte om", "frist i dag", "klikket på", "klikka på"]
LAV = ["når du har tid", "ikke viktig", "lurer på", "ønske", "forslag"]

SIKKERHETSTEGN = [
    ("klikket på lenke", re.compile(r"(?i)klikk(?:et|a) på (?:en |lenken|linken|lenke)")),
    ("oppga passord/kode", re.compile(r"(?i)(?:skrev|tastet|ga|oppga) (?:inn )?(?:passord|koden|bankid)")),
    ("ukjent innlogging", re.compile(r"(?i)(?:ukjent|uvanlig|mistenkelig) (?:innlogging|pålogging|aktivitet)")),
    ("mulig løsepengevirus", re.compile(r"(?i)løsepenge|ransomware|filene? er kryptert|\.locked\b")),
    ("passord skrevet i saken", re.compile(r"(?i)passord(?:et)?(?: mitt)?\s*(?:er|:|=)\s*\S+")),
]

PRIORITETER = ["kritisk", "høy", "middels", "lav"]


@dataclass
class Sak:
    id: str
    avsender: str
    emne: str
    tekst: str

    @property
    def helhet(self) -> str:
        return f"{self.emne}\n{self.tekst}"


@dataclass
class Sortering:
    kategori: str
    prioritet: str
    sikkerhetsflagg: list[str] = field(default_factory=list)
    begrunnelse: list[str] = field(default_factory=list)

    @property
    def rang(self) -> int:
        return PRIORITETER.index(self.prioritet)


def _treff(tekst: str, ord: list[str]) -> list[str]:
    return [o for o in ord if re.search(rf"(?<!\w){re.escape(o)}(?!\w)", tekst)]


PASSORD_SETNING = re.compile(r"(?i)[^.!?\n]*passord(?:et)?(?: mitt)?\s*(?:er|:|=)\s*\S+[^.!?\n]*")


def sorter(sak: Sak) -> Sortering:
    # En setning der brukeren oppgir passordet sitt sier ingenting om hva saken gjelder.
    tekst = PASSORD_SETNING.sub(" ", sak.helhet).lower()
    poeng = {k: len(_treff(tekst, ord)) for k, ord in KATEGORIER.items()}
    kategori = max(poeng, key=lambda k: (poeng[k], k == "sikkerhet")) if any(poeng.values()) else "annet"
    begrunnelse = [f"Kategori «{kategori}»: {', '.join(_treff(tekst, KATEGORIER[kategori]))}"] if kategori != "annet" else []

    flagg = [navn for navn, m in SIKKERHETSTEGN if m.search(sak.helhet)]
    alvorlige = [f for f in flagg if f != "passord skrevet i saken"]
    if alvorlige and kategori != "sikkerhet":
        kategori = "sikkerhet"
        begrunnelse.append("Endret til sikkerhet på grunn av sikkerhetstegn.")

    if t := _treff(tekst, KRITISK):
        prioritet = "kritisk" if kategori == "sikkerhet" or len(t) >= 2 else "høy"
        begrunnelse.append(f"Påvirker mange eller er alvorlig: {', '.join(t)}")
    elif (t := _treff(tekst, HOY)) or alvorlige:
        prioritet = "høy"
        if t:
            begrunnelse.append(f"Haster: {', '.join(t)}")
    elif t := _treff(tekst, LAV):
        prioritet = "lav"
        begrunnelse.append(f"Ikke tidskritisk: {', '.join(t)}")
    else:
        prioritet = "middels"
    if flagg:
        begrunnelse.append(f"Sikkerhetsflagg: {', '.join(flagg)}")
    return Sortering(kategori, prioritet, flagg, begrunnelse)


def ko(saker: list[Sak]) -> list[tuple[Sak, Sortering]]:
    """Sorterer saker etter prioritet (kritisk først), deretter i opprinnelig rekkefølge."""
    return sorted(((s, sorter(s)) for s in saker), key=lambda par: par[1].rang)
