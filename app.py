"""Enkel nettside for KI-helpdesk. Start med:  streamlit run app.py"""
import json
import os
import pathlib

import streamlit as st

from ki_helpdesk.innlesing import les_saker
from ki_helpdesk.personvern import masker
from ki_helpdesk.regler import Sak, ko

st.set_page_config(page_title="KI-helpdesk", page_icon="🎧", layout="wide")
st.title("🎧 KI-helpdesk")
st.write("Sorterer supportsaker etter hvor viktige de er, flagger sikkerhetshendelser og lager svarforslag med Claude.")

kilde = st.radio("Saker", ["Eksempelsaker", "Skriv inn én sak"], horizontal=True)
if kilde == "Eksempelsaker":
    saker = les_saker(pathlib.Path(__file__).parent / "eksempler" / "saker.json")
else:
    emne = st.text_input("Emne")
    tekst = st.text_area("Beskrivelse", height=150)
    saker = [Sak("1", "", emne, tekst)] if tekst.strip() else []

bruk_ki = st.toggle("Lag svarforslag med KI (krever ANTHROPIC_API_KEY)", value=bool(os.getenv("ANTHROPIC_API_KEY")))
FARGE = {"kritisk": "red", "høy": "orange", "middels": "blue", "lav": "green"}

for sak, sort in ko(saker):
    tittel = f":{FARGE[sort.prioritet]}[{sort.prioritet.upper()}] #{sak.id} {sak.emne} — {sort.kategori}"
    with st.expander(tittel, expanded=sort.prioritet == "kritisk"):
        st.write(sak.tekst)
        for b in sort.begrunnelse:
            st.caption(f"• {b}")
        maskert, funnet = masker(sak.helhet)
        if funnet:
            st.warning("Personopplysninger maskeres før sending til KI: " + ", ".join(funnet))
        if bruk_ki and st.button("Lag svarforslag", key=f"ki-{sak.id}"):
            from ki_helpdesk.ki import behandle

            with st.spinner("Claude skriver svar …"):
                try:
                    r = behandle(sak, sort)
                except Exception as feil:
                    st.error(f"Svarforslaget feilet: {feil}")
                else:
                    st.markdown(f"**Sammendrag:** {r['sammendrag']}")
                    st.markdown(f"**Sikkerhet:** {r['sikkerhetsvurdering']}")
                    st.markdown(f"**Trenger tekniker:** {'ja' if r['trenger_menneske'] else 'nei'}")
                    st.text_area("Svarforslag (rediger før du sender)", r["svarforslag"], key=f"svar-{sak.id}")

st.caption("Svarforslag er utkast og skal alltid leses av et menneske før de sendes.")
