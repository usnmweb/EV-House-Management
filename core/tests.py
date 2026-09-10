"""Dati societari: quello che il footer dichiara ha valore legale.

Non e' un test di grafica. Per una S.r.l. l'art. 2250 c.c. vuole sede, ufficio
del registro delle imprese e numero REA indicati anche sul sito; e gli stessi
dati identificano il titolare del trattamento nella privacy policy. Se una
pagina li perde per strada, non e' un difetto estetico.
"""

import json
import pathlib
import re

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


class DatiSocietariTest(TestCase):
    def setUp(self):
        self.home = self.client.get(reverse("core:home")).content.decode()

    def test_il_footer_dichiara_i_dati_obbligatori(self):
        blocco = self.home.split('footer-legal-data')[1].split("</ul>")[0]
        for atteso in (
            settings.COMPANY_LEGAL_NAME,
            settings.COMPANY_ADDRESS,
            settings.COMPANY_VAT,
            settings.COMPANY_REA,
            settings.COMPANY_PEC,
        ):
            with self.subTest(dato=atteso):
                self.assertIn(atteso, blocco)

    def test_nessun_segnaposto_nel_footer(self):
        """I «[da inserire]» erano due: se tornano, il sito sembra incompiuto."""
        self.assertNotIn("[da inserire]", self.home)

    def test_la_sede_si_compone_dai_suoi_pezzi(self):
        """Riga unica e dati strutturati vengono dallo stesso posto."""
        for pezzo in (
            settings.COMPANY_STREET,
            settings.COMPANY_POSTAL_CODE,
            settings.COMPANY_CITY,
            settings.COMPANY_PROVINCE,
        ):
            self.assertIn(pezzo, settings.COMPANY_ADDRESS)

    def test_i_dati_strutturati_sono_validi_e_coerenti(self):
        blocchi = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', self.home, re.S
        )
        self.assertTrue(blocchi, "nessun blocco di dati strutturati")
        org = json.loads(blocchi[0])          # se non e' JSON valido, qui salta
        self.assertEqual(org["name"], settings.COMPANY_LEGAL_NAME)
        self.assertEqual(org["vatID"], settings.COMPANY_VAT)
        self.assertEqual(org["address"]["postalCode"], settings.COMPANY_POSTAL_CODE)
        self.assertEqual(org["address"]["addressLocality"], settings.COMPANY_CITY)

    def test_il_telefono_e_cliccabile_senza_spazi(self):
        """«+39 327 797 9201» si legge, «tel:+393277979201» si chiama."""
        self.assertIn(settings.COMPANY_PHONE, self.home)
        self.assertIn(
            'href="tel:%s"' % settings.COMPANY_PHONE.replace(" ", ""), self.home
        )

    def test_la_privacy_indica_la_societa_come_titolare(self):
        privacy = self.client.get(reverse("core:privacy")).content.decode()
        self.assertIn(settings.COMPANY_LEGAL_NAME, privacy)
        self.assertIn(settings.COMPANY_ADDRESS, privacy)
        self.assertIn(settings.COMPANY_VAT, privacy)

    @override_settings(COMPANY_CAPITAL="10.000,00 euro interamente versato")
    def test_il_capitale_sociale_compare_solo_se_c_e(self):
        """Manca il dato: la riga non c'e'. Arriva il dato: la riga torna."""
        self.assertNotIn("Capitale sociale", self.home)
        con = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Capitale sociale", con)
        self.assertIn("10.000,00 euro interamente versato", con)


class PortaleProprietariTest(TestCase):
    """Il collegamento all'area riservata dei proprietari, sul gestionale."""

    def setUp(self):
        self.home = self.client.get(reverse("core:home")).content.decode()

    def test_il_menu_porta_al_portale(self):
        self.assertIn(f'href="{settings.OWNER_PORTAL_URL}"', self.home)

    def test_si_apre_in_una_scheda_nuova_e_lo_dice(self):
        """Una scheda che si apre da sola senza preavviso e' una sorpresa."""
        voce = self.home.split('class="nav-voce nav-portale"')[1][:600]
        self.assertIn('target="_blank"', voce)
        self.assertIn('rel="noopener"', voce)
        self.assertIn("si apre in una nuova scheda", voce)

    def test_c_e_anche_nel_footer(self):
        """Chi cerca l'area riservata guarda in fondo quanto in cima."""
        piede = self.home.split("site-footer")[1]
        self.assertIn(settings.OWNER_PORTAL_URL, piede)

    @override_settings(OWNER_PORTAL_URL="https://esempio.test/accesso")
    def test_l_indirizzo_viene_dalle_impostazioni(self):
        """Cambia il gestionale: si tocca un punto solo, non i template."""
        home = self.client.get(reverse("core:home")).content.decode()
        self.assertIn('href="https://esempio.test/accesso"', home)
        self.assertNotIn("vr.krossbooking.com", home)


class MarchioTest(TestCase):
    """Le due versioni del logo e le misure dichiarate nei template.

    Le misure nel markup non sono decorative: il browser ci riserva lo spazio
    prima che l'immagine arrivi. Sbagliate, la pagina salta al caricamento —
    e il salto si vede solo con la rete lenta, cioe' quasi mai in prova.
    """

    CARTELLA = pathlib.Path(settings.BASE_DIR) / "static" / "img"

    def test_ci_sono_tutt_e_due_le_versioni(self):
        for nome in ("logo-su-chiaro.png", "logo-su-scuro.png"):
            with self.subTest(file=nome):
                self.assertTrue((self.CARTELLA / nome).exists())

    def test_le_misure_nel_markup_sono_quelle_vere(self):
        from PIL import Image

        for nome in ("logo-su-chiaro.png", "logo-su-scuro.png"):
            with Image.open(self.CARTELLA / nome) as im:
                larghezza, altezza = im.size
            with self.subTest(file=nome):
                home = self.client.get(reverse("core:home")).content.decode()
                self.assertIn(f'width="{larghezza}" height="{altezza}"', home)

    def test_le_due_versioni_hanno_la_stessa_forma(self):
        """Se divergessero, il logo ballerebbe al cambio di tema."""
        from PIL import Image

        misure = []
        for nome in ("logo-su-chiaro.png", "logo-su-scuro.png"):
            with Image.open(self.CARTELLA / nome) as im:
                misure.append(im.size)
        self.assertEqual(*misure)

    def test_la_versione_per_fondo_scuro_ha_la_scritta_chiara(self):
        """Su nero una scritta quasi nera non si vede: e' il motivo dei due file."""
        from PIL import Image

        def quanto_e_scura(nome):
            with Image.open(self.CARTELLA / nome).convert("RGBA") as im:
                px = im.load()
                scuri = 0
                for y in range(0, im.height, 4):
                    for x in range(0, im.width, 4):
                        r, g, b, a = px[x, y]
                        massimo, minimo = max(r, g, b), min(r, g, b)
                        saturazione = 0 if massimo == 0 else (massimo - minimo) / massimo
                        if a > 200 and saturazione < 0.28 and massimo < 150:
                            scuri += 1
                return scuri

        self.assertGreater(quanto_e_scura("logo-su-chiaro.png"), 0)
        self.assertEqual(quanto_e_scura("logo-su-scuro.png"), 0)
