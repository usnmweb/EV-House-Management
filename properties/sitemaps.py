from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Property


class PropertySitemap(Sitemap):
    """Pagine di dettaglio immobile."""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Property.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Pagine statiche del sito."""

    changefreq = "monthly"

    def items(self):
        return [
            "core:home",
            "properties:list",
            "core:services",
            "core:gallery",
            "core:contact",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.7
