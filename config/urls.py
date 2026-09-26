from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from blog.sitemaps import ArticleSitemap
from core.views import robots_txt
from properties.sitemaps import PropertySitemap, StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "properties": PropertySitemap,
    "articoli": ArticleSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("properties/", include("properties.urls")),
    path("blog/", include("blog.urls")),
    # Il blog si chiamava «Giornale»: i vecchi indirizzi, gia' condivisi o
    # indicizzati, portano alla pagina nuova con un 301 invece di un 404.
    re_path(
        r"^giornale/(?P<resto>.*)$",
        RedirectView.as_view(url="/blog/%(resto)s", permanent=True, query_string=True),
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
