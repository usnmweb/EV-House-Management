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

# I nomi da vetrina al posto di quelli di lavoro del portale. Va qui e non in
# una migration perche' su un ambiente nuovo le migration girano quando gli
# immobili non esistono ancora. E' ripetibile: tocca solo i titoli ancora
# uguali a quelli del portale.
python manage.py applica_nomi_vetrina --applica

# Le copertine del Giornale riusano fotografie degli immobili, il cui percorso
# contiene il mese di scaricamento: se qui e' diverso da quello scritto nella
# migrazione, le copertine vanno ripuntate. Va dopo l'import, che e' quello
# che mette le fotografie sul disco.
python manage.py ripara_copertine --applica
