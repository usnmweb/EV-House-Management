"""L'amministrazione del sito, su misura per chi la usa.

L'amministrazione standard di Django e' pensata per sviluppatori: sezioni in
ordine alfabetico, nomi tecnici («Core», «Properties»), una pagina iniziale che
elenca tabelle. Chi la usa qui gestisce immobili, articoli e recensioni, e ha
bisogno di sapere cosa c'e' da fare, non come sono fatte le tabelle.

Questo sito prende il posto di quello predefinito (vedi `config/apps.py`),
quindi le registrazioni con `@admin.register` nei singoli moduli continuano a
funzionare senza cambiare nulla.
"""

from django.contrib import admin
from django.urls import reverse


# Ordine delle sezioni nella pagina iniziale e nel menu laterale: dal lavoro di
# tutti i giorni a quello di una volta l'anno. Le app non elencate finiscono in
# coda, in ordine alfabetico, cosi' un'app nuova non sparisce.
ORDINE_SEZIONI = ["properties", "blog", "core", "auth"]

# Nomi delle sezioni che non si possono cambiare dall'AppConfig perche' non
# sono nostre.
NOMI_SEZIONI = {"auth": "Utenti e accessi"}


class EVAdminSite(admin.AdminSite):
    site_header = "EV House Management"
    site_title = "EV House Management"
    index_title = "Pannello di gestione"
    # Il menu laterale ripeteva l'elenco delle sezioni su ogni pagina e si
    # prendeva 280px: negli elenchi erano proprio quelli che mancavano, e i
    # titoli degli immobili andavano a capo su cinque righe. Per spostarsi
    # bastano le briciole di pane e la pagina iniziale.
    enable_nav_sidebar = False

    def get_app_list(self, request, app_label=None):
        sezioni = super().get_app_list(request, app_label)
        for sezione in sezioni:
            sezione["name"] = NOMI_SEZIONI.get(sezione["app_label"], sezione["name"])

        def posizione(sezione):
            etichetta = sezione["app_label"]
            if etichetta in ORDINE_SEZIONI:
                return (ORDINE_SEZIONI.index(etichetta), "")
            return (len(ORDINE_SEZIONI), sezione["name"])

        return sorted(sezioni, key=posizione)

    def index(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), "cruscotto": self._cruscotto(request)}
        return super().index(request, extra_context)

    def _cruscotto(self, request):
        """Le schede in cima alla pagina iniziale: quanto c'e' e cosa manca.

        Ogni numero porta all'elenco gia' filtrato su quelle righe: il numero
        da solo informa, il collegamento fa risparmiare tre clic. Le schede
        compaiono solo se l'utente ha il permesso di vedere quei dati.
        """
        # Import qui dentro: questo modulo si carica prima dei modelli.
        from blog.models import Article
        from core.models import Recensione
        from properties.models import Property

        utente = request.user
        schede = []

        if utente.has_perm("properties.view_property"):
            elenco = reverse("admin:properties_property_changelist")
            pubblicati = Property.objects.published()
            senza_copertina = (
                pubblicati.exclude(images__copertina=True)
                .filter(images__isnull=False).distinct().count()
            )
            schede.append({
                "titolo": "Immobili",
                "numero": pubblicati.count(),
                "dicitura": "pubblicati sul sito",
                "dettagli": [
                    {"testo": "in bozza",
                     "numero": Property.objects.filter(status=Property.Status.DRAFT).count(),
                     "url": f"{elenco}?status__exact=draft"},
                ],
                "url": f"{elenco}?status__exact=published",
                "azione": {"testo": "Aggiungi un immobile",
                           "url": reverse("admin:properties_property_add")},
            })
            schede.append({
                "titolo": "Copertine",
                "numero": senza_copertina,
                "dicitura": "immobili con la foto scelta dal portale",
                "nota": "Apri l'immobile e spunta «Copertina» sulla foto migliore.",
                "url": f"{elenco}?status__exact=published&copertina=portale",
                "da_fare": senza_copertina > 0,
            })

        if utente.has_perm("blog.view_article"):
            elenco = reverse("admin:blog_article_changelist")
            schede.append({
                "titolo": "Il Giornale",
                "numero": Article.objects.pubblicati().count(),
                "dicitura": "articoli pubblicati",
                "dettagli": [
                    {"testo": "in bozza",
                     "numero": Article.objects.filter(pubblicato=False).count(),
                     "url": f"{elenco}?pubblicato__exact=0"},
                ],
                "url": f"{elenco}?pubblicato__exact=1",
                "azione": {"testo": "Scrivi un articolo",
                           "url": reverse("admin:blog_article_add")},
            })

        if utente.has_perm("core.view_recensione"):
            in_home = Recensione.objects.filter(in_evidenza=True).count()
            schede.append({
                "titolo": "Recensioni",
                "numero": in_home,
                "dicitura": "in evidenza in home",
                "nota": (
                    "Nessuna recensione in home: la sezione resta nascosta "
                    "finché non ne aggiungi una." if not in_home else ""
                ),
                "url": reverse("admin:core_recensione_changelist"),
                "azione": {"testo": "Aggiungi una recensione",
                           "url": reverse("admin:core_recensione_add")},
                "da_fare": in_home == 0,
            })

        return schede
