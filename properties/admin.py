from django.contrib import admin
from django.utils.html import format_html

from .models import Amenity, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0
    fields = ("preview", "image", "alt_text", "order")
    readonly_fields = ("preview",)

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
        "guests", "bedrooms", "bathrooms", "featured", "image_count",
    )
    list_display_links = ("title",)
    list_editable = ("status", "featured")
    list_filter = ("status", "category", "featured", "location")
    search_fields = ("title", "location", "address", "description", "external_id")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("amenities",)
    list_per_page = 30
    inlines = [PropertyImageInline]
    readonly_fields = ("external_id", "created_at", "updated_at")

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
            "fields": ("external_id", "created_at", "updated_at"),
        }),
    )

    actions = ["pubblica", "metti_in_bozza"]

    @admin.display(description="Foto")
    def image_count(self, obj):
        return obj.images.count()

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
    list_display = ("property", "alt_text", "order")
    list_filter = ("property__location",)
    search_fields = ("alt_text", "property__title")
    list_editable = ("order",)
