(function () {
  "use strict";
  var form = document.querySelector(".source-form");
  if (!form) return;

  var typeInput = document.getElementById("src-type");
  var tiles = form.querySelectorAll(".tile");
  var probeBtn = document.getElementById("probe-btn");
  var probeOut = document.getElementById("probe-out");

  function selectType(t) {
    typeInput.value = t;
    tiles.forEach(function (tile) {
      tile.classList.toggle("selected", tile.getAttribute("data-conn") === t);
    });
    form.querySelectorAll(".conn-fields").forEach(function (fs) {
      fs.hidden = fs.getAttribute("data-conn") !== t;
    });
    var planned = form.querySelector('.tile[data-conn="' + t + '"]').classList.contains("planned");
    probeBtn.disabled = planned;
    probeBtn.title = planned ? "Preview connector — no live connection in this prototype" : "";
    probeOut.textContent = planned
      ? "Preview connector: no live connection in this prototype."
      : "Not tested yet.";
    probeOut.className = "probe-out muted";
  }

  tiles.forEach(function (tile) {
    tile.addEventListener("click", function () { selectType(tile.getAttribute("data-conn")); });
  });

  function renderProbe(j) {
    if (!j.ok) {
      probeOut.className = "probe-out error";
      probeOut.textContent = j.error || "Connection failed.";
      return;
    }
    probeOut.className = "probe-out";
    var head = document.createElement("div");
    head.className = "probe-summary";
    head.textContent = j.summary;
    probeOut.innerHTML = "";
    probeOut.appendChild(head);
    if (j.columns && j.columns.length) {
      var t = document.createElement("table");
      t.className = "preview-table";
      var thead = document.createElement("tr");
      j.columns.forEach(function (c) {
        var th = document.createElement("th"); th.textContent = c; thead.appendChild(th);
      });
      t.appendChild(thead);
      (j.sample || []).forEach(function (row) {
        var tr = document.createElement("tr");
        j.columns.forEach(function (c) {
          var td = document.createElement("td");
          td.textContent = row[c] === undefined ? "" : row[c];
          tr.appendChild(td);
        });
        t.appendChild(tr);
      });
      var wrap = document.createElement("div");
      wrap.className = "scroll-x";
      wrap.appendChild(t);
      probeOut.appendChild(wrap);
    }
  }

  probeBtn.addEventListener("click", function () {
    probeOut.className = "probe-out muted";
    probeOut.textContent = "Testing…";
    fetch(form.getAttribute("data-probe"), { method: "POST", body: new FormData(form) })
      .then(function (r) { return r.json(); })
      .then(renderProbe)
      .catch(function () {
        probeOut.className = "probe-out error";
        probeOut.textContent = "Request failed.";
      });
  });

  selectType(typeInput.value || "csv");
})();
