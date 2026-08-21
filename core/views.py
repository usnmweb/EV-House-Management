from collections import Counter

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from properties.models import Property, PropertyImage
from properties.utils import conteggio_indicativo

from .forms import ContactForm


def home(request):
    pubblicati = Property.objects.published()

    # Nove immobili per il carosello della home. Solo con almeno una fotografia:
    # una scheda con il segnaposto "EV" in mezzo alla vetrina stona.
    # `distinct()` serve perche' il join sulle immagini duplica le righe.
    con_foto = pubblicati.filter(images__isnull=False).distinct().prefetch_related("images")
    featured = con_foto.filter(featured=True)[:9] or con_foto[:9]
    return render(
        request,
        "core/home.html",
        {
            "featured_properties": featured,
            "totale_immobili": conteggio_indicativo(pubblicati.count()),
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
        .order_by("property__title", "order")
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
