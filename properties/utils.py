"""Funzioni di supporto per la presentazione dei dati immobiliari."""


def conteggio_indicativo(n, passo=10):
    """Arrotonda per difetto e prefissa un più: 63 -> "+60", 71 -> "+70".

    Serve a comunicare l'ordine di grandezza del portfolio senza dichiarare una
    cifra esatta, che invecchierebbe a ogni immobile aggiunto o tolto. Sotto la
    soglia il numero preciso resta l'unica forma sensata: "+0" non direbbe nulla.
    """
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ""
    if n < passo:
        return str(n)
    return f"+{n // passo * passo}"


def testo_alternativo(titolo, categoria, localita, ordine, totale, limite=200):
    """Compone l'alt di una fotografia, distinto per posizione nella galleria.

    Il portale non fornisce una didascalia per singolo scatto, quindi l'alt non
    puo' descrivere cosa si vede: inventarlo sarebbe peggio che ometterlo. Si
    dichiara allora quello che si sa con certezza — immobile, tipologia, luogo e
    posizione nella galleria — cosi' ogni immagine ha un testo suo invece di
    ripetere lo stesso per tutte.
    """
    coda = (
        f"{categoria.lower()} a {localita}" if ordine == 0 and categoria
        else f"foto {ordine + 1} di {totale}"
    )
    if ordine == 0 and not categoria:
        coda = f"a {localita}"

    spazio = limite - len(coda) - 3          # 3 = lunghezza di " — "
    titolo = titolo.strip()
    if len(titolo) > spazio:
        titolo = titolo[: max(0, spazio - 1)].rstrip() + "…"
    return f"{titolo} — {coda}"


# ---------------------------------------------------------------------------
# Riconoscimento degli scatti ripetuti
#
# Il portale a volte serve due volte la stessa fotografia sotto indirizzi
# diversi. Confrontare i byte non basta: due ricompressioni dello stesso scatto
# danno file diversi. Serve un confronto su cosa si vede, non su cosa c'e'
# scritto nel file.
# ---------------------------------------------------------------------------

def impronta_visiva(sorgente, lato=8):
    """Impronta percettiva (dHash) di un'immagine.

    Si riduce a una miniatura in scala di grigi e si confronta ogni pixel con
    quello alla sua destra: il risultato dipende dalla struttura di cio' che si
    vede, non dalla risoluzione ne' dalla compressione. Due riduzioni diverse
    dello stesso scatto danno impronte quasi uguali.

    `sorgente` puo' essere un percorso, un file aperto o dei byte.
    """
    from io import BytesIO

    from PIL import Image

    if isinstance(sorgente, (bytes, bytearray)):
        sorgente = BytesIO(sorgente)
    with Image.open(sorgente) as im:
        piccola = im.convert("L").resize((lato + 1, lato), Image.LANCZOS)
        px = list(piccola.getdata())
    bit = 0
    for riga in range(lato):
        base = riga * (lato + 1)
        for col in range(lato):
            if px[base + col] > px[base + col + 1]:
                bit |= 1 << (riga * lato + col)
    return bit


def scarto_visivo(a, b):
    """Quanti bit differiscono fra due impronte. Zero = stessa immagine."""
    return bin(a ^ b).count("1")


# Sotto questa soglia due scatti sono lo stesso. Non e' un numero a caso: sul
# materiale di questo sito le coppie si dividono nettamente in due gruppi —
# da 0 a 4 sono la stessa inquadratura, da 12 in su sono stanze riprese da
# angolazioni diverse. Sei sta nel mezzo, largo abbastanza da coprire le
# ricompressioni e stretto abbastanza da non buttare via fotografie vere.
SOGLIA_DOPPIONE = 6


def rinumera_foto(immobile):
    """Ordine consecutivo e testi alternativi coerenti col totale vero.

    Serve dopo ogni cambiamento all'insieme delle fotografie di un immobile.
    Non basta sistemare `order`: il totale compare dentro il testo alternativo
    ("foto 3 di 8"), quindi togliendo uno scatto senza rifare i testi restano
    in pagina numerazioni che saltano e totali che non tornano.

    Restituisce quante righe ha toccato.
    """
    from properties.models import PropertyImage

    foto = list(immobile.images.order_by("order", "id"))
    totale = len(foto)
    toccate = 0
    for posizione, immagine in enumerate(foto):
        alt = testo_alternativo(
            immobile.title, immobile.category, immobile.location, posizione, totale
        )
        if immagine.order != posizione or immagine.alt_text != alt:
            PropertyImage.objects.filter(pk=immagine.pk).update(
                order=posizione, alt_text=alt
            )
            toccate += 1
    return toccate
