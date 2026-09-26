import io
import pathlib
import shutil
import tempfile
from datetime import date

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from properties.models import Property, PropertyImage

from .models import Article


class BaseGiornale(TestCase):
    """Parte da un Giornale vuoto.

    La migration dei contenuti gira anche sul database di prova — ed e' giusto
    cosi', perche' e' il modo in cui si verifica che gli otto articoli di
    partenza arrivino davvero su un'installazione nuova. Ma per un test sui
    filtri sono ingombri: ogni conteggio diventerebbe «uno piu' quello che c'e'
    gia'», e la prima volta che qualcuno aggiunge un articolo alla migration i
    test si romperebbero senza che nulla si sia rotto davvero.
    """

    def setUp(self):
        Article.objects.all().delete()


def _articolo(**extra):
    dati = {
        "titolo": "Un titolo di prova",
        "estratto": "Due righe di estratto.",
        "corpo": "Primo paragrafo.\n\n## Un sottotitolo\n\nSecondo paragrafo.",
        "pubblicato_il": date(2026, 5, 1),
        "pubblicato": True,
    }
    dati.update(extra)
    return Article.objects.create(**dati)


class ModelloTest(BaseGiornale):
    def test_slug_e_minuti_si_calcolano_da_soli(self):
        a = _articolo()
        self.assertEqual(a.slug, "un-titolo-di-prova")
        self.assertGreaterEqual(a.tempo_lettura, 1)

    def test_slug_non_collide(self):
        _articolo()
        b = _articolo(pubblicato_il=date(2026, 5, 2))
        self.assertEqual(b.slug, "un-titolo-di-prova-2")

    def test_corpo_diventa_blocchi_tipizzati(self):
        a = _articolo()
        self.assertEqual(
            [b["tipo"] for b in a.blocchi], ["paragrafo", "titolo", "paragrafo"]
        )
        self.assertEqual(a.blocchi[1]["testo"], "Un sottotitolo")

    def test_i_titoli_hanno_un_ancora_ricavata_dal_testo(self):
        a = _articolo(corpo="p\n\n## Il CIN\n\np\n\n## La sicurezza\n\np")
        self.assertEqual([t["id"] for t in a.sommario], ["il-cin", "la-sicurezza"])

    def test_due_titoli_uguali_non_collidono(self):
        a = _articolo(corpo="## Nota\n\np\n\n## Nota\n\np")
        self.assertEqual([t["id"] for t in a.sommario], ["nota", "nota-2"])

    def test_solo_il_primo_paragrafo_e_incipit(self):
        a = _articolo(corpo="uno\n\ndue\n\n## t\n\ntre")
        primi = [b.get("primo") for b in a.blocchi if b["tipo"] == "paragrafo"]
        self.assertEqual(primi, [True, False, False])

    def test_tag_si_separano_sulla_virgola(self):
        a = _articolo(tag=" mare , casa ,, ")
        self.assertEqual(a.elenco_tag, ["mare", "casa"])


class ElencoTest(BaseGiornale):
    def test_le_bozze_non_compaiono(self):
        _articolo(titolo="Pubblicato")
        _articolo(titolo="Bozza", pubblicato=False, pubblicato_il=date(2026, 5, 2))
        h = self.client.get(reverse("blog:list")).content.decode()
        self.assertIn("Pubblicato", h)
        self.assertNotIn("Bozza", h)

    def test_evidenza_non_si_ripete_nella_griglia(self):
        _articolo(titolo="In cima", in_evidenza=True)
        h = self.client.get(reverse("blog:list")).content.decode()
        # Due collegamenti nel riquadro d'apertura, nessuna scheda in griglia.
        self.assertEqual(h.count('class="voce-articolo"'), 0)
        self.assertEqual(h.count('class="art-evidenza"'), 1)

    def test_con_i_filtri_niente_articolo_in_apertura(self):
        _articolo(titolo="In cima", in_evidenza=True, categoria="localita")
        h = self.client.get(reverse("blog:list"), {"categoria": "localita"}).content.decode()
        self.assertNotIn('class="art-evidenza"', h)
        self.assertEqual(h.count('class="voce-articolo"'), 1)

    def test_ricerca_e_categoria(self):
        """Si controllano gli indirizzi delle schede, non le parole in pagina.

        Cercare una parola nel corpo della risposta e' fragile: «adempimenti»
        compare nel testo di presentazione del Giornale e nella meta
        description, e un test scritto cosi' fallisce per colpa della propria
        pagina invece che del filtro.
        """
        a = _articolo(titolo="Il vento di maestrale", categoria="localita")
        b = _articolo(titolo="Le scadenze del proprietario", categoria="proprietari",
                      pubblicato_il=date(2026, 5, 2))
        lista = reverse("blog:list")

        h = self.client.get(lista, {"q": "maestrale"}).content.decode()
        self.assertIn(a.get_absolute_url(), h)
        self.assertNotIn(b.get_absolute_url(), h)

        h = self.client.get(lista, {"categoria": "proprietari"}).content.decode()
        self.assertIn(b.get_absolute_url(), h)
        self.assertNotIn(a.get_absolute_url(), h)

        # Categoria e ricerca si combinano invece di annullarsi.
        h = self.client.get(lista, {"categoria": "proprietari", "q": "maestrale"}).content.decode()
        self.assertNotIn(a.get_absolute_url(), h)
        self.assertNotIn(b.get_absolute_url(), h)

    def test_categoria_inventata_non_filtra_nulla(self):
        _articolo()
        r = self.client.get(reverse("blog:list"), {"categoria": "inesistente"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["categoria_attiva"], "")


class DettaglioTest(BaseGiornale):
    def test_l_indice_compare_solo_con_almeno_tre_sezioni(self):
        due = _articolo(corpo="p\n\n## A\n\np\n\n## B\n\np")
        self.assertNotContains(self.client.get(due.get_absolute_url()), "articolo-indice")
        tre = _articolo(titolo="Con tre", pubblicato_il=date(2026, 5, 2),
                        corpo="p\n\n## A\n\np\n\n## B\n\np\n\n## C\n\np")
        r = self.client.get(tre.get_absolute_url())
        self.assertContains(r, "articolo-indice")
        # Ogni voce dell'indice punta a un titolo che esiste davvero.
        h = r.content.decode()
        for t in tre.sommario:
            self.assertIn('href="#%s"' % t["id"], h)
            self.assertIn('id="%s"' % t["id"], h)

    def test_una_bozza_da_404(self):
        a = _articolo(pubblicato=False)
        self.assertEqual(self.client.get(a.get_absolute_url()).status_code, 404)

    def test_il_corpo_non_puo_iniettare_markup(self):
        a = _articolo(corpo="<script>alert(1)</script>")
        h = self.client.get(a.get_absolute_url()).content.decode()
        self.assertNotIn("<script>alert(1)</script>", h)
        self.assertIn("&lt;script&gt;", h)

    def test_la_fascia_numeri_compare_solo_se_richiesta(self):
        a = _articolo()
        self.assertNotContains(self.client.get(a.get_absolute_url()), "articolo-numeri")
        b = _articolo(titolo="Con numeri", mostra_stagione=True,
                      pubblicato_il=date(2026, 5, 2))
        self.assertContains(self.client.get(b.get_absolute_url()), "articolo-numeri")

    def test_i_correlati_sono_tre_e_mai_se_stesso(self):
        for i in range(5):
            _articolo(titolo=f"Articolo {i}", pubblicato_il=date(2026, 5, i + 1))
        a = Article.objects.pubblicati().first()
        correlati = self.client.get(a.get_absolute_url()).context["correlati"]
        self.assertEqual(len(correlati), 3)
        self.assertNotIn(a, correlati)


class SitemapTest(BaseGiornale):
    def test_solo_i_pubblicati_finiscono_in_sitemap(self):
        _articolo(titolo="Visibile")
        _articolo(titolo="Nascosto", pubblicato=False, pubblicato_il=date(2026, 5, 2))
        xml = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/blog/visibile/", xml)
        self.assertNotIn("/blog/nascosto/", xml)
        self.assertIn("/blog/</loc>", xml)


class ContenutiInizialiTest(TestCase):
    """Gli otto articoli della migration devono esserci, e reggere una pagina."""

    def test_gli_otto_articoli_arrivano_con_le_migration(self):
        self.assertEqual(Article.objects.pubblicati().count(), 8)

    def test_ognuno_ha_copertina_estratto_e_categoria_valida(self):
        valide = dict(Article.Categoria.choices)
        for a in Article.objects.pubblicati():
            with self.subTest(articolo=a.slug):
                self.assertTrue(a.copertina, "senza copertina")
                self.assertTrue(a.estratto.strip(), "senza estratto")
                self.assertIn(a.categoria, valide)
                self.assertGreaterEqual(a.tempo_lettura, 1)
                self.assertEqual(self.client.get(a.get_absolute_url()).status_code, 200)

    def test_uno_solo_apre_l_elenco(self):
        self.assertEqual(Article.objects.in_evidenza().count(), 1)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="prova-media-"))
class RiparaCopertineTest(TestCase):
    """Il caso vero: la copertina punta al mese sbagliato.

    In produzione le fotografie degli immobili stanno nella cartella del mese
    in cui sono state scaricate, che non e' quello scritto nella migration:
    stesso nome di file, cartella diversa, copertina in 404.
    """

    def setUp(self):
        immobile = Property.objects.create(title="Prova", location="La Caletta")
        immagine = PropertyImage(property=immobile, order=0)
        immagine.image.save("prova-1.jpg", ContentFile(b"finta"), save=False)
        immagine.save()
        self.percorso_vero = immagine.image.name

    def _ripara(self, applica=True):
        uscita = io.StringIO()
        call_command("ripara_copertine", *(["--applica"] if applica else []), stdout=uscita)
        return uscita.getvalue()

    def test_ripunta_la_copertina_al_percorso_esistente(self):
        rotto = "properties/1999/01/" + pathlib.PurePosixPath(self.percorso_vero).name
        articolo = _articolo(titolo="Con copertina rotta")
        Article.objects.filter(pk=articolo.pk).update(copertina=rotto)

        self._ripara()

        articolo.refresh_from_db()
        self.assertEqual(articolo.copertina.name, self.percorso_vero)

    def test_senza_applica_non_scrive(self):
        rotto = "properties/1999/01/" + pathlib.PurePosixPath(self.percorso_vero).name
        articolo = _articolo(titolo="Solo elenco")
        Article.objects.filter(pk=articolo.pk).update(copertina=rotto)

        self._ripara(applica=False)

        articolo.refresh_from_db()
        self.assertEqual(articolo.copertina.name, rotto)

    def test_non_tocca_le_copertine_il_cui_file_esiste(self):
        """Le foto editoriali caricate a mano devono sopravvivere al comando."""
        articolo = _articolo(titolo="Copertina buona")
        Article.objects.filter(pk=articolo.pk).update(copertina=self.percorso_vero)

        self._ripara()

        articolo.refresh_from_db()
        self.assertEqual(articolo.copertina.name, self.percorso_vero)

    def test_segnala_le_copertine_senza_riscontro(self):
        articolo = _articolo(titolo="Introvabile")
        Article.objects.filter(pk=articolo.pk).update(copertina="giornale/2026/09/mai-vista.jpg")

        uscita = self._ripara()

        self.assertIn("senza riscontro", uscita)
        articolo.refresh_from_db()
        self.assertEqual(articolo.copertina.name, "giornale/2026/09/mai-vista.jpg")

    @classmethod
    def tearDownClass(cls):
        # La cartella temporanea e' della classe: si toglie di mezzo qui.
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


class VecchioIndirizzoTest(TestCase):
    """/giornale/ era l'indirizzo del blog: deve portare a /blog/ con un 301."""

    def test_elenco(self):
        r = self.client.get("/giornale/")
        self.assertRedirects(r, "/blog/", status_code=301, fetch_redirect_response=False)

    def test_articolo_e_filtri(self):
        r = self.client.get("/giornale/un-articolo/?categoria=x")
        self.assertRedirects(r, "/blog/un-articolo/?categoria=x", status_code=301,
                             fetch_redirect_response=False)
