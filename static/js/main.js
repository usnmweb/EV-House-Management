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

  /* ------------------------------------------------------------------
     Tendina delle localita' nella barra di navigazione
     Il CSS la apre gia' da solo al passaggio del mouse e quando il fuoco
     entra nella voce: quello che manca, e che il CSS non puo' fare, e' il
     comando esplicito per chi tocca lo schermo e lo stato annunciato alle
     tecnologie assistive.
     ------------------------------------------------------------------ */
  var voceTendina = document.getElementById("voce-immobili");
  var tastoTendina = document.getElementById("tendina-toggle");

  if (voceTendina && tastoTendina) {
    function apriTendina(apri) {
      voceTendina.classList.toggle("e-aperta", apri);
      // `e-chiusa` serve a battere `:focus-within`, che dopo un Esc terrebbe
      // aperta la tendina perche' il fuoco resta sul pulsante.
      voceTendina.classList.toggle("e-chiusa", !apri);
      tastoTendina.setAttribute("aria-expanded", apri ? "true" : "false");
      tastoTendina.setAttribute(
        "aria-label", apri ? "Nascondi le località" : "Mostra le località"
      );
    }

    tastoTendina.addEventListener("click", function (e) {
      e.stopPropagation();
      apriTendina(!voceTendina.classList.contains("e-aperta"));
    });

    // Un click fuori chiude. Dentro no: si sta scegliendo una localita'.
    document.addEventListener("click", function (e) {
      if (!voceTendina.contains(e.target)) apriTendina(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape" || !voceTendina.classList.contains("e-aperta")) return;
      apriTendina(false);
      tastoTendina.focus();   // il fuoco torna dove si era, non in cima alla pagina
    });

    // Uscendo dalla voce col tabulatore la tendina si chiude da se'.
    // Solo se il fuoco va da qualche altra parte: quando `relatedTarget` e'
    // nullo il fuoco non e' andato su nulla — succede cliccando il bordo del
    // pannello — e chiudere li' sarebbe una porta in faccia. A quel caso ci
    // pensa gia' il click fuori.
    voceTendina.addEventListener("focusout", function (e) {
      if (e.relatedTarget && !voceTendina.contains(e.relatedTarget)) {
        apriTendina(false);
        // Uscendo del tutto dalla voce la chiusura esplicita non serve piu':
        // altrimenti al prossimo passaggio del mouse resterebbe muta.
        voceTendina.classList.remove("e-chiusa");
      }
    });

    voceTendina.addEventListener("mouseleave", function () {
      voceTendina.classList.remove("e-chiusa");
    });
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
     Sezioni che si bloccano

     Due, sulla home. In «Come funziona» la sezione si ferma a schermo pieno e
     le tessere si scoprono una alla volta; nella vetrina degli immobili si
     ferma e la fila di schede scorre di lato. Cambia cosa succede dentro, non
     la meccanica: sono la stessa cosa e stanno nella stessa funzione.

     Quella meccanica non intercetta niente. La pagina scorre come su qualunque
     altra sezione — rotella, trackpad, frecce, barra laterale, ricerca nel
     testo — ed e' la sezione a restare incollata mentre le si scorre
     attraverso, con `position: sticky`. Quanto si e' scorso dentro quel tratto
     e' `--avanzamento`, da 0 a 1, ed e' l'unica cosa che questo codice calcola.
     ------------------------------------------------------------------ */

  /* Le timeline di scorrimento del CSS non ci sono ovunque. Dove ci sono fa
     tutto il CSS sul compositor; dove mancano l'avanzamento lo calcoliamo qui
     e lo passiamo come `--avanzamento`. Il layout e' lo stesso nei due casi,
     cambia solo chi muove le cose. */
  var timelineCSS =
    window.CSS && CSS.supports && CSS.supports("animation-timeline", "view()");
  var fermo = window.matchMedia("(prefers-reduced-motion: reduce)");

  function agganciaBlocco(sezione, quando) {
    var pin = sezione.querySelector("[data-blocco-pin]");
    if (!pin) return null;

    var sta = window.matchMedia(quando);
    var inCoda = false;

    /* Le due misure si prendono dal layout vero, non da `innerHeight` e
       `--header-h`: su iOS `innerHeight` cambia mentre la barra dell'indirizzo
       si ritira, mentre il blocco e' alto in `svh` e sta fermo. Leggendo
       l'elemento non c'e' modo che i due numeri divergano. */
    function tratti() {
      var q = sezione.getBoundingClientRect();
      var attacco = parseFloat(getComputedStyle(pin).top) || 0;
      var tratto = q.height - pin.getBoundingClientRect().height;
      return tratto > 0 ? { q: q, attacco: attacco, tratto: tratto } : null;
    }

    function aggiornaAvanzamento() {
      inCoda = false;
      var t = tratti();
      if (!t) return;
      // Quando `q.top` vale `attacco` il blocco si incolla: li' siamo a 0.
      var p = (t.attacco - t.q.top) / t.tratto;
      sezione.style.setProperty("--avanzamento", Math.min(1, Math.max(0, p)));
    }

    function alloScroll() {
      if (inCoda) return;
      inCoda = true;
      requestAnimationFrame(aggiornaAvanzamento);
    }

    var ascolta = false;
    function sincronizza() {
      var deve = sta.matches && !fermo.matches;
      sezione.classList.toggle("e-bloccata", deve);

      // L'ascoltatore serve solo dove il CSS non sa fare da solo.
      var serve = deve && !timelineCSS;
      if (serve && !ascolta) {
        window.addEventListener("scroll", alloScroll, { passive: true });
        ascolta = true;
        aggiornaAvanzamento();
      } else if (!serve && ascolta) {
        window.removeEventListener("scroll", alloScroll);
        ascolta = false;
        sezione.style.removeProperty("--avanzamento");
      }
    }

    sincronizza();
    window.addEventListener("resize", sincronizza, { passive: true });
    // Su Safari vecchio `addEventListener` sulle media query non c'e'.
    [sta, fermo].forEach(function (mq) {
      if (mq.addEventListener) mq.addEventListener("change", sincronizza);
      else if (mq.addListener) mq.addListener(sincronizza);
    });

    return {
      sezione: sezione,
      pin: pin,
      bloccata: function () { return getComputedStyle(pin).position === "sticky"; },
      // Dove va portata la pagina perche' il blocco sia a fine corsa.
      fineCorsa: function () {
        var t = tratti();
        return t ? window.scrollY + t.q.top - t.attacco + t.tratto : null;
      },
    };
  }


  /* --- «Come funziona» ---
     Si blocca solo dove le quattro tessere ci stanno davvero. Bloccata, la
     sezione ha un'altezza fissa e quello che sfora viene tagliato: a essere
     tagliata sarebbe l'ultima tessera, cioe' proprio quella che il blocco
     esiste per scoprire. Le due soglie sono misurate, non scelte a occhio —
     sotto i 1200px la griglia si stringe e le tessere crescono in altezza,
     sotto i 720px di finestra il blocco non ha piu' i pixel per contenerle.
     Fuori da li' resta la griglia normale, dove la cascata la fa gia' lo
     scorrimento e non c'e' niente da tagliare. */
  var passi = document.querySelector(".passi[data-blocco]");
  var bloccoPassi = passi &&
    agganciaBlocco(passi, "(min-width: 1200px) and (min-height: 720px)");

  if (bloccoPassi) {
    /* Una tessera non ancora scoperta e' trasparente ma resta raggiungibile
       col tabulatore: senza questo, il collegamento della quarta prenderebbe
       il fuoco mentre e' invisibile. Ci si porta a fine corsa, dove sono tutte
       in campo — la pagina si muove, il fuoco resta dov'e'. */
    document.addEventListener("focusin", function (e) {
      if (!bloccoPassi.bloccata()) return;
      if (!e.target.closest || !e.target.closest(".passi-griglia > li")) return;
      if (!passi.contains(e.target)) return;

      var avanzamento = parseFloat(
        getComputedStyle(passi).getPropertyValue("--avanzamento")
      );
      // Col CSS che guida la timeline `--avanzamento` non e' scritto: si
      // guarda allora se la tessera e' davvero visibile.
      var opaca = parseFloat(getComputedStyle(e.target.closest("li")).opacity);
      if (opaca > 0.95 || avanzamento >= 0.99) return;

      var meta = bloccoPassi.fineCorsa();
      if (meta !== null) window.scrollTo({ top: meta, behavior: "smooth" });
    });
  }


  /* --- Vetrina degli immobili ---
     Vale anche sul telefono: il pollice scorre in verticale come sempre e la
     fila avanza. Il vincolo non e' la larghezza ma l'altezza: sotto i 700px il
     blocco non ha piu' da spartire abbastanza fra intestazione, scheda e
     barra, e alla fotografia resta una striscia da ottanta pixel. Li' torna la
     fila trascinabile, che un'altezza da rispettare non ce l'ha e infatti a
     quelle misure la fotografia la fa piu' grande, non piu' piccola. */
  var pista = document.getElementById("showcase-track");
  var vetrina = pista && pista.closest(".showcase");
  var bloccoVetrina = vetrina && agganciaBlocco(vetrina, "(min-height: 700px)");

  if (bloccoVetrina) {
    /* Quando la sezione e' incollata la fila non e' un contenitore di
       scorrimento: il browser non sa come portare in vista una scheda fuori
       campo. Ci pensiamo noi scorrendo la pagina, che e' quello che muove la
       fila. */
    document.addEventListener("focusin", function (e) {
      // Nella variante trascinabile il contenitore scorre da solo: non tocchiamo.
      if (!bloccoVetrina.bloccata()) return;

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
     Contatore degli ospiti accolti

     Il numero mostrato e' `totale + ritmo x (adesso - data del totale)`, cioe'
     l'estrapolazione onesta del dato fornito. Non e' un effetto: il valore
     giusto e' gia' nel markup, e se questo codice non gira resta li'.

     Il ritmo e' quello vero — ospiti degli ultimi dodici mesi diviso i secondi
     di un anno — e a quel ritmo il numero scatta di rado: con dodicimila
     ospiti l'anno, una volta ogni quarantatre minuti. Il timer si programma
     sull'istante in cui il valore cambiera' davvero, invece di ridipingere lo
     stesso numero sessanta volte al secondo.
     ------------------------------------------------------------------ */
  var contatore = document.querySelector(".contatore");

  if (contatore) {
    var totale = parseFloat(contatore.getAttribute("data-totale"));
    var alSecondo = parseFloat(contatore.getAttribute("data-al-secondo"));
    var daQuando = parseFloat(contatore.getAttribute("data-da-quando"));
    var formato = new Intl.NumberFormat("it-IT");

    function valoreOra() {
      var trascorsi = (Date.now() - daQuando) / 1000;
      return Math.floor(totale + alSecondo * Math.max(0, trascorsi));
    }

    function scrivi(n) { contatore.textContent = formato.format(n); }

    // Il numero corretto va scritto subito: la salita da zero e' un ornamento
    // e arriva dopo, solo se e' il caso di farla.
    scrivi(valoreOra());

    function programmaProssimo() {
      if (!alSecondo) return;
      var atteso = valoreOra() + 1;
      var quando = daQuando + ((atteso - totale) / alSecondo) * 1000 - Date.now();
      // Oltre le ventiquattro ore non vale la pena tenere un timer acceso.
      if (quando > 0 && quando < 24 * 3600 * 1000) {
        setTimeout(function () { scrivi(valoreOra()); programmaProssimo(); }, quando + 50);
      }
    }
    programmaProssimo();

    /* La salita da zero parte quando il numero entra in campo, e solo se le
       animazioni sono ammesse: con "riduci movimento" il numero sta fermo sul
       valore giusto. */
    var animabile =
      document.documentElement.classList.contains("js-anim") &&
      "IntersectionObserver" in window;

    if (animabile) {
      var salito = false;
      var osservaContatore = new IntersectionObserver(function (voci) {
        voci.forEach(function (v) {
          if (!v.isIntersecting || salito) return;
          salito = true;
          osservaContatore.disconnect();

          var arrivo = valoreOra();
          var durata = 1600;
          var inizio = null;
          function passo(ora) {
            if (inizio === null) inizio = ora;
            var t = Math.min(1, (ora - inizio) / durata);
            // Rallenta verso la fine: il numero si posa invece di fermarsi.
            scrivi(Math.floor(arrivo * (1 - Math.pow(1 - t, 3))));
            if (t < 1) requestAnimationFrame(passo);
            else scrivi(valoreOra());
          }
          requestAnimationFrame(passo);
        });
      }, { threshold: 0.5 });
      osservaContatore.observe(contatore);
    }
  }

  /* ------------------------------------------------------------------
     Zone coperte: elenco e mappa si illuminano insieme
     ------------------------------------------------------------------ */
  var zoneElenco = document.querySelector(".zone-elenco");
  var zoneMappa = document.querySelector(".zone-mappa");

  if (zoneElenco && zoneMappa) {
    function accendi(slug, acceso) {
      var punto = zoneMappa.querySelector('[data-luogo="' + slug + '"]');
      if (punto) punto.classList.toggle("e-accesa", acceso);
    }
    ["mouseover", "focusin"].forEach(function (evento) {
      zoneElenco.addEventListener(evento, function (e) {
        var a = e.target.closest ? e.target.closest("[data-luogo]") : null;
        if (a) accendi(a.getAttribute("data-luogo"), true);
      });
    });
    ["mouseout", "focusout"].forEach(function (evento) {
      zoneElenco.addEventListener(evento, function (e) {
        var a = e.target.closest ? e.target.closest("[data-luogo]") : null;
        if (a) accendi(a.getAttribute("data-luogo"), false);
      });
    });
  }

  /* ------------------------------------------------------------------
     Galleria: filtri per localita' e visore a schermo intero

     Il visore e' un <dialog> aperto con `showModal()`, e questo porta con se'
     gratis quattro cose che in un finto modale andrebbero scritte a mano:
     la trappola del fuoco, la chiusura con Esc, l'inertizzazione del resto
     della pagina e il ritorno del fuoco alla tessera di partenza.

     Senza JavaScript, o su un browser senza <dialog>, ogni tessera resta il
     link alla scheda dell'immobile che e' gia' nel markup: la galleria
     funziona, semplicemente non si sfoglia.
     ------------------------------------------------------------------ */
  var mosaico = document.getElementById("mosaico");
  var visore = document.getElementById("visore");

  if (mosaico && visore && typeof visore.showModal === "function") {
    var tessere = Array.prototype.slice.call(mosaico.querySelectorAll(".tessera"));
    var filtri = document.getElementById("filtri-luogo");
    var esito = document.getElementById("filtri-esito");
    var foto = document.getElementById("visore-foto");
    var conta = document.getElementById("visore-conta");
    var titolo = document.getElementById("visore-titolo");
    var luogoVis = document.getElementById("visore-luogo");
    var scheda = document.getElementById("visore-scheda");
    var prec = document.getElementById("visore-prec");
    var succ = document.getElementById("visore-succ");

    var visibili = tessere.slice();
    var indice = 0;

    /* Il ritmo del mosaico. Le regole `:nth-child` in CSS servono da ripiego,
       ma con parte delle tessere nascoste conterebbero anche quelle: il ritmo
       si sfalderebbe. Qui si riassegna sulle sole tessere visibili. */
    var FORME = ["grande", "normale", "normale", "alta", "normale", "larga"];
    function ridisegna() {
      visibili.forEach(function (t, i) {
        t.setAttribute("data-forma", FORME[i % FORME.length]);
      });
    }

    function due(n) { return n < 10 ? "0" + n : String(n); }

    /* ---- filtri ---- */
    function filtra(luogo, scrivi) {
      visibili = tessere.filter(function (t) {
        var dentro = luogo === "tutte" || t.getAttribute("data-luogo") === luogo;
        t.hidden = !dentro;
        return dentro;
      });
      ridisegna();

      if (filtri) {
        filtri.querySelectorAll(".chip").forEach(function (c) {
          var attiva = c.getAttribute("data-luogo") === luogo;
          c.classList.toggle("is-attiva", attiva);
          c.setAttribute("aria-pressed", attiva ? "true" : "false");
        });
      }
      if (esito) {
        esito.textContent = luogo === "tutte"
          ? ""
          : visibili.length + (visibili.length === 1 ? " fotografia" : " fotografie");
      }
      // L'indirizzo tiene conto del filtro, cosi' una vista si puo' mandare a
      // qualcuno. `replaceState` e non un salto all'ancora: non deve scorrere.
      if (scrivi && window.history && history.replaceState) {
        history.replaceState(null, "",
          luogo === "tutte" ? location.pathname : location.pathname + "#luogo=" + luogo);
      }
    }

    if (filtri) {
      filtri.hidden = false;
      filtri.addEventListener("click", function (e) {
        var chip = e.target.closest ? e.target.closest(".chip") : null;
        if (chip) filtra(chip.getAttribute("data-luogo"), true);
      });
    }

    var daIndirizzo = /#luogo=([\w-]+)/.exec(location.hash);
    filtra(daIndirizzo ? daIndirizzo[1] : "tutte", false);

    /* ---- visore ---- */
    function precarica(i) {
      var t = visibili[i];
      if (!t) return;
      var img = new Image();
      img.src = t.querySelector("img").getAttribute("src");
    }

    function mostra(i) {
      if (i < 0 || i >= visibili.length) return;
      indice = i;
      var t = visibili[i];
      foto.setAttribute("src", t.querySelector("img").getAttribute("src"));
      foto.setAttribute("alt", t.getAttribute("data-alt") || "");
      conta.textContent = due(i + 1) + " / " + due(visibili.length);
      titolo.textContent = t.getAttribute("data-titolo") || "";
      luogoVis.textContent = t.getAttribute("data-localita") || "";
      scheda.setAttribute("href", t.getAttribute("data-scheda"));
      prec.disabled = i === 0;
      succ.disabled = i === visibili.length - 1;
      // Le vicine arrivano prima che servano: sfogliare deve essere istantaneo.
      precarica(i + 1);
      precarica(i - 1);
    }

    function apri(i) {
      mostra(i);
      document.documentElement.classList.add("visore-aperto");
      visore.showModal();
    }

    mosaico.addEventListener("click", function (e) {
      // Solo il collegamento sulla fotografia viene intercettato: quello del
      // pulsante «Vedi l'annuncio» deve navigare, ed e' tutto il suo scopo.
      var foto = e.target.closest ? e.target.closest(".tessera-foto") : null;
      if (!foto) return;
      var i = visibili.indexOf(foto.closest(".tessera"));
      if (i === -1) return;
      e.preventDefault();
      apri(i);
    });

    prec.addEventListener("click", function () { mostra(indice - 1); });
    succ.addEventListener("click", function () { mostra(indice + 1); });
    document.getElementById("visore-chiudi")
      .addEventListener("click", function () { visore.close(); });

    visore.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); mostra(indice + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); mostra(indice - 1); }
    });

    // Click sullo sfondo (fuori dalla fotografia): chiude.
    visore.addEventListener("click", function (e) {
      if (e.target === visore) visore.close();
    });

    visore.addEventListener("close", function () {
      document.documentElement.classList.remove("visore-aperto");
      // La sorgente si svuota: una fotografia a piena risoluzione tenuta in
      // memoria dopo la chiusura non serve a niente.
      foto.removeAttribute("src");
    });

    // Scorrimento col dito.
    var partenza = null;
    visore.addEventListener("touchstart", function (e) {
      partenza = e.changedTouches[0].clientX;
    }, { passive: true });
    visore.addEventListener("touchend", function (e) {
      if (partenza === null) return;
      var salto = e.changedTouches[0].clientX - partenza;
      partenza = null;
      if (Math.abs(salto) < 45) return;
      mostra(indice + (salto < 0 ? 1 : -1));
    }, { passive: true });
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

  /* ------------------------------------------------------------------
     Il Giornale: barra di avanzamento della lettura

     Quanto del corpo dell'articolo e' passato sopra il bordo inferiore della
     finestra. Non «quanto si e' scorso della pagina»: la testata, la fascia dei
     numeri correlati e il piede non sono lettura, e contarli farebbe arrivare
     la barra a meta' quando l'articolo e' finito.

     Dove il browser sa animare sulla posizione dello scorrimento se ne occupa
     il CSS (piu' sotto): qui si entra solo come ripiego.
     ------------------------------------------------------------------ */
  var barraLettura = document.getElementById("lettura-barra");
  var corpoArticolo = document.querySelector(".articolo-corpo");

  if (barraLettura && corpoArticolo) {
    /* Qui non si passa dalle timeline di scorrimento del CSS, e non e' una
       dimenticanza. Una timeline nominata si vede solo dai discendenti di chi
       la dichiara: la barra e' fissata in cima alla pagina, fuori dal corpo
       dell'articolo, quindi non potrebbe leggerla. Portarla dentro con
       `timeline-scope` sarebbe un supporto in meno e una riga in piu' per un
       ascoltatore che costa un `requestAnimationFrame` per fotogramma scorso.

       (Provato: agganciando la timeline da JavaScript la barra restava piena
       fin dal primo pixel — l'animazione partiva su quella del documento, con
       durata zero, e `both` la portava subito a fondo corsa.) */
    var inCodaLettura = false;

    function misuraLettura() {
      inCodaLettura = false;
      var q = corpoArticolo.getBoundingClientRect();
      var percorso = q.height - window.innerHeight;
      var letto;
      if (percorso > 0) {
        // Zero quando il corpo tocca il bordo alto, uno quando la sua fine
        // arriva al bordo basso.
        letto = -q.top / percorso;
      } else {
        // Articolo piu' corto della finestra: o e' passato, o non ancora.
        letto = q.bottom <= window.innerHeight ? 1 : 0;
      }
      barraLettura.style.setProperty("--letto", Math.min(1, Math.max(0, letto)));
    }

    function alloScrollLettura() {
      if (inCodaLettura) return;
      inCodaLettura = true;
      requestAnimationFrame(misuraLettura);
    }

    window.addEventListener("scroll", alloScrollLettura, { passive: true });
    window.addEventListener("resize", alloScrollLettura, { passive: true });
    misuraLettura();
  }

  /* ------------------------------------------------------------------
     Il Giornale: l'indice segue la lettura

     Si accende la voce della sezione in cui ci si trova. Non si usa
     IntersectionObserver ma la posizione dei titoli, e per una ragione: un
     observer dice «questo titolo e' in campo», mentre la domanda qui e'
     «in quale sezione sono», che ha una risposta anche quando nessun titolo
     e' visibile — cioe' per quasi tutta la lettura.

     Il confine e' appena sotto l'intestazione appiccicata, non a meta'
     schermo: con sezioni corte — due paragrafi — una linea piu' bassa ne
     lascia due sopra di se' contemporaneamente, e si accende la seconda
     mentre si sta ancora leggendo la prima. Misurato: a un terzo di schermo
     l'indice era avanti di una voce per tutta la lettura.
     ------------------------------------------------------------------ */
  var indice = document.querySelector(".articolo-indice");

  if (indice) {
    var voci = Array.prototype.slice.call(indice.querySelectorAll("a[href^='#']"));
    var titoli = voci
      .map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); })
      .filter(Boolean);

    if (titoli.length === voci.length && titoli.length) {
      var inCodaIndice = false;
      var correnteIndice = -1;

      function aggiornaIndice() {
        inCodaIndice = false;
        var intestazione = document.querySelector(".site-header");
        var confine = (intestazione ? intestazione.getBoundingClientRect().height : 0) + 24;
        var quale = 0;
        for (var i = 0; i < titoli.length; i++) {
          if (titoli[i].getBoundingClientRect().top <= confine) quale = i;
        }
        // Prima del primo titolo nessuna voce e' accesa: accenderne una
        // direbbe una cosa falsa, cioe' che si e' gia' in quella sezione.
        if (titoli[0].getBoundingClientRect().top > confine) quale = -1;

        if (quale === correnteIndice) return;
        correnteIndice = quale;
        voci.forEach(function (a, i) {
          var acceso = i === quale;
          a.classList.toggle("e-corrente", acceso);
          if (acceso) a.setAttribute("aria-current", "true");
          else a.removeAttribute("aria-current");
        });
      }

      window.addEventListener("scroll", function () {
        if (inCodaIndice) return;
        inCodaIndice = true;
        requestAnimationFrame(aggiornaIndice);
      }, { passive: true });
      window.addEventListener("resize", function () {
        correnteIndice = -1;
        aggiornaIndice();
      }, { passive: true });
      aggiornaIndice();
    }
  }

  /* ------------------------------------------------------------------
     Il Giornale: copia il collegamento

     Il pulsante e' nel markup con `hidden` e lo si scopre qui: senza
     JavaScript non farebbe nulla, e un comando che non fa nulla e' peggio di
     un comando in meno. Vale per quello nella firma e per le ancore dei
     titoli, che copiano il link alla singola sezione.
     ------------------------------------------------------------------ */
  var puoCopiare = !!(navigator.clipboard && navigator.clipboard.writeText);

  function confermaCopia(bottone, etichetta) {
    var testo = bottone.querySelector(".copia-testo");
    var prima = testo ? testo.textContent : null;
    bottone.classList.add("e-fatto");
    if (testo) testo.textContent = etichetta;
    clearTimeout(bottone._orologio);
    bottone._orologio = setTimeout(function () {
      bottone.classList.remove("e-fatto");
      if (testo) testo.textContent = prima;
    }, 2000);
  }

  var bottoneCopia = document.querySelector(".copia-link");
  if (bottoneCopia && puoCopiare) {
    bottoneCopia.hidden = false;
    bottoneCopia.addEventListener("click", function () {
      navigator.clipboard.writeText(bottoneCopia.getAttribute("data-copia")).then(
        function () { confermaCopia(bottoneCopia, "Copiato"); },
        function () { confermaCopia(bottoneCopia, "Non riuscito"); }
      );
    });
  }

  /* L'ancora resta un collegamento vero — funziona senza JavaScript e si puo'
     aprire in una scheda nuova. Qui si aggiunge solo la copia negli appunti,
     senza togliere il salto alla sezione. */
  if (puoCopiare) {
    document.querySelectorAll(".articolo-corpo .ancora").forEach(function (a) {
      a.addEventListener("click", function () {
        navigator.clipboard.writeText(a.href).then(function () {
          a.classList.add("e-copiata");
          clearTimeout(a._orologio);
          a._orologio = setTimeout(function () { a.classList.remove("e-copiata"); }, 1400);
        }, function () { /* appunti negati: resta il salto alla sezione */ });
      });
    });
  }

  /* ------------------------------------------------------------------
     Il Giornale: pulsante «torna su»

     Compare dopo cinquecento pixel. E' nel markup con `hidden`, quindi finche'
     non serve non e' nemmeno nell'ordine del tabulatore: un bersaglio
     invisibile ma raggiungibile e' peggio di nessun bersaglio.
     ------------------------------------------------------------------ */
  var tornaSu = document.getElementById("torna-su");

  if (tornaSu) {
    var SOGLIA_TORNA = 500;
    var inCodaTorna = false;
    function sincronizzaTornaSu() {
      inCodaTorna = false;
      tornaSu.hidden = window.scrollY < SOGLIA_TORNA;
    }
    window.addEventListener("scroll", function () {
      if (inCodaTorna) return;
      inCodaTorna = true;
      requestAnimationFrame(sincronizzaTornaSu);
    }, { passive: true });
    sincronizzaTornaSu();

    tornaSu.addEventListener("click", function (e) {
      e.preventDefault();
      var dolce = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: dolce ? "smooth" : "auto" });
      /* Riportare il fuoco in cima e' la meta' che si dimentica: senza, chi
         naviga da tastiera preme «torna su», la pagina sale e il fuoco resta
         in fondo. `main` non e' focalizzabile di suo, quindi glielo si concede
         per il tempo di questo salto. */
      var main = document.getElementById("main");
      if (main) {
        main.setAttribute("tabindex", "-1");
        main.focus({ preventScroll: true });
        main.addEventListener("blur", function ripulisci() {
          main.removeAttribute("tabindex");
          main.removeEventListener("blur", ripulisci);
        });
      }
    });
  }

  /* ------------------------------------------------------------------
     Il Giornale: i numeri della stagione salgono da zero

     Il valore giusto e' gia' nel markup — se questo codice non gira resta li'.
     La salita parte quando la fascia entra in campo, una volta sola, e solo
     dove le animazioni sono ammesse. Le voci senza `data-conta` non si
     animano: «424 / 455» non e' un numero che possa salire.
     ------------------------------------------------------------------ */
  var numeriStagione = document.querySelectorAll(".articolo-numeri .num[data-conta]");

  if (numeriStagione.length &&
      document.documentElement.classList.contains("js-anim") &&
      "IntersectionObserver" in window) {

    var osservaNumeri = new IntersectionObserver(function (voci) {
      voci.forEach(function (v) {
        if (!v.isIntersecting) return;
        var el = v.target;
        osservaNumeri.unobserve(el);

        var arrivo = parseFloat(el.getAttribute("data-conta"));
        var finale = el.getAttribute("data-testo") || el.textContent;
        if (!isFinite(arrivo)) return;

        // I decimali del valore d'arrivo, per non far ballare la larghezza
        // mentre sale: «9,3» e «93,19» occupano spazi diversi.
        var pezzi = String(arrivo).split(".");
        var decimali = pezzi.length > 1 ? pezzi[1].length : 0;
        var formato = new Intl.NumberFormat("it-IT", {
          minimumFractionDigits: decimali,
          maximumFractionDigits: decimali,
        });
        // Il contorno del numero finale — «%», «+», « / » — si conserva
        // sostituendo solo la parte numerica.
        var grezzo = String(arrivo).replace(".", ",");
        var prima = finale.indexOf(grezzo);
        var testa = prima >= 0 ? finale.slice(0, prima) : "";
        var coda = prima >= 0 ? finale.slice(prima + grezzo.length) : "";

        var durata = 1400;
        var inizio = null;
        function passoNumero(ora) {
          if (inizio === null) inizio = ora;
          var t = Math.min(1, (ora - inizio) / durata);
          // Rallenta verso la fine: il numero si posa invece di fermarsi.
          var v = arrivo * (1 - Math.pow(1 - t, 3));
          el.textContent = t < 1 ? testa + formato.format(v) + coda : finale;
          if (t < 1) requestAnimationFrame(passoNumero);
        }
        requestAnimationFrame(passoNumero);
      });
    }, { threshold: 0.6 });

    numeriStagione.forEach(function (n) { osservaNumeri.observe(n); });
  }

})();
