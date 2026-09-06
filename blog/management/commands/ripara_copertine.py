"""Rimette in sesto le copertine del Giornale che puntano a un file assente.

Le copertine di partenza non sono immagini editoriali: riusano fotografie
degli immobili, gia' presenti in MEDIA_ROOT. Il guaio e' che il percorso di
quelle fotografie contiene la data di scaricamento (`upload_to` e'
`properties/%Y/%m/`), mentre la migrazione che crea gli articoli lo scrive
fisso. In locale le due cose coincidono; su un ambiente dove le foto sono
state scaricate in un altro mese no, e la copertina finisce in 404.

Il comando cerca, per ogni copertina mancante, una fotografia di immobile con
lo stesso nome di file e ci punta. Confronta solo il nome, non la cartella:
e' esattamente la parte che l'importatore mantiene stabile
(`{slug}-{n}.jpg`), mentre la cartella e' quella che cambia.

    python manage.py ripara_copertine            # elenca e basta
    python manage.py ripara_copertine --applica  # scrive

Le copertine il cui file esiste non vengono toccate: quando arriveranno le
foto editoriali caricate dall'amministrazione, il comando le lascera' stare
anche se continua a girare a ogni rilascio.
"""

import pathlib

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from blog.models import Article
from properties.models import PropertyImage


class Command(BaseCommand):
    help = "Ripunta le copertine del Giornale rimaste senza file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--applica", action="store_true",
            help="Salva le correzioni. Senza, il comando si limita a elencare.",
        )

    def handle(self, *args, **opzioni):
        applica = opzioni["applica"]

        rotte = [
            a for a in Article.objects.exclude(copertina="")
            if not default_storage.exists(a.copertina.name)
        ]
        if not rotte:
            self.stdout.write("Copertine: nessuna da riparare.")
            return

        # Una sola lettura della tabella foto: gli articoli sono pochi, ma
        # cosi' il costo non cresce col loro numero.
        per_nome = {}
        for nome in PropertyImage.objects.values_list("image", flat=True):
            per_nome.setdefault(pathlib.PurePosixPath(nome).name, nome)

        riparate = perse = 0
        for articolo in rotte:
            cercato = pathlib.PurePosixPath(articolo.copertina.name).name
            trovato = per_nome.get(cercato)
            if trovato is None:
                perse += 1
                self.stdout.write(self.style.WARNING(
                    f"  senza riscontro: {articolo.slug} -> {articolo.copertina.name}"
                ))
                continue

            riparate += 1
            self.stdout.write(f"  {articolo.slug}: {articolo.copertina.name} -> {trovato}")
            if applica:
                # update() e non save(): salvare l'articolo ricalcolerebbe
                # slug e tempo di lettura, che qui non c'entrano nulla.
                Article.objects.filter(pk=articolo.pk).update(copertina=trovato)

        coda = "riparate" if applica else "da riparare (aggiungi --applica)"
        self.stdout.write(self.style.SUCCESS(f"Copertine {coda}: {riparate}."))
        if perse:
            self.stdout.write(self.style.WARNING(
                f"Copertine senza fotografia corrispondente: {perse}."
            ))
