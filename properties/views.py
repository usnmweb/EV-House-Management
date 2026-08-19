from django.db.models import Prefetch
from django.views.generic import DetailView, ListView

from .models import Property, PropertyImage
from .utils import conteggio_indicativo

IMMAGINI = Prefetch("images", queryset=PropertyImage.objects.order_by("order", "id"))


class PropertyListView(ListView):
    model = Property
    template_name = "properties/property_list.html"
    context_object_name = "properties"
    paginate_by = 12

    def get_queryset(self):
        qs = Property.objects.published().prefetch_related(IMMAGINI)
        location = self.request.GET.get("location")
        if location:
            qs = qs.filter(location=location)
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        guests = self.request.GET.get("guests")
        if guests and guests.isdigit():
            qs = qs.filter(guests__gte=int(guests))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pubblicati = Property.objects.published()
        ctx["locations"] = (
            pubblicati.order_by("location").values_list("location", flat=True).distinct()
        )
        ctx["categories"] = (
            pubblicati.exclude(category="")
            .order_by("category").values_list("category", flat=True).distinct()
        )
        ctx["active_location"] = self.request.GET.get("location", "")
        ctx["active_category"] = self.request.GET.get("category", "")
        ctx["active_guests"] = self.request.GET.get("guests", "")
        ctx["total_count"] = conteggio_indicativo(pubblicati.count())
        # Con un filtro attivo il numero di risultati e' un dato funzionale e va
        # dato preciso; senza filtri e' un'affermazione sul portfolio, e li' si usa
        # la forma indicativa.
        ctx["filtri_attivi"] = any(
            self.request.GET.get(k) for k in ("location", "category", "guests")
        )
        ctx["page_title"] = "Immobili in gestione"
        ctx["meta_description"] = (
            f"{ctx['total_count']} immobili in gestione EV House Management in Sardegna: "
            "appartamenti, aparthotel e ville per soggiorni brevi."
        )
        return ctx


class PropertyDetailView(DetailView):
    model = Property
    template_name = "properties/property_detail.html"
    context_object_name = "property"

    def get_queryset(self):
        # Le bozze non sono raggiungibili dal sito pubblico.
        return Property.objects.published().prefetch_related(IMMAGINI, "amenities")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        if obj.meta_title:
            ctx["page_title_exact"] = obj.meta_title
        ctx["page_title"] = obj.seo_title
        ctx["meta_description"] = obj.seo_description
        ctx["gallery"] = list(obj.images.all())
        ctx["amenities"] = list(obj.amenities.all())
        ctx["related"] = (
            Property.objects.published()
            .filter(location=obj.location).exclude(pk=obj.pk)
            .prefetch_related(IMMAGINI)[:3]
            or Property.objects.published().exclude(pk=obj.pk).prefetch_related(IMMAGINI)[:3]
        )
        return ctx
