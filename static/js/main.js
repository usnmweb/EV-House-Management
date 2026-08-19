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
