from django.conf import settings


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
    }
