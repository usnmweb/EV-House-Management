from django.contrib import admin

# Register your models here.

from .models import Recensione


@admin.register(Recensione)
class RecensioneAdmin(admin.ModelAdmin):
    list_display = ("autore", "voce", "canale", "data", "in_evidenza", "ordine")
    list_filter = ("voce", "in_evidenza", "canale")
    list_editable = ("in_evidenza", "ordine")
    search_fields = ("autore", "testo", "canale", "luogo")
    date_hierarchy = "data"

    def changelist_view(self, request, extra_context=None):
        extra_context = {"title": "Recensioni", **(extra_context or {})}
        return super().changelist_view(request, extra_context)
    fieldsets = (
        ("Chi", {"fields": ("autore", "voce", "luogo")}),
        ("Cosa", {"fields": ("testo",)}),
        ("Da dove", {
            "fields": ("canale", "data", "url"),
            "description": (
                "Canale e data sono obbligatori: senza, la recensione non è "
                "verificabile e non puo' essere pubblicata. Il collegamento "
                "all'originale, quando esiste, è quello che rende controllabile "
                "cio' che il sito afferma."
            ),
        }),
        ("In home", {"fields": ("in_evidenza", "ordine")}),
    )
