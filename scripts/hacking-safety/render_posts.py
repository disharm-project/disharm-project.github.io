"""Render each record of hacking_safety.json as a generic blog post (HTML),
wrapping the sentences listed in `flagged` with <mark>. Sentences that the
guardrails rated as not safe (the `guardrails` field, see add_guardrails.py)
get <mark class="unsafe">, with each guard's verdict as a tooltip.

Usage:
    python render_posts.py [input.json] [output.json] [--pages DIR]

Adds an `html` field to every record and writes output.json.
With --pages DIR, also writes one .html file per record into DIR, plus
an index.html listing them all (searchable, sortable).
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

CSS = """
:root { --bg:#fafaf7; --fg:#222; --muted:#777; --accent:#2b6cb0; --mark:#fff3a3; --rule:#e5e5e0;
        --unsafe:#ffd6d0; --unsafe-ink:#b42318; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font:18px/1.7 Georgia, "Times New Roman", serif; }
header.site { border-bottom:1px solid var(--rule); padding:14px 16px; text-align:center;
              font:600 14px/1 -apple-system, Helvetica, Arial, sans-serif;
              letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }
article { max-width:680px; margin:0 auto; padding:40px 16px 64px; }
article h1 { font:700 34px/1.25 -apple-system, Helvetica, Arial, sans-serif; margin:0 0 8px; }
.meta { font:14px/1.4 -apple-system, Helvetica, Arial, sans-serif; color:var(--muted);
        margin-bottom:32px; word-break:break-all; }
.meta a { color:var(--accent); text-decoration:none; }
article p { margin:0 0 1.2em; }
mark { background:var(--mark); padding:0 2px; border-radius:2px; }
mark.unsafe { background:var(--unsafe); box-shadow:inset 0 -2px 0 var(--unsafe-ink); }
footer { max-width:680px; margin:0 auto; padding:16px; border-top:1px solid var(--rule);
         font:13px -apple-system, Helvetica, Arial, sans-serif; color:var(--muted); }
"""


def title_from_url(url, max_len=90):
    """Best-effort post title from the URL slug, falling back to the domain.
    Segments that look like ids/tokens (any word over 30 chars) are skipped."""
    p = urlparse(url)
    parts = [s for s in unquote(p.path).split("/") if s]
    for seg in reversed(parts):
        seg = re.sub(r"\.(php|html?|aspx?)$", "", seg, flags=re.I)
        title = re.sub(r"[-_+]+", " ", seg).strip()
        if (re.search(r"[a-zA-Z]{3,}", title) and not title.isdigit()
                and max(map(len, title.split())) <= 30):
            title = title.capitalize()
            return title if len(title) <= max_len else title[:max_len].rsplit(" ", 1)[0] + "…"
    return p.netloc or "Untitled"


GUARDS = {"llama_guard": "Llama Guard", "md_judge": "MD-Judge", "qwen_guard": "Qwen3Guard"}


def verdict_text(name, v):
    cats = ", ".join(v["categories"])
    return f"{GUARDS[name]}: {v['label']}" + (f" ({cats})" if cats else "")


def render_body(sents, flagged, guardrails=()):
    """Join sentences into paragraphs; a blank line inside a sentence
    starts a new paragraph. Not-safe sentences get class="unsafe" and
    their guard verdicts as a tooltip."""
    flagged = set(flagged)
    unsafe = {g["sent"]: g for g in guardrails}
    paragraphs, current = [], []
    for i, s in enumerate(sents):
        # blank lines inside a sentence become paragraph breaks; other whitespace collapses
        chunks = [" ".join(c.split()) for c in re.split(r"\n\s*\n", s)]
        for j, chunk in enumerate(chunks):
            if j > 0 and current:
                paragraphs.append(current)
                current = []
            if not chunk:
                continue
            text = html.escape(chunk)
            if i in unsafe:
                tip = html.escape("; ".join(verdict_text(n, unsafe[i][n]) for n in GUARDS), quote=True)
                text = f'<mark class="unsafe" data-sent="{i}" title="{tip}">{text}</mark>'
            elif i in flagged:
                text = f'<mark data-sent="{i}">{text}</mark>'
            current.append(text)
    if current:
        paragraphs.append(current)
    return "\n".join(f"<p>{' '.join(p)}</p>" for p in paragraphs)


def render_post(x):
    url = x.get("url", "")
    domain = urlparse(url).netloc or "blog"
    title = html.escape(title_from_url(url))
    guardrails = x.get("guardrails", [])
    body = render_body(x["sents"], x.get("flagged", []), guardrails)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<header class="site">{html.escape(domain)}</header>
<article>
<h1>{title}</h1>
<div class="meta">Source: <a href="{html.escape(url, quote=True)}">{html.escape(url)}</a></div>
{body}
</article>
<footer>{len(x.get('flagged', []))} of {len(x['sents'])} sentences flagged &middot;
{len(guardrails)} not safe according to the guardrails</footer>
</body>
</html>"""


INDEX_CSS = """
:root { --bg:#fafaf7; --fg:#222; --muted:#777; --accent:#2b6cb0; --mark:#fff3a3; --rule:#e5e5e0; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 -apple-system, Helvetica, Arial, sans-serif; }
main { max-width:1100px; margin:0 auto; padding:32px 16px; }
h1 { margin:0 0 4px; font-size:28px; }
.sub { color:var(--muted); margin-bottom:20px; }
.controls { display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:12px; }
.controls input[type=search] { flex:1; min-width:220px; padding:8px 10px; font-size:15px;
                               border:1px solid var(--rule); border-radius:6px; }
#count { color:var(--muted); }
table { width:100%; border-collapse:collapse; }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--rule); vertical-align:top; }
th { cursor:pointer; user-select:none; position:sticky; top:0; background:var(--bg); }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
td.dom { color:var(--muted); word-break:break-all; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
.unsafe { color:#b42318; font-weight:600; }
.bar { display:inline-block; height:8px; background:var(--mark); border:1px solid #e0c840;
       border-radius:2px; vertical-align:middle; margin-left:6px; }
"""

INDEX_JS = """
const rows = [...document.querySelectorAll('tbody tr')];
const q = document.getElementById('q'), only = document.getElementById('only'),
      onlyUnsafe = document.getElementById('only-unsafe'),
      count = document.getElementById('count'), tbody = document.querySelector('tbody');
function filter() {
  const s = q.value.toLowerCase(); let n = 0;
  for (const r of rows) {
    const ok = (!s || r.dataset.text.includes(s)) && (!only.checked || +r.dataset.flagged > 0) &&
               (!onlyUnsafe.checked || +r.dataset.unsafe > 0);
    r.hidden = !ok; if (ok) n++;
  }
  count.textContent = n + ' of ' + rows.length + ' posts';
}
let dir = {};
document.querySelectorAll('th').forEach((th, c) => th.addEventListener('click', () => {
  const key = th.dataset.key; dir[key] = -(dir[key] || -1);
  rows.sort((a, b) => {
    const x = a.dataset[key], y = b.dataset[key];
    return (isNaN(x) ? x.localeCompare(y) : x - y) * dir[key];
  });
  tbody.append(...rows);
}));
q.addEventListener('input', filter); only.addEventListener('change', filter);
onlyUnsafe.addEventListener('change', filter); filter();
"""


def page_name(i):
    return f"{i:05d}.html"


def page_nav(i, n):
    """Index / prev / next links for a standalone page."""
    links = ['<a href="index.html">Index</a>']
    if i > 0:
        links.append(f'<a href="{page_name(i - 1)}">&larr; Prev</a>')
    if i < n - 1:
        links.append(f'<a href="{page_name(i + 1)}">Next &rarr;</a>')
    return '<nav style="text-align:center;padding:8px;font:14px sans-serif">' + " &middot; ".join(links) + "</nav>"


def render_index(data):
    rows = []
    for i, x in enumerate(data):
        url = x.get("url", "")
        title = title_from_url(url)
        domain = urlparse(url).netloc
        nf, ns = len(x.get("flagged", [])), len(x["sents"])
        nu = len(x.get("guardrails", []))
        pct = nf / ns if ns else 0
        text = html.escape(f"{title} {url}".lower(), quote=True)
        rows.append(
            f'<tr data-i="{i}" data-title="{html.escape(title.lower(), quote=True)}" '
            f'data-domain="{html.escape(domain, quote=True)}" data-flagged="{nf}" '
            f'data-sents="{ns}" data-unsafe="{nu}" data-pct="{pct:.4f}" data-text="{text}">'
            f'<td class="num">{i}</td>'
            f'<td><a href="{page_name(i)}">{html.escape(title)}</a></td>'
            f'<td class="dom">{html.escape(domain)}</td>'
            f'<td class="num">{nf}</td>'
            f'<td class="num{" unsafe" if nu else ""}">{nu}</td><td class="num">{ns}</td>'
            f'<td class="num">{pct:.0%}<span class="bar" style="width:{pct * 40:.0f}px"></span></td></tr>'
        )
    total_flagged = sum(len(x.get("flagged", [])) for x in data)
    total_unsafe = sum(len(x.get("guardrails", [])) for x in data)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hacking Safety Posts</title>
<style>{INDEX_CSS}</style>
</head>
<body>
<main>
<h1>Hacking safety posts</h1>
<div class="sub">{len(data)} posts &middot; {total_flagged} flagged sentences &middot;
{total_unsafe} not safe according to the guardrails &middot; click a column header to sort</div>
<div class="controls">
  <input id="q" type="search" placeholder="Filter by title or URL&hellip;">
  <label><input id="only" type="checkbox"> Only posts with flags</label>
  <label><input id="only-unsafe" type="checkbox"> Only posts with not-safe sentences</label>
  <span id="count"></span>
</div>
<table>
<thead><tr>
  <th class="num" data-key="i">#</th><th data-key="title">Title</th><th data-key="domain">Domain</th>
  <th class="num" data-key="flagged">Flagged</th><th class="num" data-key="unsafe">Not safe</th>
  <th class="num" data-key="sents">Sentences</th>
  <th class="num" data-key="pct">% flagged</th>
</tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
</main>
<script>{INDEX_JS}</script>
</body>
</html>"""


def main(argv):
    pages = None
    if "--pages" in argv:
        k = argv.index("--pages")
        pages = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    src = argv[0] if argv else "hacking_safety.json"
    dst = argv[1] if len(argv) > 1 else "hacking_safety_html.json"

    data = json.load(open(src, encoding="utf-8"))
    if pages:
        Path(pages).mkdir(parents=True, exist_ok=True)
    for i, x in enumerate(data):
        x["html"] = render_post(x)
        if pages:
            nav = page_nav(i, len(data))
            page = x["html"].replace("<body>\n", f"<body>\n{nav}\n", 1).replace(
                "</footer>", f"</footer>\n{nav}", 1)
            Path(pages, page_name(i)).write_text(page, encoding="utf-8")
    if pages:
        Path(pages, "index.html").write_text(render_index(data), encoding="utf-8")
    json.dump(data, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Rendered {len(data)} posts -> {dst}" + (f" (+ pages in {pages}/)" if pages else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
