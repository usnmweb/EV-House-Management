"""I nomi che si leggono in vetrina, e quelli che usa il portale.

Il portale usa nomi di lavoro — «Villetta G2», «Via Gallura - Siniscola» —
buoni per l'agenda interna e muti per chi cerca casa: non dicono dove si e' ne'
quanto dista il mare. Qui stanno le riscritture, in un elenco solo.

L'abbinamento e' sull'`external_id`, che e' l'identificatore del portale e non
cambia. Il nome vecchio si controlla lo stesso: se non corrisponde, la riga si
salta. Meglio un nome non aggiornato che il nome di un'altra casa.
"""

# (external_id, nome sul portale, nome in vetrina)
NOMI = [
    ("91",  "Brezza D'Amore",
            "[Brezza D'Amore] APT con verande a 400mt dal Mare"),
    ("89",  "Casa Rudalza",
            "[Casa Rudalza] Villa privata | 5 min Porto Rotondo"),
    ("95",  "San Lorenzo",
            "[San Lorenzo] Veranda Vista Mare, Spiaggia a 7 min"),
    ("107", "Baia Caddinas",
            "[Loft Vista mare Golfo Aranci] 200mt dalla Spiaggia"),
    ("93",  "Villetta A1",
            "[Villetta A1] 300mt dalla spiaggia"),
    ("92",  "Villetta G2",
            "[Villetta G2] 400mt dalla Spiaggia"),
    ("104", "Via Gallura - Siniscola",
            "Vacanze da sogno in Sardegna [APT a 7km dal mare]"),
    ("88",  "[2 min dal Mare] Apt moderno - Bunte 18:03",
            "[Fronte Mare] APT Nuovo & Moderno - Murta Maria"),
    ("122", "Trilocale con Giardino a 3 minuti dal Mare",
            "[Tanaunella] giardino con BBQ | Mare 3 min"),
]


def applica(Property, scrivi=True):
    """Riscrive i titoli non ancora riscritti. Restituisce l'elenco dei tocchi.

    Riscrive solo dove il titolo e' ancora quello del portale: un nome gia'
    sistemato, o cambiato a mano nell'amministrazione in modo diverso da
    questo elenco, non si tocca. Da cui l'essere ripetibile — gira a ogni
    rilascio e la seconda volta non fa niente.

    Lo slug resta com'e': e' l'indirizzo della pagina, cambiarlo romperebbe i
    collegamenti gia' in giro e quel che i motori hanno indicizzato. Il meta
    title invece si svuota, cosi' si ricompone dal nome nuovo; se restasse, il
    risultato di ricerca continuerebbe a mostrare il nome vecchio.
    """
    fatti = []
    for external_id, vecchio, nuovo in NOMI:
        righe = Property.objects.filter(external_id=external_id, title=vecchio)
        if not righe.exists():
            continue
        fatti.append((external_id, vecchio, nuovo))
        if scrivi:
            righe.update(title=nuovo, meta_title="")
    return fatti
