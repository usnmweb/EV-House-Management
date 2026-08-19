from django.db.models import Prefetch
from django.views.generic import DetailView, ListView

from .models import Property, PropertyImage


class PropertyListView(ListView):
    model = Property
    template_name = "properties/property_list.html"
    context_object_name = "properties"
    paginate_by = 9

    def get_queryset(self):
        qs = Property.objects.prefetch_related(
            Prefetch("images", queryset=PropertyImage.objects.order_by("order", "id"))
        )
        location = self.request.GET.get("location")
        if location:
            qs = qs.filter(location__icontains=location)
        guests = self.request.GET.get("guests")
        if guests and guests.isdigit():
            qs = qs.filter(guests__gte=int(guests))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["locations"] = (
            Property.objects.order_by("location")
            .values_list("location", flat=True)
            .distinct()
        )
        ctx["active_location"] = self.request.GET.get("location", "")
        ctx["active_guests"] = self.request.GET.get("guests", "")
        ctx["page_title"] = "Immobili"
        ctx["meta_description"] = (
            "Scopri gli immobili in gestione EV House Management: appartamenti e "
            "residenze selezionate, pronte per il soggiorno."
        )
        return ctx


class PropertyDetailView(DetailView):
    model = Property
    template_name = "properties/property_detail.html"
    context_object_name = "property"

    def get_queryset(self):
        return Property.objects.prefetch_related(
            Prefetch("images", queryset=PropertyImage.objects.order_by("order", "id"))
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        # meta_title, se compilato, e già il titolo completo: non appendere il nome sito.
        if obj.meta_title:
            ctx["page_title_exact"] = obj.meta_title
        ctx["page_title"] = obj.seo_title
        ctx["meta_description"] = obj.seo_description
        ctx["gallery"] = list(obj.images.all())
        ctx["related"] = (
            Property.objects.exclude(pk=obj.pk)
            .prefetch_related("images")[:3]
        )
        return ctx
