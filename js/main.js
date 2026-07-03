// 간다GO — minimal progressive enhancement
(function () {
  "use strict";
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }
  // Mark current nav link
  var here = location.pathname.replace(/index\.html$/, "");
  document.querySelectorAll(".nav a").forEach(function (a) {
    var href = a.getAttribute("href");
    if (!href) return;
    var path = new URL(href, location.href).pathname.replace(/index\.html$/, "");
    if (path === here) a.setAttribute("aria-current", "page");
  });
})();
