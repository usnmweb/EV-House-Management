"""Importa gli immobili dal portale EV House Management.

I dati vengono da uno snapshot versionato in properties/data/portale_immobili.json,
estratto da evhouse.kross.travel. Le fotografie non sono nel repository: il comando
le scarica dal CDN del portale dentro MEDIA_ROOT, saltando quelle già presenti.

    python manage.py import_properties                 # importa tutto
    python manage.py import_properties --no-images     # solo i dati testuali
    python manage.py import_properties --limit 10      # primi 10, per una prova
    python manage.py import_properties --reset         # svuota prima di importare
"""

import json
import pathlib
import re
import time
import urllib.error
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import Truncator

from properties.models import Amenity, Property, PropertyImage
from properties.utils import testo_alternativo

SNAPSHOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "portale_immobili.json"
# Il portale antepone alla descrizione un blocco di dati: "Descrizione",
# ospiti, camere, bagni, codici. Sono cose che il sito tiene gia' nei propri
# campi, e in cima al testo diventano rumore — in home, dentro le schede, si
# leggeva "Descrizione 4 Ospiti 2 camere da letto 1 bagno Codice..." al posto
# della presentazione dell'immobile.
RIGA_DI_SERVIZIO = re.compile(
    r"""^\s*[-–•]?\s*(?:      # a volte la riga e' puntata: "-1° piano"
          descrizione\b[^:\n]*:?            # "Descrizione", "DESCRIZIONE ALLOGGIO:"
        | \d+(?:[.,]\d+)?\s+ospit[ei]
        | \d+(?:[.,]\d+)?\s+camer[ae](?:\s+da\s+letto)?
        | \d+(?:[.,]\d+)?\s+bagn[oi]
        | \d+(?:[.,]\d+)?\s+lett[oi]
        | \d+(?:[.,]\d+)?\s*°?\s*piano          # "1° piano"
        | \d+(?:[.,]\d+)?\s*m\s*[²2]\b           # "100 m2"
        | codice\s+licenza\s*:.*
        | codice\s+identificativo\s+nazionale\s*:.*
        | cin\s*:.*
    )\s*$""",
    re.IGNORECASE | re.VERBOSE,
)


def ripulisci_descrizione(testo):
    """Toglie l'intestazione del portale, fermandosi alla prima riga di prosa.

    Salta solo le righe in testa: una riga di servizio che comparisse in mezzo
    al testo resta dov'e', perche' li' potrebbe essere voluta. Se dopo la
    pulizia non resta nulla si tiene il testo originale — meglio un'intestazione
    che una scheda vuota.
    """
    righe = testo.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(righe) and (not righe[i].strip() or RIGA_DI_SERVIZIO.match(righe[i])):
        i += 1
    return "\n".join(righe[i:]).strip() or testo.strip()


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://evhouse.kross.travel/",
}


def riferimento(url):
    """Nome del file sul CDN, usato per non riscaricare la stessa foto."""
    return url.rsplit("/", 1)[-1].rsplit(".", 1)[0]


class Command(BaseCommand):
    help = "Importa gli immobili dallo snapshot del portale."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Elimina gli immobili esistenti prima di importare.")
        parser.add_argument("--no-images", action="store_true",
                            help="Non scaricare le fotografie.")
        parser.add_argument("--limit", type=int, default=0,
                            help="Importa solo i primi N immobili.")

    def handle(self, *args, **options):
        if not SNAPSHOT.is_file():
            raise CommandError(f"Snapshot non trovato: {SNAPSHOT}")

        dati = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        if options["limit"]:
            dati = dati[: options["limit"]]

        if options["reset"]:
            n, _ = Property.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Eliminati {n} oggetti."))

        # Le dotazioni sono condivise fra immobili: si creano una volta sola.
        nomi = sorted({a.strip() for r in dati for a in r["dotazioni"] if a.strip()})
        for nome in nomi:
            Amenity.objects.get_or_create(name=nome)
        mappa = {a.name: a for a in Amenity.objects.all()}
        self.stdout.write(f"Dotazioni disponibili: {len(mappa)}")

        creati = aggiornati = foto_scaricate = foto_saltate = errori = 0

        for i, r in enumerate(dati, 1):
            with transaction.atomic():
                obj, nuovo = self._salva(r, mappa)
            creati += nuovo
            aggiornati += (not nuovo)

            if not options["no_images"]:
                a, b, c = self._immagini(obj, r)
                foto_scaricate += a
                foto_saltate += b
                errori += c

            stato = "nuovo" if nuovo else "agg."
            self.stdout.write(
                f"  {i:3}/{len(dati)}  [{stato}] {obj.title[:52]:<52} "
                f"{obj.get_status_display()}  {obj.images.count()} foto"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nImmobili: {Property.objects.count()} totali "
            f"({Property.objects.published().count()} pubblicati, "
            f"{creati} creati, {aggiornati} aggiornati).\n"
            f"Foto: {PropertyImage.objects.count()} in archivio "
            f"({foto_scaricate} scaricate ora, {foto_saltate} già presenti, {errori} errori)."
        ))

    # ------------------------------------------------------------------ dati

    def _salva(self, r, mappa):
        descrizione = ripulisci_descrizione(r["descrizione"])
        breve = Truncator(descrizione.replace("\n", " ")).chars(300, truncate="…")
        citta = r["citta"] or "Sardegna"

        campi = {
            "title": r["titolo"][:200],
            "status": r["stato"],
            "category": r["categoria"],
            "location": citta,
            "address": r["indirizzo"][:250],
            "short_description": breve,
            "description": descrizione,
            "bedrooms": r["camere"],
            "bathrooms": r["bagni"],
            "guests": r["ospiti"],
            "booking_url": r["booking_url"],
            "license_code": r["codice_licenza"][:60],
            "meta_title": Truncator(f"{r['titolo']} a {citta}").chars(70, truncate=""),
            "meta_description": Truncator(breve).chars(160, truncate=""),
        }
        for chiave, sorgente in (("latitude", "lat"), ("longitude", "lon")):
            try:
                campi[chiave] = round(float(r[sorgente]), 7)
            except (TypeError, ValueError):
                campi[chiave] = None

        obj, nuovo = Property.objects.update_or_create(
            external_id=r["external_id"], defaults=campi
        )
        obj.amenities.set([mappa[a] for a in r["dotazioni"] if a in mappa])
        return obj, nuovo

    # ----------------------------------------------------------------- foto

    def _immagini(self, obj, r):
        scaricate = saltate = errori = 0
        totale = len(r["foto"])
        # L'alt viene ricalcolato anche per le foto gia' presenti: cosi' una
        # rilettura dello snapshot corregge i testi senza riscaricare nulla.
        esistenti = {i.source_ref: i for i in obj.images.all()}

        for ordine, url in enumerate(r["foto"]):
            ref = riferimento(url)
            alt = testo_alternativo(obj.title, obj.category, obj.location, ordine, totale)

            gia = esistenti.get(ref)
            if gia is not None:
                if gia.alt_text != alt or gia.order != ordine:
                    gia.alt_text = alt
                    gia.order = ordine
                    gia.save(update_fields=["alt_text", "order"])
                saltate += 1
                continue
            try:
                richiesta = urllib.request.Request(url, headers=HEADERS)
                contenuto = urllib.request.urlopen(richiesta, timeout=45).read()
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                errori += 1
                self.stderr.write(f"      foto non scaricata ({ref}): {exc}")
                continue

            immagine = PropertyImage(
                property=obj, alt_text=alt, order=ordine, source_ref=ref
            )
            immagine.image.save(f"{obj.slug}-{ordine + 1}.jpg",
                                ContentFile(contenuto), save=False)
            immagine.save()
            scaricate += 1
            time.sleep(0.15)   # cortesia verso il CDN del portale

        return scaricate, saltate, errori
