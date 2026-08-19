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
