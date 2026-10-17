/*! 盈康 — mobile drawer + search overlay */
(function () {
  var body = document.body;
  var toggle = document.getElementById("nav-toggle");
  var drawer = document.getElementById("nav-drawer");
  var backdrop = document.getElementById("drawer-backdrop");
  var closeBtn = document.getElementById("nav-close");

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    if (backdrop) {
      backdrop.hidden = false;
      backdrop.classList.add("open");
    }
    if (toggle) toggle.setAttribute("aria-expanded", "true");
    body.classList.add("drawer-open");
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    if (backdrop) {
      backdrop.classList.remove("open");
      backdrop.hidden = true;
    }
    if (toggle) toggle.setAttribute("aria-expanded", "false");
    body.classList.remove("drawer-open");
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      if (drawer && drawer.classList.contains("open")) closeDrawer();
      else openDrawer();
    });
  }
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  if (backdrop) backdrop.addEventListener("click", closeDrawer);

  var ov = document.getElementById("search-overlay");
  var searchBtn = document.getElementById("open-search");
  function openSearch() {
    if (!ov) return;
    closeDrawer();
    ov.classList.add("open");
    var i = ov.querySelector("input");
    if (i) i.focus();
  }
  function closeSearch() {
    if (ov) ov.classList.remove("open");
  }
  if (searchBtn && ov) {
    searchBtn.addEventListener("click", openSearch);
    ov.addEventListener("click", function (e) {
      if (e.target === ov) closeSearch();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeDrawer();
      closeSearch();
    }
  });
})();
