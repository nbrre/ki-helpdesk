import pathlib
import unittest
from types import SimpleNamespace

from ki_helpdesk import ki
from ki_helpdesk.innlesing import les_saker
from ki_helpdesk.kunnskap import for_kategori
from ki_helpdesk.personvern import masker
from ki_helpdesk.regler import Sak, ko, sorter

EKS = pathlib.Path(__file__).resolve().parent.parent / "eksempler"


def sak(emne, tekst):
    return Sak("x", "", emne, tekst)


class TestRegler(unittest.TestCase):
    def setUp(self):
        self.saker = {s.id: s for s in les_saker(EKS / "saker.json")}

    def test_losepengevirus_er_kritisk_sikkerhet(self):
        s = sorter(self.saker["104"])
        self.assertEqual((s.kategori, s.prioritet), ("sikkerhet", "kritisk"))
        self.assertIn("mulig løsepengevirus", s.sikkerhetsflagg)

    def test_phishing_klikk_blir_sikkerhet_hoy(self):
        s = sorter(self.saker["103"])
        self.assertEqual((s.kategori, s.prioritet), ("sikkerhet", "høy"))
        self.assertIn("klikket på lenke", s.sikkerhetsflagg)
        self.assertIn("oppga passord/kode", s.sikkerhetsflagg)

    def test_last_ute_er_innlogging_hoy(self):
        s = sorter(self.saker["102"])
        self.assertEqual((s.kategori, s.prioritet), ("passord og innlogging", "høy"))

    def test_skriver_er_lav(self):
        s = sorter(self.saker["101"])
        self.assertEqual((s.kategori, s.prioritet), ("maskinvare", "lav"))

    def test_passord_i_saken_flagges_uten_a_bli_sikkerhetshendelse(self):
        s = sorter(self.saker["107"])
        self.assertEqual(s.kategori, "programvare og lisens")
        self.assertIn("passord skrevet i saken", s.sikkerhetsflagg)

    def test_ko_har_kritisk_forst(self):
        koen = ko(list(self.saker.values()))
        self.assertEqual(koen[0][0].id, "104")
        self.assertEqual(koen[-1][1].prioritet, "lav")

    def test_ukjent_sak_er_annet_middels(self):
        s = sorter(sak("Spørsmål", "Hvordan endrer jeg bakgrunnsbildet?"))
        self.assertEqual((s.kategori, s.prioritet), ("annet", "middels"))


class TestPersonvern(unittest.TestCase):
    def test_maskerer_personopplysninger(self):
        tekst, funnet = masker("Fnr 01019912345, tlf 912 34 567, e-post ola@firma.example, passordet er Hemmelig1")
        for rå in ("01019912345", "912 34 567", "ola@firma.example", "Hemmelig1"):
            self.assertNotIn(rå, tekst)
        self.assertEqual(set(funnet), {"FØDSELSNUMMER", "TELEFON", "E-POST", "PASSORD"})

    def test_vanlig_tekst_endres_ikke(self):
        self.assertEqual(masker("Skriveren virker ikke i dag."), ("Skriveren virker ikke i dag.", {}))


class TestKunnskap(unittest.TestCase):
    def test_finner_artikkel(self):
        self.assertIn("VPN", for_kategori("nettverk og vpn"))
        self.assertEqual(for_kategori("annet"), "")


class FalskKlient:
    """Later som den er Claude, så vi kan teste uten API-nøkkel."""

    def __init__(self):
        self.kall = None
        self.messages = self

    def create(self, **kwargs):
        self.kall = kwargs
        svar = {"kategori": "sikkerhet", "prioritet": "høy", "sammendrag": "Bruker oppga passord på falsk side.",
                "svarforslag": "Bytt passord nå fra en annen enhet.", "trenger_menneske": True,
                "sikkerhetsvurdering": "Konto kan være kompromittert."}
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=svar)])


class TestKI(unittest.TestCase):
    def test_sender_maskert_sak_med_kunnskap_og_struktur(self):
        klient = FalskKlient()
        s = Sak("9", "", "Klikket på lenke", "Jeg klikket på lenken. Ring 912 34 567.")
        r = ki.behandle(s, sorter(s), klient=klient)
        innhold = klient.kall["messages"][0]["content"]
        self.assertNotIn("912 34 567", innhold)
        self.assertIn("<sak>", innhold)
        self.assertIn("Koble PC-en fra nettet".lower(), innhold.lower())
        self.assertEqual(klient.kall["tool_choice"]["name"], "behandling")
        self.assertTrue(r["trenger_menneske"])
        self.assertEqual(r["maskert"], {"TELEFON": 1})


if __name__ == "__main__":
    unittest.main()
