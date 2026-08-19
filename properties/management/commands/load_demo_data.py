"""Carica gli immobili demo usando le fotografie reali in properties/demo_media/.

Uso:
    python manage.py load_demo_data
    python manage.py load_demo_data --reset   # elimina prima i dati esistenti

NOTA SUI CONTENUTI
    Le fotografie sono quelle del sito evhousemanagement.com. I titoli, le
    località e le descrizioni sono invece PLACEHOLDER redazionali, scritti per
    corrispondere a cio' che si vede nelle foto: vanno sostituiti con i dati
    reali di ciascun immobile prima della pubblicazione.
"""

import pathlib

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from properties.models import Property, PropertyImage

DEMO_MEDIA = pathlib.Path(__file__).resolve().parents[2] / "demo_media"

DEMO_PROPERTIES = [
    {
        "slug": "villa-con-piscina-e-uliveto",
        "title": "Villa con Piscina e Uliveto",
        "location": "Orosei",
        "short_description": (
            "Villa indipendente con piscina privata immersa in un uliveto, "
            "ampia zona pranzo all'aperto con barbecue in muratura."
        ),
        "description": (
            "Una villa indipendente circondata da ulivi secolari, con piscina privata "
            "affacciata sulla campagna e sul profilo delle montagne.\n\n"
            "L'area esterna è il cuore della casa: solarium attrezzato con lettini, "
            "zona pranzo ombreggiata per otto persone e barbecue in muratura per le "
            "cene all'aperto. La vegetazione mediterranea garantisce ombra e "
            "riservatezza per tutta la giornata.\n\n"
            "Gli interni si sviluppano su un unico livello, con quattro camere da letto "
            "e tre bagni. Cucina completamente attrezzata, aria condizionata in tutti "
            "gli ambienti e parcheggio privato all'interno della proprietà'."
        ),
        "bedrooms": 4,
        "bathrooms": 3,
        "guests": 8,
        "featured": True,
        "booking_url": "",
        "meta_title": "Villa con Piscina e Uliveto a Orosei | EV House Management",
        "meta_description": (
            "Villa con piscina privata e uliveto a Orosei: 4 camere, 3 bagni, "
            "fino a 8 ospiti. Gestione EV House Management."
        ),
        "images": [
            ("villa-uliveto-1-piscina-uliveto.jpg", "Piscina privata circondata da ulivi"),
            ("villa-uliveto-2-piscina-vista-monti.jpg", "Piscina con vista sulle montagne"),
            ("villa-uliveto-3-pranzo-esterno-barbecue.jpg", "Zona pranzo all'aperto con barbecue in muratura"),
            ("villa-uliveto-4-tavola-apparecchiata.jpg", "Tavola apparecchiata in giardino"),
        ],
    },
    {
        "slug": "casa-in-pietra-nel-borgo",
        "title": "Casa in Pietra nel Borgo",
        "location": "Dorgali",
        "short_description": (
            "Casa storica in pietra ristrutturata nel centro del borgo, con soggiorno "
            "a doppia altezza e travi a vista."
        ),
        "description": (
            "Una casa tradizionale in pietra nel cuore del borgo, ristrutturata "
            "conservando i muri originali, le travi in legno e i solai a vista.\n\n"
            "Il soggiorno si sviluppa a doppia altezza, con soppalco raggiungibile da "
            "una scala interna e parete in pietra a vista. La camera da letto principale "
            "si affaccia sul soppalco, sotto il tetto in legno.\n\n"
            "All'esterno una corte privata con tavolo da pranzo all'ombra degli alberi, "
            "ideale per le cene estive. Il centro del paese, i negozi e i ristoranti "
            "sono raggiungibili a piedi in pochi minuti."
        ),
        "bedrooms": 2,
        "bathrooms": 1,
        "guests": 4,
        "featured": True,
        "booking_url": "",
        "meta_title": "Casa in Pietra a Dorgali | EV House Management",
        "meta_description": (
            "Casa storica in pietra a Dorgali con soggiorno a doppia altezza: "
            "2 camere, 1 bagno, fino a 4 ospiti."
        ),
        "images": [
            ("casa-pietra-1-soggiorno-travi.jpg", "Soggiorno con travi a vista e soppalco"),
            ("casa-pietra-2-camera-soppalco.jpg", "Camera da letto sotto il tetto in legno"),
            ("casa-pietra-3-pranzo-sotto-gli-alberi.jpg", "Tavolo da pranzo nella corte alberata"),
            ("casa-pietra-4-esterno-scala-pietra.jpg", "Ingresso e scala esterna in pietra"),
        ],
    },
    {
        "slug": "appartamento-moderno-centro",
        "title": "Appartamento Moderno",
        "location": "Cala Gonone",
        "short_description": (
            "Appartamento luminoso e recentemente rinnovato, con cucina a vista, "
            "arredi contemporanei e ampie finestre."
        ),
        "description": (
            "Un appartamento completamente rinnovato, pensato per soggiorni comodi "
            "sia brevi sia di media durata.\n\n"
            "La zona giorno unisce soggiorno e cucina a vista: divano, smart TV e "
            "tavolo da pranzo per quattro persone. Le grandi finestre garantiscono "
            "luce naturale per tutta la giornata.\n\n"
            "Due camere da letto con armadiatura dedicata, bagno con doccia e zona "
            "guardaroba all'ingresso. Aria condizionata, connessione Wi-Fi e "
            "lavastoviglie. A pochi minuti dal mare e dai servizi."
        ),
        "bedrooms": 2,
        "bathrooms": 1,
        "guests": 4,
        "featured": True,
        "booking_url": "",
        "meta_title": "Appartamento Moderno a Cala Gonone | EV House Management",
        "meta_description": (
            "Appartamento rinnovato a Cala Gonone: 2 camere, 1 bagno, fino a 4 ospiti. "
            "Luminoso e a pochi minuti dal mare."
        ),
        "images": [
            ("appartamento-moderno-1-cucina-soggiorno.jpg", "Zona giorno con cucina a vista"),
            ("appartamento-moderno-2-soggiorno-divano.jpg", "Soggiorno con divano e smart TV"),
            ("appartamento-moderno-3-cucina-pranzo.jpg", "Cucina attrezzata con tavolo da pranzo"),
            ("appartamento-moderno-4-ingresso-scala.jpg", "Ingresso luminoso con scala interna"),
            ("appartamento-moderno-5-zona-guardaroba.jpg", "Zona guardaroba"),
        ],
    },
    {
        "slug": "villa-con-solarium-e-idromassaggio",
        "title": "Villa con Solarium e Idromassaggio",
        "location": "Siniscola",
        "short_description": (
            "Villa con giardino, piscina e ampio solarium sul tetto attrezzato con "
            "vasca idromassaggio."
        ),
        "description": (
            "Una villa moderna con giardino curato e piscina, pensata per soggiorni "
            "all'insegna del relax.\n\n"
            "Il solarium panoramico sul tetto è attrezzato con vasca idromassaggio, "
            "lettini e ombrellone: uno spazio riservato per godersi il tramonto. Al "
            "piano terra la piscina è circondata da un'area verde con lettini e "
            "zona d'ombra.\n\n"
            "Tre camere da letto, due bagni e un ampio portico esterno arredato per "
            "pranzi e cene. Parcheggio privato e Wi-Fi in tutta la proprietà'."
        ),
        "bedrooms": 3,
        "bathrooms": 2,
        "guests": 6,
        "featured": False,
        "booking_url": "",
        "meta_title": "Villa con Solarium e Idromassaggio a Siniscola | EV House Management",
        "meta_description": (
            "Villa con piscina e solarium con idromassaggio a Siniscola: "
            "3 camere, 2 bagni, fino a 6 ospiti."
        ),
        "images": [
            ("villa-solarium-1-solarium-idromassaggio.jpg", "Solarium sul tetto con vasca idromassaggio"),
            ("villa-solarium-2-piscina-lettini.jpg", "Piscina con lettini e area verde"),
            ("villa-solarium-3-esterno-giardino.jpg", "Esterno della villa con giardino e portico"),
        ],
    },
]


class Command(BaseCommand):
    help = "Carica gli immobili demo con le fotografie reali di properties/demo_media/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina tutti gli immobili esistenti prima di caricare i dati demo.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not DEMO_MEDIA.is_dir():
            raise CommandError(f"Cartella delle foto demo non trovata: {DEMO_MEDIA}")

        missing = [
            name
            for data in DEMO_PROPERTIES
            for name, _ in data["images"]
            if not (DEMO_MEDIA / name).is_file()
        ]
        if missing:
            raise CommandError(
                "Foto mancanti in properties/demo_media/:\n  - " + "\n  - ".join(missing)
            )

        if options["reset"]:
            deleted, _ = Property.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Eliminati {deleted} oggetti esistenti."))

        for data in DEMO_PROPERTIES:
            fields = {k: v for k, v in data.items() if k != "images"}
            obj, created = Property.objects.update_or_create(
                slug=fields.pop("slug"), defaults=fields
            )

            if not created and obj.images.exists():
                self.stdout.write(f"  = {obj.title} (già presente, immagini invariate)")
                continue

            obj.images.all().delete()
            for order, (name, alt) in enumerate(data["images"]):
                image = PropertyImage(property=obj, alt_text=alt, order=order)
                image.image.save(
                    name, ContentFile((DEMO_MEDIA / name).read_bytes()), save=False
                )
                image.save()

            verb = "Creato" if created else "Aggiornato"
            self.stdout.write(
                self.style.SUCCESS(
                    f"  + {verb}: {obj.title} ({len(data['images'])} foto)"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompletato. Immobili: {Property.objects.count()}, "
                f"immagini: {PropertyImage.objects.count()}."
            )
        )
