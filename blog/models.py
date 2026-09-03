import re

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ArticoloQuerySet(models.QuerySet):
    def pubblicati(self):
        return self.filter(pubblicato=True)

    def in_evidenza(self):
        return self.pubblicati().filter(in_evidenza=True)


class Article(models.Model):
    """Un articolo del Giornale.

    Il corpo e' testo semplice, non HTML: i paragrafi si separano con una riga
    vuota e una riga che comincia per «## » diventa un sottotitolo. E' un
    formato minuscolo, ma toglie di mezzo il problema piu' grosso di un blog
    redazionale — il markup incollato dall'amministrazione finisce stampato
    cosi' com'e', quindi niente `|safe` e niente iniezione possibile. Chi
    scrive non deve sapere cos'e' un tag.
    """

    class Categoria(models.TextChoices):
        PROPRIETARI = "proprietari", "Per i proprietari"
        LOCALITA = "localita", "Località"
        OSPITI = "ospiti", "Consigli per ospiti"
        NOVITA = "novita", "Novità"

    titolo = models.CharField("Titolo", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True, blank=True)
    categoria = models.CharField(
        "Categoria", max_length=20, choices=Categoria.choices,
        default=Categoria.NOVITA, db_index=True,
        help_text="Compare come occhiello sopra il titolo e nella barra dei filtri.",
    )
    estratto = models.TextField(
        "Estratto", max_length=400,
        help_text="Due righe. Si leggono nell'elenco e nei risultati di ricerca.",
    )
    sottotitolo = models.CharField(
        "Sottotitolo", max_length=300, blank=True,
        help_text="Facoltativo: la frase sotto il titolo nella pagina dell'articolo.",
    )
    corpo = models.TextField(
        "Corpo",
        help_text="Paragrafi separati da una riga vuota. Una riga che comincia "
                  "per «## » diventa un sottotitolo.",
    )

    citazione = models.TextField(
        "Citazione", blank=True,
        help_text="Facoltativa: compare a meta' articolo, in corsivo.",
    )
    citazione_fonte = models.CharField("Fonte della citazione", max_length=160, blank=True)

    copertina = models.ImageField(
        "Copertina", upload_to="giornale/%Y/%m/", blank=True,
    )
    copertina_alt = models.CharField(
        "Testo alternativo della copertina", max_length=200, blank=True,
    )

    pubblicato_il = models.DateField("Data di pubblicazione", db_index=True)
    tempo_lettura = models.PositiveIntegerField(
        "Tempo di lettura (minuti)", default=0,
        help_text="Lasciare a zero: viene calcolato dal corpo alla prima salvata.",
    )
    autore = models.CharField("Firma", max_length=120, default="Redazione EV House")

    tag = models.CharField(
        "Tag", max_length=250, blank=True,
        help_text="Separati da virgola. Sono etichette da leggere, non filtri: "
                  "a filtrare ci pensa la categoria.",
    )

    mostra_stagione = models.BooleanField(
        "Mostra i numeri della stagione", default=False,
        help_text="Aggiunge la fascia con occupazione, notti e immobili gestiti. "
                  "I valori sono quelli di settings.py, gli stessi della home: "
                  "non vanno riscritti qui, altrimenti un giorno divergono.",
    )

    in_evidenza = models.BooleanField(
        "In evidenza", default=False,
        help_text="Il piu' recente fra quelli in evidenza apre l'elenco.",
    )
    pubblicato = models.BooleanField(
        "Pubblicato", default=False,
        help_text="Solo gli articoli pubblicati compaiono sul sito e in sitemap.",
    )

    meta_description = models.CharField("Meta description", max_length=160, blank=True)
    creato_il = models.DateTimeField("Creato il", auto_now_add=True)
    aggiornato_il = models.DateTimeField("Aggiornato il", auto_now=True)

    objects = ArticoloQuerySet.as_manager()

    class Meta:
        verbose_name = "Articolo"
        verbose_name_plural = "Articoli"
        ordering = ["-pubblicato_il", "-id"]
        indexes = [models.Index(fields=["pubblicato", "-pubblicato_il"])]

    def __str__(self):
        return self.titolo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titolo)[:200] or "articolo"
            candidato, n = base, 2
            while Article.objects.filter(slug=candidato).exclude(pk=self.pk).exists():
                candidato = f"{base}-{n}"
                n += 1
            self.slug = candidato
        if not self.tempo_lettura:
            self.tempo_lettura = self.minuti_stimati()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    def minuti_stimati(self):
        """Duecento parole al minuto, arrotondate per eccesso, minimo uno.

        E' una stima dichiarata come tale: duecento e' la velocita' di lettura
        attenta su schermo comunemente usata. Meglio un numero che l'autore
        puo' correggere a mano che nessun numero.
        """
        parole = len(re.findall(r"\w+", self.corpo))
        return max(1, round(parole / 200)) if parole else 1

    @property
    def blocchi(self):
        """Il corpo spezzato in blocchi tipizzati, pronti per il template.

        Ogni blocco e' `{"tipo": "titolo"|"paragrafo", "testo": ...}`; i titoli
        portano anche un `id` e i paragrafi un `primo` che marca l'incipit. Il
        template li stampa con l'escaping normale di Django.

        Gli `id` servono all'indice laterale e ai collegamenti diretti a una
        sezione. Si ricavano dal testo del titolo e non dalla posizione, cosi'
        un link condiviso resta valido anche se piu' avanti si aggiunge un
        paragrafo: sarebbe fragile il contrario, `#sezione-3` che cambia
        significato a ogni modifica.
        """
        fuori = []
        visti = {}
        primo_paragrafo = True
        for pezzo in re.split(r"\n\s*\n", self.corpo.strip()):
            testo = pezzo.strip()
            if not testo:
                continue
            if testo.startswith("## "):
                testo = testo[3:].strip()
                base = slugify(testo)[:60] or "sezione"
                visti[base] = visti.get(base, 0) + 1
                ident = base if visti[base] == 1 else f"{base}-{visti[base]}"
                fuori.append({"tipo": "titolo", "testo": testo, "id": ident})
            else:
                fuori.append({"tipo": "paragrafo", "testo": testo, "primo": primo_paragrafo})
                primo_paragrafo = False
        return fuori

    @property
    def sommario(self):
        """I soli titoli, per l'indice laterale."""
        return [b for b in self.blocchi if b["tipo"] == "titolo"]

    @property
    def elenco_tag(self):
        return [t.strip() for t in self.tag.split(",") if t.strip()]

    @property
    def seo_description(self):
        return self.meta_description or self.estratto[:157].strip()
