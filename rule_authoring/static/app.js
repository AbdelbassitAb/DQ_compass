(function () {
  "use strict";

  // --- theme toggle -----------------------------------------------------
  var root = document.documentElement;
  var themeBtn = document.getElementById("themeToggle");
  function currentTheme() {
    return root.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("dq-theme", next); } catch (e) {}
    });
  }

  // --- mobile sidebar -------------------------------------------------
  var sidebar = document.getElementById("sidebar");
  var scrim = document.getElementById("scrim");
  var menuBtn = document.getElementById("menuToggle");
  function closeNav() { document.body.classList.remove("nav-open"); }
  if (menuBtn) menuBtn.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
  if (scrim) scrim.addEventListener("click", closeNav);

  // --- editor field autosubmit on blur -----------------------------
  var editor = document.querySelector(".editor-form input");
  if (editor) {
    editor.addEventListener("change", function () { editor.form.submit(); });
  }

  // --- list filtering (catalogue + generic) ------------------------
  document.querySelectorAll("[data-filter-root]").forEach(function (root) {
    var search = root.querySelector("[data-filter-search]");
    var chips = root.querySelectorAll("[data-filter-chip]");
    var items = root.querySelectorAll("[data-item]");
    var state = { q: "", groups: {} };

    function apply() {
      var visible = 0;
      items.forEach(function (el) {
        var hay = (el.getAttribute("data-search") || "").toLowerCase();
        var okText = !state.q || hay.indexOf(state.q) >= 0;
        var okChips = Object.keys(state.groups).every(function (g) {
          var want = state.groups[g];
          if (!want || !want.length) return true;
          var vals = (el.getAttribute("data-" + g) || "").split(/\s+/);
          return want.some(function (w) { return vals.indexOf(w) >= 0; });
        });
        var show = okText && okChips;
        el.hidden = !show;
        var detail = el.nextElementSibling;
        if (detail && detail.hasAttribute("data-detail")) detail.hidden = !show;
        if (show) visible++;
      });
      var empty = root.querySelector("[data-filter-empty]");
      if (empty) empty.hidden = visible > 0;
    }

    if (search) search.addEventListener("input", function () {
      state.q = search.value.trim().toLowerCase(); apply();
    });

    // annotate each chip with how many items match that single facet
    chips.forEach(function (chip) {
      var g = chip.getAttribute("data-group");
      var v = chip.getAttribute("data-filter-chip");
      if (v === "") return;
      var n = 0;
      items.forEach(function (el) {
        var vals = (el.getAttribute("data-" + g) || "").split(/\s+/);
        if (vals.indexOf(v) >= 0) n++;
      });
      var c = document.createElement("span");
      c.className = "fc-count";
      c.textContent = n;
      chip.appendChild(c);
      if (n === 0) chip.classList.add("is-zero");
    });

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var g = chip.getAttribute("data-group");
        var v = chip.getAttribute("data-filter-chip");
        state.groups[g] = state.groups[g] || [];
        var i = state.groups[g].indexOf(v);
        if (v === "") { state.groups[g] = []; }
        else if (i >= 0) { state.groups[g].splice(i, 1); }
        else { state.groups[g].push(v); }
        root.querySelectorAll('[data-group="' + g + '"]').forEach(function (c) {
          var cv = c.getAttribute("data-filter-chip");
          c.classList.toggle("on",
            cv === "" ? (state.groups[g].length === 0) : state.groups[g].indexOf(cv) >= 0);
        });
        apply();
      });
    });
  });

  // --- list sorting (run detail control results, generic) ---------
  document.querySelectorAll("[data-sort-select]").forEach(function (sel) {
    var root = sel.closest("[data-filter-root]") || document;
    var rows = root.querySelector(".rows");
    if (!rows) return;
    var sevRank = { High: 0, Medium: 1, Low: 2 };
    var stRank = { FAIL: 0, ERROR: 1, PASS: 2 };
    var pairs = [];
    root.querySelectorAll("[data-item]").forEach(function (item, i) {
      var d = item.nextElementSibling;
      pairs.push({ item: item, detail: (d && d.hasAttribute("data-detail")) ? d : null, i: i });
    });
    function rank(map, v) { return (v in map) ? map[v] : 9; }
    sel.addEventListener("change", function () {
      var m = sel.value;
      pairs.slice().sort(function (a, b) {
        var A = a.item.dataset, B = b.item.dataset;
        if (m === "sev") return rank(sevRank, A.sev) - rank(sevRank, B.sev) || a.i - b.i;
        if (m === "status") return rank(stRank, A.st) - rank(stRank, B.st) || a.i - b.i;
        if (m === "triage")
          return (rank(stRank, A.st) - rank(stRank, B.st)) ||
                 (rank(sevRank, A.sev) - rank(sevRank, B.sev)) || a.i - b.i;
        return a.i - b.i;
      }).forEach(function (p) {
        rows.appendChild(p.item);
        if (p.detail) rows.appendChild(p.detail);
      });
    });
  });

  // --- expandable rows ---------------------------------------------
  document.querySelectorAll("[data-expand]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      if (e.target.closest("a,button,form,summary,input")) return;
      var d = el.nextElementSibling;
      if (d && d.hasAttribute("data-detail")) d.classList.toggle("open");
    });
  });
})();
