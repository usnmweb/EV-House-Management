"""Mette in vetrina i nomi scelti al posto di quelli di lavoro del portale.

    python manage.py applica_nomi_vetrina              # elenca e basta
    python manage.py applica_nomi_vetrina --applica    # scrive

Gira in `build.sh` dopo `import_properties`, e non come migration, perche' su
un ambiente nuovo le migration girano quando gli immobili non ci sono ancora:
una migration non troverebbe niente da rinominare e i nomi non arriverebbero
mai. Dopo l'importazione, invece, le righe ci sono sempre.

E' ripetibile: riscrive solo i titoli ancora uguali a quelli del portale.
"""

from django.core.management.base import BaseCommand

from properties.models import Property
from properties.nomi_vetrina import NOMI, applica


class Command(BaseCommand):
    help = "Applica i nomi da vetrina agli immobili importati dal portale."

    def add_arguments(self, parser):
        parser.add_argument(
            "--applica", action="store_true",
            help="Scrive i nomi. Senza, il comando si limita a elencare.",
        )

    def handle(self, *args, **opzioni):
        scrivi = opzioni["applica"]
        fatti = applica(Property, scrivi=scrivi)

        for external_id, vecchio, nuovo in fatti:
            self.stdout.write(f"  {vecchio}  ->  {nuovo}")

        if not fatti:
            self.stdout.write("Nomi in vetrina: gia' a posto.")
            return

        coda = "applicati" if scrivi else "da applicare (aggiungi --applica)"
        self.stdout.write(self.style.SUCCESS(f"Nomi {coda}: {len(fatti)} su {len(NOMI)}."))
