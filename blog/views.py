from django.conf import settings
from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Article


def _numeri_stagione():
    """I numeri della stagione, presi da settings.py e non riscritti qui.

    Sono gli stessi della barra in home. Duplicarli su ogni articolo
    significherebbe che il giorno in cui cambiano restano indietro in un posto
    solo — quello che nessuno ricontrolla. Le voci senza valore non vengono
    proprio prodotte: una casella vuota in mezzo a dei numeri e' peggio di una
    casella in meno.
    """
    voci = []
    if settings.SEASON_OCCUPANCY:
        voci.append({
            "numero": f"{settings.SEASON_OCCUPANCY}%",
            "etichetta": "Occupazione",
            "sotto": f"nella settimana del {settings.SEASON_WEEK}" if settings.SEASON_WEEK else "",
            # `conta` dice a main.js se il numero puo' salire da zero: le
            # percentuali si', le frazioni «424 / 455» no.
            "conta": settings.SEASON_OCCUPANCY.replace(",", "."),
        })
    if settings.SEASON_NIGHTS_SOLD and settings.SEASON_NIGHTS_AVAILABLE:
        voci.append({
            "numero": f"{settings.SEASON_NIGHTS_SOLD} / {settings.SEASON_NIGHTS_AVAILABLE}",
            "etichetta": "Notti occupate su disponibili",
            "sotto": "",
            "conta": "",
        })
    if settings.PROPERTIES_MANAGED:
        voci.append({
            "numero": settings.PROPERTIES_MANAGED,
            "etichetta": "Immobili gestiti",
            "sotto": "",
            "conta": settings.PROPERTIES_MANAGED.lstrip("+"),
        })
    if settings.SEASON_FIRST_YEAR.isdigit():
        from datetime import date
        stagioni = date.today().year - int(settings.SEASON_FIRST_YEAR)
        voci.append({
            "numero": str(stagioni),
            "etichetta": "Stagioni complete",
            "sotto": f"dal {settings.SEASON_FIRST_YEAR}",
            "conta": str(stagioni),
        })
    return voci


class ArticleListView(ListView):
    model = Article
    template_name = "blog/article_list.html"
    context_object_name = "articoli"
    paginate_by = 9

    def get_queryset(self):
        qs = Article.objects.pubblicati()
        categoria = self.request.GET.get("categoria")
        if categoria in dict(Article.Categoria.choices):
            qs = qs.filter(categoria=categoria)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(titolo__icontains=q) | Q(estratto__icontains=q)
                | Q(corpo__icontains=q) | Q(tag__icontains=q)
            )
        # L'articolo in evidenza apre la pagina per conto suo: lasciarlo anche
        # nella griglia lo farebbe comparire due volte. Ma solo quando e'
        # davvero li' sopra, cioe' senza filtri.
        evidenza = self._in_evidenza()
        if evidenza is not None:
            qs = qs.exclude(pk=evidenza.pk)
        return qs

    def _in_evidenza(self):
        """L'articolo di apertura, o None se ci sono filtri attivi.

        Con un filtro attivo la pagina risponde a una domanda precisa, e un
        articolo messo in cima perche' «in evidenza» sarebbe fuori posto: chi
        ha filtrato vuole vedere i risultati, non la vetrina.
        """
        if getattr(self, "_filtri", None):
            return None
        if not hasattr(self, "_evidenza_cache"):
            self._evidenza_cache = Article.objects.in_evidenza().first()
        return self._evidenza_cache

    def get(self, request, *args, **kwargs):
        self._filtri = bool(request.GET.get("categoria") or (request.GET.get("q") or "").strip())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        categoria = self.request.GET.get("categoria", "")
        q = (self.request.GET.get("q") or "").strip()

        # Conteggi per categoria: un filtro che porta a zero risultati e' un
        # vicolo cieco, e il numero accanto all'etichetta lo evita in anticipo.
        conteggi = {}
        for chiave, _ in Article.Categoria.choices:
            conteggi[chiave] = Article.objects.pubblicati().filter(categoria=chiave).count()

        ctx["categorie"] = [
            {"chiave": chiave, "nome": nome, "quanti": conteggi[chiave]}
            for chiave, nome in Article.Categoria.choices if conteggi[chiave]
        ]
        ctx["categoria_attiva"] = categoria if categoria in conteggi else ""
        # Il nome per esteso viene dalle choices, non dal primo risultato:
        # con zero risultati il primo risultato non c'e'.
        ctx["categoria_attiva_nome"] = dict(Article.Categoria.choices).get(categoria, "")
        ctx["ricerca"] = q
        ctx["filtri_attivi"] = self._filtri
        ctx["evidenza"] = self._in_evidenza()
        ctx["totale"] = Article.objects.pubblicati().count()
        ctx["page_title"] = "Il Giornale"
        ctx["meta_description"] = (
            "Note dalla costa: gestione degli affitti brevi, adempimenti, località "
            "e consigli per gli ospiti, scritti da chi gestisce le case in Sardegna."
        )
        return ctx


class ArticleDetailView(DetailView):
    model = Article
    template_name = "blog/article_detail.html"
    context_object_name = "articolo"

    def get_queryset(self):
        # Le bozze non sono raggiungibili dal sito pubblico.
        return Article.objects.pubblicati()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        ctx["page_title"] = obj.titolo
        ctx["meta_description"] = obj.seo_description
        ctx["stagione"] = _numeri_stagione() if obj.mostra_stagione else []
        # Prima gli articoli della stessa categoria; se non bastano, si completa
        # con i piu' recenti. Meglio tre suggerimenti che uno solo pertinente.
        stessa = list(
            Article.objects.pubblicati()
            .filter(categoria=obj.categoria).exclude(pk=obj.pk)[:3]
        )
        if len(stessa) < 3:
            visti = {a.pk for a in stessa} | {obj.pk}
            stessa += list(
                Article.objects.pubblicati().exclude(pk__in=visti)[: 3 - len(stessa)]
            )
        ctx["correlati"] = stessa
        return ctx
