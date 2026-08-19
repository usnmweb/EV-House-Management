#!/usr/bin/env bash
# Eseguito da Render a ogni rilascio. Si ferma al primo errore.
set -o errexit

pip install -r requirements.txt

# I file statici finiscono in STATIC_ROOT, da dove li serve WhiteNoise.
python manage.py collectstatic --no-input

python manage.py migrate --no-input

# Importa gli immobili dallo snapshot versionato e scarica le fotografie.
# È ripetibile: le foto già presenti sul disco vengono riconosciute e saltate,
# quindi dal secondo rilascio in poi questo passaggio è quasi immediato.
python manage.py import_properties
