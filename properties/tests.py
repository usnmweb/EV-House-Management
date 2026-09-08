"""Verifica che il capitolato sia soddisfatto dall'amministrazione di Django:
elenco, scheda singola, foto, descrizione e caratteristiche, tutti gestibili
senza toccare il codice.

I test girano su un database temporaneo e su una cartella media temporanea:
non toccano i dati reali.
"""

import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from properties.models import Amenity, Property, PropertyImage

MEDIA_TEMP = tempfile.mkdtemp(prefix="ev-test-media-")


def immagine_finta(nome="scatto.jpg", colore=(120, 90, 40)):
    """Un JPEG valido in memoria: ImageField rifiuta i file non riconosciuti."""
    buf = io.BytesIO()
    Image.new("RGB", (60, 40), colore).save(buf, format="JPEG")
    return SimpleUploadedFile(nome, buf.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class AmministrazioneImmobiliTest(TestCase):
    """Percorso completo del redattore: crea, modifica, pubblica, elimina."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            username="redattore", email="redattore@example.com", password="prova-12345"
        )
        cls.dotazione = Amenity.objects.create(name="Aria condizionata")

    def setUp(self):
        self.client.force_login(self.staff)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEMP, ignore_errors=True)
        super().tearDownClass()

    # ---------------------------------------------------------------- elenco

    def test_elenco_immobili_raggiungibile(self):
        Property.objects.create(title="Casa di prova", location="Siniscola")
        r = self.client.get(reverse("admin:properties_property_changelist"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Casa di prova")

    def test_elenco_filtrabile_e_ricercabile(self):
        Property.objects.create(title="Villa Alfa", location="Orosei",
                                category="Villa", status=Property.Status.PUBLISHED)
        Property.objects.create(title="Appartamento Beta", location="Posada",
                                category="Appartamento", status=Property.Status.DRAFT)
        url = reverse("admin:properties_property_changelist")

        r = self.client.get(url, {"status__exact": "published"})
        self.assertContains(r, "Villa Alfa")
        self.assertNotContains(r, "Appartamento Beta")

        r = self.client.get(url, {"q": "Beta"})
        self.assertContains(r, "Appartamento Beta")
        self.assertNotContains(r, "Villa Alfa")

    # ----------------------------------------------------- creazione da admin

    def _payload(self, **extra):
        dati = {
            "status": Property.Status.PUBLISHED,
            "title": "Dimora sul mare",
            "slug": "dimora-sul-mare",
            "category": "Villa",
            "location": "Budoni",
            "address": "Via delle Dune 4",
            "latitude": "40.7000000",
            "longitude": "9.7000000",
            "short_description": "Villa fronte mare con giardino.",
            "description": "Ampio soggiorno, cucina attrezzata e veranda coperta.",
            "guests": 6,
            "bedrooms": 3,
            "bathrooms": 2,
            "amenities": [self.dotazione.pk],
            "booking_url": "https://evhouse.kross.travel/budoni/dimora",
            "license_code": "IT091000X0000X0001",
            "meta_title": "",
            "meta_description": "",
            # formset delle foto
            "images-TOTAL_FORMS": "1",
            "images-INITIAL_FORMS": "0",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "images-0-id": "",
            "images-0-property": "",
            "images-0-alt_text": "Veranda vista mare",
            "images-0-order": "0",
            "images-0-image": immagine_finta(),
        }
        dati.update(extra)
        return dati

    def test_creazione_completa_con_foto(self):
        r = self.client.post(
            reverse("admin:properties_property_add"), self._payload(), follow=True
        )
        self.assertEqual(r.status_code, 200)
        imm = Property.objects.get(slug="dimora-sul-mare")

        # descrizione e caratteristiche
        self.assertEqual(imm.guests, 6)
        self.assertEqual(imm.bedrooms, 3)
        self.assertEqual(imm.bathrooms, 2)
        self.assertEqual(imm.category, "Villa")
        self.assertIn("veranda coperta", imm.description)
        self.assertEqual(list(imm.amenities.all()), [self.dotazione])
        self.assertEqual(imm.license_code, "IT091000X0000X0001")

        # foto caricata dall'inline
        self.assertEqual(imm.images.count(), 1)
        foto = imm.images.first()
        self.assertTrue(foto.image.name.endswith(".jpg"))
        self.assertEqual(foto.alt_text, "Veranda vista mare")

    def test_immobile_creato_compare_sul_sito(self):
        self.client.post(reverse("admin:properties_property_add"), self._payload())
        self.client.logout()

        elenco = self.client.get(reverse("properties:list"))
        self.assertContains(elenco, "Dimora sul mare")

        scheda = self.client.get(
            reverse("properties:detail", kwargs={"slug": "dimora-sul-mare"})
        )
        self.assertEqual(scheda.status_code, 200)
        self.assertContains(scheda, "veranda coperta")
        self.assertContains(scheda, "Aria condizionata")
        self.assertContains(scheda, "Veranda vista mare")   # alt della foto

    # ------------------------------------------------------------- modifica

    def test_modifica_di_descrizione_e_caratteristiche(self):
        self.client.post(reverse("admin:properties_property_add"), self._payload())
        imm = Property.objects.get(slug="dimora-sul-mare")

        modificato = self._payload(
            description="Testo riscritto dal redattore.",
            guests=8,
            images_extra=None,
        )
        modificato.pop("images_extra")
        modificato["images-INITIAL_FORMS"] = "1"
        modificato["images-0-id"] = str(imm.images.first().pk)
        modificato["images-0-property"] = str(imm.pk)
        modificato.pop("images-0-image")          # foto invariata

        r = self.client.post(
            reverse("admin:properties_property_change", args=[imm.pk]), modificato
        )
        self.assertEqual(r.status_code, 302)
        imm.refresh_from_db()
        self.assertEqual(imm.description, "Testo riscritto dal redattore.")
        self.assertEqual(imm.guests, 8)
        self.assertEqual(imm.images.count(), 1)   # la foto non si e' persa

    def test_pubblicazione_e_bozza_governano_la_visibilita(self):
        imm = Property.objects.create(
            title="Casa riservata", location="Orosei",
            slug="casa-riservata", status=Property.Status.DRAFT,
        )
        url = reverse("properties:detail", kwargs={"slug": imm.slug})
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.post(
            reverse("admin:properties_property_changelist"),
            {"action": "pubblica", "_selected_action": [str(imm.pk)]},
            follow=True,
        )
        imm.refresh_from_db()
        self.assertEqual(imm.status, Property.Status.PUBLISHED)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_eliminazione_immobile_rimuove_le_foto(self):
        self.client.post(reverse("admin:properties_property_add"), self._payload())
        imm = Property.objects.get(slug="dimora-sul-mare")
        self.assertEqual(PropertyImage.objects.count(), 1)

        self.client.post(
            reverse("admin:properties_property_delete", args=[imm.pk]),
            {"post": "yes"}, follow=True,
        )
        self.assertFalse(Property.objects.filter(pk=imm.pk).exists())
        self.assertEqual(PropertyImage.objects.count(), 0)

    # ------------------------------------------------------------- dotazioni

    def test_dotazioni_gestibili_dall_amministrazione(self):
        r = self.client.post(
            reverse("admin:properties_amenity_add"),
            {"name": "Piscina privata", "slug": "piscina-privata"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Amenity.objects.filter(name="Piscina privata").exists())

    # --------------------------------------------------------------- accessi

    def test_amministrazione_chiusa_ai_non_staff(self):
        self.client.logout()
        r = self.client.get(reverse("admin:properties_property_changelist"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r.url)


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class CopertinaSceltaTest(TestCase):
    """La copertina la sceglie il gestore, non l'ordine con cui arriva dal portale."""

    def setUp(self):
        self.casa = Property.objects.create(
            title="Casa con vista", location="La Caletta",
            status=Property.Status.PUBLISHED, short_description="Due righe.",
        )
        self.foto = [
            PropertyImage.objects.create(
                property=self.casa, order=n, source_ref=f"rif-{n}",
                image=immagine_finta(f"scatto-{n}.jpg", (n * 40, 90, 40)),
            )
            for n in range(3)
        ]

    def test_senza_scelta_vale_la_prima_del_portale(self):
        self.assertEqual(self.casa.cover_image, self.foto[0])

    def test_la_foto_spuntata_diventa_la_copertina(self):
        self.foto[2].copertina = True
        self.foto[2].save()
        self.assertEqual(self.casa.cover_image, self.foto[2])

    def test_una_sola_copertina_per_immobile(self):
        self.foto[1].copertina = True
        self.foto[1].save()
        self.foto[2].copertina = True
        self.foto[2].save()

        self.foto[1].refresh_from_db()
        self.assertFalse(self.foto[1].copertina, "la precedente doveva liberarsi")
        self.assertEqual(
            list(PropertyImage.objects.filter(property=self.casa, copertina=True)),
            [self.foto[2]],
        )

    def test_la_scelta_non_esce_dall_immobile(self):
        """Due immobili hanno ognuno la propria copertina, senza interferenze."""
        altra = Property.objects.create(
            title="Casa accanto", location="Siniscola", status=Property.Status.PUBLISHED
        )
        sua = PropertyImage.objects.create(
            property=altra, order=0, image=immagine_finta("altra-0.jpg")
        )
        sua.copertina = True
        sua.save()

        self.foto[1].copertina = True
        self.foto[1].save()

        sua.refresh_from_db()
        self.assertTrue(sua.copertina)
        self.assertEqual(altra.cover_image, sua)

    def test_se_la_copertina_sparisce_si_torna_alla_prima(self):
        self.foto[2].copertina = True
        self.foto[2].save()
        self.foto[2].delete()
        self.assertEqual(self.casa.cover_image, self.foto[0])

    def test_la_scelta_vale_su_scheda_pagina_e_anteprima_social(self):
        self.foto[2].copertina = True
        self.foto[2].save()
        scelta = self.foto[2].image.url

        elenco = self.client.get(reverse("properties:list")).content.decode()
        self.assertIn(scelta, elenco)

        scheda = self.client.get(self.casa.get_absolute_url()).content.decode()
        # og:image e prima foto della galleria: la stessa, quella scelta.
        self.assertIn(f'property="og:image" content="http://testserver{scelta}"', scheda)
        self.assertIn(f'id="gallery-main-img" src="{scelta}"', scheda)

    def test_la_scelta_apre_anche_la_galleria(self):
        self.foto[2].copertina = True
        self.foto[2].save()
        galleria = self.client.get(reverse("core:gallery")).content.decode()
        # La galleria prende due scatti per immobile: la copertina e' il primo.
        posizione_scelta = galleria.find(self.foto[2].image.url)
        posizione_prima = galleria.find(self.foto[0].image.url)
        self.assertNotEqual(posizione_scelta, -1)
        self.assertLess(posizione_scelta, posizione_prima)

    def test_i_testi_alternativi_contano_dalla_copertina(self):
        """La numerazione negli alt segue l'ordine con cui le foto si vedono.

        Il primo scatto ha un alt suo — «tipologia a localita'» — e gli altri
        sono numerati. Scelta la copertina, quel testo deve spostarsi su di
        lei: altrimenti in pagina la prima foto direbbe «foto 3 di 3».
        """
        from properties.utils import rinumera_foto

        self.foto[2].copertina = True
        self.foto[2].save()
        rinumera_foto(self.casa)

        for foto in self.foto:
            foto.refresh_from_db()
        self.assertIn("a La Caletta", self.foto[2].alt_text)
        self.assertIn("foto 2 di 3", self.foto[0].alt_text)
        self.assertIn("foto 3 di 3", self.foto[1].alt_text)

    def test_la_rinumerazione_non_perde_la_scelta(self):
        """La rinumerazione gira a ogni rilascio: non deve disfare la scelta."""
        from properties.utils import rinumera_foto

        self.foto[1].copertina = True
        self.foto[1].save()
        rinumera_foto(self.casa)

        self.assertEqual(self.casa.cover_image, PropertyImage.objects.get(pk=self.foto[1].pk))

    def test_la_spunta_e_accanto_all_anteprima_nell_amministrazione(self):
        """Si sceglie guardando le foto: la casella sta di fianco alla miniatura."""
        staff = get_user_model().objects.create_superuser(
            username="capo", email="capo@example.com", password="prova-12345"
        )
        self.client.force_login(staff)
        pagina = self.client.get(
            reverse("admin:properties_property_change", args=[self.casa.pk])
        ).content.decode()

        self.assertIn("images-0-copertina", pagina)
        self.assertLess(pagina.index("Anteprima"), pagina.index("Copertina"))


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class NomiInVetrinaTest(TestCase):
    """I nomi riscritti per la vetrina devono sopravvivere ai rilasci.

    L'importazione gira a ogni rilascio e riscrive i campi dallo snapshot del
    portale: senza una guardia, il primo rilascio utile rimetterebbe «Villetta
    G2» al posto del nome scelto, in silenzio.
    """

    RECORD = {
        "external_id": "999", "titolo": "Villetta Z9", "stato": "published",
        "categoria": "Aparthotel", "citta": "Budoni", "indirizzo": "Via Prova 1",
        "descrizione": "Due righe di descrizione.", "camere": 2, "bagni": 1,
        "ospiti": 4, "booking_url": "", "codice_licenza": "", "dotazioni": [],
        "lat": "40.5", "lon": "9.6", "foto": [],
    }

    def _importa(self, titolo=None):
        """Un giro di importazione per un solo immobile, senza rete."""
        from properties.management.commands.import_properties import Command

        record = dict(self.RECORD)
        if titolo:
            record["titolo"] = titolo
        return Command()._salva(record, {})[0]

    def test_la_prima_importazione_prende_il_nome_dal_portale(self):
        immobile = self._importa()
        self.assertEqual(immobile.title, "Villetta Z9")
        self.assertEqual(immobile.valori_portale["title"], "Villetta Z9")

    def test_un_nome_riscritto_a_mano_non_viene_sovrascritto(self):
        immobile = self._importa()
        Property.objects.filter(pk=immobile.pk).update(
            title="[Villetta Z9] 300mt dalla spiaggia", meta_title=""
        )

        self._importa()

        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "[Villetta Z9] 300mt dalla spiaggia")
        self.assertEqual(immobile.meta_title, "", "il meta title tornerebbe al nome vecchio")

    def test_il_nome_del_portale_resta_registrato_anche_dopo(self):
        """Cambiando nome sul portale, in vetrina resta quello scelto qui."""
        immobile = self._importa()
        Property.objects.filter(pk=immobile.pk).update(title="[Villetta Z9] 300mt dalla spiaggia")

        self._importa(titolo="Villetta Z9 - rev 2")

        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "[Villetta Z9] 300mt dalla spiaggia")
        self.assertEqual(immobile.valori_portale["title"], "Villetta Z9 - rev 2")

    def test_gli_aparthotel_del_portale_diventano_appartamenti(self):
        """«Aparthotel» promette servizi alberghieri che questi immobili non hanno."""
        immobile = self._importa()
        self.assertEqual(immobile.category, Property.Category.APARTMENT)
        self.assertEqual(
            immobile.valori_portale["category"], Property.Category.APARTMENT,
            "va registrato il valore corretto, non quello grezzo: altrimenti al "
            "giro dopo la riga risulterebbe riscritta a mano",
        )

    def test_una_tipologia_corretta_a_mano_non_viene_sovrascritta(self):
        """Segnata una villa nell'amministrazione, deve restare una villa."""
        immobile = self._importa()
        Property.objects.filter(pk=immobile.pk).update(category=Property.Category.VILLA)

        self._importa()

        immobile.refresh_from_db()
        self.assertEqual(immobile.category, Property.Category.VILLA)

    def test_le_altre_tipologie_del_portale_restano_come_sono(self):
        immobile = self._importa()
        Property.objects.filter(pk=immobile.pk).delete()
        record = dict(self.RECORD, categoria="Villa")
        from properties.management.commands.import_properties import Command
        immobile = Command()._salva(record, {})[0]
        self.assertEqual(immobile.category, Property.Category.VILLA)

    def test_senza_riscritture_l_importazione_aggiorna_come_prima(self):
        immobile = self._importa()
        self._importa(titolo="Villetta Z9 - rev 2")
        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "Villetta Z9 - rev 2")


class NomiInVetrinaApplicatiTest(TestCase):
    """Il comando che mette in vetrina i nomi scelti."""

    def _immobile(self, titolo, external_id="104"):
        return Property.objects.create(
            title=titolo, location="Siniscola", external_id=external_id,
            valori_portale={"title": titolo}, meta_title=f"{titolo} a Siniscola",
        )

    def _applica(self, scrivi=True):
        uscita = io.StringIO()
        call_command("applica_nomi_vetrina", *(["--applica"] if scrivi else []), stdout=uscita)
        return uscita.getvalue()

    def test_riscrive_il_nome_di_lavoro_del_portale(self):
        immobile = self._immobile("Via Gallura - Siniscola")

        self._applica()

        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "Vacanze da sogno in Sardegna [APT a 7km dal mare]")
        self.assertEqual(immobile.meta_title, "", "il meta title terrebbe il nome vecchio")

    def test_l_indirizzo_della_pagina_non_si_sposta(self):
        """Cambiare lo slug romperebbe i collegamenti gia' in giro."""
        immobile = self._immobile("Via Gallura - Siniscola")
        slug = immobile.slug

        self._applica()

        immobile.refresh_from_db()
        self.assertEqual(immobile.slug, slug)

    def test_e_ripetibile(self):
        """Gira a ogni rilascio: la seconda volta non deve fare niente."""
        immobile = self._immobile("Via Gallura - Siniscola")
        self._applica()
        seconda = self._applica()

        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "Vacanze da sogno in Sardegna [APT a 7km dal mare]")
        self.assertIn("gia' a posto", seconda)

    def test_non_tocca_un_nome_gia_cambiato_a_mano(self):
        immobile = self._immobile("Via Gallura - Siniscola")
        Property.objects.filter(pk=immobile.pk).update(title="Nome scelto dal gestore")

        self._applica()

        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "Nome scelto dal gestore")

    def test_senza_applica_non_scrive(self):
        immobile = self._immobile("Via Gallura - Siniscola")

        uscita = self._applica(scrivi=False)

        immobile.refresh_from_db()
        self.assertEqual(immobile.title, "Via Gallura - Siniscola")
        self.assertIn("da applicare", uscita)

    def test_l_elenco_dei_nomi_non_ha_ripetizioni(self):
        """Due righe sullo stesso immobile sarebbero una in silenzio ignorata."""
        from properties.nomi_vetrina import NOMI

        identificatori = [n[0] for n in NOMI]
        self.assertEqual(len(identificatori), len(set(identificatori)))
        nuovi = [n[2] for n in NOMI]
        self.assertEqual(len(nuovi), len(set(nuovi)))
