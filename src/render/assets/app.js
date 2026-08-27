(function () {
  "use strict";

  var form = document.querySelector("[data-filter-form]");
  if (!form) {
    return;
  }

  var rows = Array.prototype.slice.call(document.querySelectorAll("[data-instrument]"));
  var count = document.querySelector("[data-result-count]");

  function value(name) {
    var field = form.elements.namedItem(name);
    return field ? String(field.value || "").trim().toLowerCase() : "";
  }

  function applyFilters() {
    var search = value("search");
    var country = value("country");
    var asset = value("asset");
    var theme = value("theme");
    var visible = 0;

    rows.forEach(function (row) {
      var matches =
        (!search || row.dataset.search.indexOf(search) !== -1) &&
        (!country || row.dataset.country.toLowerCase() === country) &&
        (!asset || row.dataset.asset.toLowerCase() === asset) &&
        (!theme || row.dataset.themes.split(" ").indexOf(theme) !== -1);
      row.hidden = !matches;
      if (matches) {
        visible += 1;
      }
    });

    if (count) {
      count.textContent = String(visible);
    }
  }

  form.addEventListener("input", applyFilters);
  form.addEventListener("change", applyFilters);
  form.addEventListener("reset", function () {
    window.setTimeout(applyFilters, 0);
  });
}());
