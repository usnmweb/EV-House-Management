"""Trova ed elimina gli scatti ripetuti dentro lo stesso immobile.

Il portale a volte serve due volte la stessa fotografia sotto indirizzi
diversi: i byte non coincidono — sono ricompressioni distinte — quindi il
controllo su `source_ref` dell'importatore non le vede passare. Qui il
confronto e' su cosa si vede, con l'impronta percettiva di properties.utils.

    python manage.py pulisci_foto_doppie              # elenca e basta
    python manage.py pulisci_foto_doppie --applica    # elimina
    python manage.py pulisci_foto_doppie --soglia 8   # piu' permissivo

Senza --applica non tocca niente: su una cancellazione di contenuti il modo
predefinito deve essere quello che non fa danni.
"""

import collections

from django.core.management.base import BaseCommand

from properties.models import PropertyImage
from properties.utils import (
    SOGLIA_DOPPIONE,
    impronta_visiva,
    rinumera_foto,
    scarto_visivo,
)


class Command(BaseCommand):
    help = "Elimina le fotografie ripetute all'interno dello stesso immobile."

    def add_arguments(self, parser):
        parser.add_argument(
            "--applica", action="store_true",
            help="Elimina davvero. Senza, il comando si limita a elencare.",
        )
        parser.add_argument(
            "--soglia", type=int, default=SOGLIA_DOPPIONE,
            help=f"Scarto massimo per considerare due scatti uguali (predefinito {SOGLIA_DOPPIONE}).",
        )

    def handle(self, *args, **opzioni):
        applica = opzioni["applica"]
        soglia = opzioni["soglia"]

        per_immobile = collections.defaultdict(list)
        for foto in PropertyImage.objects.select_related("property").order_by(
            "property_id", "order", "id"
        ):
            per_immobile[foto.property_id].append(foto)

        da_eliminare = []
        illeggibili = 0

        for scatti in per_immobile.values():
            tenute = []          # (foto, impronta) di quelle che restano
            for foto in scatti:
                try:
                    impronta = impronta_visiva(foto.image.path)
                except Exception:
                    illeggibili += 1
                    tenute.append((foto, None))
                    continue

                gemella = next(
                    (t for t, imp in tenute
                     if imp is not None and scarto_visivo(imp, impronta) <= soglia),
                    None,
                )
                if gemella is None:
                    tenute.append((foto, impronta))
                else:
                    # Si tiene sempre la prima: l'ordine viene dal portale ed e'
                    # quello scelto da chi ha caricato le fotografie.
                    da_eliminare.append((foto, gemella))

        for foto, gemella in da_eliminare:
            self.stdout.write(
                f"  {foto.property.title[:44]:<44}  "
                f"{foto.image.name.split('/')[-1]}  =  {gemella.image.name.split('/')[-1]}"
            )

        if illeggibili:
            self.stdout.write(self.style.WARNING(f"\nFile illeggibili, saltati: {illeggibili}"))

        if not da_eliminare:
            self.stdout.write(self.style.SUCCESS("\nNessuno scatto ripetuto."))
            if applica:
                self._rinumera_tutti(per_immobile)
            return

        if not applica:
            self.stdout.write(self.style.WARNING(
                f"\n{len(da_eliminare)} scatti ripetuti. "
                "Niente e' stato toccato: ripeti con --applica per eliminarli."
            ))
            return

        immobili_toccati = set()
        for foto, _ in da_eliminare:
            immobili_toccati.add(foto.property_id)
            percorso = foto.image.name
            foto.delete()
            # Il file si cancella solo se nessun'altra riga lo usa: due righe
            # sullo stesso file sarebbero rare, ma cancellarlo sotto i piedi
            # della superstite lascerebbe una scheda con un buco.
            if not PropertyImage.objects.filter(image=percorso).exists():
                try:
                    foto.image.storage.delete(percorso)
                except Exception:
                    pass

        # Rinumerazione di tutti, non solo dei toccati: e' l'occasione per
        # rimettere in riga anche eventuali numerazioni rimaste indietro da
        # cancellazioni fatte a mano dall'amministrazione.
        righe = self._rinumera_tutti(per_immobile)

        self.stdout.write(self.style.SUCCESS(
            f"\nEliminati {len(da_eliminare)} scatti ripetuti "
            f"in {len(immobili_toccati)} immobili. "
            f"Ordine e testi alternativi rifatti su {righe} fotografie."
        ))

    def _rinumera_tutti(self, per_immobile):
        immobili = {foto[0].property for foto in per_immobile.values() if foto}
        return sum(rinumera_foto(p) for p in immobili)
