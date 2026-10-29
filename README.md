# 🎧 KI-helpdesk

Sorterer **supportsaker** etter hvor viktige de er, flagger **sikkerhetshendelser** (phishing,
løsepengevirus, passord på avveie) og lager **svarforslag med Claude** – laget for IT-support i
norske småbedrifter. Personopplysninger maskeres **før** noe sendes til KI-modellen.

*AI helpdesk assistant: triages support tickets, flags security incidents and drafts replies with
Claude. Personal data is masked before anything leaves your machine. Text is in Norwegian.*

![Tester](../../actions/workflows/tester.yml/badge.svg)

## Hva den gjør

| Steg | Hva skjer | Fil |
|---|---|---|
| 1. Sortering | Kategori (sikkerhet, innlogging, tilgang, e-post, nettverk, maskinvare, programvare) og prioritet (kritisk → lav) | `ki_helpdesk/regler.py` |
| 2. Sikkerhetsflagg | Klikket på lenke, oppga passord, ukjent innlogging, mulig løsepengevirus, passord skrevet i saken | `ki_helpdesk/regler.py` |
| 3. Personvern | Fødselsnummer, kort-/kontonummer, passord, e-post og telefon byttes ut med `[FØDSELSNUMMER]` osv. | `ki_helpdesk/personvern.py` |
| 4. Kunnskapsbase | Relevante standardløsninger hentes fra `kunnskap/` og gis til modellen | `ki_helpdesk/kunnskap.py` |
| 5. Svarforslag | Claude svarer gjennom et verktøykall med fast skjema: sammendrag, svar, om en tekniker må inn, sikkerhetsvurdering | `ki_helpdesk/ki.py` |

```
saker (JSON/CSV) ──► regelsortering ──► kø (kritisk først)
                                         │
                       maskering av personopplysninger + kunnskapsbase
                                         │
                                         ▼
                                Claude ──► svarforslag (menneske godkjenner)
```

**Sikkerhet i designet**
- Dataminimering (GDPR art. 5): bare maskert tekst sendes til API-et.
- Saken pakkes i `<sak>`-markører og behandles som data – vern mot *prompt injection*.
- Modellen får beskjed om aldri å be om passord eller finne på interne rutiner.
- Svarene er **utkast**: et menneske leser og sender.

## Kom i gang

```bash
git clone https://github.com/nbrre/ki-helpdesk.git
cd ki-helpdesk
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                  # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."

python -m ki_helpdesk eksempler/saker.json --uten-ki   # bare sortering, ingen nøkkel trengs
python -m ki_helpdesk eksempler/saker.json --sak 103   # svarforslag for én sak
streamlit run app.py
```

## Eksempel

```
$ python -m ki_helpdesk eksempler/saker.json --uten-ki
8 saker i køen (viktigste først):

[KRITISK ] #104 Ingen får åpnet filer på fellesdisken!  (sikkerhet)  ⚠ mulig løsepengevirus
[  HØY   ] #102 Låst ute av kontoen  (passord og innlogging)
[  HØY   ] #103 Klikket på lenke i e-post fra «DNB»  (sikkerhet)  ⚠ klikket på lenke, oppga passord/kode
[  HØY   ] #107 Excel krasjer  (programvare og lisens)  ⚠ passord skrevet i saken
[MIDDELS ] #105 VPN hjemmefra  (nettverk og vpn)
[MIDDELS ] #106 Tilgang til økonomimappa  (tilgang)
[  LAV   ] #101 Skriveren på 2. etasje  (maskinvare)
[  LAV   ] #108 Forslag  (maskinvare)
```

Eksempelsakene er oppdiktede, og personnumre og telefonnumre i dem er ikke ekte.

## Tester

```bash
python -m unittest -v
```

Testene kjører uten internett og uten API-nøkkel – KI-delen testes med en falsk klient, og
sjekker blant annet at telefonnummeret faktisk er fjernet før saken sendes.

## Videre arbeid

- Hente saker direkte fra e-post eller et sakssystem (f.eks. Jira Service Management, Freshdesk)
- Lære av løste saker: legge gode svar inn i kunnskapsbasen
- Måle treffsikkerhet på et fast sett med saker

## Om meg

Laget av **Barre**, bachelor i informasjonsteknologi/informasjonssikkerhet.

Lisens: MIT
