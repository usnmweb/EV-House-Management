from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.views import robots_txt
from properties.sitemaps import PropertySitemap, StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "properties": PropertySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("properties/", include("properties.urls")),
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

admin.site.site_header = "EV House Management"
admin.site.site_title = "EV House Management"
admin.site.index_title = "Amministrazione sito"
