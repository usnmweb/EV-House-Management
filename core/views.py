import json
import pathlib
from collections import Counter
from datetime import date, datetime, time, timezone

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from properties.models import ORDINE_FOTO, Property, PropertyImage

from .forms import ContactForm
from .models import Recensione


SARDEGNA = json.loads(
    (pathlib.Path(__file__).resolve().parent / "data" / "sardegna.json").read_text()
)


def _numero(valore):
    """Legge un'impostazione numerica tollerando spazi, punti e vuoto."""
    testo = (valore or "").replace(".", "").replace(" ", "").strip()
    return int(testo) if testo.isdigit() else None


def _con_migliaia(n):
    """3406 -> «3.406»: la stessa grafia dei numeri scritti nelle impostazioni.

    Serve al valore che finisce nel markup, quello che si vede senza
    JavaScript: l'animazione poi lo riscrive con Intl.NumberFormat, e le due
    grafie devono coincidere o il numero cambia forma sotto gli occhi.
    """
    return f"{n:,}".replace(",", ".")


def _ospiti_accolti():
    """Totale ospiti e ritmo con cui sale, dai dati forniti dal gestore.

    Il ritmo e' ospiti-degli-ultimi-dodici-mesi diviso i secondi di un anno, e
    nient'altro. Con dodicimila ospiti l'anno fa un ospite ogni quarantatre
    minuti: in pagina il contatore non si vedra' quasi mai scattare, ed e'
    esattamente cio' che deve succedere. Un contatore che corre piu' del reale
    e' un numero falso che si aggiorna da solo.
    """
    totale = _numero(settings.GUESTS_TOTAL)
    ultimi = _numero(settings.GUESTS_LAST_12M)
    if totale is None:
        return None
    try:
        alla_data = date.fromisoformat(settings.GUESTS_AS_OF)
    except ValueError:
        # Senza data di riferimento il totale si mostra fermo. La data serve a
        # far salire il contatore, non a rendere vero il numero: pretenderla
        # significherebbe nascondere un dato che c'e' per far mancare
        # un'animazione che non serve.
        return {
            "totale": totale,
            "scritto": _con_migliaia(totale),
            "al_secondo": 0,
            "da_quando": 0,
            "ultimi_dodici_mesi": None,
        }
    return {
        "totale": totale,
        "scritto": _con_migliaia(totale),
        "al_secondo": (ultimi / (365 * 24 * 3600)) if ultimi else 0,
        # In millisecondi dall'epoca: il conto in pagina parte da qui, non da
        # "adesso", altrimenti il numero mostrato dipenderebbe da quando la
        # pagina viene aperta invece che da quanto tempo e' passato davvero.
        "da_quando": int(
            datetime.combine(alla_data, time.min, tzinfo=timezone.utc).timestamp() * 1000
        ),
        "ultimi_dodici_mesi": ultimi,
    }


def _rinnovi():
    """Percentuale di proprietari che restano, calcolata — non dichiarata."""
    serviti = _numero(settings.OWNERS_SERVED)
    rimasti = _numero(settings.OWNERS_RETAINED)
    if not serviti or rimasti is None or rimasti > serviti:
        return None
    return {
        "serviti": serviti,
        "rimasti": rimasti,
        "percentuale": round(rimasti / serviti * 100),
    }


def _zone_coperte():
    """Localita' con almeno un immobile pubblicato, proiettate sulla mappa.

    Le coordinate sono quelle vere degli immobili: il punto di una zona e' il
    centro dei suoi immobili, non una posizione messa a occhio.
    """
    r = SARDEGNA["riquadro"]
    scala = SARDEGNA["altezza"] / (r["lat_max"] - r["lat_min"])

    gruppi = {}
    for immobile in (
        Property.objects.published()
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .only("location", "latitude", "longitude")
    ):
        gruppi.setdefault(immobile.location, []).append(
            (float(immobile.latitude), float(immobile.longitude))
        )

    zone = []
    for nome, punti in gruppi.items():
        lat = sum(p[0] for p in punti) / len(punti)
        lon = sum(p[1] for p in punti) / len(punti)
        zone.append({
            "nome": nome,
            "slug": slugify(nome),
            "quanti": len(punti),
            # Stringhe, non numeri: con LANGUAGE_CODE="it-it" il template
            # scriverebbe "505,8" al posto di "505.8", e l'SVG rifiuta la
            # virgola — i punti finirebbero tutti a 0,0. E' la stessa trappola
            # delle coordinate nei dati strutturati.
            "x": "%g" % round((lon - r["lon_min"]) * r["k"] * scala, 1),
            "y": "%g" % round((r["lat_max"] - lat) * scala, 1),
        })
    zone.sort(key=lambda z: (-z["quanti"], z["nome"]))

    # Indice per la cascata sulla mappa: da nord a sud, cioe' nell'ordine in
    # cui la costa scorre sotto gli occhi. L'elenco accanto resta ordinato per
    # numero di immobili, che li' e' l'informazione utile.
    for i, z in enumerate(sorted(zone, key=lambda z: float(z["y"]))):
        z["ordine_mappa"] = i

    L, H = SARDEGNA["larghezza"], SARDEGNA["altezza"]
    if not zone:
        # Nessun immobile pubblicato con coordinate (database appena creato,
        # tutto in bozza): l'isola intera, senza punti. Prima di questa uscita
        # il calcolo del riquadro faceva `max()` su una lista vuota e la home
        # rispondeva 500.
        return zone, {"viewbox": "0 0 %g %g" % (L, H), "sfuma": None}

    # Inquadratura: il quadrante nord-orientale, con attorno abbastanza isola
    # da riconoscerlo. Le due prove estreme non funzionavano: ritagliata
    # stretta sull'area coperta restava un tratto di costa senza capo ne' coda,
    # e l'isola intera spingeva le 19 localita' in un angolo del disegno.
    #
    # Il riquadro parte dall'area coperta e la allarga di due terzi del suo
    # lato maggiore: verso nord arriva al mare (la Gallura, con la sua costa
    # frastagliata, e' quel che rende riconoscibile il punto dell'isola),
    # verso est al bordo dell'isola, verso ovest e sud entra nella terraferma.
    xs = [float(z["x"]) for z in zone]
    ys = [float(z["y"]) for z in zone]
    margine = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.65
    x0 = max(0.0, min(xs) - margine)
    y0 = max(0.0, min(ys) - margine)
    x1 = min(L, max(xs) + margine)
    y1 = min(H, max(ys) + margine)
    w, h = x1 - x0, y1 - y0

    # Dove il riquadro taglia la terraferma, il bordo si sfuma. Un taglio
    # netto sembra un errore di disegno; una dissolvenza dice «l'isola
    # continua», che e' quello che succede davvero.
    sfuma = {
        "x": "%g" % round(x0, 1), "y": "%g" % round(y0, 1),
        "w": "%g" % round(w, 1), "h": "%g" % round(h, 1),
        # sinistra: da trasparente a pieno nel primo quarto del riquadro
        "sx_da": "%g" % round(x0, 1),
        "sx_a": "%g" % round(x0 + w * 0.28, 1) if x0 > 0 else "%g" % round(x0, 1),
        # basso: da pieno a trasparente nell'ultimo quinto
        "giu_da": "%g" % round(y1 - h * 0.22, 1) if y1 < H else "%g" % round(y1, 1),
        "giu_a": "%g" % round(y1, 1),
    }

    # La misura dei punti, in pixel di resa: il disegno si vede largo circa
    # 300px, e le misure si scrivono pensando a quello. Convertite in unita'
    # del riquadro restano giuste anche se l'inquadratura un giorno cambia —
    # prima erano scritte in unita' del disegno, e allargando lo zoom i punti
    # diventavano capocchie di spillo.
    #
    # L'alone cresce con la radice del numero di immobili (l'occhio confronta
    # aree, non raggi) piu' una base, perche' una localita' con un immobile
    # solo deve restare visibile accanto a Siniscola.
    unita_per_pixel = w / 300
    for z in zone:
        z["r_punto"] = "%g" % round(4.5 * unita_per_pixel, 2)
        z["r_alone"] = "%g" % round((7 + 4.8 * z["quanti"] ** 0.5) * unita_per_pixel, 2)

    inquadratura = {
        "viewbox": "%g %g %g %g" % (round(x0, 1), round(y0, 1), round(w, 1), round(h, 1)),
        "sfuma": sfuma,
        # anche il tratto della costa e' in pixel di resa, per lo stesso motivo
        "tratto": "%g" % round(1.4 * unita_per_pixel, 2),
    }
    return zone, inquadratura


ORDINALI = {
    1: "prima", 2: "seconda", 3: "terza", 4: "quarta", 5: "quinta",
    6: "sesta", 7: "settima", 8: "ottava", 9: "nona", 10: "decima",
}


def home(request):
    pubblicati = Property.objects.published()

    # Nove immobili per il carosello della home. Solo con almeno una fotografia:
    # una scheda con il segnaposto "EV" in mezzo alla vetrina stona.
    # `distinct()` serve perche' il join sulle immagini duplica le righe.
    con_foto = pubblicati.filter(images__isnull=False).distinct().prefetch_related("images")
    featured = con_foto.filter(featured=True)[:9] or con_foto[:9]
    # Numeri della stagione. Quelli che questo database conosce si calcolano
    # qui; quelli che vengono dal portale prenotazioni arrivano dalle
    # impostazioni e restano vuoti finche' il gestore non li fornisce.
    stagione = {
        "anno": settings.SEASON_YEAR,
        "occupazione": settings.SEASON_OCCUPANCY,
        "settimana": settings.SEASON_WEEK,
        "notti_vendute": settings.SEASON_NIGHTS_SOLD,
        "notti_disponibili": settings.SEASON_NIGHTS_AVAILABLE,
        "notti_anno": settings.SEASON_NIGHTS_YEAR,
        "prenotazioni": settings.SEASON_BOOKINGS_VALUE,
        "primo_anno": settings.SEASON_FIRST_YEAR,
    }
    # «La nostra quinta stagione»: si conta rispetto all'anno della stagione
    # mostrata, non a oggi, cosi' la frase resta coerente con i numeri sotto
    # anche quando l'anno solare cambia prima dei dati.
    if settings.SEASON_FIRST_YEAR.isdigit() and settings.SEASON_YEAR.isdigit():
        n = int(settings.SEASON_YEAR) - int(settings.SEASON_FIRST_YEAR)
        stagione["ordinale"] = ORDINALI.get(n, "")

    recensioni = list(Recensione.objects.filter(in_evidenza=True))
    zone, inquadratura = _zone_coperte()

    return render(
        request,
        "core/home.html",
        {
            "featured_properties": featured,
            "stagione": stagione,
            "immobili_gestiti": settings.PROPERTIES_MANAGED,
            "ospiti": _ospiti_accolti(),
            "rinnovi": _rinnovi(),
            "zone": zone,
            "mappa": SARDEGNA,
            "inquadratura": inquadratura,
            "recensioni": recensioni,
            "totale_localita": pubblicati.values("location").distinct().count(),
            "page_title": "Gestione immobiliare di lusso",
            "meta_description": (
                "EV House Management: gestione completa di immobili e affitti brevi. "
                "Selezione, cura e valorizzazione della tua proprietà."
            ),
        },
    )


def services(request):
    # I contenuti stanno qui e non nel template: sono dati, e averli in un punto
    # solo evita che descrizione, ordine e icona vadano fuori sincrono.
    # `icona` e' la chiave letta da core/_icona_servizio.html.
    servizi = [
        {
            "icona": "casa",
            "title": "Gestione operativa",
            "text": "Check-in e check-out, pulizie, biancheria, manutenzione ordinaria e "
                    "straordinaria. Coordiniamo i fornitori e assistiamo gli ospiti.",
        },
        {
            "icona": "andamento",
            "title": "Revenue management",
            "text": "Prezzi dinamici e analisi di mercato costanti per massimizzare la resa "
                    "del tuo immobile senza sacrificare la qualità.",
        },
        {
            "icona": "canali",
            "title": "Distribuzione multicanale",
            "text": "Pubblicazione e sincronizzazione su Airbnb, Booking.com e canali diretti, "
                    "con calendario unico e zero overbooking.",
        },
        {
            "icona": "fotocamera",
            "title": "Fotografia e styling",
            "text": "Servizi fotografici professionali e home staging per presentare la "
                    "proprietà al massimo del suo potenziale.",
        },
        {
            "icona": "rendiconto",
            "title": "Reportistica trasparente",
            "text": "Rendiconti mensili chiari su occupazione, ricavi e costi, sempre "
                    "accessibili al proprietario.",
        },
        {
            "icona": "conformita",
            "title": "Conformità e adempimenti",
            "text": "Contratti, notifiche agli enti, tassa di soggiorno e adempimenti locali "
                    "gestiti integralmente da noi.",
        },
    ]

    # Il confronto fra le due colonne e' il messaggio: e' la lunghezza delle due
    # liste a dire come si dividono i compiti, non un aggettivo.
    riparto = {
        "tuo": [
            "Ci consegni le chiavi",
            "Approvi il piano di gestione",
            "Ricevi il rendiconto ogni mese",
        ],
        "nostro": [
            "Accoglienza e assistenza agli ospiti",
            "Pulizie, biancheria e riassetto",
            "Manutenzione e coordinamento dei fornitori",
            "Prezzi, calendario e pubblicazione sui portali",
            "Fotografia e presentazione dell'immobile",
            "Adempimenti, tassa di soggiorno e comunicazioni agli enti",
        ],
    }

    percorso = [
        {
            "title": "Sopralluogo",
            "text": "Visitiamo l'immobile e ne valutiamo posizione, stato e potenziale di rendita.",
        },
        {
            "title": "Proposta",
            "text": "Ti presentiamo un piano di gestione con stime di occupazione e ricavo.",
        },
        {
            "title": "Attivazione",
            "text": "Styling, servizio fotografico, pubblicazione degli annunci e avvio operativo.",
        },
        {
            "title": "Gestione",
            "text": "Operatività continua e rendiconti mensili trasparenti, senza pensieri per te.",
        },
    ]

    return render(
        request,
        "core/services.html",
        {
            "servizi": servizi,
            "riparto": riparto,
            "percorso": percorso,
            "page_title": "Servizi",
            "meta_description": (
                "Gestione completa, revenue management, distribuzione multicanale e "
                "reportistica trasparente per il tuo immobile in Sardegna."
            ),
        },
    )


def gallery(request):
    """Galleria: due scatti per immobile, alternati fra immobili diversi.

    Prima erano le prime 120 fotografie ordinate per titolo dell'immobile:
    otto per casa, quindi in pagina finivano gli scatti di quindici immobili
    su sessantatre. Gli altri quarantotto non comparivano affatto.
    """
    scatti = (
        PropertyImage.objects.select_related("property")
        .filter(property__status=Property.Status.PUBLISHED)
        # La copertina scelta a mano apre anche la fila della galleria:
        # e' la stessa regola della scheda, applicata dove i posti sono due.
        .order_by("property__title", *ORDINE_FOTO)
    )

    per_immobile = {}
    for scatto in scatti:
        per_immobile.setdefault(scatto.property_id, []).append(scatto)

    # Due per immobile, presi a giro: cosi' due tessere vicine vengono quasi
    # sempre da case diverse, invece di otto foto di fila della stessa.
    QUANTI = 2
    galleria = []
    for giro in range(QUANTI):
        for elenco in per_immobile.values():
            if giro < len(elenco):
                galleria.append(elenco[giro])

    # Filtri per localita'. Solo quelle con almeno due immobili: sotto, un
    # filtro selezionerebbe una manciata di scatti e non serve a nessuno.
    conteggi = Counter(s.property.location for s in galleria)
    immobili_per_luogo = Counter(
        p.location for p in Property.objects.published().only("location")
    )
    luoghi = [
        {"nome": nome, "slug": slugify(nome), "quanti": conteggi[nome]}
        for nome in sorted(conteggi, key=lambda n: (-conteggi[n], n))
        if immobili_per_luogo[nome] >= 2
    ]

    for scatto in galleria:
        scatto.slug_luogo = slugify(scatto.property.location)

    return render(
        request,
        "core/gallery.html",
        {
            "scatti": galleria,
            "luoghi": luoghi,
            "totale": len(galleria),
            "page_title": "Galleria",
            "meta_description": (
                "Gli interni, i dettagli e le viste degli immobili gestiti da "
                "EV House Management in Sardegna."
            ),
        },
    )


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Nessun invio email reale in questa fase: log su console.
            print("\n=== NUOVO MESSAGGIO DAL MODULO CONTATTI ===")
            print(f"Nome:      {data['name']}")
            print(f"Email:     {data['email']}")
            print(f"Telefono:  {data['phone'] or '-'}")
            print(f"Privacy:   {'accettata' if data['privacy'] else 'non accettata'}")
            print(f"Messaggio: {data['message']}")
            print(f"Destinatario configurato: {settings.CONTACT_RECIPIENT_EMAIL}")
            print("===========================================\n", flush=True)

            messages.success(
                request,
                "Grazie! Il tuo messaggio e stato inviato. Ti risponderemo al più presto.",
            )
            return redirect(reverse("core:contact"))
        messages.error(request, "Controlla i campi evidenziati e riprova.")
    else:
        form = ContactForm()

    return render(
        request,
        "core/contact.html",
        {
            "form": form,
            "page_title": "Contatti",
            "meta_description": (
                "Contatta EV House Management per affidarci la gestione del tuo immobile."
            ),
        },
    )


def privacy(request):
    return render(
        request,
        "legal/privacy.html",
        {
            "page_title": "Privacy Policy",
            "meta_description": "Informativa sul trattamento dei dati personali.",
            "noindex": True,
        },
    )


def cookies(request):
    return render(
        request,
        "legal/cookies.html",
        {
            "page_title": "Cookie Policy",
            "meta_description": "Informativa sull'uso dei cookie su questo sito.",
            "noindex": True,
        },
    )


@require_GET
def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "",
        f"Sitemap: {sitemap_url}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
