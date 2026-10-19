"""Build the "Hacking safety" section of the DISHARM site
(https://disharm-project.github.io/) from hacking_safety.json.

Usage:
    python build_site.py REPO_DIR [input.json] [--all]

Writes into REPO_DIR/hacking-safety/:
    index.html            searchable, sortable list of the published posts
    posts/NNNNN.html      one blog-style page per record, flagged sentences in <mark>,
                          not-safe ones per the guardrails in red (see add_guardrails.py)
    random.html           redirects to a random published post

Only records with at most 35% of their sentences flagged are published
(see keep()), unless --all is given; NNNNN is the record's index in the input JSON. Every page is noindex.

The site header/nav and footer are copied from REPO_DIR/about.html so the
section stays in sync with the rest of the site; styling lives in
REPO_DIR/assets/css/style.css (".hs-" classes).
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from render_posts import render_body, title_from_url

SECTION = "hacking-safety"
NAV_LABEL = "Hacking safety"


def site_chrome(repo):
    """Return (head_links, header, footer) HTML taken from about.html."""
    src = Path(repo, "about.html").read_text(encoding="utf-8")
    head = re.search(r'<link rel="icon".*?<link rel="stylesheet"[^>]*>', src, re.S).group(0)
    header = re.search(r'<a class="skip-link".*?</header>', src, re.S).group(0)
    footer = re.search(r'<footer class="site-footer">.*?</footer>\s*<script.*?</script>\s*<script>.*?</script>',
                       src, re.S).group(0)
    header = header.replace(' aria-current="page"', "")
    return head, header, footer


def relink(fragment, prefix):
    """Prefix site-relative href/src values so they work from a subdirectory."""
    return re.sub(r'(href|src)="(?!https?:|mailto:|#|/)([^"]*)"',
                  lambda m: f'{m.group(1)}="{prefix}{m.group(2)}"', fragment)


def mark_current(header, prefix):
    return header.replace(f'<a href="{prefix}{SECTION}/index.html">',
                          f'<a href="{prefix}{SECTION}/index.html" aria-current="page">', 1)


def page(title, description, chrome, prefix, main, robots=False):
    head, header, footer = (relink(c, prefix) for c in chrome)
    header = mark_current(header, prefix)
    meta_robots = '\n  <meta name="robots" content="noindex">' if robots else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — DISHARM</title>
  <meta name="description" content="{html.escape(description, quote=True)}">{meta_robots}
  {head}
</head>
<body>
  {header}

  <main id="main">
{main}
  </main>

  {footer}
</body>
</html>
"""


def post_name(i):
    return f"{i:05d}.html"


def keep(x):
    """Publish a post only if at most 35% of its sentences are flagged."""
    return 100 * len(x.get("flagged", [])) <= 35 * len(x["sents"])


def render_post_page(k, items, chrome):
    """Page for items[k]; items is the list of (dataset index, record) being published."""
    i, x = items[k]
    url = x.get("url", "")
    domain = urlparse(url).netloc
    title = html.escape(title_from_url(url))
    nf, ns = len(x.get("flagged", [])), len(x["sents"])
    guardrails = x.get("guardrails", [])
    nu = len(guardrails)
    unsafe_chip = (f' <span class="hs-chip hs-chip--unsafe">{nu} not safe per guardrails</span>'
                   if nu else "")
    prev_link = (f'<a class="btn btn--ghost" href="{post_name(items[k - 1][0])}">&larr; Previous</a>'
                 if k > 0 else "")
    next_link = (f'<a class="btn btn--ghost" href="{post_name(items[k + 1][0])}">Next &rarr;</a>'
                 if k < len(items) - 1 else "")
    main = f"""    <section class="page-hero hs-post">
      <div class="wrap">
        <span class="page-hero__kicker"><a href="../index.html">{NAV_LABEL}</a> &middot; Post {i}</span>
        <h1 class="page-hero__title">{title}</h1>
        <p class="hs-post__source">{html.escape(domain)} &middot;
          <a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener nofollow">{html.escape(url)}</a></p>
        <p class="hs-post__stats"><span class="hs-chip">{nf} of {ns} sentences flagged</span>{unsafe_chip}</p>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <nav class="hs-pager" aria-label="Post navigation">
          {prev_link}
          <a class="btn" href="../index.html">All posts</a>
          <a class="btn btn--ghost" href="../random.html?from={i}">Random post</a>
          {next_link}
        </nav>
        <article class="hs-post__body">
{render_body(x["sents"], x.get("flagged", []), guardrails)}
        </article>
      </div>
    </section>"""
    return page(title, f"Post {i} of the hacking safety dataset, from {domain}.",
                chrome, "../../", main, robots=True)


INDEX_JS = """
  <script>
  (function () {
    var tbody = document.querySelector(".hs-table tbody");
    var rows = Array.prototype.slice.call(tbody.rows);
    var q = document.getElementById("hs-q"), count = document.getElementById("hs-count"),
        onlyUnsafe = document.getElementById("hs-unsafe");
    function filter() {
      var s = q.value.toLowerCase(), n = 0;
      rows.forEach(function (r) {
        var ok = (!s || r.dataset.text.indexOf(s) !== -1) && (!onlyUnsafe.checked || +r.dataset.unsafe > 0);
        r.hidden = !ok; if (ok) n++;
      });
      count.textContent = n.toLocaleString() + " of " + rows.length.toLocaleString() + " posts";
    }
    var dir = {};
    document.querySelectorAll(".hs-table th").forEach(function (th) {
      th.addEventListener("click", function () {
        var key = th.dataset.key; dir[key] = -(dir[key] || -1);
        document.querySelectorAll(".hs-table th").forEach(function (h) { h.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", dir[key] > 0 ? "ascending" : "descending");
        rows.sort(function (a, b) {
          var x = a.dataset[key], y = b.dataset[key];
          return (isNaN(x) ? x.localeCompare(y) : x - y) * dir[key];
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
      });
    });
    q.addEventListener("input", filter); onlyUnsafe.addEventListener("change", filter); filter();
  })();
  </script>"""


def render_index_page(items, chrome, filtered=True):
    rows = []
    for i, x in items:
        url = x.get("url", "")
        title = title_from_url(url)
        domain = urlparse(url).netloc
        nf, ns = len(x.get("flagged", [])), len(x["sents"])
        nu = len(x.get("guardrails", []))
        pct = nf / ns if ns else 0
        rows.append(
            f'<tr data-i="{i}" data-title="{html.escape(title.lower(), quote=True)}" '
            f'data-domain="{html.escape(domain, quote=True)}" data-flagged="{nf}" data-unsafe="{nu}" data-sents="{ns}" '
            f'data-pct="{pct:.4f}" data-text="{html.escape((title + " " + url).lower(), quote=True)}">'
            f'<td class="hs-num">{i}</td>'
            f'<td><a href="posts/{post_name(i)}">{html.escape(title)}</a></td>'
            f'<td class="hs-domain">{html.escape(domain)}</td>'
            f'<td class="hs-num">{nf}</td>'
            f'<td class="hs-num{" hs-unsafe" if nu else ""}">{nu}</td><td class="hs-num">{ns}</td>'
            f'<td class="hs-num">{pct:.0%}<span class="hs-bar" style="width:{pct * 3:.2f}rem"></span></td></tr>'
        )
    total_flagged = sum(len(x.get("flagged", [])) for _, x in items)
    sentences = sum(len(x["sents"]) for _, x in items)
    total_unsafe = sum(len(x.get("guardrails", [])) for _, x in items)
    main = f"""    <section class="page-hero">
      <div class="wrap">
        <span class="page-hero__kicker">Dataset</span>
        <h1 class="page-hero__title">{NAV_LABEL}</h1>
        <p class="hs-warning" role="note"><strong>Trigger warning</strong> The posts below are unedited web pages from Common Crawl. They may contain offensive, explicit or disturbing material, including hate speech, sexual content, violence and discrimination. They are shown for research purposes only and do not reflect the views of the DISHARM project.</p>
        <p class="page-hero__lede">Web pages from the hacking safety dataset, rendered as posts.
          Sentences flagged by the classifier are <mark class="hs-mark">highlighted</mark>;
          those that at least one guardrail (Llama Guard, MD-Judge, Qwen3Guard) rated as not safe
          are <mark class="hs-mark hs-mark--unsafe">marked in red</mark>.
          {"Only pages with at most 35% of their sentences flagged are shown." if filtered else
           "All pages are shown, whatever their share of flagged sentences."}</p>
        <div class="hs-stats">
          <div><strong>{len(items):,}</strong><span>posts</span></div>
          <div><strong>{sentences:,}</strong><span>sentences</span></div>
          <div><strong>{total_flagged:,}</strong><span>flagged sentences</span></div>
          <div><strong>{total_unsafe:,}</strong><span>not safe per guardrails</span></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="hs-controls">
          <input id="hs-q" type="search" placeholder="Filter by title or URL&hellip;" aria-label="Filter posts">
          <label><input id="hs-unsafe" type="checkbox"> Only posts with not-safe sentences</label>
          <a class="btn" href="random.html">Random post</a>
          <span id="hs-count" aria-live="polite"></span>
        </div>
        <div class="hs-table-wrap">
          <table class="hs-table">
            <thead><tr>
              <th class="hs-num" data-key="i">#</th><th data-key="title">Title</th><th data-key="domain">Domain</th>
              <th class="hs-num" data-key="flagged">Flagged</th><th class="hs-num" data-key="unsafe">Not safe</th>
              <th class="hs-num" data-key="sents">Sentences</th>
              <th class="hs-num" data-key="pct">% flagged</th>
            </tr></thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>
      </div>
    </section>"""
    out = page(NAV_LABEL, "Browse the hacking safety dataset: web pages with flagged sentences highlighted.",
               chrome, "../", main, robots=True)
    return out.replace("</body>", INDEX_JS + "\n</body>")


def render_random_page(items):
    """Tiny page that redirects to a random published post (skipping ?from=N)."""
    ids = json.dumps([i for i, _ in items], separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="robots" content="noindex">
  <title>Random post — DISHARM</title>
  <script>
  (function () {{
    var ids = {ids};
    var from = +new URLSearchParams(location.search).get("from");
    var i;
    do {{ i = ids[Math.floor(Math.random() * ids.length)]; }} while (ids.length > 1 && i === from);
    location.replace("posts/" + String(i).padStart(5, "0") + ".html");
  }})();
  </script>
</head>
<body>
  <p><a href="index.html">Back to all posts</a></p>
</body>
</html>
"""


def main(argv):
    show_all = "--all" in argv
    argv = [a for a in argv if a != "--all"]
    repo = Path(argv[0])
    src = argv[1] if len(argv) > 1 else "hacking_safety.json"
    data = json.load(open(src, encoding="utf-8"))
    chrome = site_chrome(repo)

    out = repo / SECTION
    if out.exists():
        shutil.rmtree(out)
    (out / "posts").mkdir(parents=True)
    items = [(i, x) for i, x in enumerate(data) if show_all or keep(x)]
    for k, (i, _) in enumerate(items):
        (out / "posts" / post_name(i)).write_text(render_post_page(k, items, chrome), encoding="utf-8")
    (out / "index.html").write_text(render_index_page(items, chrome, filtered=not show_all), encoding="utf-8")
    (out / "random.html").write_text(render_random_page(items), encoding="utf-8")
    print(f"Wrote {len(items)} of {len(data)} posts + index + random to {out}/")


if __name__ == "__main__":
    main(sys.argv[1:])
