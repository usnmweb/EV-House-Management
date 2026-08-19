from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from properties.models import Property, PropertyImage
from properties.utils import conteggio_indicativo

from .forms import ContactForm


def home(request):
    pubblicati = Property.objects.published()
    featured = (
        pubblicati.filter(featured=True).prefetch_related("images")[:3]
        or pubblicati.prefetch_related("images")[:3]
    )
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
    service_list = [
        {
            "title": "Gestione completa",
            "text": "Ci occupiamo di ogni aspetto operativo: check-in, pulizie, manutenzione e "
                    "assistenza agli ospiti 24/7.",
        },
        {
            "title": "Revenue management",
            "text": "Prezzi dinamici e analisi di mercato costanti per massimizzare la resa "
                    "del tuo immobile senza sacrificare la qualità.",
        },
        {
            "title": "Distribuzione multicanale",
            "text": "Pubblicazione e sincronizzazione su Airbnb, Booking.com e canali diretti, "
                    "con calendario unico e zero overbooking.",
        },
        {
            "title": "Fotografia e styling",
            "text": "Servizi fotografici professionali e home staging per presentare la "
                    "proprietà al massimo del suo potenziale.",
        },
        {
            "title": "Reportistica trasparente",
            "text": "Rendiconti mensili chiari su occupazione, ricavi e costi, sempre "
                    "accessibili al proprietario.",
        },
        {
            "title": "Conformita e burocrazia",
            "text": "Contratti, notifiche agli enti, tassa di soggiorno e adempimenti locali "
                    "gestiti integralmente da noi.",
        },
    ]
    return render(
        request,
        "core/services.html",
        {
            "services": service_list,
            "page_title": "Servizi",
            "meta_description": (
                "Gestione completa, revenue management, distribuzione multicanale e "
                "reportistica trasparente per il tuo immobile."
            ),
        },
    )


def gallery(request):
    images = (
        PropertyImage.objects.select_related("property")
        .filter(property__status=Property.Status.PUBLISHED)
        .order_by("property__title", "order")[:120]
    )
    return render(
        request,
        "core/gallery.html",
        {
            "images": images,
            "page_title": "Galleria",
            "meta_description": (
                "Una selezione di immagini degli immobili gestiti da EV House Management."
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
