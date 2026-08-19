from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Amenity(models.Model):
    """Dotazione di un immobile (aria condizionata, lavatrice, ...)."""

    name = models.CharField("Nome", max_length=120, unique=True)
    slug = models.SlugField("Slug", max_length=140, unique=True, blank=True)

    class Meta:
        verbose_name = "Dotazione"
        verbose_name_plural = "Dotazioni"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)


class PropertyQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Property.Status.PUBLISHED)

    def featured(self):
        return self.published().filter(featured=True)


class Property(models.Model):
    """Immobile gestito da EV House Management."""

    class Status(models.TextChoices):
        PUBLISHED = "published", "Pubblicato"
        DRAFT = "draft", "Bozza"

    class Category(models.TextChoices):
        APARTMENT = "Appartamento", "Appartamento"
        APARTHOTEL = "Aparthotel", "Aparthotel"
        VILLA = "Villa", "Villa"
        HOTEL = "Hotel", "Hotel"

    title = models.CharField("Titolo", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True, blank=True)
    status = models.CharField(
        "Stato", max_length=12, choices=Status.choices, default=Status.DRAFT,
        help_text="Solo gli immobili pubblicati compaiono sul sito e nella sitemap.",
    )
    category = models.CharField(
        "Tipologia", max_length=32, choices=Category.choices, blank=True
    )

    location = models.CharField("Località", max_length=200)
    address = models.CharField("Indirizzo", max_length=250, blank=True)
    latitude = models.DecimalField(
        "Latitudine", max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        "Longitudine", max_digits=10, decimal_places=7, null=True, blank=True
    )

    short_description = models.TextField("Descrizione breve", max_length=400, blank=True)
    description = models.TextField("Descrizione completa", blank=True)

    bedrooms = models.PositiveIntegerField("Camere da letto", default=1)
    bathrooms = models.PositiveIntegerField("Bagni", default=1)
    guests = models.PositiveIntegerField("Ospiti", default=2)
    amenities = models.ManyToManyField(
        Amenity, verbose_name="Dotazioni", related_name="properties", blank=True
    )

    featured = models.BooleanField("In evidenza", default=False)
    booking_url = models.URLField(
        "URL prenotazione", blank=True,
        help_text="Scheda sul portale esterno: da lì passano disponibilità e tariffe.",
    )
    license_code = models.CharField(
        "Codice licenza", max_length=60, blank=True,
        help_text="Codice identificativo obbligatorio per le locazioni brevi.",
    )
    external_id = models.CharField(
        "ID sul portale", max_length=32, blank=True, db_index=True
    )

    meta_title = models.CharField("Meta title", max_length=70, blank=True)
    meta_description = models.CharField("Meta description", max_length=160, blank=True)
    created_at = models.DateTimeField("Creato il", auto_now_add=True)
    updated_at = models.DateTimeField("Aggiornato il", auto_now=True)

    objects = PropertyQuerySet.as_manager()

    class Meta:
        verbose_name = "Immobile"
        verbose_name_plural = "Immobili"
        ordering = ["-featured", "title"]
        indexes = [models.Index(fields=["status", "location"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "immobile"
            candidate, counter = base, 2
            while Property.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("properties:detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def seo_title(self):
        return self.meta_title or f"{self.title} - {self.location}"

    @property
    def seo_description(self):
        if self.meta_description:
            return self.meta_description
        text = self.short_description or self.description
        return text[:157].strip()

    @property
    def cover_image(self):
        return self.images.first()


class PropertyImage(models.Model):
    """Immagine associata a un immobile."""

    property = models.ForeignKey(
        Property, verbose_name="Immobile", related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField("Immagine", upload_to="properties/%Y/%m/")
    alt_text = models.CharField("Testo alternativo", max_length=200, blank=True)
    order = models.PositiveIntegerField("Ordine", default=0)
    source_ref = models.CharField(
        "Riferimento originale", max_length=120, blank=True, db_index=True,
        help_text="Nome del file sul portale: evita di riscaricare la stessa foto.",
    )

    class Meta:
        verbose_name = "Immagine immobile"
        verbose_name_plural = "Immagini immobile"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.property.title} - immagine {self.order}"

    # NB: il campo FK `property` oscura il builtin `property` nel corpo della
    # classe, quindi qui si usa un metodo semplice (i template lo chiamano comunque).
    def display_alt(self):
        return self.alt_text or self.property.title
