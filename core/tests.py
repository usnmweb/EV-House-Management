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


class PannelloAmministrazioneTest(TestCase):
    """L'amministrazione su misura: pagina iniziale, sezioni, filtri."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        from properties.models import Property, PropertyImage

        self.staff = get_user_model().objects.create_superuser(
            username="gestore", email="gestore@example.com", password="prova-12345"
        )
        self.client.force_login(self.staff)
        self.con_scelta = Property.objects.create(
            title="Casa scelta", location="Siniscola", status=Property.Status.PUBLISHED
        )
        self.dal_portale = Property.objects.create(
            title="Casa dal portale", location="Siniscola", status=Property.Status.PUBLISHED
        )
        PropertyImage.objects.create(property=self.con_scelta, image="x/a.jpg", copertina=True)
        PropertyImage.objects.create(property=self.dal_portale, image="x/b.jpg")

    def test_la_pagina_iniziale_mostra_il_pannello(self):
        pagina = self.client.get(reverse("admin:index"))
        self.assertEqual(pagina.status_code, 200)
        schede = {s["titolo"]: s for s in pagina.context["cruscotto"]}
        self.assertEqual(schede["Immobili"]["numero"], 2)
        self.assertEqual(schede["Copertine"]["numero"], 1, "conta solo chi usa ancora la foto del portale")
        self.assertTrue(schede["Copertine"]["da_fare"])
        self.assertTrue(schede["Recensioni"]["da_fare"], "senza recensioni la sezione in home resta nascosta")

    def test_le_sezioni_hanno_nomi_italiani_e_un_ordine_di_lavoro(self):
        pagina = self.client.get(reverse("admin:index"))
        nomi = [s["name"] for s in pagina.context["app_list"]]
        self.assertEqual(nomi, ["Immobili", "Blog", "Recensioni", "Utenti e accessi"])

    def test_il_filtro_copertina_separa_scelte_e_portale(self):
        elenco = reverse("admin:properties_property_changelist")
        portale = self.client.get(elenco + "?copertina=portale").context["cl"].result_list
        scelte = self.client.get(elenco + "?copertina=scelta").context["cl"].result_list
        self.assertEqual([p.title for p in portale], ["Casa dal portale"])
        self.assertEqual([p.title for p in scelte], ["Casa scelta"])

    def test_la_scheda_copertine_porta_all_elenco_filtrato(self):
        """Il numero del pannello e l'elenco a cui porta devono dire la stessa cosa."""
        pagina = self.client.get(reverse("admin:index"))
        scheda = next(s for s in pagina.context["cruscotto"] if s["titolo"] == "Copertine")
        righe = self.client.get(scheda["url"]).context["cl"].result_count
        self.assertEqual(righe, scheda["numero"])

    def test_le_pagine_principali_si_aprono(self):
        for nome in ("admin:properties_property_changelist", "admin:blog_article_changelist",
                     "admin:core_recensione_changelist", "admin:properties_property_add"):
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)
        scheda = reverse("admin:properties_property_change", args=[self.con_scelta.pk])
        self.assertEqual(self.client.get(scheda).status_code, 200)

    def test_la_pagina_di_accesso_ha_il_marchio(self):
        self.client.logout()
        pagina = self.client.get(reverse("admin:login")).content.decode()
        self.assertIn("logo-su-chiaro.png", pagina)
        self.assertIn("css/admin.css", pagina)


class AssicuraAmministratoreTest(TestCase):
    """L'utente dell'amministrazione sul sito pubblicato, dalle variabili d'ambiente."""

    VARIABILI = {
        "DJANGO_SUPERUSER_USERNAME": "gestore-online",
        "DJANGO_SUPERUSER_PASSWORD": "una-password-di-prova-12",
        "DJANGO_SUPERUSER_EMAIL": "gestore@example.com",
    }

    def _esegui(self, variabili):
        import io
        from unittest import mock
        from django.core.management import call_command

        uscita = io.StringIO()
        pulite = {k: "" for k in self.VARIABILI}
        with mock.patch.dict("os.environ", {**pulite, **variabili}):
            call_command("assicura_amministratore", stdout=uscita)
        return uscita.getvalue()

    def test_crea_l_utente_se_manca(self):
        from django.contrib.auth import authenticate, get_user_model

        self._esegui(self.VARIABILI)

        utente = get_user_model().objects.get(username="gestore-online")
        self.assertTrue(utente.is_superuser and utente.is_staff)
        self.assertIsNotNone(authenticate(username="gestore-online",
                                          password="una-password-di-prova-12"))

    def test_non_reimposta_la_password_a_ogni_rilascio(self):
        """Cambiata dall'amministrazione, la password non deve tornare quella vecchia."""
        from django.contrib.auth import authenticate, get_user_model

        self._esegui(self.VARIABILI)
        utente = get_user_model().objects.get(username="gestore-online")
        utente.set_password("cambiata-dal-gestore-34")
        utente.save()

        uscita = self._esegui(self.VARIABILI)

        self.assertIn("esiste già", uscita)
        self.assertIsNotNone(authenticate(username="gestore-online",
                                          password="cambiata-dal-gestore-34"))

    def test_senza_variabili_non_fa_nulla_e_non_fallisce(self):
        """Un rilascio non deve fermarsi perche' manca l'utente."""
        from django.contrib.auth import get_user_model

        uscita = self._esegui({})

        self.assertIn("nessun utente creato", uscita)
        self.assertFalse(get_user_model().objects.exists())
