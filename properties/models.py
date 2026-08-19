from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class PropertyQuerySet(models.QuerySet):
    def featured(self):
        return self.filter(featured=True)


class Property(models.Model):
    """Immobile gestito da EV House Management."""

    title = models.CharField("Titolo", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True, blank=True)
    location = models.CharField("Località", max_length=200)
    short_description = models.TextField("Descrizione breve", max_length=400)
    description = models.TextField("Descrizione completa")
    bedrooms = models.PositiveIntegerField("Camere da letto", default=1)
    bathrooms = models.PositiveIntegerField("Bagni", default=1)
    guests = models.PositiveIntegerField("Ospiti", default=2)
    featured = models.BooleanField("In evidenza", default=False)
    booking_url = models.URLField("URL prenotazione", blank=True)
    meta_title = models.CharField("Meta title", max_length=70, blank=True)
    meta_description = models.CharField("Meta description", max_length=160, blank=True)
    created_at = models.DateTimeField("Creato il", auto_now_add=True)
    updated_at = models.DateTimeField("Aggiornato il", auto_now=True)

    objects = PropertyQuerySet.as_manager()

    class Meta:
        verbose_name = "Immobile"
        verbose_name_plural = "Immobili"
        ordering = ["-featured", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "immobile"
            candidate = base
            counter = 2
            while Property.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("properties:detail", kwargs={"slug": self.slug})

    @property
    def seo_title(self):
        return self.meta_title or f"{self.title} - {self.location}"

    @property
    def seo_description(self):
        return self.meta_description or self.short_description[:157]

    @property
    def cover_image(self):
        return self.images.first()


class PropertyImage(models.Model):
    """Immagine associata a un immobile."""

    property = models.ForeignKey(
        Property,
        verbose_name="Immobile",
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField("Immagine", upload_to="properties/%Y/%m/")
    alt_text = models.CharField("Testo alternativo", max_length=200, blank=True)
    order = models.PositiveIntegerField("Ordine", default=0)

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
