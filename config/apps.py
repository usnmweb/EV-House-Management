from django.contrib.admin.apps import AdminConfig


class EVAdminConfig(AdminConfig):
    """L'amministrazione di Django con il sito su misura di `config/admin.py`.

    `default_site` fa si' che `admin.site` — quello su cui ogni app registra i
    propri modelli con `@admin.register` — sia gia' il nostro: nessun modulo
    deve sapere che esiste.
    """

    default_site = "config.admin.EVAdminSite"
