(function () {
  "use strict";

  var nav = document.querySelector(".site-nav");
  var toggle = document.querySelector(".nav-toggle");

  if (nav && toggle) {
    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    nav.querySelectorAll(".site-nav__links a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // Highlight the current in-page section link on the homepage.
  var sections = document.querySelectorAll("main [id]");
  var navLinks = document.querySelectorAll(".site-nav__links a[href^='#']");

  if (sections.length && navLinks.length && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          navLinks.forEach(function (link) {
            var match = link.getAttribute("href") === "#" + entry.target.id;
            link.toggleAttribute("aria-current", match);
            if (match) {
              link.setAttribute("aria-current", "page");
            } else {
              link.removeAttribute("aria-current");
            }
          });
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );

    sections.forEach(function (section) {
      observer.observe(section);
    });
  }

  // Publication lists, built from assets/data/publications.js.
  // <ul data-pubs="all"> lists every entry; <ul data-pubs="recent"> the first three.
  var pubs = window.DISHARM_PUBLICATIONS || [];

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function link(href, label) {
    var a = el("a", "", label);
    a.href = href;
    return a;
  }

  document.querySelectorAll("ul[data-pubs]").forEach(function (list) {
    var recent = list.getAttribute("data-pubs") === "recent";
    var items = recent ? pubs.slice(0, 3) : pubs;

    if (!items.length) {
      list.appendChild(el("li", "pub-list__empty", "Publications will be listed here soon."));
      return;
    }

    items.forEach(function (pub) {
      var card = el("li", "pub-card");
      if (!recent) card.id = pub.id;

      var meta = el("div", "pub-card__meta");
      meta.appendChild(el("span", "", pub.type));
      meta.appendChild(el("span", "", String(pub.year)));
      card.appendChild(meta);

      card.appendChild(el("h3", "pub-card__title", pub.title));

      var authors = el("p", "pub-card__authors", pub.authors);
      if (pub.venue) {
        authors.appendChild(document.createTextNode(" — "));
        authors.appendChild(el("em", "", pub.venue));
      }
      card.appendChild(authors);

      if (pub.abstract) card.appendChild(el("p", "pub-card__abstract", pub.abstract));

      var links = el("div", "pub-card__links");
      if (recent) links.appendChild(link("publications.html#" + pub.id, "Read abstract"));
      if (pub.pdf) links.appendChild(link(pub.pdf, "PDF"));
      if (pub.doi) links.appendChild(link(pub.doi, "DOI"));
      if (!recent && pub.bibtex) links.appendChild(link(pub.bibtex, "BibTeX"));
      if (links.children.length) card.appendChild(links);

      list.appendChild(card);
    });
  });

  // Lists are built after load, so re-apply a #pub-N jump from another page.
  if (location.hash && document.querySelector("ul[data-pubs='all']")) {
    var target = document.getElementById(location.hash.slice(1));
    if (target) target.scrollIntoView();
  }
})();
