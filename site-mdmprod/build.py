#!/usr/bin/env python3
"""Génère le site statique mdmprod.fr dans dist/ à partir de src/, assets/ et content/.

PREVIEW = True : toutes les pages sont en noindex et un bandeau « version de test »
s'affiche. Passer à False le jour de la bascule du domaine.
"""
import html
import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

PREVIEW = True
SITE = "https://www.mdmprod.fr"
ROOT = Path(__file__).resolve().parent
SRC, ASSETS, CONTENT, DIST = ROOT / "src", ROOT / "assets", ROOT / "content", ROOT / "dist"

HEADER = (SRC / "header.html").read_text(encoding="utf-8")
FOOTER = (SRC / "footer.html").read_text(encoding="utf-8")
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
SITEMAP = []


def esc(s):
    return html.escape(s or "", quote=True)


def load(name):
    p = CONTENT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def date_fr(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def local(url):
    """Les liens absolus vers mdmprod.fr deviennent relatifs au nouveau site."""
    return re.sub(r"^https?://(www\.)?mdmprod\.fr", "", url or "") or "/"


def img_url(url, w=1600):
    """Image Wix redimensionnée côté Wix (on garde l'original si l'URL n'est pas une image Wix)."""
    m = re.match(r"(https://static\.wixstatic\.com/media/([^/]+))", url or "")
    if not m:
        return url
    base, name = m.group(1), m.group(2)
    return f"{base}/v1/fill/w_{w},h_{round(w * 0.6667)},al_c,q_85/{name}"


def page(path, title, description, main, current=None, og_image=None, jsonld=None, index=True):
    robots = '<meta name="robots" content="noindex, nofollow">' if (PREVIEW or not index) else ""
    header = HEADER
    if current:
        header = header.replace(f'href="{current}"', f'href="{current}" aria-current="page"', 1)
    bar = ('<div class="preview-bar"><div class="wrap">Version de test du nouveau site. '
           'Elle n\'est pas référencée par Google.</div></div>') if PREVIEW else ""
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>'
                 for x in (jsonld or []))
    doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE}{path}">
{robots}
<meta property="og:type" content="website">
<meta property="og:site_name" content="MDMProd">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{SITE}{path}">
{og}
<link rel="icon" type="image/png" href="/assets/img/favicon.png">
<link rel="stylesheet" href="/assets/site.css">
{ld}
</head>
<body>
{bar}
{header}
<main>
{main}
</main>
{FOOTER}
<script src="/assets/site.js" defer></script>
</body>
</html>
"""
    out = DIST / path.strip("/") / "index.html" if path != "/" else DIST / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if index:
        SITEMAP.append(path)


def cta_band(title="Parlons de votre projet.", text="Quelques lignes suffisent. Nous revenons vers vous avec une proposition."):
    return f"""<section class="band band--alt cta-band">
  <div class="wrap stack stack--center center narrow">
    <h2 style="font-size: var(--h2); line-height: 1.08;">{esc(title)}</h2>
    <p class="lead">{esc(text)}</p>
    <div class="actions"><a class="pill" href="/nous-contacter">Présenter un projet</a><a class="more" href="tel:+33182289960">01 82 28 99 60</a></div>
  </div>
</section>"""


def text_to_html(text):
    """Texte brut des fiches Wix → HTML : lignes courtes sans ponctuation finale = intertitres."""
    out = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        while lines:
            line = lines[0]
            link = re.match(r"^(.{3,80}?)\s*:\s*(https?://\S+)$", line)
            if link:
                out.append(f'<p><a href="{esc(local(link.group(2)))}">{esc(link.group(1))}</a></p>')
                lines.pop(0)
                continue
            if len(lines) >= 1 and len(line) <= 90 and not re.search(r"[.!?:;…,]$", line):
                out.append(f"<h2>{esc(line)}</h2>")
                lines.pop(0)
                continue
            out.append("<p>" + "<br>".join(esc(l) for l in lines) + "</p>")
            lines = []
    return "\n".join(out)


def contact_block():
    c = load("pages.json") or {}
    vcita = c.get("vcita_src")
    form = (f'<iframe class="vcita" src="{esc(vcita)}" title="Formulaire de présentation de projet" loading="lazy"></iframe>'
            if vcita else '<p class="lead">Formulaire en cours de raccordement.</p>')
    return f"""<div class="contact-grid">
        <div class="card" style="background: var(--bg-alt);">{form}</div>
        <div class="card coords" style="background: var(--bg-alt);">
          <dl>
            <div><dt>Téléphone</dt><dd><a href="tel:+33182289960" style="color: inherit;">01 82 28 99 60</a></dd></div>
            <div><dt>E-mail</dt><dd><a href="mailto:contact@mdmprod.fr" style="color: inherit;">contact@mdmprod.fr</a></dd></div>
            <div><dt>WhatsApp</dt><dd class="plain"><a class="wa" href="https://wa.me/33745174129" target="_blank" rel="noopener">Écrire sur WhatsApp ›</a></dd></div>
            <div><dt>Adresses</dt><dd class="plain">6 rue d'Armaillé, 75017 Paris<br>61 rue de Lyon, 75012 Paris</dd></div>
          </dl>
        </div>
      </div>"""


ORG = {
    "@context": "https://schema.org", "@type": "Organization", "name": "MDMProd",
    "url": SITE, "logo": f"{SITE}/assets/img/logo-mdmprod-full.png",
    "email": "contact@mdmprod.fr", "telephone": "+33 1 82 28 99 60",
    "address": {"@type": "PostalAddress", "streetAddress": "6 rue d'Armaillé",
                "postalCode": "75017", "addressLocality": "Paris", "addressCountry": "FR"},
    "areaServed": "FR",
    "sameAs": ["https://www.linkedin.com/company/11108022", "https://www.facebook.com/mdmpdt",
               "https://www.instagram.com/mdmprod"],
}


def build_home():
    main = (SRC / "home_main.html").read_text(encoding="utf-8")
    clients = json.loads((SRC / "clients.json").read_text(encoding="utf-8"))
    scale = {"Hermès": 1, "Mauboussin": .95, "Moët & Chandon": 1.05, "LVMH": .8,
             "Paris Aéroport": 1.2, "Chaussea": .85, "SNCF": .95, "TF1": .95}
    marks = "\n".join(
        f'        <li><span class="logo-mark" role="img" aria-label="{esc(c["name"])}" '
        f'style="--src: url(\'/assets/img/clients/{c["file"]}\'); --ar: {c["w"]} / {c["h"]}; --s: {scale[c["name"]]};"></span></li>'
        for c in clients)
    main = main.replace("{{CLIENTS}}", marks).replace("{{CONTACT_BLOCK}}", contact_block())
    faq = [
        ("Quelle différence entre organiser et coproduire ?", "Organiser : vous nous confiez votre date et nous la prenons en charge. Coproduire : nous produisons le spectacle avec vous, et les apports comme les recettes sont répartis selon un contrat de coproduction."),
        ("Qui emploie les artistes et les techniciens ?", "MDM. Nous les engageons et faisons les déclarations. Vous recevez un seul contrat et une seule facture."),
        ("Avez-vous une licence d'entrepreneur de spectacles ?", "Oui. MDM, enseigne de Neshama Music, est titulaire du récépissé PLATESV-R-2021-012818."),
        ("Où intervenez-vous ?", "Partout en France."),
        ("Pouvez-vous filmer le spectacle ?", "Oui. MDMProd, la société audiovisuelle du groupe, réalise la captation et le montage."),
    ]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    page("/", "Organisation de spectacles et coproduction | Groupe MDM",
         "MDM organise et coproduit vos spectacles, concerts et galas partout en France : programmation, production, équipes artistiques. Présentez votre projet.",
         main, og_image=f"{SITE}/assets/img/logo-mdmprod-full.png", jsonld=[ORG, faq_ld])


def build_contact():
    main = f"""<section class="page-head">
  <div class="wrap stack stack--center center narrow">
    <p class="eyebrow">Contact</p>
    <h1>Parlons de votre projet.</h1>
    <p class="lead">Un spectacle, un concert, un gala ou une vidéo ? Décrivez-le en quelques lignes, ou appelez-nous.</p>
  </div>
</section>
<section class="band" style="padding-top: 0;">
  <div class="wrap">
    {contact_block()}
  </div>
</section>"""
    page("/nous-contacter", "Contact MDM & MDMProd | Spectacle et audiovisuel",
         "Un spectacle, un concert, un gala ou un projet vidéo ? Contactez MDM et MDMProd, partout en France : 01 82 28 99 60 ou contact@mdmprod.fr.",
         main, current="/nous-contacter", jsonld=[ORG])


def article(eyebrow, title, lead, meta, cover, body_html, related=None):
    cov = ""
    if cover and cover.get("url"):
        cov = (f'<figure class="wrap cover"><img src="{esc(img_url(cover["url"]))}" alt="{esc(cover.get("alt", ""))}" '
               f'width="1600" height="1067" fetchpriority="high"></figure>')
    rel = ""
    if related:
        items = "".join(f'<li><a href="{esc(local(u))}">{esc(t)}</a></li>' for t, u in related)
        rel = f'<nav class="wrap related" aria-label="À lire aussi"><h2>À lire aussi</h2><ul>{items}</ul></nav>'
    meta_html = f'<p class="meta">{esc(meta)}</p>' if meta else ""
    return f"""<article>
<header class="page-head">
  <div class="wrap stack stack--center center narrow">
    <p class="eyebrow">{esc(eyebrow)}</p>
    <h1>{esc(title)}</h1>
    <p class="lead">{esc(lead)}</p>
    {meta_html}
  </div>
</header>
{cov}
<div class="wrap"><div class="prose">
{body_html}
</div></div>
{rel}
</article>
{cta_band()}"""


def card(href, img, title, text, meta=""):
    im = f'<img src="{esc(img_url(img["url"], 800))}" alt="{esc(img.get("alt", ""))}" loading="lazy" width="800" height="533">' if img and img.get("url") else ""
    mt = f'<p class="meta">{esc(meta)}</p>' if meta else ""
    return (f'<a class="card-link" href="{esc(href)}">{im}<div class="card-body">{mt}<h3>{esc(title)}</h3>'
            f'<p>{esc(text)}</p></div></a>')


def build_portfolio():
    data = load("portfolio.json")
    if not data:
        return
    cols = {c["id"]: c for c in data["collections"]}
    by_col = {}
    for p in data["projects"]:
        if p.get("hidden"):
            continue
        for cid in p.get("collectionIds", []):
            col = cols.get(cid)
            if not col:
                continue
            path = f"/portfolio-collections/{col['slug']}/{p['slug']}"
            by_col.setdefault(cid, []).append((path, p))
            related = []
            for d in p.get("details", []):
                if d.get("linkUrl"):
                    related.append((d.get("linkText") or d.get("label"), d["linkUrl"]))
            eyebrow = "Spectacle vivant · MDM" if "spectacle" in p["slug"] or col["slug"] == "emploi-intermittents" else "Vidéo · MDMProd"
            if p["slug"] in ("production-deleguee",):
                eyebrow = "Production déléguée"
            main = article(eyebrow, p["title"], p.get("seoDescription", ""), "", p.get("cover"),
                           text_to_html(p.get("description", "")), related)
            page(path, p.get("seoTitle") or p["title"], p.get("seoDescription", ""), main,
                 current="/realisations", og_image=(p.get("cover") or {}).get("url"), jsonld=[ORG])
    # pages collections + hub /realisations
    sections = []
    for cid, items in by_col.items():
        col = cols[cid]
        cards = "".join(card(path, p.get("cover"), p["title"], p.get("seoDescription", "")) for path, p in items)
        block = f'<h2 class="section-title">{esc(col["title"])}</h2><div class="cards">{cards}</div>'
        sections.append(block)
        main = f"""<section class="page-head"><div class="wrap stack stack--center center narrow">
<p class="eyebrow">Prestations</p><h1>{esc(col['title'])}</h1>
<p class="lead">{esc(col.get('description') or '')}</p></div></section>
<section class="band" style="padding-top: 0;"><div class="wrap"><div class="cards">{cards}</div></div></section>
{cta_band()}"""
        page(f"/portfolio-collections/{col['slug']}", f"{col['title']} | MDM & MDMProd",
             col.get("description") or col["title"], main, current="/realisations")
    main = f"""<section class="page-head"><div class="wrap stack stack--center center narrow">
<p class="eyebrow">Prestations</p><h1>Ce que nous faisons.</h1>
<p class="lead">MDM organise et produit vos spectacles. MDMProd filme vos spectacles et réalise vos vidéos. Partout en France.</p></div></section>
<section class="band" style="padding-top: 0;"><div class="wrap">{''.join(sections)}</div></section>
{cta_band()}"""
    page("/realisations", "Organisation de spectacles et prestations audiovisuelles | Groupe MDM",
         "MDM organise vos concerts, galas et spectacles partout en France. MDMProd réalise les captations et vidéos associées. Présentez votre projet.",
         main, current="/realisations", jsonld=[ORG])


def build_blog():
    data = load("blog.json")
    if not data:
        return
    posts = sorted(data["posts"], key=lambda p: p["firstPublishedDate"], reverse=True)
    cards = []
    for p in posts:
        path = f"/post/{p['slug']}"
        meta = f"{date_fr(p['firstPublishedDate'])} · {p.get('minutesToRead', 2)} min de lecture"
        main = article("Blog", p["title"], p.get("excerpt", ""), meta, p.get("cover"), p["html"])
        ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
              "datePublished": p["firstPublishedDate"], "dateModified": p.get("lastPublishedDate"),
              "author": {"@type": "Organization", "name": "MDMProd"},
              "publisher": {"@type": "Organization", "name": "MDMProd"},
              "mainEntityOfPage": f"{SITE}{path}"}
        if (p.get("cover") or {}).get("url"):
            ld["image"] = p["cover"]["url"]
        page(path, p.get("seoTitle") or p["title"], p.get("seoDescription") or p.get("excerpt", ""), main,
             current="/blog", og_image=(p.get("cover") or {}).get("url"), jsonld=[ld])
        cards.append(card(path, p.get("cover"), p["title"], p.get("excerpt", ""), meta))
    main = f"""<section class="page-head"><div class="wrap stack stack--center center narrow">
<p class="eyebrow">Blog</p><h1>Conseils et méthodes.</h1>
<p class="lead">Faire jouer des artistes, organiser une date, préparer une captation : nos repères pour réussir votre projet.</p></div></section>
<section class="band" style="padding-top: 0;"><div class="wrap"><div class="cards">{''.join(cards)}</div></div></section>
{cta_band()}"""
    page("/blog", "Blog MDM & MDMProd : spectacle, vidéo et intermittents",
         "Conseils pour faire jouer des artistes et produire une vidéo : qui est l'employeur, quels contrats, comment présenter votre date.",
         main, current="/blog")


def build_static_pages():
    data = load("pages.json") or {}
    for p in data.get("pages", []):
        main = article(p.get("eyebrow", ""), p["h1"], p.get("lead", ""), "", None, p["html"], p.get("related"))
        page(p["path"], p["title"], p["description"], main, current=p.get("current"),
             jsonld=[ORG], index=p.get("index", True))


def build_404():
    main = f"""<section class="page-head" style="padding-bottom: 120px;"><div class="wrap stack stack--center center narrow">
<p class="eyebrow">Erreur 404</p><h1>Cette page n'existe plus.</h1>
<p class="lead">Elle a peut-être changé d'adresse.</p>
<div class="actions"><a class="pill" href="/">Retour à l'accueil</a><a class="more" href="/nous-contacter">Nous contacter</a></div>
</div></section>"""
    page("/404", "Page introuvable | MDMProd", "Cette page n'existe plus.", main, index=False)
    (DIST / "404.html").write_text((DIST / "404" / "index.html").read_text(encoding="utf-8"), encoding="utf-8")


def finish():
    shutil.copytree(ASSETS, DIST / "assets", dirs_exist_ok=True)
    shutil.copy(SRC / "site.css", DIST / "assets" / "site.css")
    shutil.copy(SRC / "site.js", DIST / "assets" / "site.js")
    if PREVIEW:
        (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    else:
        (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{SITE}{p}</loc></url>" for p in SITEMAP)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8")
    zpath = ROOT / "release" / "site.zip"
    zpath.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(DIST.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(DIST).as_posix())
    print(f"{len(SITEMAP)} pages indexables, zip {zpath.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    build_home()
    build_contact()
    build_portfolio()
    build_blog()
    build_static_pages()
    build_404()
    finish()
