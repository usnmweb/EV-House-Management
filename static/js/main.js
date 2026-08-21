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
