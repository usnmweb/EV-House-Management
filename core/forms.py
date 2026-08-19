from django import forms


class ContactForm(forms.Form):
    """Modulo contatti della pagina /contact/."""

    name = forms.CharField(
        label="Nome e cognome",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Mario Rossi", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"placeholder": "mario@esempio.ch", "autocomplete": "email"}
        ),
    )
    phone = forms.CharField(
        label="Telefono (facoltativo)",
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+41 79 000 00 00", "autocomplete": "tel"}),
    )
    message = forms.CharField(
        label="Messaggio",
        widget=forms.Textarea(
            attrs={"rows": 6, "placeholder": "Raccontaci del tuo immobile o della tua richiesta..."}
        ),
    )
    privacy = forms.BooleanField(
        label="Ho letto e accetto l'informativa sulla privacy",
        required=True,
        error_messages={"required": "Devi accettare l'informativa sulla privacy per procedere."},
    )
    # Honeypot anti-spam: se compilato, la richiesta viene scartata.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Inserisci un nome valido.")
        return name

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Il messaggio deve contenere almeno 10 caratteri.")
        return message

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Richiesta non valida.")
        return ""
