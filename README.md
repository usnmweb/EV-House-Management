# EV House Management

Sito vetrina per una societa di property management: presentazione degli immobili in
gestione, servizi offerti, galleria e modulo contatti.

---

## Stack

| Componente | Versione |
|---|---|
| Python | 3.12 (richiesto 3.11+) |
| Django | 5.2 LTS |
| Pillow | 12.x (gestione immagini) |
| Database | SQLite (file `db.sqlite3`) |

Nessuna dipendenza JavaScript esterna: il front-end usa CSS e JS vanilla.
L'unica risorsa remota sono i font Google (Cormorant Garamond + Inter).

---

## Installazione

Dalla cartella del progetto:

```bash
# 1. Virtualenv (richiede Python 3.11+)
python3.12 -m venv venv

# 2. Attivazione
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Dipendenze
pip install -r requirements.txt

# 4. Database
python manage.py migrate

# 5. Dati demo (4 immobili con immagini placeholder generate localmente)
python manage.py load_demo_data

# 6. Utente amministratore
python manage.py createsuperuser

# 7. Avvio
python manage.py runserver
```

Il sito e disponibile su <http://localhost:8000> e l'admin su
<http://localhost:8000/admin/>.

> Se `python3.12` non e presente su macOS: `brew install python@3.12`.

---

## Comandi utili

```bash
python manage.py load_demo_data           # inserisce/aggiorna i 4 immobili demo
python manage.py load_demo_data --reset   # cancella tutti gli immobili e li ricrea
python manage.py makemigrations           # dopo ogni modifica ai modelli
python manage.py migrate
python manage.py check                    # controlli di integrita
python manage.py check --deploy           # controlli aggiuntivi per la produzione
python manage.py collectstatic            # solo in produzione
```

I file in `media/` sono esclusi dal versionamento: dopo un clone rigenera le
immagini demo con `python manage.py load_demo_data`.

---

## Struttura

```
EV-House-Management/
├── config/              # settings, urls, wsgi/asgi del progetto
├── core/                # pagine statiche, form contatti, robots.txt
│   ├── context_processors.py
│   ├── forms.py
│   ├── urls.py
│   └── views.py
├── properties/          # immobili
│   ├── management/commands/load_demo_data.py
│   ├── migrations/
│   ├── admin.py
│   ├── models.py        # Property, PropertyImage
│   ├── sitemaps.py
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── base.html        # header, footer, blocchi title/meta/content
│   ├── core/            # home, services, gallery, contact
│   ├── properties/      # property_list, property_detail, _property_card
│   └── legal/           # privacy, cookies
├── static/              # css, js, img (sorgenti)
├── media/               # upload immagini immobili (non versionato)
├── manage.py
├── requirements.txt
└── README.md
```

---

## Fotografie

Le 16 fotografie in `properties/demo_media/` provengono dal sito attuale
evhousemanagement.com (CDN globaluserfiles.com), ridimensionate a 1600px di
larghezza e ottimizzate per il web. In `static/img/` ci sono il logo ufficiale
(`logo-ev.png`, PNG con trasparenza, quindi utilizzabile su fondo chiaro e scuro)
e l'immagine Open Graph (`og-default.jpg`) generata dal logo.

`python manage.py load_demo_data` copia le foto da `properties/demo_media/` dentro
`media/`, raggruppate in 4 immobili. A differenza delle foto, **titoli, localita e
descrizioni degli immobili sono placeholder redazionali**: sono stati scritti per
corrispondere a cio' che si vede nelle immagini, non ai dati reali degli immobili.

---

## Rotte

| URL | Descrizione |
|---|---|
| `/` | Home: hero, immobili in evidenza, servizi, CTA |
| `/properties/` | Elenco immobili con filtri per localita e numero di ospiti |
| `/properties/<slug>/` | Dettaglio immobile: galleria, specifiche, CTA di prenotazione |
| `/services/` | Servizi offerti |
| `/gallery/` | Galleria di tutte le immagini |
| `/contact/` | Modulo contatti |
| `/privacy/` | Privacy Policy |
| `/cookies/` | Cookie Policy |
| `/sitemap.xml` | Sitemap generata dinamicamente |
| `/robots.txt` | Consente l'indicizzazione, esclude `/admin/` |
| `/admin/` | Pannello di amministrazione |

---

## SEO

- `<title>` e meta description dinamici per ogni pagina; i campi `meta_title` e
  `meta_description` dell'immobile hanno la precedenza, con fallback automatico su
  titolo e descrizione breve.
- Tag `canonical`, Open Graph e Twitter Card in `base.html`.
- `sitemap.xml` generata da `properties/sitemaps.py` (pagine statiche + dettaglio
  immobili, con `lastmod`). Usa l'host della richiesta, quindi non richiede
  configurazione aggiuntiva tra sviluppo e produzione.
- JSON-LD `VacationRental` + `BreadcrumbList` su ogni pagina di dettaglio.
- Le pagine legali sono marcate `noindex, follow`.

---

## Hero della home

La prima schermata usa una fotografia a piena larghezza (`static/img/hero-*.jpg`,
tre varianti servite via `srcset`: 1000 / 1600 / 2400px).

Scelte tecniche:

- **L'hero ha una palette propria** (`--hero-text`, `--hero-accent`, ...) fissa
  chiaro-su-scuro: sopra la foto il testo deve restare leggibile a prescindere dal
  tema attivo, quindi non eredita i token della pagina.
- **Scrim a due livelli** sopra la foto: uno scurimento diagonale sul lato del testo
  e un velo superiore che stacca l'header.
- **Dissolvenza inferiore ad altezza fissa** (`--hero-fade`, 140px su mobile e 190px
  da 900px in su), applicata con `.hero-scrim::after`. Il `padding-bottom` dell'hero
  riserva esattamente quello spazio, cosi' nessun contenuto finisce sbiadito.
  La sfumatura parte da `--bg-0` (lo sfondo della pagina con alpha 0) e non da
  `transparent`: quest'ultimo equivale a nero trasparente e su tema chiaro
  produrrebbe una banda grigia.
- **Header trasparente** finche' non si scorre: la classe `has-hero` sul `<body>`
  attiva la variante, e il JS aggiunge `is-solid` all'header oltre i 40px di scroll
  (o quando si apre il menu mobile). L'hero ha `margin-top` negativo pari a
  `--header-h`, cosi' la foto passa dietro all'header.
- Le tre statistiche stanno in una **fascia separata sotto l'hero** (`.stats-band`),
  non sovrapposte alla foto: impilate sotto i 600px, su tre colonne oltre.

Per cambiare l'immagine basta sostituire i tre file `hero-*.jpg` mantenendo il
rapporto 16:9.

---

## Tema chiaro / scuro

Il sito supporta entrambi i temi, con un pulsante nell'header (icona luna/sole).

Tre stati possibili:

| Stato | Comportamento |
|---|---|
| Nessuna scelta salvata | Segue `prefers-color-scheme` del sistema operativo, anche se cambia mentre la pagina e aperta |
| `data-theme="light"` | Chiaro forzato dall'utente |
| `data-theme="dark"` | Scuro forzato dall'utente |

Come funziona:

- I colori sono definiti come token CSS in `static/css/style.css`. La palette chiara
  sta su `:root`; quella scura e ridefinita due volte, sotto
  `@media (prefers-color-scheme: dark)` (con guardia `:root:not([data-theme="light"])`)
  e sotto `:root[data-theme="dark"]`, cosi il toggle vince in entrambe le direzioni.
- La scelta viene salvata in `localStorage` con chiave `ev-theme`.
- Uno script inline in `<head>` (`templates/base.html`) applica il tema salvato
  **prima del primo paint**, per evitare il flash di tema errato al caricamento.
- La proprieta `color-scheme` viene impostata insieme ai token, cosi anche i controlli
  nativi (select, input, checkbox, scrollbar) seguono il tema.
- Il `<meta name="theme-color">` viene aggiornato via JS, per la barra del browser su mobile.

Per cambiare i colori basta modificare i token nei tre blocchi in cima al foglio di stile:
`--bg`, `--surface`, `--border`, `--text`, `--text-muted`, `--accent`, `--on-accent` e simili.

---

## Modulo contatti

Campi: nome, email, telefono (facoltativo), messaggio, checkbox privacy obbligatoria,
piu un campo honeypot nascosto anti-spam.

In questa fase **non viene inviata nessuna email**: i dati validati vengono stampati
nella console del server (`core/views.py`). Dopo l'invio l'utente viene reindirizzato
con un messaggio di conferma (pattern POST/redirect/GET).

Per attivare l'invio reale, imposta le variabili SMTP indicate sotto e sostituisci il
blocco `print(...)` con `django.core.mail.send_mail`.

---

## Variabili d'ambiente

Tutte opzionali in sviluppo: il progetto parte senza configurazione. In produzione
imposta almeno le prime tre.

| Variabile | Default | Note |
|---|---|---|
| `DJANGO_SECRET_KEY` | chiave di sviluppo | **Obbligatoria in produzione.** |
| `DJANGO_DEBUG` | `True` | Impostare a `False` in produzione. |
| `DJANGO_ALLOWED_HOSTS` | `*` | Elenco separato da virgole. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | vuoto | Es. `https://www.esempio.ch`. |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` se `DEBUG=False` | Redirect HTTPS. |
| `DJANGO_SECURE_HSTS_SECONDS` | `31536000` | Attivo solo con `DEBUG=False`. |
| `DJANGO_EMAIL_BACKEND` | backend console | Per SMTP reale usare `django.core.mail.backends.smtp.EmailBackend`. |
| `EMAIL_HOST` / `EMAIL_PORT` | vuoto / `587` | Server SMTP. |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | vuoto | Credenziali SMTP. |
| `EMAIL_USE_TLS` | `True` | |
| `DEFAULT_FROM_EMAIL` | `noreply@evhousemanagement.com` | Mittente. |
| `CONTACT_RECIPIENT_EMAIL` | `evhouse92@gmail.com` | Destinatario del modulo contatti. |
| `SITE_NAME` | `EV House Management` | Usato nei `<title>`. |
| `SITE_DOMAIN` | `www.evhousemanagement.com` | Dominio di riferimento. |
| `COMPANY_LEGAL_NAME` | `EV House Management` | Footer e JSON-LD. **Manca la ragione sociale completa.** |
| `COMPANY_VAT` | `01634110918` | P.IVA reale, presa dal sito attuale. |
| `COMPANY_ADDRESS` | `Sardegna, Italia` | **Da sostituire con l'indirizzo completo.** |
| `COMPANY_EMAIL` | `evhouse92@gmail.com` | Email reale, presa dal sito attuale. |
| `COMPANY_PHONE` | vuoto | Se vuoto la riga sparisce da footer e contatti. |

Le variabili vengono lette con `os.environ`: esportale nella shell, nel file di
servizio systemd o nel pannello dell'hosting. Non e incluso un loader `.env`.

Esempio per la produzione:

```bash
export DJANGO_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(50))')"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="www.evhousemanagement.ch,evhousemanagement.ch"
```

---

## Da completare prima della pubblicazione

- [ ] Completare i dati societari: ragione sociale completa, indirizzo, telefono,
      e i campi `[da inserire]` nel footer e nelle pagine legali.
- [ ] Far revisionare Privacy e Cookie Policy da un consulente legale (GDPR / LPD).
- [ ] Sostituire titoli, localita e descrizioni demo degli immobili con i dati reali
      (le fotografie sono gia' quelle vere).
- [ ] Impostare `DJANGO_SECRET_KEY` e `DJANGO_DEBUG=False`.
- [ ] Restringere `DJANGO_ALLOWED_HOSTS` al dominio reale.
- [ ] Configurare l'invio email SMTP e attivare `send_mail` nel modulo contatti.
- [ ] Servire `static/` e `media/` tramite web server (in produzione Django non li serve).
