/* EV House Management - interazioni minime */
(function () {
  "use strict";

  /* ------------------------------------------------------------------
     Tema chiaro / scuro
     Tre stati: nessuna scelta (segue il sistema), "light", "dark".
     La scelta esplicita viene salvata in localStorage.
     ------------------------------------------------------------------ */
  var STORAGE_KEY = "ev-theme";
  var THEME_COLORS = { light: "#faf8f4", dark: "#0a0a0a" };

  var root = document.documentElement;
  var themeToggle = document.getElementById("theme-toggle");
  var themeMeta = document.getElementById("meta-theme-color");
  var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  function activeTheme() {
    var explicit = root.getAttribute("data-theme");
    if (explicit === "dark" || explicit === "light") return explicit;
    return darkQuery.matches ? "dark" : "light";
  }

  function syncThemeUI() {
    var theme = activeTheme();
    if (themeMeta) themeMeta.setAttribute("content", THEME_COLORS[theme]);
    if (themeToggle) {
      themeToggle.setAttribute(
        "aria-label",
        theme === "dark" ? "Attiva il tema chiaro" : "Attiva il tema scuro"
      );
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = activeTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) { /* storage non disponibile: la scelta vale per questa pagina */ }
      syncThemeUI();
    });
  }

  // Se l'utente non ha mai scelto, segui i cambi di tema del sistema.
  var onSystemChange = function () {
    if (!root.getAttribute("data-theme")) syncThemeUI();
  };
  if (darkQuery.addEventListener) {
    darkQuery.addEventListener("change", onSystemChange);
  } else if (darkQuery.addListener) {
    darkQuery.addListener(onSystemChange); // Safari < 14
  }

  syncThemeUI();

  /* ------------------------------------------------------------------
     Consenso cookie
     Nessuno strumento di misurazione e' attivo oggi: la scelta viene
     registrata e resa disponibile a `window.evConsenso`, cosi' quando se ne
     aggiungera' uno bastera' agganciarlo qui senza rimettere mano al banner.
     ------------------------------------------------------------------ */
  var CHIAVE = "ev-cookie";
  var banner = document.getElementById("cookie-banner");

  function leggiScelta() {
    try {
      var v = localStorage.getItem(CHIAVE);
      return v ? JSON.parse(v) : null;
    } catch (e) { return null; }
  }

  function salvaScelta(misurazione) {
    var scelta = { misurazione: !!misurazione, versione: 1 };
    try { localStorage.setItem(CHIAVE, JSON.stringify(scelta)); } catch (e) {}
    // Cookie tecnico, cosi' la scelta e' leggibile anche lato server.
    document.cookie = "ev_cookie_consent=" + (misurazione ? "all" : "necessary") +
                      ";path=/;max-age=15552000;SameSite=Lax";
    window.evConsenso = scelta;
    if (banner) banner.hidden = true;
  }

  if (banner) {
    var prefs = document.getElementById("cookie-prefs");
    var check = document.getElementById("cookie-analytics");
    var scelta = leggiScelta();

    window.evConsenso = scelta || { misurazione: false, versione: 0 };
    if (!scelta) banner.hidden = false;

    banner.addEventListener("click", function (e) {
      var azione = e.target.closest("[data-cookie]");
      if (!azione) return;
      switch (azione.getAttribute("data-cookie")) {
        case "accept": salvaScelta(true); break;
        case "reject": salvaScelta(false); break;
        case "save":   salvaScelta(check && check.checked); break;
        case "prefs":
          if (prefs) {
            prefs.hidden = !prefs.hidden;
            if (check) check.checked = !!(leggiScelta() || {}).misurazione;
          }
          break;
      }
    });

    // La Cookie Policy puo' riaprire il pannello per cambiare idea.
    document.addEventListener("click", function (e) {
      var riapri = e.target.closest("[data-cookie-riapri]");
      if (!riapri) return;
      e.preventDefault();
      banner.hidden = false;
      if (prefs) prefs.hidden = false;
      if (check) check.checked = !!(leggiScelta() || {}).misurazione;
      banner.scrollIntoView({ block: "center" });
    });
  }

  /* ------------------------------------------------------------------
     Animazioni
     La classe .js-anim e' gia' stata messa (o no) dallo script inline in
     <head>: qui ci limitiamo a far scattare le sequenze.
     ------------------------------------------------------------------ */
  var animate = root.classList.contains("js-anim");

  if (animate) {
    // Ingresso: due frame di attesa perche' lo stato iniziale sia stato
    // dipinto, altrimenti il browser salta la transizione.
    function avviaHome() {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { root.classList.add("is-loaded"); });
      });
    }

    /* ---------------- Sipario d'ingresso ----------------
       Il movimento e' gia' scritto in CSS. Qui restano due cose: far partire
       la home mentre il nero si dissolve (i due tempi si sovrappongono, cosi'
       non c'e' uno stacco) e togliere il blocco dello scorrimento alla fine.

       Le durate si leggono dai token CSS: sono dichiarate una volta sola in
       style.css e non possono andare fuori sincrono con quelle qui. */
    var sipario = document.getElementById("intro");
    var conSipario = sipario && root.classList.contains("ev-intro");

    if (!conSipario) {
      avviaHome();
    } else {
      var stili = getComputedStyle(root);

      function durata(nome, ripiego) {
        var v = stili.getPropertyValue(nome).trim();
        var n = parseFloat(v);
        if (!n) return ripiego;
        return /ms$/.test(v) ? n : n * 1000;   // i token sono in ms, ma non si sa mai
      }

      var attesa = durata("--intro-attesa", 1700);
      var uscita = durata("--intro-uscita", 620);

      var chiuso = false;
      function chiudiSipario() {
        if (chiuso) return;
        chiuso = true;
        root.classList.remove("ev-intro");   // sblocca lo scorrimento
        avviaHome();                          // se non era ancora partita
      }

      // Chi ha fretta lo salta: un click, un tasto, una rotella, un tocco.
      var saltato = false;
      function salta() {
        if (chiuso || saltato) return;
        saltato = true;
        sipario.style.animation = "ev-intro-esce 260ms ease both";
        avviaHome();
        setTimeout(chiudiSipario, 280);
      }
      ["click", "keydown", "wheel", "touchstart"].forEach(function (evento) {
        document.addEventListener(evento, salta, { once: true, passive: true });
      });

      setTimeout(avviaHome, attesa);
      // Rete di sicurezza: se `animationend` non arriva (scheda in secondo
      // piano, animazione interrotta) il sipario se ne va lo stesso.
      setTimeout(chiudiSipario, attesa + uscita + 150);
      sipario.addEventListener("animationend", function (e) {
        if (e.target === sipario) chiudiSipario();
      });
    }

    /* --- Entrata a scossa ---
       Si osservano le singole schede, e il ritardo lo detta la posizione
       dentro il *lotto* che entra in campo nello stesso momento.

       E' quello che fa funzionare la sequenza sia in riga che in colonna:
       su schermo largo le tre schede varcano la soglia nello stesso
       fotogramma, arrivano in un'unica chiamata e prendono ritardi 0, 200,
       400ms — una alla volta. Sul telefono la griglia e' a una colonna, si
       incontrano una per volta scorrendo, ogni chiamata ne porta una sola e il
       ritardo e' sempre zero: la sequenza la fa gia' lo scorrimento, un attesa
       in piu' sarebbe solo una scheda che tarda a comparire.

       Osservare il gruppo invece delle schede sarebbe stato piu' corto ma
       sbagliato in colonna: la seconda e la terza si sarebbero animate fuori
       campo, e arrivandoci si sarebbero trovate gia' ferme.

       Vale sempre, anche dove il browser ha le timeline di scorrimento: qui
       serve il tempo. Un'oscillazione legata alla posizione si fermerebbe a
       meta' fermando il dito, lasciando una scheda storta. */
    var schede = document.querySelectorAll("[data-scossa] > *");
    if (schede.length && "IntersectionObserver" in window) {
      var PASSO_SCOSSA = 200;   // ms fra una scheda e la successiva
      var scossaViva = false;

      var osservaScossa = new IntersectionObserver(
        function (voci) {
          scossaViva = true;
          var entranti = voci.filter(function (v) { return v.isIntersecting; });
          entranti.forEach(function (v, i) {
            v.target.style.setProperty("--ritardo-scossa", i * PASSO_SCOSSA + "ms");
            v.target.classList.add("e-in-scena");
            osservaScossa.unobserve(v.target);   // una volta sola
          });
        },
        { rootMargin: "0px 0px -10% 0px", threshold: 0.2 }
      );
      schede.forEach(function (c) { osservaScossa.observe(c); });

      // Stessa rete di sicurezza della rivelazione: se l'observer non da'
      // segni di vita si mostra tutto. Meglio senza effetto che vuoto.
      setTimeout(function () {
        if (scossaViva) return;
        schede.forEach(function (c) { c.classList.add("e-in-scena"); });
      }, 2000);
    }

    // Rivelazione allo scroll.
    // Se il browser sa animare sulla timeline dello scroll, il CSS fa tutto da
    // solo (vedi il blocco @supports in style.css) e qui non si crea nulla:
    // niente observer, niente cambi di classe, niente lavoro sul main thread.
    var timelineNativa =
      window.CSS && CSS.supports && CSS.supports("animation-timeline", "view()");

    var targets = timelineNativa ? [] : document.querySelectorAll("[data-reveal]");
    if (targets.length) {
      var observerAlive = false;

      var observer = new IntersectionObserver(
        function (entries) {
          // Un observer funzionante emette sempre una prima callback per ogni
          // elemento osservato, anche quando non interseca: ci basta come
          // prova di funzionamento.
          observerAlive = true;
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);   // si anima una volta sola
          });
        },
        { rootMargin: "0px 0px -10% 0px", threshold: 0.05 }
      );
      targets.forEach(function (el) { observer.observe(el); });

      // Rete di sicurezza: se l'observer non da' segni di vita, mostra tutto.
      // Meglio perdere l'animazione che lasciare la pagina vuota.
      setTimeout(function () {
        if (observerAlive) return;
        targets.forEach(function (el) { el.classList.add("is-visible"); });
      }, 2000);
    }
  }

  /* ------------------------------------------------------------------
     Video di sfondo dell'hero
     Il markup non porta `src`: e' qui che si decide se vale la pena
     scaricarlo. Se la risposta e' no — e anche se questo file non gira
     affatto — l'hero resta sulla fotografia, che e' un fotogramma dello
     stesso video.
     ------------------------------------------------------------------ */
  var video = document.getElementById("hero-video");
  var comandoVideo = document.getElementById("hero-video-toggle");

  if (video) {
    var rete = navigator.connection || {};
    var saltaVideo =
      rete.saveData === true ||                             // risparmio dati
      /(^|-)2g$/.test(rete.effectiveType || "") ||           // rete lenta
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!saltaVideo) {
      var pausaUtente = false;

      function riprendiVideo() {
        if (pausaUtente || !video.paused) return;
        var p = video.play();
        if (p && p.catch) p.catch(function () {});
      }

      function attaccaVideo() {
        // La sorgente si sceglie una volta sola, sulla larghezza d'apertura:
        // cambiarla dopo farebbe ricominciare lo scaricamento da zero.
        var piccolo = window.innerWidth <= 760;
        video.src = video.getAttribute(piccolo ? "data-src-piccolo" : "data-src-grande");
        video.muted = true;          // senza questo l'avvio automatico e' vietato
        video.preload = "auto";

        video.addEventListener("playing", function () {
          video.classList.add("e-pronto");
          if (comandoVideo) comandoVideo.hidden = false;
        }, { once: true });

        var avvio = video.play();
        // Avvio automatico negato o formato rifiutato: si resta sulla
        // fotografia. Non e' un errore da segnalare in console.
        if (avvio && avvio.catch) avvio.catch(function () {});
      }

      // Si parte a pagina caricata: il video non deve contendere la banda alla
      // fotografia dell'hero, che e' l'elemento misurato come LCP.
      if (document.readyState === "complete") attaccaVideo();
      else window.addEventListener("load", attaccaVideo, { once: true });

      // Fuori dallo schermo o in una scheda in secondo piano non si decodifica
      // nulla: e' batteria e ventola risparmiate senza che nessuno lo noti.
      document.addEventListener("visibilitychange", function () {
        if (document.hidden) video.pause();
        else riprendiVideo();
      });

      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (voci) {
          voci.forEach(function (v) {
            if (v.isIntersecting) riprendiVideo();
            else video.pause();
          });
        }, { threshold: 0 }).observe(video);
      }

      if (comandoVideo) {
        comandoVideo.addEventListener("click", function () {
          pausaUtente = !pausaUtente;
          comandoVideo.classList.toggle("in-pausa", pausaUtente);
          comandoVideo.setAttribute(
            "aria-label",
            pausaUtente ? "Riprendi il video di sfondo" : "Metti in pausa il video di sfondo"
          );
          if (pausaUtente) video.pause();
          else { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
        });
      }
    }
  }

  /* ------------------------------------------------------------------
     Menu mobile + header sopra l'hero
     Sulle pagine con hero l'header e' trasparente finche' non si scorre
     (o finche' il menu mobile non viene aperto).
     ------------------------------------------------------------------ */
  var navToggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("primary-nav");
  var header = document.getElementById("site-header");
  var hasHero = document.body.classList.contains("has-hero");

  function syncHeader() {
    if (!hasHero || !header) return;
    var solid = window.scrollY > 40 || (nav && nav.classList.contains("is-open"));
    header.classList.toggle("is-solid", solid);
  }

  if (hasHero && header) {
    window.addEventListener("scroll", syncHeader, { passive: true });
    syncHeader();
  }

  if (navToggle && nav) {
    navToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      navToggle.setAttribute("aria-label", open ? "Chiudi il menu" : "Apri il menu");
      syncHeader();
    });

    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
        syncHeader();
      }
    });
  }

  /* ------------------------------------------------------------------
     Vetrina bloccata: schede raggiunte col tabulatore
     Quando la sezione e' incollata, la fila non e' un contenitore di
     scorrimento: il browser non sa come portare in vista una scheda fuori
     campo. Ci pensiamo noi scorrendo la pagina, che e' quello che muove la
     fila. Il rapporto e' 1 a 1 — l'altezza della sezione e' calcolata apposta
     in style.css — quindi lo spostamento richiesto e' anche i pixel da
     scorrere, senza conversioni.
     ------------------------------------------------------------------ */
  var pista = document.getElementById("showcase-track");
  var vetrina = pista && pista.closest(".showcase");
  var blocco = pista && pista.closest(".showcase-pin");

  if (pista && vetrina && blocco) {
    /* --- quando bloccare ---
       Schermo largo e nessuna richiesta di ridurre le animazioni. Sotto quella
       soglia, o con la preferenza attiva, resta la fila trascinabile: cambiare
       il senso dello scorrimento e' esattamente la sorpresa che quella
       preferenza vuole evitare, e su un telefono il gesto naturale e' gia'
       quello laterale. */
    /* Vale anche sul telefono: il pollice scorre in verticale come sempre e la
       fila avanza. Il vincolo non e' la larghezza ma l'altezza — sotto i 520px
       (telefono coricato) non resterebbe spazio per una scheda leggibile, e li'
       si torna alla fila trascinabile. */
    var alto = window.matchMedia("(min-height: 520px)");
    var fermo = window.matchMedia("(prefers-reduced-motion: reduce)");

    /* Le timeline di scorrimento del CSS non ci sono ovunque: oggi mancano a
       Firefox e alle versioni di Safari precedenti alla 26. Dove ci sono fa
       tutto il CSS sul compositor; dove mancano l'avanzamento lo calcoliamo
       qui e lo passiamo come `--avanzamento`. Il layout e' lo stesso nei due
       casi, cambia solo chi muove la fila. */
    var timelineCSS =
      window.CSS && CSS.supports && CSS.supports("animation-timeline", "view()");

    var inCoda = false;
    function aggiornaAvanzamento() {
      inCoda = false;
      /* Le due misure si prendono dal layout vero, non da `innerHeight` e
         `--header-h`: su iOS `innerHeight` cambia mentre la barra
         dell'indirizzo si ritira, mentre il blocco e' alto in `svh` e sta
         fermo. Leggendo l'elemento non c'e' modo che i due numeri divergano. */
      var q = vetrina.getBoundingClientRect();
      var attacco = parseFloat(getComputedStyle(blocco).top) || 0;
      var tratto = q.height - blocco.getBoundingClientRect().height;
      if (tratto <= 0) return;
      // Quando `q.top` vale `attacco` il blocco si incolla: li' siamo a 0.
      var p = (attacco - q.top) / tratto;
      vetrina.style.setProperty("--avanzamento", Math.min(1, Math.max(0, p)));
    }

    function alloScroll() {
      if (inCoda) return;
      inCoda = true;
      requestAnimationFrame(aggiornaAvanzamento);
    }

    var ascolta = false;
    function sincronizza() {
      var deve = alto.matches && !fermo.matches;
      vetrina.classList.toggle("e-bloccata", deve);

      // L'ascoltatore serve solo dove il CSS non sa fare da solo.
      var serve = deve && !timelineCSS;
      if (serve && !ascolta) {
        window.addEventListener("scroll", alloScroll, { passive: true });
        ascolta = true;
        aggiornaAvanzamento();
      } else if (!serve && ascolta) {
        window.removeEventListener("scroll", alloScroll);
        ascolta = false;
        vetrina.style.removeProperty("--avanzamento");
      }
    }

    sincronizza();
    window.addEventListener("resize", sincronizza, { passive: true });
    // Su Safari vecchio `addEventListener` sulle media query non c'e'.
    [alto, fermo].forEach(function (mq) {
      if (mq.addEventListener) mq.addEventListener("change", sincronizza);
      else if (mq.addListener) mq.addListener(sincronizza);
    });

    document.addEventListener("focusin", function (e) {
      // Nella variante trascinabile il contenitore scorre da solo: non tocchiamo.
      if (getComputedStyle(blocco).position !== "sticky") return;

      var tessera = e.target.closest ? e.target.closest(".showcase-item") : null;
      if (!tessera || !pista.contains(tessera)) return;

      var q = tessera.getBoundingClientRect();
      var margine = 32;
      var delta = 0;
      if (q.right > window.innerWidth - margine) {
        delta = q.right - (window.innerWidth - margine);
      } else if (q.left < margine) {
        delta = q.left - margine;
      }
      // `--ritmo` dice quanti pixel percorre la fila per pixel scorso: per
      // spostarla di `delta` bisogna scorrere di `delta / ritmo`.
      var ritmo = parseFloat(getComputedStyle(vetrina).getPropertyValue("--ritmo")) || 1;
      if (delta) window.scrollBy({ top: delta / ritmo, behavior: "smooth" });
    });
  }

  /* ------------------------------------------------------------------
     Galleria immobile: click sulla miniatura aggiorna l'immagine principale
     ------------------------------------------------------------------ */
  var mainImg = document.getElementById("gallery-main-img");
  var thumbs = document.querySelectorAll(".gallery-thumb");

  if (mainImg && thumbs.length) {
    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        var src = thumb.getAttribute("data-full");
        var alt = thumb.getAttribute("data-alt") || "";
        if (!src) return;
        mainImg.setAttribute("src", src);
        mainImg.setAttribute("alt", alt);
        thumbs.forEach(function (t) { t.classList.remove("is-active"); });
        thumb.classList.add("is-active");
      });
    });
  }
})();
