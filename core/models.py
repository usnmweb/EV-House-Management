from django.db import models


class Recensione(models.Model):
    """Una recensione di un proprietario o di un ospite.

    A database e non in un file di configurazione, per due ragioni. La prima e'
    che sono contenuti che cresceranno e che deve poter gestire il cliente
    dall'amministrazione, come gli immobili. La seconda e' che una recensione
    porta con se' un'attribuzione — chi l'ha scritta, quando, su quale canale —
    e quei tre campi devono essere obbligatori per costruzione: la direttiva
    Omnibus (recepita nel Codice del Consumo, art. 22 comma 4-bis) impone di
    dichiarare se e come le recensioni pubblicate sono verificate, e senza
    canale e data non c'e' niente da verificare.

    Nessuna recensione e' precaricata. La sezione in home compare solo quando
    ce n'e' almeno una: una vetrina di testimonianze inventate non e' un
    segnaposto grafico, e' pubblicita' ingannevole.
    """

    class Voce(models.TextChoices):
        PROPRIETARIO = "owner", "Proprietario"
        OSPITE = "guest", "Ospite"

    autore = models.CharField(
        "nome", max_length=80,
        help_text="Come compare sul canale di origine. Anche solo nome e iniziale.",
    )
    voce = models.CharField(
        "chi parla", max_length=10, choices=Voce.choices, default=Voce.OSPITE,
    )
    testo = models.TextField(
        "testo", help_text="Riportato fedelmente. Si puo' accorciare, non riscrivere.",
    )
    canale = models.CharField(
        "canale", max_length=60,
        help_text="Dove e' stata pubblicata: Airbnb, Booking.com, Google, email…",
    )
    data = models.DateField("data")
    url = models.URLField(
        "collegamento", blank=True,
        help_text="Alla recensione originale, se e' pubblica. Rende verificabile ciò che si afferma.",
    )
    luogo = models.CharField(
        "località", max_length=100, blank=True,
        help_text="Facoltativo: l'immobile o la zona a cui si riferisce.",
    )
    in_evidenza = models.BooleanField(
        "in evidenza", default=True,
        help_text="Se disattivata, resta in archivio ma non compare in home.",
    )
    ordine = models.PositiveIntegerField("ordine", default=0)

    class Meta:
        verbose_name = "recensione"
        verbose_name_plural = "recensioni"
        ordering = ["ordine", "-data"]

    def __str__(self):
        return f"{self.autore} — {self.get_voce_display()} ({self.data})"
