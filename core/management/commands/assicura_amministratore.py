"""Crea l'utente dell'amministrazione sul sito pubblicato, se manca.

Le credenziali arrivano da tre variabili d'ambiente, impostate nel pannello di
Render e mai nel repository:

    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_PASSWORD
    DJANGO_SUPERUSER_EMAIL      (facoltativa)

Gira in `build.sh` a ogni rilascio, ed e' fatto per poterlo fare:

- se l'utente esiste gia', non lo tocca. In particolare non gli reimposta la
  password: se qualcuno la cambia dall'amministrazione, il rilascio dopo non
  deve rimettere quella vecchia;
- se le variabili mancano, lo dice e si ferma senza errore. Un rilascio non
  deve fallire perche' manca un utente: il sito funziona lo stesso, e l'utente
  si puo' aggiungere dopo.

Perche' non `createsuperuser --noinput`, che legge le stesse variabili: fallisce
se l'utente esiste gia', e al secondo rilascio fermerebbe tutto il deploy.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea l'utente amministratore dalle variabili d'ambiente, se non esiste."

    def handle(self, *args, **opzioni):
        nome = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()

        if not nome or not password:
            self.stdout.write(
                "Amministratore: variabili DJANGO_SUPERUSER_USERNAME e "
                "DJANGO_SUPERUSER_PASSWORD non impostate, nessun utente creato."
            )
            return

        Utente = get_user_model()
        if Utente.objects.filter(username=nome).exists():
            self.stdout.write(f"Amministratore: «{nome}» esiste già, non modificato.")
            return

        Utente.objects.create_superuser(username=nome, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Amministratore: «{nome}» creato."))
