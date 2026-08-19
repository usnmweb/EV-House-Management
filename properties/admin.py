from django.contrib import admin
from django.utils.html import format_html

from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ("image", "preview", "alt_text", "order")
    readonly_fields = ("preview",)

    @admin.display(description="Anteprima")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="height:70px;border-radius:4px;" />', obj.image.url
            )
        return "-"


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "location",
        "guests",
        "bedrooms",
        "bathrooms",
        "featured",
        "image_count",
        "created_at",
    )
    list_filter = ("featured", "location", "bedrooms", "created_at")
    list_editable = ("featured",)
    search_fields = ("title", "location", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    inlines = [PropertyImageInline]
    fieldsets = (
        ("Informazioni principali", {
            "fields": ("title", "slug", "location", "featured", "booking_url"),
        }),
        ("Descrizioni", {
            "fields": ("short_description", "description"),
        }),
        ("Caratteristiche", {
            "fields": (("guests", "bedrooms", "bathrooms"),),
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("meta_title", "meta_description"),
            "description": "Se vuoti vengono generati automaticamente da titolo e descrizione breve.",
        }),
    )

    @admin.display(description="Immagini")
    def image_count(self, obj):
        return obj.images.count()


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "alt_text", "order")
    list_filter = ("property",)
    search_fields = ("alt_text", "property__title")
    list_editable = ("order",)
