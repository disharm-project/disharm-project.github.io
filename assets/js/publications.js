// Publication lists, built from assets/data/publications.bib.
// <ul data-pubs="all"> lists every entry; <ul data-pubs="recent"> the three newest.
(function () {
  "use strict";

  var lists = document.querySelectorAll("ul[data-pubs]");
  if (!lists.length) return;

  var BIB_URL = "assets/data/publications.bib";

  var TYPE_LABELS = {
    article: "Journal article",
    inproceedings: "Conference paper",
    conference: "Conference paper",
    incollection: "Book chapter",
    inbook: "Book chapter",
    book: "Book",
    phdthesis: "PhD thesis",
    mastersthesis: "Master's thesis",
    techreport: "Technical report",
    unpublished: "Preprint",
    misc: "Publication"
  };

  // ---- BibTeX parsing -------------------------------------------------------

  // Read a {...} or "..." value starting at s[i]; returns [value, nextIndex].
  function readDelimited(s, i) {
    if (s[i] === "{") {
      var depth = 0, start = i + 1;
      for (; i < s.length; i++) {
        if (s[i] === "\\") { i++; continue; }
        if (s[i] === "{") depth++;
        else if (s[i] === "}" && --depth === 0) return [s.slice(start, i), i + 1];
      }
    } else {
      var j = i + 1, d = 0;
      for (; j < s.length; j++) {
        if (s[j] === "\\") { j++; continue; }
        if (s[j] === "{") d++;
        else if (s[j] === "}") d--;
        else if (s[j] === '"' && d === 0) return [s.slice(i + 1, j), j + 1];
      }
    }
    return [s.slice(i), s.length];
  }

  function parseBib(text) {
    var entries = [];
    var re = /@(\w+)\s*\{/g;
    var m;
    while ((m = re.exec(text))) {
      var type = m[1].toLowerCase();
      var body = readDelimited(text, re.lastIndex - 1);
      re.lastIndex = body[1];
      if (type === "comment" || type === "string" || type === "preamble") continue;

      var s = body[0];
      var comma = s.indexOf(",");
      if (comma < 0) continue;
      var entry = { type: type, key: s.slice(0, comma).trim(), fields: {}, order: [] };

      var i = comma + 1;
      var fieldRe = /\s*([\w-]+)\s*=\s*/y;
      while (i < s.length) {
        fieldRe.lastIndex = i;
        var f = fieldRe.exec(s);
        if (!f) { i++; continue; }
        var name = f[1].toLowerCase();
        i = fieldRe.lastIndex;
        var value;
        if (s[i] === "{" || s[i] === '"') {
          var r = readDelimited(s, i);
          value = r[0];
          i = r[1];
        } else {
          var end = s.indexOf(",", i);
          if (end < 0) end = s.length;
          value = s.slice(i, end).trim();
          i = end;
        }
        entry.fields[name] = value;
        entry.order.push(name);
        var next = s.indexOf(",", i);
        i = next < 0 ? s.length : next + 1;
      }
      entries.push(entry);
    }
    return entries;
  }

  // ---- LaTeX → plain text ---------------------------------------------------

  var ACCENTS = {
    "'": "́", "`": "̀", "^": "̂", '"': "̈", "~": "̃",
    "=": "̄", ".": "̇", "u": "̆", "v": "̌", "H": "̋",
    "c": "̧", "k": "̨"
  };
  var SYMBOLS = {
    ss: "ß", ae: "æ", AE: "Æ", oe: "œ", OE: "Œ", o: "ø", O: "Ø",
    aa: "å", AA: "Å", l: "ł", L: "Ł", i: "ı", j: "ȷ"
  };

  function delatex(s) {
    return String(s || "")
      .replace(/\\([`'^"~=.uvHck])\s*\{?\\?([A-Za-z])\}?/g, function (_, acc, ch) {
        return (ch + ACCENTS[acc]).normalize("NFC");
      })
      .replace(/\\(ss|ae|AE|oe|OE|aa|AA|o|O|l|L|i|j)(?![A-Za-z])\s?/g, function (_, c) {
        return SYMBOLS[c];
      })
      .replace(/\\(?:emph|textit|textbf|textsc|texttt|mathrm|url)\s*\{([^{}]*)\}/g, "$1")
      .replace(/\\([&%$#_{}])/g, "$1")
      .replace(/---/g, "—")
      .replace(/--/g, "–")
      .replace(/~/g, " ")
      .replace(/[{}]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  // "Last, First and First Last" → "First Last, First Last"
  function formatAuthors(s) {
    if (!s) return "";
    return s.split(/\s+and\s+/i).map(function (name) {
      name = delatex(name);
      if (name.toLowerCase() === "others") return "et al.";
      var parts = name.split(/\s*,\s*/);
      return parts.length > 1 ? parts.slice(1).join(" ") + " " + parts[0] : name;
    }).join(", ").replace(/, et al\.$/, " et al.");
  }

  function toPublication(entry, index) {
    var f = entry.fields;
    var preprint = f.eprint || /arxiv|biorxiv|ssrn/i.test(f.journal || f.publisher || f.howpublished || "");
    var doi = f.doi ? delatex(f.doi).replace(/^https?:\/\/(dx\.)?doi\.org\//, "") : "";

    return {
      id: entry.key,
      index: index,
      type: preprint && (entry.type === "misc" || entry.type === "article" || entry.type === "unpublished")
        ? "Preprint"
        : TYPE_LABELS[entry.type] || "Publication",
      year: parseInt(f.year, 10) || 0,
      title: delatex(f.title),
      authors: formatAuthors(f.author),
      venue: delatex(f.journal || f.booktitle || f.school || f.institution || f.howpublished || f.publisher ||
        (f.archiveprefix && f.eprint ? f.archiveprefix + ":" + f.eprint : "")),
      abstract: delatex(f.abstract),
      pdf: f.pdf || f.url || (f.eprint && /arxiv/i.test(f.archiveprefix || "arxiv") ? "https://arxiv.org/abs/" + f.eprint : ""),
      doi: doi ? "https://doi.org/" + doi : "",
      bibtex: toBibtex(entry)
    };
  }

  // Citation without the abstract, for the BibTeX box.
  function toBibtex(entry) {
    var names = entry.order.filter(function (n) { return n !== "abstract"; });
    var width = Math.max.apply(null, names.map(function (n) { return n.length; }).concat([0]));
    var lines = names.map(function (n) {
      return "  " + n + new Array(width - n.length + 1).join(" ") + " = {" + entry.fields[n] + "}";
    });
    return "@" + entry.type + "{" + entry.key + ",\n" + lines.join(",\n") + "\n}";
  }

  // ---- Rendering ------------------------------------------------------------

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function link(href, label) {
    var a = el("a", "", label);
    a.href = href;
    if (/^https?:/.test(href)) {
      a.target = "_blank";
      a.rel = "noopener";
    }
    return a;
  }

  function card(pub, recent) {
    var li = el("li", "pub-card");
    if (!recent) li.id = pub.id;

    var meta = el("div", "pub-card__meta");
    meta.appendChild(el("span", "", pub.type));
    if (pub.year) meta.appendChild(el("span", "", String(pub.year)));
    li.appendChild(meta);

    li.appendChild(el("h3", "pub-card__title", pub.title));

    var authors = el("p", "pub-card__authors", pub.authors);
    if (pub.venue) {
      if (pub.authors) authors.appendChild(document.createTextNode(" — "));
      authors.appendChild(el("em", "", pub.venue));
    }
    li.appendChild(authors);

    if (pub.abstract) li.appendChild(el("p", "pub-card__abstract", pub.abstract));

    var links = el("div", "pub-card__links");
    if (recent) links.appendChild(link("publications.html#" + encodeURIComponent(pub.id), "Read abstract"));
    if (pub.pdf) links.appendChild(link(pub.pdf, "PDF"));
    if (pub.doi) links.appendChild(link(pub.doi, "DOI"));
    li.appendChild(links);

    var bib = null;
    if (!recent) {
      bib = el("details", "pub-card__bibtex");
      bib.appendChild(el("summary", "", "BibTeX"));
      var pre = el("pre", "", pub.bibtex);
      bib.appendChild(pre);
      var copy = el("button", "pub-card__copy", "Copy");
      copy.type = "button";
      copy.addEventListener("click", function () {
        navigator.clipboard.writeText(pub.bibtex).then(function () {
          copy.textContent = "Copied";
          setTimeout(function () { copy.textContent = "Copy"; }, 1500);
        });
      });
      bib.appendChild(copy);
    }

    if (!links.children.length) li.removeChild(links);
    if (bib) li.appendChild(bib);
    return li;
  }

  function render(pubs) {
    lists.forEach(function (list) {
      var recent = list.getAttribute("data-pubs") === "recent";
      var items = recent ? pubs.slice(0, 3) : pubs;
      if (!items.length) {
        list.appendChild(el("li", "pub-list__empty", "Publications will be listed here soon."));
        return;
      }
      items.forEach(function (pub) { list.appendChild(card(pub, recent)); });
    });

    // Lists are built after load, so re-apply a #key jump from another page.
    if (location.hash && document.querySelector("ul[data-pubs='all']")) {
      var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) target.scrollIntoView();
    }
  }

  fetch(BIB_URL)
    .then(function (res) {
      if (!res.ok) throw new Error(res.status);
      return res.text();
    })
    .then(function (text) {
      var pubs = parseBib(text).map(toPublication);
      // Newest year first; same year keeps file order.
      pubs.sort(function (a, b) { return b.year - a.year || a.index - b.index; });
      render(pubs);
    })
    .catch(function () {
      render([]);
    });
})();
