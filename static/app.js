/* Shel Property: small, dependency-free behaviour for the draft site. */
(function () {
  "use strict";
  var KEY = "shel-saved";
  function readSaved() {
    try { var v = JSON.parse(localStorage.getItem(KEY) || "[]"); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function writeSaved(list) { try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) { /* storage blocked: keep in memory only */ } }
  var saved = readSaved();

  function refreshSaved() {
    document.querySelectorAll(".save[data-ref]").forEach(function (b) {
      var on = saved.indexOf(b.dataset.ref) !== -1;
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.setAttribute("aria-label", on ? "Remove from saved homes" : "Save this home");
      var t = b.querySelector(".save-text"); if (t) t.textContent = on ? (b.dataset.on || "Saved") : (b.dataset.off || "Save this home");
    });
    document.querySelectorAll("[data-saved-count]").forEach(function (c) {
      c.textContent = saved.length; c.hidden = saved.length === 0;
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".save[data-ref]");
    if (!b) return;
    e.preventDefault(); e.stopPropagation();
    var r = b.dataset.ref, i = saved.indexOf(r);
    if (i === -1) saved.push(r); else saved.splice(i, 1);
    writeSaved(saved); refreshSaved();
    if (document.getElementById("saved-list")) renderSavedPage();
  });

  /* hero search */
  var hero = document.getElementById("hero-search");
  if (hero) {
    var purpose = "for-sale";
    hero.querySelectorAll(".tab").forEach(function (t) {
      t.addEventListener("click", function () {
        hero.querySelectorAll(".tab").forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
        t.setAttribute("aria-pressed", "true"); purpose = t.dataset.purpose;
        var sc = hero.querySelector("[data-sale-only]"); if (sc) sc.hidden = purpose !== "for-sale";
      });
    });
    hero.addEventListener("submit", function (e) {
      e.preventDefault();
      var pages = JSON.parse(hero.dataset.pages);
      var catSel = hero.querySelector("[name=cat]");
      if (purpose === "for-sale" && catSel && catSel.value) purpose = catSel.value;
      var area = hero.querySelector("[name=area]").value;
      var url = (area && pages[purpose + "/" + area]) ? pages[purpose + "/" + area] : pages[purpose];
      var params = [];
      ["type", "max", "beds"].forEach(function (n) { var v = hero.querySelector("[name=" + n + "]").value; if (v) params.push(n + "=" + encodeURIComponent(v)); });
      try { if (params.length) sessionStorage.setItem("shel-filters", params.join("&")); else sessionStorage.removeItem("shel-filters"); } catch (err) {}
      window.location.href = url;
    });
  }

  /* results filtering */
  var filters = document.getElementById("filters");
  if (filters) {
    var cards = Array.prototype.slice.call(document.querySelectorAll(".grid .card"));
    var grid = document.querySelector(".grid");
    var countEl = document.getElementById("result-count");
    var empty = document.getElementById("empty");
    try {
      var pre = sessionStorage.getItem("shel-filters");
      if (pre) {
        pre.split("&").forEach(function (kv) {
          var p = kv.split("="), el = filters.querySelector("[name=" + p[0] + "]");
          if (el) el.value = decodeURIComponent(p[1]);
        });
        sessionStorage.removeItem("shel-filters");
      }
    } catch (err) {}
    function apply() {
      var f = new FormData(filters);
      var type = f.get("type"), min = +f.get("min") || 0, max = +f.get("max") || Infinity, beds = +(f.get("beds") || 0);
      var deed = f.get("deed"), pool = f.get("pool"), sea = f.get("seaview"), novat = f.get("novat");
      var shown = 0;
      cards.forEach(function (c) {
        var d = c.dataset, ok = true;
        if (type && d.kind !== type) ok = false;
        if (+d.price < min || +d.price > max) ok = false;
        if (beds && (d.beds === "" || +d.beds < beds)) ok = false;
        if (deed && d.deed !== "issued") ok = false;
        if (pool && d.features.indexOf("pool") === -1) ok = false;
        if (sea && d.features.indexOf("sea view") === -1) ok = false;
        if (novat && d.vat === "1") ok = false;
        if (f.get("vat5") && d.vat5 !== "1") ok = false;
        c.hidden = !ok; if (ok) shown++;
        var pin = document.querySelector('.pin[data-ref="' + d.ref + '"]');
        if (pin) { if (ok) pin.removeAttribute("hidden"); else pin.setAttribute("hidden", ""); }
      });
      if (countEl) countEl.textContent = shown + " " + (shown === 1 ? (countEl.dataset.one || "property") : (countEl.dataset.many || "properties"));
      if (empty) empty.hidden = shown !== 0;
    }
    function sort() {
      var how = document.getElementById("sort").value;
      cards.sort(function (a, b) {
        if (how === "low") return a.dataset.price - b.dataset.price;
        if (how === "high") return b.dataset.price - a.dataset.price;
        if (how === "sea") return (+a.dataset.sea || 99) - (+b.dataset.sea || 99);
        return b.dataset.added.localeCompare(a.dataset.added);
      });
      cards.forEach(function (c) { grid.appendChild(c); });
    }
    filters.addEventListener("change", apply);
    filters.addEventListener("input", apply);
    filters.addEventListener("reset", function () { setTimeout(apply, 0); });
    filters.addEventListener("submit", function (e) { e.preventDefault(); apply(); });
    var sortEl = document.getElementById("sort");
    if (sortEl) sortEl.addEventListener("change", sort);
    apply();
    /* card <-> pin */
    cards.forEach(function (c) {
      var pin = document.querySelector('.pin[data-ref="' + c.dataset.ref + '"]');
      if (!pin) return;
      c.addEventListener("mouseenter", function () { pin.classList.add("active"); pin.parentNode.appendChild(pin); });
      c.addEventListener("mouseleave", function () { pin.classList.remove("active"); });
    });
  }

  /* reveal notes */
  document.querySelectorAll("[data-reveal]").forEach(function (b) {
    b.addEventListener("click", function () { var t = document.getElementById(b.dataset.reveal); if (t) { t.hidden = false; } });
  });

  /* draft forms: nothing is sent */
  document.querySelectorAll("form[data-draft]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var note = form.querySelector(".form-note");
      if (note) { note.hidden = false; note.textContent = form.dataset.draft; note.focus(); }
    });
  });

  /* saved page */
  function renderSavedPage() {
    var list = document.getElementById("saved-list"), tpl = document.getElementById("saved-data");
    if (!list || !tpl) return;
    var all = JSON.parse(tpl.textContent);
    var mine = all.filter(function (l) { return saved.indexOf(l.ref) !== -1; });
    list.innerHTML = "";
    document.getElementById("saved-empty").hidden = mine.length !== 0;
    mine.forEach(function (l) {
      var holder = document.createElement("div");
      holder.innerHTML = l.card;
      list.appendChild(holder.firstElementChild);
    });
    refreshSaved();
  }
  renderSavedPage();
  refreshSaved();


  /* Sale drop-down in the main menu */
  document.querySelectorAll(".nav-drop").forEach(function (drop) {
    var btn = drop.querySelector(".nav-drop-btn"), menu = drop.querySelector(".nav-drop-menu");
    var setOpen = function (open) {
      btn.setAttribute("aria-expanded", open ? "true" : "false"); menu.hidden = !open;
      if (open) { var r = btn.getBoundingClientRect(); document.documentElement.style.setProperty("--drop-top", (r.bottom + 6) + "px"); }
    };
    var hover = window.matchMedia && window.matchMedia("(hover: hover) and (min-width: 901px)").matches;
    /* With a mouse the menu is already open from hovering, so a click keeps it open; the keyboard toggles it */
    btn.addEventListener("click", function (e) { e.stopPropagation(); setOpen(hover && e.detail > 0 ? true : menu.hidden); });
    document.addEventListener("click", function (e) { if (!drop.contains(e.target)) setOpen(false); });
    drop.addEventListener("keydown", function (e) { if (e.key === "Escape") { setOpen(false); btn.focus(); } });
    drop.addEventListener("focusout", function (e) { if (!drop.contains(e.relatedTarget)) setOpen(false); });
    if (hover) {
      var t;
      drop.addEventListener("mouseenter", function () { clearTimeout(t); setOpen(true); });
      drop.addEventListener("mouseleave", function () { t = setTimeout(function () { setOpen(false); }, 250); });
    }
  });

  /* ---- v2 ---- */
  var FX = { GBP: { r: 0.87, sym: "£" }, ILS: { r: 3.90, sym: "₪" } };
  function fmt(n) { return Math.round(n).toLocaleString("en-GB"); }

  /* currency switch on results pages: prices stay in euros at heart, others are approximate */
  var cur = document.getElementById("currency");
  if (cur) {
    var prices = Array.prototype.slice.call(document.querySelectorAll(".card .price[data-eur]"));
    prices.forEach(function (p) { p.dataset.orig = p.innerHTML; });
    var setCur = function () {
      var c = cur.value;
      prices.forEach(function (p) {
        if (c === "EUR") { p.innerHTML = p.dataset.orig; return; }
        var f = FX[c], v = (+p.dataset.eur) * f.r;
        p.innerHTML = p.dataset.orig.replace(/€[\d,]+/, "<span title=\"Approximate, at a sample rate\">~" + f.sym + fmt(v) + "</span>");
      });
      try { sessionStorage.setItem("shel-cur", c); } catch (e) {}
    };
    try { var saved_c = sessionStorage.getItem("shel-cur"); if (saved_c) cur.value = saved_c; } catch (e) {}
    cur.addEventListener("change", setCur); setCur();
  }

  /* approximate price under the euro price on a listing */
  document.querySelectorAll(".fx[data-fx]").forEach(function (el) {
    var f = FX[el.dataset.fx]; if (!f) return;
    el.textContent = el.dataset.approx + " " + f.sym + fmt((+el.dataset.eur) * f.r);
    el.title = el.dataset.note;
  });

  /* contact bar: reveal the phone note and bring it into view */
  document.querySelectorAll("[data-scroll]").forEach(function (b) {
    b.addEventListener("click", function () { var t = document.getElementById(b.dataset.reveal); if (t) { t.hidden = false; t.scrollIntoView({ behavior: "smooth", block: "center" }); } });
  });
  document.querySelectorAll("[data-view]").forEach(function (a) {
    a.addEventListener("click", function () { var s = document.querySelector(".enquiry [name=view]"); if (s) s.value = a.dataset.view; });
  });

  /* permit checker */
  var citizen = document.getElementById("citizen");
  if (citizen) {
    citizen.addEventListener("change", function () {
      var v = citizen.value;
      document.getElementById("ans-eu").hidden = v !== "eu";
      document.getElementById("ans-noneu").hidden = !(v === "uk" || v === "il" || v === "other");
      document.getElementById("ans-uk").hidden = v !== "uk";
      document.getElementById("ans-il").hidden = v !== "il";
    });
  }

  /* buying costs calculator */
  var calc = document.getElementById("calc");
  if (calc) {
    var $ = function (id) { return document.getElementById(id); };
    try {
      var q = new URLSearchParams(window.location.search);
      if (q.get("price")) $("c-price").value = q.get("price");
      if (q.get("type") && ["resale", "new", "land", "landvat"].indexOf(q.get("type")) !== -1) $("c-type").value = q.get("type");
    } catch (e) {}
    var eur = function (n) { return "€" + fmt(n); };
    var run = function () {
      var ty = $("c-type").value, p = Math.max(0, +$("c-price").value || 0), isNew = ty === "new" || ty === "landvat";
      var area = +$("c-area").value || 0, main = $("c-main").checked;
      calc.querySelector(".vat-only").hidden = ty !== "new";
      var transfer = 0, vat = 0, note = "";
      if (!isNew) {
        transfer = (0.03 * Math.min(p, 85000) + 0.05 * Math.max(0, Math.min(p, 170000) - 85000) + 0.08 * Math.max(0, p - 170000)) / 2;
      } else {
        var eligible = ty === "new" && main && area > 0 && area <= 190 && p <= 475000;
        if (eligible) {
          var reduced = Math.min(p * Math.min(1, 130 / area), 350000);
          vat = reduced * 0.05 + (p - reduced) * 0.19;
          note = "(5% on " + eur(reduced) + ", 19% on the rest, if the Tax Department agrees)";
        } else {
          vat = p * 0.19;
          note = (ty === "landvat" || !main) ? "(19%)" : (!(area > 0) ? "(19%: add the covered area to check the 5% rate)" : "(19%: over 190 m² or €475,000, so no 5% rate)");
        }
      }
      var stamp = $("c-stamp").checked ? (0.0015 * Math.max(0, Math.min(p, 170000) - 5000) + 0.002 * Math.max(0, p - 170000)) : 0;
      var legal = p * 0.01 * 1.19;
      $("o-price").textContent = eur(p);
      $("o-transfer").textContent = eur(transfer);
      $("o-vat").textContent = eur(vat); $("o-vatnote").textContent = note;
      $("o-stamp").textContent = eur(stamp);
      $("o-legal").textContent = eur(legal);
      $("o-total").textContent = eur(transfer + vat + stamp + legal);
      calc.parentNode.querySelector(".row-resale").hidden = isNew;
      calc.parentNode.querySelector(".row-new").hidden = !isNew;
      calc.parentNode.querySelector(".row-stamp").hidden = !$("c-stamp").checked;
    };
    calc.addEventListener("input", run); calc.addEventListener("change", run); run();
  }

  /* report form: fill in the reference from the link */
  var refIn = document.querySelector("form [name=ref]");
  if (refIn) { try { var r0 = new URLSearchParams(window.location.search).get("ref"); if (r0) refIn.value = r0; } catch (e) {} }
})();

/* Interactive maps: Leaflet + OpenStreetMap, loaded only on pages that have a map */
(function () {
  var maps = document.querySelectorAll(".lmap[data-map]");
  if (!maps.length) return;
  var css = document.createElement("link"); css.rel = "stylesheet";
  css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"; document.head.appendChild(css);
  var js = document.createElement("script"); js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
  js.onload = function () {
    maps.forEach(function (el) {
      var d; try { d = JSON.parse(el.getAttribute("data-map")); } catch (e) { return; }
      var box = document.createElement("div"); box.className = "lmap-canvas"; el.appendChild(box);
      var map = L.map(box, { scrollWheelZoom: false, attributionControl: true });
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
      var pts = [];
      d.pins.forEach(function (p) {
        pts.push([p.lat, p.lng]);
        if (d.circle) {
          L.circle([p.lat, p.lng], { radius: 700, color: "#0E4470", weight: 2, fillColor: "#24ADA9", fillOpacity: .18 }).addTo(map);
        } else {
          var icon = L.divIcon({ className: "lmap-pin", html: "<span>" + p.label + "</span>", iconSize: null });
          L.marker([p.lat, p.lng], { icon: icon, title: p.title }).addTo(map)
            .bindPopup('<a href="' + p.href + '"><strong>' + p.title + "</strong></a><br>" + p.area + " · " + p.label);
        }
      });
      if (pts.length === 1) map.setView(pts[0], d.circle ? 13 : 14);
      else map.fitBounds(pts, { padding: [40, 40] });
      el.classList.add("is-live");
    });
  };
  document.head.appendChild(js);
})();
