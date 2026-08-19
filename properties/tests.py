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
