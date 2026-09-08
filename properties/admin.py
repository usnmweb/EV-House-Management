from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .models import CAMPI_PROTETTI, Amenity, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0
    # La spunta sta subito accanto all'anteprima: la copertina si sceglie
    # guardando le foto, non leggendo i nomi dei file.
    fields = ("preview", "copertina", "image", "alt_text", "order")
    readonly_fields = ("preview",)
    classes = ("foto-immobile",)

    @admin.display(description="Anteprima")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="height:72px;border-radius:3px;" />', obj.image.url
            )
        return "—"


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "property_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Immobili")
    def property_count(self, obj):
        return obj.properties.count()


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title", "status", "category", "location",
        "guests", "bedrooms", "bathrooms", "featured", "image_count", "copertina_scelta",
    )
    list_display_links = ("title",)
    list_editable = ("status", "featured")
    list_filter = ("status", "category", "featured", "location")
    search_fields = ("title", "location", "address", "description", "external_id")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("amenities",)
    list_per_page = 30
    inlines = [PropertyImageInline]
    readonly_fields = ("external_id", "dal_portale", "created_at", "updated_at")

    fieldsets = (
        ("Pubblicazione", {
            "fields": ("status", "featured", "title", "slug", "category"),
            "description": "Solo gli immobili <b>pubblicati</b> compaiono sul sito e nella sitemap.",
        }),
        ("Dove si trova", {
            "fields": ("location", "address", ("latitude", "longitude")),
        }),
        ("Descrizioni", {
            "fields": ("short_description", "description"),
        }),
        ("Caratteristiche", {
            "fields": (("guests", "bedrooms", "bathrooms"), "amenities"),
        }),
        ("Prenotazione e adempimenti", {
            "fields": ("booking_url", "license_code"),
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("meta_title", "meta_description"),
            "description": "Se vuoti vengono generati da titolo e descrizione breve.",
        }),
        ("Provenienza", {
            "classes": ("collapse",),
            "fields": ("external_id", "dal_portale", "created_at", "updated_at"),
            "description": "Cosa dice il portale per i campi riscrivibili. Dove il "
                           "valore qui sopra e' diverso, il campo e' stato riscritto "
                           "per la vetrina e l'importazione non lo tocca piu'.",
        }),
    )

    actions = ["pubblica", "metti_in_bozza"]

    @admin.display(description="Dal portale")
    def dal_portale(self, obj):
        """Titolo e tipologia come li manda GR8, e se sono stati riscritti."""
        valori = obj.valori_portale or {}
        if not valori:
            return "—"
        righe = []
        for campo in CAMPI_PROTETTI:
            atteso = valori.get(campo)
            if not atteso:
                continue
            nota = " · riscritto qui" if obj.riscritto_a_mano(campo) else ""
            etichetta = obj._meta.get_field(campo).verbose_name
            righe.append(format_html("<b>{}</b>: {}{}", etichetta, atteso, nota))
        return format_html_join(mark_safe("<br>"), "{}", ((r,) for r in righe)) or "—"

    @admin.display(description="Foto")
    def image_count(self, obj):
        return obj.images.count()

    @admin.display(description="Copertina", boolean=True)
    def copertina_scelta(self, obj):
        """Se la copertina e' stata scelta a mano o e' quella del portale.

        Serve a vedere in un colpo d'occhio quali immobili sono gia' stati
        passati in rassegna: senza, l'unico modo di saperlo e' aprirli uno
        per uno.
        """
        return obj.images.filter(copertina=True).exists()

    @admin.action(description="Pubblica gli immobili selezionati")
    def pubblica(self, request, queryset):
        n = queryset.update(status=Property.Status.PUBLISHED)
        self.message_user(request, f"{n} immobili pubblicati.")

    @admin.action(description="Riporta in bozza gli immobili selezionati")
    def metti_in_bozza(self, request, queryset):
        n = queryset.update(status=Property.Status.DRAFT)
        self.message_user(request, f"{n} immobili riportati in bozza.")


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("miniatura", "property", "alt_text", "order", "copertina")
    list_display_links = ("property",)
    list_filter = ("copertina", "property__location")
    search_fields = ("alt_text", "property__title")
    list_editable = ("order", "copertina")

    @admin.display(description="Foto")
    def miniatura(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;border-radius:3px;" />', obj.image.url
            )
        return "—"
