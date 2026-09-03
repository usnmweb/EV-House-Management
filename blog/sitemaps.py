from django.contrib.sitemaps import Sitemap

from .models import Article


class ArticleSitemap(Sitemap):
    """Articoli del Giornale."""

    changefreq = "monthly"
    priority = 0.6

    def items(self):
        # Le bozze non vanno in sitemap: non sono pagine pubbliche.
        return Article.objects.pubblicati()

    def lastmod(self, obj):
        return obj.aggiornato_il
