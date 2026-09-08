from django.conf import settings
from django.db.models import Count
from django.utils.functional import SimpleLazyObject


def _localita_pubblicate():
    """Localita' con almeno un immobile pubblicato, in ordine alfabetico.

    Serve al menu a tendina della barra di navigazione, che sta in base.html e
    quindi comparirebbe su ogni pagina. Per questo il valore e' avvolto in
    SimpleLazyObject: la query parte solo se un template la usa davvero, e
    l'amministrazione — che ha i propri template — non la paga.
    """
    from properties.models import Property

    conteggi = (
        Property.objects.published()
        .values("location")
        .annotate(quanti=Count("id"))
        .order_by("location")
    )
    return [
        {"nome": r["location"], "quanti": r["quanti"]}
        for r in conteggi
        if r["location"]
    ]


def site_settings(request):
    """Espone i dati societari e di sito a tutti i template."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
        "COMPANY_LEGAL_NAME": settings.COMPANY_LEGAL_NAME,
        "COMPANY_VAT": settings.COMPANY_VAT,
        "COMPANY_ADDRESS": settings.COMPANY_ADDRESS,
        "COMPANY_EMAIL": settings.COMPANY_EMAIL,
        "COMPANY_PHONE": settings.COMPANY_PHONE,
        "COMPANY_STREET": settings.COMPANY_STREET,
        "COMPANY_POSTAL_CODE": settings.COMPANY_POSTAL_CODE,
        "COMPANY_CITY": settings.COMPANY_CITY,
        "COMPANY_PROVINCE": settings.COMPANY_PROVINCE,
        "COMPANY_REA": settings.COMPANY_REA,
        "COMPANY_PEC": settings.COMPANY_PEC,
        "COMPANY_CAPITAL": settings.COMPANY_CAPITAL,
        "BOOKING_URL": settings.BOOKING_URL,
        "OWNER_PORTAL_URL": settings.OWNER_PORTAL_URL,
        "LOCALITA_NAV": SimpleLazyObject(_localita_pubblicate),
    }
