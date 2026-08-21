# DISHARM project website

A small, static, scroll-based website for the DISHARM project. Plain HTML/CSS/JS —
no build step, no framework, no Jekyll. GitHub Pages serves the files in this
repository directly.

## Structure

- `index.html` — the one-page scrollable homepage: acronym + title hero, a short
  project presentation, a preview of recent publications, and the footer.
- `about.html` — the About page (background, approach, funding, team).
- `press.html` — the Press page (media mentions, press kit contact).
- `publications.html` — the full publication list with abstracts.
- `assets/css/style.css` — all styling.
- `assets/js/main.js` — mobile nav toggle + active-section highlighting.
- `assets/img/` — favicon and any images; add funder/partner logos here.

## Editing content

There's no CMS or templating — content lives directly in the HTML files. Anything
still needing real copy is wrapped in `[square brackets]` or flagged with a
`TODO` comment; search for `[` or `TODO` across the HTML files to find every
placeholder before publishing:

```bash
grep -rn '\[' *.html
```

Things to replace:

- **Acronym & title** (`index.html`): the expanded project title in the hero,
  and the page `<title>`/`<meta description>` tags on every page.
- **Presentation** (`index.html`, `#presentation` section): the short project
  summary paragraph(s).
- **Publications** (`index.html` preview cards and `publications.html`): titles,
  authors, venues, abstracts, and PDF/DOI/BibTeX links. Keep the `id="pub-N"`
  anchors in `publications.html` in sync with the "Read abstract" links on the
  homepage.
- **About page** (`about.html`): background, methods, funding, and team.
- **Press page** (`press.html`): media mentions and press contact.
- **Social links**: LinkedIn, X, Slack, and Bluesky URLs appear in the nav and
  footer of every page — update the `href` on each `.social-btn`.
- **Footer**: the about blurb, contact email/address, and the funder/partner
  "logo slots" (`.footer-logo-slot` in each page's footer) — replace each slot's
  placeholder text with an `<img>` pointing at a logo in `assets/img/`.

## Running locally

No build tooling required — just open `index.html` in a browser, or serve the
directory with any static file server, e.g.:

```bash
python3 -m http.server
```

## Deployment

GitHub Pages serves this repository's files directly (Settings → Pages →
deploy from branch). No Jekyll processing or build step is required.
