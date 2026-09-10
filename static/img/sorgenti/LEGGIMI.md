# Sorgenti del marchio

`logo-2025-originale.png` è il file consegnato dal cliente (4858 × 2696, PNG con
trasparenza, scritta quasi nera e tetti dorati). Da qui si ricavano i due file
che il sito usa davvero, in `static/img/`:

- **`logo-su-chiaro.png`** — ritagliato ai margini pieni e ridotto a 922 × 512.
- **`logo-su-scuro.png`** — lo stesso, con la scritta portata ad avorio
  (`#f7f4ee`) perché su fondo nero quella quasi nera sparirebbe. La selezione
  guarda la **saturazione**, non la sola luminosità: così i bordi scuri dell'oro
  non vengono scambiati per testo e ricolorati anche loro.

Rigenerarli:

```python
from PIL import Image
sorgente = Image.open("static/img/sorgenti/logo-2025-originale.png").convert("RGBA")
logo = sorgente.crop(sorgente.getchannel("A").getbbox())
chiaro = logo.resize((922, 512), Image.LANCZOS)
chiaro.save("static/img/logo-su-chiaro.png", optimize=True)

scuro = chiaro.copy(); px = scuro.load()
for y in range(scuro.height):
    for x in range(scuro.width):
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        massimo, minimo = max(r, g, b), min(r, g, b)
        saturazione = 0 if massimo == 0 else (massimo - minimo) / massimo
        if saturazione < 0.28 and massimo < 150:      # grigio scuro: è testo
            px[x, y] = (247, 244, 238, a)
scuro.save("static/img/logo-su-scuro.png", optimize=True)
```

Cambiando le dimensioni vanno aggiornati anche gli attributi `width`/`height`
nei template (`base.html`, `_intro.html`): servono al browser per riservare lo
spazio prima che l'immagine arrivi, e un test li verifica.
