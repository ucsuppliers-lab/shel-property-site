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

  /* ---- search: query string carries the filters between pages (shareable links) ---- */
  var CAT_PAGE = { "for-sale": "for-sale/index.html", "resale": "resale/index.html", "new-build": "new-build/index.html", "land": "land/index.html" };

  /* multi-select drop-downs (Area, Condition, …) */
  function initMsel(root) {
    root.querySelectorAll(".msel").forEach(function (m) {
      var btn = m.querySelector(".msel-btn"), panel = m.querySelector(".msel-panel"), val = m.querySelector(".msel-val"), find = m.querySelector(".msel-find");
      function label() {
        var on = Array.prototype.filter.call(m.querySelectorAll("input[type=checkbox]"), function (c) { return c.checked; }).map(function (c) { return c.value; });
        val.textContent = on.length === 0 ? val.dataset.any : (on.length === 1 ? on[0] : on.length + " selected");
      }
      m._label = label;
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var open = panel.hidden;
        document.querySelectorAll(".msel-panel").forEach(function (p) { p.hidden = true; p.parentNode.querySelector(".msel-btn").setAttribute("aria-expanded", "false"); });
        panel.hidden = !open; btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open && find) find.focus();
      });
      panel.addEventListener("click", function (e) { e.stopPropagation(); });
      panel.addEventListener("change", label);
      if (find) find.addEventListener("input", function () {
        var q = find.value.toLowerCase();
        m.querySelectorAll(".msel-list label").forEach(function (l) { l.hidden = q && l.textContent.toLowerCase().indexOf(q) === -1; });
      });
      label();
    });
    document.addEventListener("click", function () { root.querySelectorAll(".msel-panel").forEach(function (p) { p.hidden = true; }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") root.querySelectorAll(".msel-panel").forEach(function (p) { p.hidden = true; }); });
  }
  function formToQuery(form, skip) {
    var parts = [];
    new FormData(form).forEach(function (v, k) { if (v !== "" && k !== skip && !(k === "district" && v === "paphos")) parts.push(encodeURIComponent(k) + "=" + encodeURIComponent(v)); });
    return parts.join("&");
  }
  function queryToForm(form, qs) {
    var q = new URLSearchParams(qs);
    q.forEach(function (v, k) {
      form.querySelectorAll('[name="' + k + '"]').forEach(function (el) {
        if (el.type === "checkbox") { if (el.value === v) el.checked = true; }
        else if (k !== "cat") el.value = v;
      });
    });
    form.querySelectorAll(".msel").forEach(function (m) { if (m._label) m._label(); });
  }

  /* home search bar */
  var hero = document.getElementById("hero-search");
  if (hero) {
    initMsel(hero);
    hero.addEventListener("submit", function (e) {
      e.preventDefault();
      var cat = hero.querySelector("[name=cat]").value || "for-sale";
      var q = formToQuery(hero, "cat");
      window.location.href = hero.dataset.root + CAT_PAGE[cat] + (q ? "?" + q : "");
    });
  }

  /* results filtering, sorting and pages */
  var filters = document.getElementById("filters");
  if (filters) {
    initMsel(filters);
    var scope = filters.dataset.scope;
    var cards = Array.prototype.slice.call(document.querySelectorAll(".grid .card"));
    var grid = document.querySelector(".grid");
    var per = +(grid.dataset.perPage || 12), page = 1;
    var countEl = document.getElementById("result-count"), empty = document.getElementById("empty"), pager = document.querySelector(".pager");
    queryToForm(filters, location.search);
    var more = filters.querySelector(".fx-more"), adv = document.getElementById("fx-adv");
    if (more && location.hash === "#fx-adv") { document.getElementById("fx-adv").hidden = false; more.setAttribute("aria-expanded", "true"); }
    if (more) {
      more.addEventListener("click", function () { adv.hidden = !adv.hidden; more.setAttribute("aria-expanded", adv.hidden ? "false" : "true"); });
      if (adv.querySelector("select option:checked:not([value=''])") || adv.querySelector("input:checked")) { adv.hidden = false; more.setAttribute("aria-expanded", "true"); }
    }
    function all(name) { return Array.prototype.map.call(filters.querySelectorAll('[name="' + name + '"]:checked'), function (c) { return c.value; }); }
    function num(name) { var v = filters.querySelector('[name="' + name + '"]'); return v && v.value !== "" ? +v.value : null; }
    function between(x, lo, hi) { if (lo === null && hi === null) return true; if (x === "" || x === undefined) return false; x = +x; return (lo === null || x >= lo) && (hi === null || x <= hi); }
    var visible = [];
    function apply(keepPage) {
      var type = filters.querySelector("[name=type]").value, ref = (filters.querySelector("[name=ref]").value || "").trim().toLowerCase();
      var locs = all("loc"), cond = all("cond"), zone = all("zone"), furn = all("furn");
      var subs = all("subh").concat(all("subl")), suba = filters.querySelector("[name=suba]").value;
      var deed = all("deed").length, pool = all("pool").length, sea = all("seaview").length, novat = all("novat").length;
      visible = cards.filter(function (c) {
        var d = c.dataset;
        if (type && d.type !== type) return false;
        if (ref && d.ref.toLowerCase().indexOf(ref) === -1) return false;
        if (locs.length && locs.indexOf(d.loc) === -1) return false;
        if (!between(d.beds, num("bmin"), num("bmax"))) return false;
        if (!between(d.price, num("pmin"), num("pmax"))) return false;
        if (!between(d.year, num("ymin"), num("ymax"))) return false;
        if (!between(d.covered, num("cmin"), num("cmax"))) return false;
        if (!between(d.plot, num("lmin"), num("lmax"))) return false;
        if (cond.length && cond.indexOf(d.cond) === -1) return false;
        if (zone.length && zone.indexOf(d.zone) === -1) return false;
        if (furn.length && furn.indexOf(d.furn) === -1) return false;
        if (subs.length && subs.indexOf(d.sub) === -1) return false;
        if (suba && d.sub !== suba) return false;
        if (deed && d.deed !== "issued") return false;
        if (pool && d.features.indexOf("pool") === -1) return false;
        if (sea && d.features.indexOf("sea view") === -1) return false;
        if (novat && d.vat === "1") return false;
        return true;
      });
      if (!keepPage) page = 1;
      render();
      var q = formToQuery(filters, "cat");
      try { history.replaceState(null, "", location.pathname + (q ? "?" + q : "")); } catch (err) {}
      var refs = {}; visible.forEach(function (c) { refs[c.dataset.ref] = 1; });
      document.querySelectorAll(".lmap-pin [data-ref], .pin[data-ref]").forEach(function (p) { var el = p.closest(".lmap-pin") || p; el.style.display = refs[p.dataset.ref] ? "" : "none"; });
    }
    function render() {
      var pages = Math.max(1, Math.ceil(visible.length / per));
      if (page > pages) page = pages;
      cards.forEach(function (c) { c.hidden = true; });
      visible.slice((page - 1) * per, page * per).forEach(function (c) { c.hidden = false; });
      if (countEl) countEl.textContent = visible.length + " " + (visible.length === 1 ? countEl.dataset.one : countEl.dataset.many);
      if (empty) empty.hidden = visible.length !== 0;
      if (!pager) return;
      pager.hidden = pages < 2; pager.innerHTML = "";
      function add(label, p, cur, aria) {
        var b = document.createElement("button"); b.type = "button"; b.textContent = label; if (aria) b.setAttribute("aria-label", aria);
        if (cur) b.setAttribute("aria-current", "page"); if (p === null) b.disabled = true;
        b.addEventListener("click", function () { page = p; render(); window.scrollTo({ top: document.querySelector(".fx-bar").offsetTop - 90, behavior: "smooth" }); });
        pager.appendChild(b);
      }
      add("‹", page > 1 ? page - 1 : null, false, "Previous page");
      for (var i = 1; i <= pages; i++) {
        if (i === 1 || i === pages || Math.abs(i - page) <= 1) add(String(i), i, i === page);
        else if (Math.abs(i - page) === 2) { var s = document.createElement("span"); s.textContent = "…"; pager.appendChild(s); }
      }
      add("›", page < pages ? page + 1 : null, false, "Next page");
    }
    function sort() {
      var how = document.getElementById("sort").value;
      cards.sort(function (a, b) {
        if (how === "low") return a.dataset.price - b.dataset.price;
        if (how === "high") return b.dataset.price - a.dataset.price;
        if (how === "old") return a.dataset.added.localeCompare(b.dataset.added);
        return b.dataset.added.localeCompare(a.dataset.added);
      });
      cards.forEach(function (c) { grid.appendChild(c); });
      apply(true);
    }
    filters.addEventListener("change", function (e) {
      if (e.target.name === "cat") {
        var q = formToQuery(filters, "cat");
        window.location.href = filters.dataset.root + CAT_PAGE[e.target.value] + (q ? "?" + q : "");
        return;
      }
      apply();
    });
    filters.querySelector("[name=ref]").addEventListener("input", function () { apply(); });
    filters.addEventListener("reset", function () {
      setTimeout(function () { filters.querySelector("[name=cat]").value = scope; filters.querySelectorAll(".msel").forEach(function (m) { m._label(); }); apply(); }, 0);
    });
    filters.addEventListener("submit", function (e) { e.preventDefault(); apply(); });
    var sortEl = document.getElementById("sort");
    if (sortEl) sortEl.addEventListener("change", sort);
    apply();
    var mt = document.getElementById("map-toggle"), mp = document.getElementById("map-panel");
    if (mt && mp) mt.addEventListener("click", function () {
      mp.hidden = !mp.hidden; mt.setAttribute("aria-expanded", mp.hidden ? "false" : "true");
      mt.lastChild.textContent = mp.hidden ? " Show map" : " Hide map";
      var lm = mp.querySelector(".lmap"); if (lm && lm._map) setTimeout(function () { lm._map.invalidateSize(); if (lm._fit) lm._fit(); }, 50);
    });
  }

  /* photo slider on property pages */
  document.querySelectorAll(".slider").forEach(function (sl) {
    var track = sl.querySelector(".slides"), n = sl.querySelector(".sl-n"), thumbs = sl.querySelectorAll(".thumbs button");
    if (!track) return;
    var count = track.children.length;
    function idx() { return Math.round(Math.abs(track.scrollLeft) / track.clientWidth); }
    function go(i) { i = (i + count) % count; track.scrollTo({ left: (document.dir === "rtl" ? -1 : 1) * i * track.clientWidth, behavior: "smooth" }); }
    function mark() { var i = idx(); if (n) n.textContent = i + 1; thumbs.forEach(function (t, k) { t.setAttribute("aria-current", k === i ? "true" : "false"); }); }
    var p = sl.querySelector(".sl-prev"), q = sl.querySelector(".sl-next");
    if (p) p.addEventListener("click", function () { go(idx() - 1); });
    if (q) q.addEventListener("click", function () { go(idx() + 1); });
    thumbs.forEach(function (t) { t.addEventListener("click", function () { go(+t.dataset.i); }); });
    track.addEventListener("scroll", function () { clearTimeout(track._t); track._t = setTimeout(mark, 80); });
    track.addEventListener("keydown", function (e) { if (e.key === "ArrowRight") go(idx() + 1); if (e.key === "ArrowLeft") go(idx() - 1); });
    mark();
  });
  document.querySelectorAll("[data-print]").forEach(function (b) { b.addEventListener("click", function () { window.print(); }); });

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
          var icon = L.divIcon({ className: "lmap-pin", html: '<span data-ref="' + (p.ref || "") + '">' + p.label + "</span>", iconSize: null });
          L.marker([p.lat, p.lng], { icon: icon, title: p.title }).addTo(map)
            .bindPopup('<a href="' + p.href + '"><strong>' + p.title + "</strong></a><br>" + p.area + " · " + p.label);
        }
      });
      el._map = map;
      el._fit = function () { if (pts.length === 1) map.setView(pts[0], d.circle ? 13 : 14); else map.fitBounds(pts, { padding: [40, 40] }); };
      el._fit();
      el.classList.add("is-live");
    });
  };
  document.head.appendChild(js);
})();
