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
**Nessuna risorsa remota**: i caratteri sono ospitati insieme al sito, quindi
una pagina non apre connessioni verso domini di terzi.

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

## Messa online (Render)

> **Il servizio deve essere un Web Service, non uno Static Site.** Uno Static Site
> chiede una *publish directory* — una cartella di file già costruiti — e Django non
> ne ha una: da lì l'errore `Publish directory ... does not exist`. Se hai già creato
> un Static Site, eliminalo e ricomincia da qui.

Il repository contiene `render.yaml`, quindi il modo più rapido è il **Blueprint**:

1. Su Render: **New +** → **Blueprint**.
2. Collega il repository: Render legge `render.yaml` e propone il servizio già configurato.
3. Al primo rilascio compila `DJANGO_ALLOWED_HOSTS` con il dominio assegnato
   (es. `ev-house-management.onrender.com`).
4. Crea l'utente amministratore dalla Shell del servizio:
   `python manage.py createsuperuser`.

### Se crei il servizio a mano

Il blueprint è la strada consigliata proprio perché imposta tutto da solo. Creando
il servizio a mano (**New +** → **Web Service**, runtime *Python*) **niente di
`render.yaml` viene letto**: build command, comando di avvio e variabili d'ambiente
vanno compilati uno per uno.

| Campo | Valore |
|---|---|
| Build command | `./build.sh` |
| Start command | `gunicorn config.wsgi:application` |

Il build command suggerito da Render per Django si ferma a `pip install` e
`collectstatic`: **non esegue le migrazioni**, e il sito parte con il database vuoto
(`no such table: properties_property`). `build.sh` fa anche `migrate` e
`import_properties`.

Variabili d'ambiente da impostare a mano:

| Variabile | Valore |
|---|---|
| `DJANGO_SECRET_KEY` | una stringa casuale lunga |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | il dominio assegnato |
| `DJANGO_DB_PATH` | `/var/data/db.sqlite3` *(solo con disco persistente)* |
| `DJANGO_MEDIA_ROOT` | `/var/data/media` *(solo con disco persistente)* |

**`DJANGO_DEBUG=False` non è un dettaglio estetico.** Con `DEBUG=True` una qualsiasi
eccezione mostra al pubblico la pagina di debug di Django, che elenca l'intera
configurazione: percorsi, app installate, impostazioni email, host consentiti. Va
impostata prima di rendere l'indirizzo raggiungibile a chiunque.

La versione di Python è fissata da `.python-version`; senza, Render usa la propria
predefinita, che può non coincidere con quella di sviluppo.

### Cosa fa il rilascio

`build.sh` installa le dipendenze, esegue `collectstatic` e `migrate`, poi lancia
`import_properties`, che importa gli 84 immobili dallo snapshot e scarica le
fotografie. **Il primo rilascio richiede una decina di minuti** per via delle 533
immagini; dai successivi il comando riconosce le foto già presenti e finisce subito.

### Il disco persistente non è opzionale

`render.yaml` monta un disco su `/var/data` e ci fa puntare database e fotografie
tramite `DJANGO_DB_PATH` e `DJANGO_MEDIA_ROOT`.

Senza disco persistente il filesystem è effimero: a ogni rilascio o riavvio si
perdono le immagini e — cosa più seria — **tutto quello che è stato modificato
dall'amministrazione**. Gli immobili tornerebbero allo stato dello snapshot,
vanificando il requisito di gestibilità da backoffice.

Il disco richiede un piano a pagamento (nel blueprint è `starter`). Sul piano
gratuito il sito funziona come vetrina dimostrativa, ma va messo in conto che le
modifiche fatte dall'amministrazione non sopravvivono al riavvio.

### File statici

Sono serviti da **WhiteNoise** dal processo Django, senza bisogno di un web server
davanti. In produzione usa lo storage con manifest: i nomi dei file portano un hash,
quindi si possono mettere in cache a lungo senza rischiare di servire versioni vecchie.

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

## Immobili e fotografie

Gli immobili provengono dal portale prenotazioni **evhouse.kross.travel**, dove
sono già in gestione. Lo snapshot dei dati è versionato in
`properties/data/portale_immobili.json` (84 immobili, 293 KB); le fotografie no,
perché pesano circa 92 MB.

```bash
python manage.py import_properties               # dati + fotografie
python manage.py import_properties --no-images   # solo i dati testuali
python manage.py import_properties --limit 10    # prova sui primi 10
python manage.py import_properties --reset       # svuota prima di importare
```

Il comando è **ripetibile**: le foto già scaricate vengono riconosciute dal campo
`source_ref` e saltate, quindi una seconda esecuzione non riscarica nulla.

### Pulizia delle descrizioni

Il portale antepone al testo un blocco di dati — `Descrizione`, ospiti, camere,
bagni, superficie, piano, codice licenza — che il sito tiene già nei propri
campi. In pagina diventava rumore: le schede si aprivano con «Descrizione 4
Ospiti 2 camere da letto 1 bagno Codice Identificativo Nazionale: IT090…» invece
che con la presentazione dell'immobile.

`ripulisci_descrizione()` in `import_properties.py` toglie quelle righe, e si
ferma alla prima riga di prosa: una riga di servizio che comparisse *in mezzo* al
testo resta dov'è, perché lì potrebbe essere voluta. Se dopo la pulizia non
restasse nulla, si tiene il testo originale.

Vale per tutti e 63 i pubblicati, e siccome `meta_description` deriva da
`short_description`, le descrizioni per i motori di ricerca sono migliorate di
conseguenza. Lo snapshot JSON resta il testo grezzo del portale: la pulizia
avviene in importazione, così il dato di partenza rimane fedele alla sorgente.

### Pubblicati e bozze

Degli 84 immobili, **63 sono pubblicati** e **21 restano in bozza**: sono quelli a
cui manca la descrizione, mancano le dotazioni o hanno meno di cinque fotografie.
Le bozze non compaiono in elenco, non entrano nella sitemap e la loro pagina
risponde 404. Si pubblicano dall'amministrazione, singolarmente o con l'azione
massiva, una volta completati i dati.

Ogni immobile porta con sé la propria scheda sul portale: dalla pagina di dettaglio
il pulsante di prenotazione rimanda lì, perché disponibilità e tariffe restano
gestite dal portale (fuori perimetro, §7 del capitolato).

Le fotografie sono limitate a **8 per immobile** (533 in tutto), scaricate dal CDN
del portale alla dimensione da 1310px.

---

## Consenso cookie

Il banner compare al primo accesso e resta finché non si sceglie. **Rifiuta e
Accetta hanno lo stesso rilievo visivo**: il GDPR non ammette che negare il
consenso costi più fatica che concederlo. "Personalizza" apre il dettaglio per
categoria.

La scelta finisce in `localStorage` e in un cookie tecnico `ev_cookie_consent`
(leggibile anche lato server), e viene esposta a `window.evConsenso`.

Oggi il sito **non usa alcuno strumento di misurazione**: la relativa categoria è
predisposta ma inattiva, e la Cookie Policy lo dice. Quando se ne aggiungerà uno,
va agganciato a `window.evConsenso.misurazione` senza rimettere mano al banner.
Dalla Cookie Policy si riaprono le preferenze per cambiare idea.

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

- **Title e meta description per pagina**: generati dalla vista, con i campi
  `meta_title` e `meta_description` dell'immobile a prevalere quando compilati.
  Sulle 63 schede sono tutti unici e nessuno supera i 160 caratteri.
- **URL leggibili**: `/properties/<slug>/`, slug derivato dal titolo.
- **`sitemap.xml`** generata da `properties/sitemaps.py`: pagine statiche più le
  sole schede pubblicate, con `lastmod`. Usa l'host della richiesta, quindi non
  va configurata diversamente fra sviluppo e produzione.
- **`robots.txt`** consente tutto tranne `/admin/` e dichiara la sitemap.
- **Dati strutturati** su ogni pagina:
  - `LodgingBusiness` dell'azienda, in `base.html`, con un `@id` a cui le altre
    entità rimandano invece di ripetere gli stessi dati;
  - `BreadcrumbList` su tutte le pagine interne;
  - `ItemList` sull'elenco immobili;
  - `VacationRental` sulla scheda, con indirizzo, coordinate, dotazioni,
    capienza e l'azione di prenotazione verso il portale.
- **Testo alternativo**: composto per singola fotografia da
  `properties/utils.testo_alternativo()`. Il portale non fornisce didascalie per
  scatto, quindi l'alt non descrive cosa si vede — inventarlo sarebbe peggio che
  ometterlo — ma dichiara immobile, tipologia, luogo e posizione in galleria:
  533 testi distinti su 533 immagini. Le miniature della galleria hanno
  `alt=""` perché decorative: il pulsante che le contiene ha già `aria-label`.
- Le pagine legali sono marcate `noindex, follow`.

---

## Hero della home

La prima schermata usa un **video di sfondo** (`static/video/hero.mp4`) con sotto
una fotografia (`static/img/hero-video-*.jpg`, tre varianti servite via `srcset`:
1000 / 1600 / 2400px). La fotografia e' un fotogramma del video stesso, quindi i
due strati combaciano e il passaggio non si vede.

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

### Il video

Due varianti, scelte da `main.js` sulla larghezza della finestra:

| file | risoluzione | peso | quando |
|---|---|---|---|
| `static/video/hero-960.mp4` | 960x540 | 700 KB | finestra fino a 760px |
| `static/video/hero.mp4` | 1920x1080 | 3,0 MB | oltre |

Solo H.264: su questo materiale (ripresa aerea, molto fogliame) la stessa clip in
VP9/WebM veniva **piu' pesante** della MP4, quindi un secondo formato sarebbe
stato peso in piu' senza guadagno.

**Quando parte.** Il `<video>` nel markup non ha `src`: e' `main.js` a metterlo,
dopo l'evento `load`, e solo se ha senso. Salta lo scaricamento se l'utente ha
chiesto di ridurre le animazioni, se ha attivo il risparmio dati
(`navigator.connection.saveData`) o se e' su una rete 2G. In tutti quei casi
l'hero resta sulla fotografia, che e' completa e nessuno si accorge di nulla.
Lo stesso vale se JavaScript e' spento, se l'avvio automatico viene negato o se
il formato viene rifiutato.

**Quando si ferma.** Il video va in pausa quando l'hero esce dallo schermo e
quando la scheda passa in secondo piano: niente decodifica inutile, niente
batteria sprecata. E c'e' un bottone di pausa in basso a destra dell'hero,
richiesto dal criterio WCAG 2.2.2 (un movimento che parte da solo e dura piu' di
cinque secondi deve poter essere fermato). Il bottone compare solo quando il
video parte davvero.

**L'anello e' cucito.** La clip originale e' una discesa con drone: ripartendo da
capo si vedrebbe un salto di quota. La coda viene dissolta sulla testa, cosi' il
punto di giunzione non si nota. La differenza media di luminanza fra l'ultimo e
il primo fotogramma e' 5,5/255, contro 30,4 fra due fotogrammi qualsiasi a
distanza di otto secondi.

### Rigenerare i file dal master

Il master (4K, 45 MB) non sta in repository — e' in `.gitignore`. Da un nuovo
video si rifa' tutto cosi', sostituendo `SORGENTE` e la durata:

```bash
SRC=video_villaggio_con_piscina.mp4
D=16      # durata della sorgente in secondi
F=1.5     # durata della dissolvenza che cuce l'anello

for W in 960 1920; do
  [ $W = 960 ] && CRF=33 || CRF=31
  [ $W = 960 ] && OUT=static/video/hero-960.mp4 || OUT=static/video/hero.mp4
  ffmpeg -i "$SRC" -filter_complex "\
[0:v]scale=$W:-2,fps=25,format=yuv420p,split=3[s0][s1][s2];\
[s0]trim=start=$(echo "$D-$F"|bc):end=$D,setpts=PTS-STARTPTS,fps=25[coda];\
[s1]trim=start=0:end=$F,setpts=PTS-STARTPTS,fps=25[testa];\
[s2]trim=start=$F:end=$(echo "$D-$F"|bc),setpts=PTS-STARTPTS,fps=25[resto];\
[coda][testa]xfade=transition=fade:duration=$F:offset=0[giunto];\
[giunto][resto]concat=n=2:v=1:a=0[v]" -map "[v]" -an \
    -c:v libx264 -preset slow -crf $CRF -pix_fmt yuv420p -movflags +faststart -y "$OUT"
done

# la fotografia di riserva: lo stesso fotogramma da cui parte l'anello
for W in 1000 1600 2400; do
  ffmpeg -ss $(echo "$D-$F"|bc) -i "$SRC" -frames:v 1 \
    -vf "scale=$W:-2:flags=lanczos" -q:v 4 -y "static/img/hero-video-$W.jpg"
done
```

Due dettagli che fanno fallire il comando se si tolgono: `fps=25` prima dello
split (senza, `xfade` rifiuta l'ingresso perche' il frame rate non e' costante) e
di nuovo `fps=25` dopo ogni `setpts`, perche' `trim` perde quel dato.

`-movflags +faststart` sposta l'indice del file in testa: senza, il browser deve
scaricare tutto prima di poter cominciare.

### Richieste parziali

Safari riproduce un `<video>` solo se il server risponde alle richieste per
intervalli di byte. WhiteNoise le gestisce (risponde `206 Partial Content`),
quindi in produzione va. Il server di sviluppo di Django no: restituisce sempre
il file intero. Chrome e Firefox non se ne accorgono, Safari in locale potrebbe.

---

## Vetrina degli immobili in evidenza

Nove immobili in carosello sulla home, con una decima tessera che porta
all'elenco completo. Lo stesso markup si comporta in due modi.

**Il modo normale** è quello bloccato: la sezione si ferma a schermo pieno e lo
scorrimento verticale diventa avanzamento orizzontale. Finite le schede, la
pagina riprende da sola a scorrere in verticale. Vale su desktop, tablet e
telefono: il pollice scorre come sempre, è la fila che si sposta.

**Il ripiego** è una fila che si trascina in orizzontale, con aggancio alle
schede (`scroll-snap`). Si attiva con «riduci movimento», senza JavaScript, e
sotto i **520px di altezza** — cioè in pratica solo col telefono coricato, dove
non resterebbe spazio per una scheda leggibile.

Il vincolo è l'altezza e non la larghezza: quello che serve al blocco è poter
mostrare una scheda intera sopra la piega, e una finestra stretta ma alta ci
riesce benissimo. `main.js` mette la classe `e-bloccata` sulla sezione e la
toglie se la finestra cambia o se la preferenza cambia — il passaggio avviene a
caldo, senza ricaricare.

### Su schermo piccolo

Tre aggiustamenti, tutti sotto i 760px:

- tessere da 260px invece di 300, così si vede una scheda intera più uno
  spiraglio della successiva;
- via il testo introduttivo e l'estratto della scheda: il titolo dice già cosa
  sono le schede, e su uno schermo basso ogni riga di testo la paga la
  fotografia (sull'iPhone piccolo la foto passa da 134 a 185px);
- titolo della sezione più contenuto, così non si mangia l'altezza utile.

**L'altezza della scheda non è indovinata in `vh`**: il blocco è una colonna
flessibile e la fila è l'unico elemento che si allunga, quindi prende lo spazio
che avanza dopo intestazione e barra. Non esiste combinazione di schermo e
lunghezza del titolo che possa far sforare il contenuto, e il guadagno vale
anche sul desktop.

**Le altezze si misurano in `svh`, non in `vh` né in `dvh`.** Su iOS `100vh` è
l'altezza con la barra dell'indirizzo già ritirata, quindi il blocco
sborderebbe; `100dvh` cambia *mentre* la barra si ritira, e cambierebbe
l'altezza della sezione a metà corsa — con essa il rapporto fra scorrimento e
spostamento. `svh` è l'unica delle tre che sta ferma. Per lo stesso motivo il
calcolo in JavaScript legge l'altezza reale del blocco invece di
`window.innerHeight`, che su iOS varia: così i due numeri non possono
divergere.

Non c'è nessun `preventDefault` sulla rotella: la pagina scorre come sempre, è la
fila che si sposta in funzione di quanto si è scorso. Rotella, trackpad, frecce,
barra laterale, ricerca nel testo e ripristino della posizione continuano a
funzionare.

### Due motori, un solo layout

Le timeline di scorrimento del CSS non ci sono ovunque: oggi mancano a Firefox e
a Safari prima della 26. Il blocco non può dipendere da loro, altrimenti su
quei browser la sezione scorre e basta.

|  | chi muove la fila |
|---|---|
| Con `animation-timeline` | il CSS, sul compositor: non tocca il main thread e non perde un fotogramma nemmeno scorrendo di scatto |
| Senza | `main.js`, che a ogni frame utile scrive `--avanzamento` (0 → 1) sulla sezione |

Il layout è dichiarato **una volta sola**, sotto `.showcase.e-bloccata`, e la
fila ha una sola regola di movimento:

```css
transform: translateX(calc(var(--avanzamento, 0) * (-100% + 100vw)));
```

Dove le timeline ci sono, il blocco `@supports` mette un'animazione sulla stessa
proprietà, e **un'animazione in corso ha la precedenza sulle dichiarazioni
normali**: prende il sopravvento da sola, senza che nessuno debba disattivare
l'altra strada. È la stessa regola della cascata che altrove in questo progetto
ha rotto il sollevamento delle schede — qui invece è quella che tiene insieme i
due motori senza duplicare una riga di layout.

L'ascoltatore di scroll viene aggiunto solo dove serve davvero: sui browser
capaci non esiste.

### Come sono legate le misure

```
corsa           = larghezza della fila − larghezza della finestra
tratto da scorrere = corsa / --ritmo
altezza sezione = altezza del blocco + tratto da scorrere
altezza blocco  = 100vh − altezza dell'intestazione
```

**`--ritmo`** dice quanti pixel percorre la fila per ogni pixel scorso, ed è
l'unico numero da toccare per accorciare o allungare la sezione. A 1440×900,
con dieci tessere:

| `--ritmo` | resta incollata per | in schermate |
|---|---|---|
| 1 | 2016 px | 2,24 |
| 1,5 | 1344 px | 1,49 |
| **2** (in vigore) | **1008 px** | **1,12** |
| 2,5 | 806 px | 0,90 |
| 3 | 672 px | 0,75 |

Sotto l'1 non ha senso: la fila andrebbe più lenta della rotella. Sopra il 2,5
le schede passano troppo in fretta per essere lette.

Nessuno scorrimento è a vuoto, a nessun ritmo — verificato in Chrome e in
Firefox: l'intervallo dell'animazione è
`contain 0%` → `contain 100%`, cioè esattamente il tratto in cui la sezione
copre lo schermo, che è anche quello in cui resta incollata. La fila finisce la
corsa nell'istante in cui il blocco si stacca — misurato, all'ultimo pixel del
tratto l'ultima tessera è esattamente sul margine destro del contenitore.

Perché torni, l'altezza deve partire dall'altezza del **blocco** e non da
`100vh`: `contain` vale altezza-della-sezione meno altezza-utile, e l'altezza
utile è già scontata dell'intestazione. Per lo stesso motivo serve
`view-timeline-inset: var(--header-h) 0`, che sposta l'inizio della timeline
sotto l'intestazione appiccicata: senza, timeline e blocco vanno fuori passo di
quei pixel.

Il calcolo in JavaScript arriva allo stesso numero per altra via:
`(altezza intestazione − top della sezione) / tratto`, ritagliato fra 0 e 1 —
normalizzato, quindi indipendente da `--ritmo`. Il ritmo serve invece a
`main.js` per portare in vista una scheda raggiunta col tabulatore: per spostare
la fila di `delta` bisogna scorrere di `delta / ritmo`.

### Dettagli che sembrano opzionali e non lo sono

- **La larghezza della fila si calcola, non si deduce.** `width: max-content`
  sembrava la scelta pulita, ma su un contenitore flex Firefox non lo ricava
  dalla base flessibile delle tessere: misurava **11694px** al posto di 3936.
  Tutto quello che si appoggiava a quella larghezza ne usciva sballato — la fila
  correva a velocità tripla, finiva la corsa a un sesto del tratto e poi
  restava incollata a vuoto per il resto. Le tessere hanno larghezza fissa,
  quindi `--larghezza-fila` le somma e basta.
- Per lo stesso motivo lo spostamento è `translateX(calc(… * --corsa))` e non
  `translateX(calc(… * (-100% + 100vw)))`: la percentuale si riferisce alla
  larghezza calcolata dell'elemento, che è proprio il dato di cui non ci si può
  fidare ovunque.
- `overflow: clip` e non `hidden` sul blocco. `hidden` creerebbe un contenitore
  di scorrimento: portando a fuoco col tabulatore una scheda fuori campo, il
  browser lo farebbe scorrere di nascosto e la fila andrebbe fuori sincrono con
  la pagina.
- Niente `data-reveal` sulle schede del carosello (`senza_reveal=1`
  nell'`include`). La rivelazione dipende dalla posizione verticale, che dentro
  un contenitore bloccato non avanza mai: le schede resterebbero invisibili.
- Titolo a **due righe fisse**, non massime. Con l'altezza massima un titolo
  corto lascia meno spazio e le fotografie non sono più allineate lungo la fila.

### Per cambiare il numero di immobili

Due punti, da tenere allineati: `[:9]` in `core/views.py` e `--tessere` in
`style.css`, che vale immobili + 1 per la tessera finale.

---

## Pagina Servizi

Rifatta partendo dal difetto principale: i **quattro passi** del percorso erano
resi con le stesse schede dei **sei servizi**, quindi niente diceva che fossero
consecutivi. Una sequenza mostrata come griglia non si legge come sequenza.

La pagina ora è in quattro momenti, ognuno con una forma diversa:

| sezione | forma | cosa risponde |
|---|---|---|
| Testata | titolo + occhiello | dove sono |
| Come si comincia | percorso in quattro passi | da dove parto |
| Cosa comprende | sei voci con icona | cosa ricevo |
| Chi fa cosa | due colonne a confronto | e io cosa devo fare |

Gli sfondi si alternano chiaro / scuro / chiaro: due sezioni consecutive con lo
stesso fondo si fonderebbero in una sola. Spostando il percorso in testa vanno
riassegnati, non basta muovere il blocco.

**La testata porta l'H1.** Prima la pagina cominciava con un `<h2>` e non aveva
un titolo di primo livello — un difetto per gli screen reader e per i motori di
ricerca. *Restano senza H1 `/properties/`, `/gallery/` e `/contact/`.*

**Le icone non sono decorazione**: sono quello che rende scorribile con lo
sguardo un elenco di sei voci altrimenti da leggere riga per riga. Stanno in
`core/_icona_servizio.html`, una sola chiave per servizio nella vista, nessun
markup da marcare `safe`. Solo tratto, `currentColor`, 24×24.

**La numerazione 01–06 è sparita dai servizi.** Non erano passi: numerarli
suggeriva un ordine che non esiste. I numeri restano dove l'ordine c'è
davvero, nel percorso.

**Il confronto in due colonne** è la sezione che risponde alla domanda vera del
proprietario. Il messaggio lo dà la lunghezza delle due liste — tre voci contro
sei — non un aggettivo.

### Il percorso

Quattro passi uniti da una linea che si traccia mentre si scorre, con i numeri
che si riempiono al passaggio. In riga sopra i 900px, in colonna sotto.

**La linea è un tratto per passo, non una linea sola.** La prima versione era
un unico elemento tirato da un capo all'altro, e sbordava: `right: 26px` lo
porta al bordo del contenitore, non al centro dell'ultimo nodo. Si poteva
calcolare — con N colonne uguali il centro dell'ultimo nodo cade a
`100% − (100%/N − gap·(N−1)/N − nodo/2)` — ma in colonna non basta, perché le
righe hanno altezze diverse e non c'è formula.

Con un `::before` per passo non c'è niente da calcolare: ogni tratto va dal
proprio nodo a quello dopo e resta esatto a qualunque misura, con qualunque
numero di passi. Sull'ultimo `content: none`. In più ogni tratto si disegna
quando si arriva al proprio passo, quindi la sequenza si costruisce sotto gli
occhi invece di essere già lì.

### Perché griglia e percorso usano `data-reveal="fade"`

La rivelazione normale sposta in verticale di 22px, scaglionata. Dove gli
elementi sono uniti — da una linea, o da una griglia a filetti come l'elenco dei
servizi — bastano pochi pixel di sfasamento perché si legga come
**disallineamento** invece che come animazione. E su una timeline di
scorrimento lo sfasamento resta finché non si scorre oltre: fermandosi a metà
si vedrebbe una fila storta.

La variante `fade` scaglionata solo nell'opacità dà la stessa sequenza senza
mai spostare niente. Verificato a metà rivelazione: tutti i bordi superiori
allo stesso pixel, tutte le trasformazioni all'identità.


## Galleria

Rifatta partendo da un difetto di dati, non di grafica: erano le **prime 120
fotografie ordinate per titolo dell'immobile**. Otto scatti per casa, quindi in
pagina finivano gli immobili di quindici case su sessantatre. Le altre
quarantotto non comparivano affatto.

E cliccare una foto portava alla scheda dell'immobile: la galleria era un muro
di miniature che non si potevano guardare.

Ora sono **due scatti per immobile, presi a giro** — 126 in tutto, tutti e 63
gli immobili rappresentati, e due tessere vicine vengono quasi sempre da case
diverse.

### Il mosaico

Le fotografie sono tutte in 3:2. Con tessere tutte uguali una griglia di 126
immagini somiglia a un foglio di calcolo, quindi il mosaico alterna quattro
forme su un ritmo di sei: **grande (2×2), normale, normale, alta (1×2),
normale, larga (2×1)**. Il taglio lo fa `object-fit: cover`, nessuna foto viene
deformata.

Il ritmo lo assegna `main.js` con `data-forma`, e lo **riassegna dopo ogni
filtro**. Le regole `:nth-child` in CSS servono da ripiego per chi non ha
JavaScript, ma da sole non basterebbero: `:nth-child` conta anche le tessere
nascoste, quindi filtrando il ritmo si sfalderebbe.

Sotto i 1000px le tessere tornano tutte uguali: su due colonne il ritmo non si
leggerebbe comunque.

### I filtri

Per località, solo quelle con almeno due immobili — sotto, un filtro
selezionerebbe una manciata di scatti. Sono nascosti nel markup e scoperti da
`main.js`: mostrare comandi che senza JavaScript non fanno niente è peggio che
non mostrarli. Il filtro attivo finisce nell'indirizzo (`#luogo=la-caletta`) con
`replaceState`, così una vista si può mandare a qualcuno e viene ripristinata al
caricamento.

### Il visore

Un `<dialog>` aperto con `showModal()`. La scelta non è stilistica: porta con sé
gratis quattro cose che in un finto modale vanno scritte a mano, e quasi sempre
scritte male —

- la **trappola del fuoco**;
- la chiusura con **Esc**;
- l'**inertizzazione** del resto della pagina;
- il **ritorno del fuoco** alla tessera di partenza.

Verificato: aprendo con Invio da una tessera a fuoco, il fuoco entra nel visore
e alla chiusura torna **esattamente su quella tessera**.

Si sfoglia con le frecce, con i pulsanti, o col dito (soglia 45px). Le vicine
si precaricano, quindi il passaggio è istantaneo. Il contatore usa
`font-variant-numeric: tabular-nums` per non ballare. Alle estremità le frecce
si disabilitano invece di girare in tondo. Alla chiusura la sorgente si svuota:
una foto a piena risoluzione tenuta in memoria dopo non serve.

Senza JavaScript, o su un browser senza `<dialog>`, ogni tessera resta il link
alla scheda dell'immobile che è già nel markup: la galleria funziona,
semplicemente non si sfoglia.

### Due dettagli che sembrano pignoleria

- **`.tessera[hidden] { display: none }`** serve davvero. La regola d'autore
  `display: block` batte quella del browser per `[hidden]`, quindi senza questa
  riga le tessere filtrate resterebbero in pagina.
- La scena del visore ha **`grid-template-rows: minmax(0, 1fr)`**. Con la riga
  `auto` si dimensiona sul contenuto, quindi il `max-height: 100%` della
  fotografia non ha una base su cui risolversi e viene ignorato: la foto
  sfondava sotto la didascalia di 149px.


## Tipografia

**Fraunces** per i titoli, **Archivo** per tutto il resto. Prima erano Cormorant
Garamond e Inter: elegante ma è l'accoppiata che si trova su metà dei siti
"eleganti", e Inter è il font che si sceglie quando non si sceglie.

| ruolo | carattere | perché |
|---|---|---|
| Titoli | Fraunces | serif contemporaneo, alto contrasto, con **asse di dimensione ottica** |
| Testo e interfaccia | Archivo | grottesco stretto, molto leggibile ai corpi piccoli, con terminali suoi |

### L'asse ottico non è un vezzo

Fraunces è variabile su `opsz` (9–144), e `font-optical-sizing: auto` lo muove
in funzione del corpo: nei titoli grandi le grazie si assottigliano e il
contrasto cresce, in quelli piccoli si ispessiscono e il disegno si apre.
È il motivo per cui un H1 da 87px e un H3 non sembrano *lo stesso disegno
scalato* — che è esattamente il difetto da cui siamo partiti.

### Quattro trame, non quattro corpi

Il salto di gerarchia non è solo dimensionale. Il sistema distingue per
**famiglia e trattamento**:

| livello | trama |
|---|---|
| Titoli di pagina e sezione | Fraunces, interlinea sotto l'unità (0,98), spaziatura −0,03em |
| Nomi propri (immobili) | Fraunces, peso 500, corpo medio |
| Etichette e categorie (servizi, passi) | **Archivo maiuscolo**, peso 600, spaziatura +0,1em |
| Micro-etichette (occhielli, menu, bottoni) | Archivo, corpo minimo, spaziatura +0,26em |
| Testo corrente | Archivo 400 |
| Sottotitoli | Archivo **300**, corpo più grande del testo |

La distinzione fra le righe 2 e 3 è la scelta di sistema: *una casa ha un nome*
e resta nel carattere da titoli; *un servizio è una categoria* e va in maiuscolo
spaziato. Non è decorazione, è una regola che si può applicare a contenuti nuovi.

### La scala

Prima c'erano **66 dichiarazioni di `font-size` decise una per una** e sette
valori di `letter-spacing` a occhio. Ora ci sono nove corpi
(`--t-2xs` → `--t-4xl`), cinque spaziature e quattro interlinee, e ogni regola
del foglio pesca da lì.

L'ingrandimento sopra i 900px sta su `:root`, non su `body`: le misure sono in
`rem`, che si riferiscono alla radice. Prima cresceva solo il testo corrente e
tutti i rapporti si sfasavano del 6%.

### Perché i caratteri sono ospitati qui

Due ragioni, e la prima non è tecnica.

**Conformità.** Chiamare `fonts.gstatic.com` manda l'indirizzo IP del visitatore
a Google prima ancora che veda il banner cookie. È il genere di trasferimento
che la privacy policy di questo sito dichiara di non fare, ed è quello che il
tribunale di Monaco ha già considerato una violazione del GDPR.

**Prestazione.** Spariscono due `preconnect` verso un dominio terzo e un foglio
di stile che bloccava il rendering. I file partono a **34ms** invece che dopo
la catena DNS + TLS + CSS di Google.

Fraunces e Archivo sono entrambi in licenza SIL Open Font, quindi
ridistribuibili con il sito.

### Cosa si scarica davvero

| file | peso | quando |
|---|---|---|
| `fraunces-var-latin.woff2` | 66 KB | sempre (precaricato) |
| `archivo-var-latin.woff2` | 34 KB | sempre (precaricato) |
| `fraunces-italic-latin.woff2` | 22 KB | dove c'è un `<em>` in un titolo |
| `*-latin-ext.woff2` | 59 + 32 KB | quasi mai |

**122 KB** su una pagina italiana. I `latin-ext` esistono ma non partono:
`unicode-range` li lascia a terra finché in pagina non compare un carattere che
li richiede, e l'italiano sta tutto in `latin`. Per questo non è un dettaglio.

Il corsivo di Fraunces è **statico a un peso solo**, non variabile: serve per
poche parole dentro i titoli grandi, e la versione variabile costava 80 KB
invece di 22.

I due file sempre usati sono in `<link rel="preload">`, perché citati dentro il
foglio di stile il browser li scoprirebbe solo dopo averlo scaricato e
interpretato.

### Rigenerare i file

```bash
# Fraunces variabile (pesi 300-700, dimensioni ottiche 9-144)
https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..700
# Fraunces corsivo, un peso solo, dimensione ottica massima
https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@1,144,400
# Archivo variabile
https://fonts.googleapis.com/css2?family=Archivo:wght@300..700
```

Vanno richiesti con uno user-agent recente (altrimenti Google serve TTF al posto
di WOFF2), si tengono solo i sottoinsiemi `latin` e `latin-ext`, e gli
`unicode-range` vanno copiati da lì dentro `@font-face`.


## Animazioni

Tre meccanismi distinti.

**Il sipario** (solo home): schermo nero con logo e claim *Scegli i
professionisti*, poi dissolvenza sulla home. Dura circa 2,3 secondi in tutto e si
salta con un click, un tasto, la rotella o un tocco.

Compare **una volta per sessione del browser**: la seconda visita alla home apre
la pagina direttamente. Per rivederlo senza chiudere il browser si aggiunge
`?intro=1` all'indirizzo.

Il markup sta in `templates/_intro.html`, incluso dalla home tramite i blocchi
`sipario` e `intro` di `base.html`. Per metterlo anche altrove basta ridefinire
quei due blocchi nella pagina; per toglierlo del tutto si cancellano dalla home.

Il ritmo si regola da due token in `static/css/style.css`:

```css
:root {
  --intro-attesa: 1700ms;   /* quanto resta fermo prima di dissolversi */
  --intro-uscita: 620ms;    /* durata della dissolvenza */
}
```

`main.js` li rilegge da lì, quindi non c'è un secondo posto da aggiornare. La
comparsa della home parte quando il nero inizia a svanire, non quando è sparito:
i due movimenti si sovrappongono e il passaggio non ha stacchi.

**All'ingresso** (solo home): la fotografia dell'hero fa un lieve zoom
all'indietro (`scale(1.07)` → `1`) mentre eyebrow, titolo, testo e bottoni
compaiono scaglionati. Non dipendono dallo scroll ma dalla classe `is-loaded`,
aggiunta su `<html>` dopo due `requestAnimationFrame` — serve che lo stato
iniziale sia stato dipinto almeno una volta, altrimenti il browser salta la
transizione e gli elementi appaiono di colpo.

**Allo scroll**: gli elementi marcati `data-reveal` salgono di 22px sfumando in
opacità quando entrano nel viewport, tramite un `IntersectionObserver` che li
smette di osservare dopo la prima comparsa (si animano una volta sola). Un
contenitore marcato `data-stagger` assegna ai figli un indice `--i` che ritarda
ogni elemento di 90ms, per l'effetto a cascata su griglie e gallerie.

Per animare un nuovo elemento basta aggiungere `data-reveal` nel template
(`data-reveal="fade"` per la sola dissolvenza, senza spostamento) e
`data-stagger` sul contenitore se si vuole la cascata sui figli.

### Entrata a scossa (sezione «Un servizio completo»)

Le tre schede compaiono **una alla volta** e si assestano con un'oscillazione
smorzata: entrano dal basso storte di 4°, sbandano di 13px, rientrano. Perno a
`50% 90%`, vicino alla base, così sembrano appoggiate e spinte invece che
appese e fatte girare.

Si attiva con `data-scossa` sul contenitore. È l'unica animazione del sito
legata al **tempo** e non alla posizione nello scorrimento, e deve esserlo:
un'oscillazione su timeline di scorrimento si fermerebbe a metà non appena si
smette di scorrere, lasciando una scheda storta sullo schermo.

**Lo scaglionamento non viene da `data-stagger`.** `main.js` osserva le singole
schede e scrive il ritardo su ognuna in base alla sua posizione dentro il
*lotto* che entra in campo nello stesso momento:

| | cosa succede | ritardi |
|---|---|---|
| Schermo largo, tre in riga | varcano la soglia nello stesso fotogramma, arrivano in un'unica chiamata | 0, 200, 400ms |
| Telefono, una colonna | si incontrano una per volta scorrendo, ogni chiamata ne porta una sola | 0, 0, 0 |

In colonna la sequenza la fa già lo scorrimento: un'attesa in più sarebbe solo
una scheda che tarda a comparire. Osservare il *contenitore* invece delle
schede sarebbe stato più corto ma sbagliato in colonna — la seconda e la terza
si sarebbero animate fuori campo, e arrivandoci si sarebbero trovate già ferme.

Per estenderla ad altre sezioni basta `data-scossa` sul contenitore e togliere
`data-reveal` dai figli.

### Perché non si rompe mai

Le animazioni partono solo se `<html>` porta la classe `js-anim`, aggiunta dallo
script inline in `<head>` **solo quando** JS è attivo, `IntersectionObserver`
esiste e l'utente non ha chiesto di ridurre le animazioni. Senza quella classe il
CSS non nasconde nulla: il sito resta completo e leggibile.

In più, se l'observer viene creato ma non emette mai la prima callback (un
observer sano la emette sempre, anche per elementi non intersecanti), dopo 2
secondi un timer mostra tutto. Meglio perdere l'animazione che lasciare la
pagina vuota.

Lo stesso vale per il sipario, che è governato dalla classe `ev-intro`: se JS è
spento la classe non c'è e il CSS lo tiene a `display: none`. E se lo script si
interrompe a metà il sipario se ne va lo stesso, perché l'animazione finale
termina su `visibility: hidden` — smette di coprire e di intercettare i click
anche senza che nessuno tolga la classe.

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
più un campo honeypot nascosto anti-spam.

In questa fase **non viene inviata nessuna email**: i dati validati vengono stampati
nella console del server (`core/views.py`). Dopo l'invio l'utente viene reindirizzato
con un messaggio di conferma (pattern POST/redirect/GET).

Per attivare l'invio reale, imposta le variabili SMTP indicate sotto e sostituisci il
blocco `print(...)` con `django.core.mail.send_mail`.

### Prima di attivarlo: salvare la prova del consenso

Oggi la spunta privacy viene **validata ma non conservata**, perché nulla lascia il
server. Finché il modulo si limita a stampare in console il punto è teorico.

**Nel momento in cui il modulo comincia a recapitare o a salvare i messaggi, il
consenso va registrato.** Il GDPR non chiede solo di raccoglierlo: all'articolo 7
comma 1 chiede di essere in grado di *dimostrare* di averlo raccolto. Una spunta che
non lascia traccia non dimostra nulla, e in caso di contestazione l'onere della prova
è del titolare del trattamento.

Cosa conservare, per ogni invio:

- **data e ora** della spunta;
- **il testo esatto** dell'informativa accettata, o una sua versione identificabile
  (es. `privacy-v2-2026-03`): l'informativa cambia nel tempo, e serve sapere a quale
  versione l'utente ha aderito;
- i **dati inviati** a cui il consenso si riferisce;
- facoltativo ma utile: indirizzo IP e user agent della richiesta.

In pratica significa introdurre un modello — per esempio `core.MessaggioContatto` —
che salvi il messaggio insieme a questi campi, e scrivere il record **prima**
dell'invio della email: se l'SMTP fallisce, il messaggio non deve andare perso.

Il rovescio della medaglia: da quel momento si conservano dati personali, quindi
vanno definiti un **periodo di conservazione** e una procedura di cancellazione, e la
Privacy Policy va aggiornata di conseguenza (oggi il periodo è un segnaposto).

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
- [ ] Completare i 21 immobili in bozza (descrizione, dotazioni, fotografie)
      e pubblicarli dall'amministrazione.
- [ ] Impostare `DJANGO_SECRET_KEY` e `DJANGO_DEBUG=False`.
- [ ] Restringere `DJANGO_ALLOWED_HOSTS` al dominio reale.
- [ ] Configurare l'invio email SMTP e attivare `send_mail` nel modulo contatti.
- [ ] **Insieme all'attivazione del modulo**: salvare la prova del consenso privacy
      (data e ora, versione dell'informativa, dati inviati) e definire il periodo
      di conservazione. Vedi "Modulo contatti".
- [ ] Servire `static/` e `media/` tramite web server (in produzione Django non li serve).
