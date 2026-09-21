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


class CopertinaFilter(admin.SimpleListFilter):
    """Chi ha gia' una copertina scelta a mano e chi usa ancora quella del portale.

    E' il filtro a cui porta la scheda «Copertine» del pannello iniziale: da li'
    si passano in rassegna solo gli immobili che ne hanno bisogno.
    """

    title = "copertina"
    parameter_name = "copertina"

    def lookups(self, request, model_admin):
        return (("scelta", "Scelta a mano"), ("portale", "Quella del portale"))

    def queryset(self, request, queryset):
        scelte = queryset.filter(images__copertina=True)
        if self.value() == "scelta":
            return scelte.distinct()
        if self.value() == "portale":
            return queryset.exclude(pk__in=scelte.values("pk"))
        return queryset


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    # La miniatura per prima: gli immobili si riconoscono dalla foto prima che
    # dal nome, soprattutto quando i nomi sono lunghi e si somigliano.
    # Solo quel che serve per riconoscere un immobile e decidere cosa farne.
    # Con ospiti, camere e bagni in piu' la tabella usciva dallo schermo e i
    # titoli andavano a capo su cinque righe: quei numeri stanno nella scheda.
    list_display = (
        "miniatura", "title", "status", "location", "category",
        "featured", "copertina_scelta", "image_count",
    )
    list_display_links = ("miniatura", "title")
    list_editable = ("status", "featured")
    # La tipologia filtra sui valori che ci sono davvero, non sulle quattro
    # scelte possibili: «Aparthotel» non lo usa piu' nessuno (vedi
    # import_properties) e offrirlo come filtro darebbe un elenco vuoto.
    list_filter = (
        "status", CopertinaFilter, ("category", admin.AllValuesFieldListFilter),
        "featured", "location",
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = {"title": "Immobili", **(extra_context or {})}
        return super().changelist_view(request, extra_context)
    search_fields = ("title", "location", "address", "description", "external_id")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("amenities",)
    list_per_page = 30
    inlines = [PropertyImageInline]
    readonly_fields = ("external_id", "dal_portale", "created_at", "updated_at")

    fieldsets = (
        ("Pubblicazione", {
            # La regola sui pubblicati la dice gia' l'aiuto del campo «Stato»:
            # ripeterla qui la faceva comparire due volte a tre righe di
            # distanza.
            "fields": ("status", "featured", "title", "slug", "category"),
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
                           "valore qui sopra è diverso, il campo è stato riscritto "
                           "per la vetrina e l'importazione non lo tocca più.",
        }),
    )

    actions = ["pubblica", "metti_in_bozza"]

    @admin.display(description="Foto")
    def miniatura(self, obj):
        # Dal prefetch dell'elenco quando c'e' (vedi get_queryset): senza,
        # sarebbe una query per riga.
        foto = next(iter(obj.images.all()), None)
        if not foto or not foto.image:
            return format_html('<span class="miniatura-vuota" title="Nessuna foto">—</span>')
        return format_html(
            '<img class="miniatura" src="{}" alt="" loading="lazy" width="64" height="48">',
            foto.image.url,
        )

    def get_queryset(self, request):
        from django.db.models import Prefetch
        from .models import ORDINE_FOTO
        return super().get_queryset(request).prefetch_related(
            Prefetch("images", queryset=PropertyImage.objects.order_by(*ORDINE_FOTO))
        )

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

    @admin.display(description="N. foto")
    def image_count(self, obj):
        return obj.images.count()

    @admin.display(description="Copertina")
    def copertina_scelta(self, obj):
        """Se la copertina e' stata scelta a mano o e' quella del portale.

        Serve a vedere in un colpo d'occhio quali immobili sono gia' stati
        passati in rassegna. Non una crocetta rossa: «dal portale» non e' un
        errore, e' lo stato di partenza, e una colonna di crocette rosse fa
        sembrare rotto un elenco che sta benissimo.
        """
        # Dal prefetch dell'elenco: una query in piu' per riga si sentirebbe.
        if any(foto.copertina for foto in obj.images.all()):
            return format_html('<span class="stato-pill stato-fatto">Scelta</span>')
        return format_html('<span class="stato-pill">Dal portale</span>')

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
