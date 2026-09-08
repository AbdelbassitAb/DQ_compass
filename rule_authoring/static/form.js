(function () {
  "use strict";
  var form = document.querySelector(".rule-form");
  if (!form || form.classList.contains("source-form")) return;

  var colsEl = document.getElementById("dataset-columns");
  var COLS = {};
  try { COLS = JSON.parse((colsEl && colsEl.textContent) || "{}") || {}; } catch (e) {}

  var typeSel = document.getElementById("control_type");
  var dsSel = document.getElementById("dataset_scope");
  var refSel = document.getElementById("ref_dataset_scope");

  function refreshTypeVisibility() {
    var t = typeSel ? typeSel.value : "";
    form.querySelectorAll(".param-group").forEach(function (g) {
      var types = (g.getAttribute("data-types") || "").split(/\s+/);
      g.style.display = types.indexOf(t) >= 0 ? "" : "none";
    });
    refreshValidity();
  }

  function refreshValidity() {
    var checked = form.querySelector("input[name=p_validity_mode]:checked");
    var mode = checked ? checked.value : null;
    form.querySelectorAll(".validity .sub").forEach(function (s) {
      s.style.display = s.getAttribute("data-vmode") === mode ? "" : "none";
    });
  }

  function fillList(id, cols) {
    var dl = document.getElementById(id);
    if (!dl) return;
    dl.innerHTML = "";
    (cols || []).forEach(function (c) {
      var o = document.createElement("option");
      o.value = c;
      dl.appendChild(o);
    });
  }

  function refreshColumns() {
    fillList("cols_main", COLS[dsSel && dsSel.value]);
    fillList("cols_ref", COLS[refSel && refSel.value]);
  }

  var timer;
  function preview() {
    clearTimeout(timer);
    timer = setTimeout(function () {
      var url = form.getAttribute("data-preview");
      if (!url) return;
      fetch(url, { method: "POST", body: new FormData(form) })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          setText("preview-plain", j.plain);
          setText("preview-logic", j.logic);
          setText("preview-de", j.data_element);
          setText("preview-th", j.threshold);
        })
        .catch(function () {});
    }, 250);
  }

  function setText(id, v) {
    var e = document.getElementById(id);
    if (e) e.textContent = v || "—";
  }

  if (typeSel) typeSel.addEventListener("change", function () { refreshTypeVisibility(); preview(); });
  if (dsSel) dsSel.addEventListener("change", function () { refreshColumns(); preview(); });
  if (refSel) refSel.addEventListener("change", function () { refreshColumns(); preview(); });
  form.addEventListener("input", preview);
  form.addEventListener("change", refreshValidity);

  refreshTypeVisibility();
  refreshColumns();
  preview();
})();
