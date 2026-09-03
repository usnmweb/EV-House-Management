from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("titolo", "categoria", "pubblicato_il", "tempo_lettura",
                    "in_evidenza", "pubblicato")
    list_filter = ("pubblicato", "in_evidenza", "categoria")
    list_editable = ("in_evidenza", "pubblicato")
    search_fields = ("titolo", "estratto", "corpo", "tag")
    date_hierarchy = "pubblicato_il"
    prepopulated_fields = {"slug": ("titolo",)}
    ordering = ("-pubblicato_il",)

    fieldsets = (
        ("Testo", {
            "fields": ("titolo", "slug", "categoria", "estratto", "sottotitolo", "corpo"),
            "description": "Nel corpo, i paragrafi si separano con una riga vuota; "
                           "una riga che comincia per «## » diventa un sottotitolo. "
                           "Non serve (e non funziona) scrivere HTML.",
        }),
        ("Citazione", {
            "fields": ("citazione", "citazione_fonte"),
            "classes": ("collapse",),
        }),
        ("Copertina", {"fields": ("copertina", "copertina_alt")}),
        ("Pubblicazione", {
            "fields": ("pubblicato_il", "autore", "tempo_lettura", "tag",
                       "mostra_stagione", "in_evidenza", "pubblicato"),
        }),
        ("SEO", {"fields": ("meta_description",), "classes": ("collapse",)}),
    )
