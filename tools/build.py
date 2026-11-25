"""Build the static site in site/ from data/ (texts and photos read from the old Wix site).

    python tools/build.py

Every page is real HTML (good for Google), with the same look and smooth
transitions between pages. Change DOMAIN once the site has its own address.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DOMAIN = "https://www.maria-aiach-architecte.fr"   # to change for the real address

import hashlib
ASSET_V = hashlib.md5(b"".join((SITE / "assets" / f).read_bytes() for f in ("style.css", "site.js"))).hexdigest()[:8]  # new value when CSS/JS change: browsers reload them

source = json.loads((ROOT / "data" / "source.json").read_text("utf-8"))
images = json.loads((ROOT / "data" / "images.json").read_text("utf-8"))
raw = json.loads((ROOT / "data" / "raw" / "site.json").read_text("utf-8"))
GROUPS = {g["key"]: g for g in source["groups"]}

NAME = "Maria Aiach"
PHONE = "06 14 46 06 62"
PHONE_INTL = "+33614460662"
EMAIL = "maria.aiach@gmail.com"
ADDRESS = ("9, rue de l'Amiral Roussin", "75015 Paris")
SIRET = "888 747 920 000 13"

# ---------------------------------------------------------------- projects
# kind: complete | partial | studio | plans
PROJECTS = [
    # order shown on the site: the most beautiful first, Le Parc de Redoute (plans only) last
    dict(slug="paris-7-rue-oudinot", key="1er-projet", name="Rue Oudinot",
         place="Paris 7e", surface="139 m²", year="2020", duration="3 mois", kind="complete", cover=1,
         summary="Rénovation d'un appartement de cinq pièces, parquet massif d'origine conservé."),
    dict(slug="vanves-allee-du-progres", key="copie-de-rue-ledion-75014", name="Allée du Progrès",
         place="Vanves", surface="42 m²", year="2021", duration="1 mois", kind="partial", cover=12,
         summary="Après un dégât des eaux : solives remplacées, plancher isolé, parquet massif neuf."),
    dict(slug="paris-14-rue-ledion", key="2e-projet", name="Rue Ledion",
         place="Paris 14e", surface="68 m²", year="2019", duration="2 mois", kind="complete", cover=3,
         summary="Rénovation complète d'un trois pièces, placards sur mesure dans chaque pièce."),
    dict(slug="paris-7-rue-oudinot-studette", key="copie-de-rue-de-tocqueville-75017", name="Rue Oudinot, studette",
         place="Paris 7e", surface="13 m² + terrasse", year="2020", duration="2 semaines", kind="studio", cover=0,
         summary="Une studette et sa terrasse de 10 m² sur les toits de Paris, rénovées en deux semaines."),
    dict(slug="paris-15-rue-lacretelle", key="copie-de-av-de-fontainebleau-94-krem", name="Rue Lacretelle",
         place="Paris 15e", surface="50 m²", year="2021", duration="3 mois et demi", kind="complete", cover=8,
         summary="Rénovation énergétique de qualité : chaque centimètre carré est exploité."),
    dict(slug="paris-15-rue-de-l-amiral-roussin", key="4e-projet", name="Rue de l'Amiral Roussin",
         place="Paris 15e", surface="78 m²", year="2013", duration="3 mois", kind="complete", cover=0,
         summary="Deux appartements réunis en un, et des portes coulissantes en métal découpées au laser."),
    dict(slug="colombes-rue-de-stalingrad", key="copie-de-rue-cotentin-75015", name="Rue de Stalingrad",
         place="Colombes", surface="76 m²", year="2020", duration="2 mois et demi", kind="complete", cover=12,
         summary="Un quatre pièces devient un cinq pièces pour une colocation de quatre personnes."),
    dict(slug="paris-16-avenue-de-versailles", key="5e-projet", name="Avenue de Versailles",
         place="Paris 16e", surface="58 m²", year="2019", duration="3 mois", kind="partial", cover=4,
         summary="Un grand deux pièces rénové en vue d'une location."),
    dict(slug="paris-15-rue-blomet", key="copie-de-rue-oudinot-studio-75007", name="Rue Blomet",
         place="Paris 15e", surface="13 m²", year="2020", duration="2 mois et demi", kind="studio", cover=0,
         summary="Un studio aux poutres apparentes, entièrement repensé et rénové thermiquement."),
    dict(slug="boulogne-rue-de-heyrault", key="copie-de-rue-de-l-amiral-roussin-6ème-1", name="Rue de Heyrault",
         place="Boulogne-Billancourt", surface="62 m²", year="2024", duration="4 mois", kind="complete", cover=1, crop=(0.515, 0, 1.0, 0.945),
         summary="Rénovation totale d'un trois pièces, création d'une cuisine ouverte sur double séjour."),
    dict(slug="paris-15-place-cherioux", key="copie-de-issy-les-moulineaux-92130-2", name="Place Chérioux",
         place="Paris 15e", surface="17 m² + 4 m²", year="2024", duration="3 mois", kind="studio", cover=2, crop=(0.01, 0.01, 0.745, 0.915),
         summary="Une loge de gardien devient un studio, avec mezzanine, salle de bains, kitchenette et buanderie."),
    dict(slug="paris-6-rue-de-fleurus", key="copie-de-place-du-tertre-75018", name="Rue de Fleurus",
         place="Paris 6e", surface="12 m²", year="2021", duration="", kind="studio", cover=14,
         summary="Un studio près du jardin du Luxembourg, entièrement refait : pas un centimètre carré perdu."),
    dict(slug="kremlin-bicetre-avenue-de-fontainebleau", key="copie-de-rue-fleurus-75006", name="Avenue de Fontainebleau",
         place="Le Kremlin-Bicêtre", surface="30 m²", year="2021", duration="6 semaines", kind="studio", cover=15,
         summary="Un studio au dixième étage : cuisine, salle de bains et nouvelles fenêtres, loué aussitôt."),
    dict(slug="paris-17-rue-de-tocqueville", key="6e-projet", name="Rue de Tocqueville",
         place="Paris 17e", surface="61 m²", year="2016", duration="6 semaines", kind="partial", cover=1,
         summary="Un trois pièces mis en valeur avec un budget minimum, en vue de sa vente."),
    dict(slug="paris-15-place-violet", key="copie-de-3e-projet", name="Place Violet",
         place="Paris 15e", surface="73 m²", year="2004", duration="3 mois", kind="complete", cover=0,
         summary="Un trois pièces optimisé pour une famille de quatre : le mieux conçu de l'immeuble."),
    dict(slug="paris-15-rue-de-l-amiral-roussin-sous-les-toits", key="copie-de-rue-oudinot-75007", name="Rue de l'Amiral Roussin, 6e étage",
         place="Paris 15e", surface="23 m²", year="2022", duration="1 mois", kind="partial", cover=8,
         summary="Un deux pièces sous les combles isolé par l'intérieur : ni trop chaud l'été, ni trop froid l'hiver."),
    dict(slug="paris-16-rue-montevideo", key="copie-de-rue-oudinot-75007-1", name="Rue Montevideo",
         place="Paris 16e", surface="9,20 m²", year="2024", duration="1 mois", kind="studio", cover=0, crop=(0.39, 0.03, 0.975, 0.895),
         summary="Rénovation complète d'une studette, pour des propriétaires installés à Hong Kong."),
    dict(slug="fort-de-france-le-parc-de-redoute", key="copie-de-issy-les-moulineaux-92130", name="Le Parc de Redoute",
         place="Fort-de-France, Martinique", surface="51 m²", year="2023", duration="Plans et descriptif", kind="plans", cover=0,
         summary="Un plan repensé pour une retraite confortable : salle de bains, cuisine et chambre accessibles."),
]
KINDS = {"complete": "Rénovation complète", "partial": "Rénovation partielle", "studio": "Studio", "plans": "Plans et conception"}

GARDENS = [
    dict(slug="jardin-partage-rue-de-l-amiral-roussin", key="copie-de-l-art", name="Le jardin partagé",
         place="Rue de l'Amiral Roussin, Paris 15e", surface="400 m²", year="Depuis 2018",
         summary="Un terrain abandonné depuis quatorze ans devenu un jardin partagé par une vingtaine de voisins."),
    dict(slug="cour-interieure-rue-de-l-amiral-roussin", key="copie-de-espace-paysager-le-jardin", name="La cour intérieure",
         place="Rue de l'Amiral Roussin, Paris 15e", surface="40 m²", year="Depuis 2013",
         summary="Une cour à l'abandon transformée en espace fleuri, et des fenêtres en avalanche de couleurs."),
    dict(slug="cour-privee-avenue-du-maine", key="copie-de-espace-paysager-cour-place", name="Cour privée, avenue du Maine",
         place="Paris 14e", surface="100 m²", year="Projet",
         summary="Une cour spacieuse et secrète, pensée en plusieurs recoins : bacs, grimpantes, lumière."),
]

HERO = [  # (project slug, item index) : the opening slideshow.
    # Chosen only on how attractive the photo is full screen: light, space, finishes.
    # Rue Oudinot's large living room always first (asked by Raf on 2026-11-25).
    ("paris-7-rue-oudinot", 1), ("paris-14-rue-ledion", 3), ("paris-16-avenue-de-versailles", 4),
    ("paris-7-rue-oudinot", 3), ("vanves-allee-du-progres", 12), ("paris-7-rue-oudinot", 2),
]

SKIP_CAPTION = {"", ".", "wix issy copy", "boulogne 3", "boulogne 4", "vu", "test"}

# --------------------------------------------------------------- helpers
E = html.escape


def items_of(key):
    out = []
    for idx, it in enumerate(GROUPS.get(key, {"items": []})["items"]):
        info = images.get(it["uri"])
        if not info or "file" not in info:
            continue
        cap = re.sub(r"\s+", " ", (it.get("title") or "").strip())
        if cap.lower() in SKIP_CAPTION:
            cap = ""
        cap = cap[:1].upper() + cap[1:]
        is_plan = info["drawing"] or bool(re.search(r"\bplans?\b|croquis|calpinage", cap, re.I))
        out.append(dict(idx=idx, file=info["file"], w=info["w"], h=info["h"], lqip=info["lqip"], cap=cap, plan=is_plan))
    return out


def img(it, sizes="100vw", cls="", eager=False, vt=None, alt=None):
    src = f"/img/{it['file']}-1000.webp"
    srcset = f"/img/{it['file']}-1000.webp 1000w, /img/{it['file']}-2000.webp 2000w"
    style = f"background-image:url({it['lqip']});"
    if vt:
        style += f"view-transition-name:{vt};"
    return (f'<img class="ph {cls}" src="{src}" srcset="{srcset}" sizes="{sizes}" width="{it["w"]}" height="{it["h"]}" '
            f'alt="{E(alt if alt is not None else it["cap"])}" style="{style}" '
            f'{"fetchpriority=high" if eager else "loading=lazy"} decoding="async">')


JUNK = re.compile(r"press to zoom|Voir les créations|SIRET|^rue de l'amiral Roussin 6ème étage$|mariaaiach\.wixsite|^\s*​\s*$", re.I)


def description(key, meta_words=()):
    """Her own text for a page, without the Wix menu, the gallery captions and the facts shown elsewhere."""
    paras = []
    for line in raw.get(key, {}).get("text", []):
        line = line.replace("​", "").strip()
        if "Retourner à la page d'accueil" in line:
            line = line.split("Retourner à la page d'accueil", 1)[1].strip()
        line = re.sub(r"SIRET.*$", "", line).strip()
        if not line or JUNK.search(line):
            continue
        short = len(line) < 45 and not line.endswith(":") and not line.startswith("-")
        if short:
            continue
        line = re.sub(r"\s{2,}", " ", line)
        line = re.sub(r"\s+([:;!?])", " \\1", line)  # French spacing
        paras.append(line)
    return paras


def paragraphs_html(paras):
    out, bullets = [], []
    def flush():
        if bullets:
            out.append("<ul>" + "".join(f"<li>{E(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()
    for p in paras:
        if p.startswith("-"):
            bullets.append(p.lstrip("- ").strip())
            continue
        flush()
        if p.endswith(":") and len(p) < 60:
            out.append(f"<h3>{E(p.rstrip(':').strip())}</h3>")
        else:
            out.append(f"<p>{E(p)}</p>")
    flush()
    return "\n".join(out)


def layout(*, title, description_text, path, body, cls="", jsonld=None, image=None):
    canonical = DOMAIN + path
    og_image = f"{DOMAIN}/img/{image}-2000.webp" if image else ""
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add("js")</script>
<title>{E(title)}</title>
<meta name="description" content="{E(description_text)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description_text)}">
<meta property="og:url" content="{canonical}">
{f'<meta property="og:image" content="{og_image}">' if og_image else ''}
<meta name="theme-color" content="#f3f0ea">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/CormorantGaramond-normal-500.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/Manrope-normal-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/style.css?v={ASSET_V}">
{ld}
</head>
<body class="{cls}">
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="top" data-top>
  <a class="brand" href="/" aria-label="{NAME}, accueil"><span class="brand-name">Maria Aiach</span><span class="brand-role">Architecte DPLG</span></a>
  <nav class="nav" aria-label="Menu principal">
    <a href="/#projets">Projets</a><a href="/#approche">Approche</a><a href="/#paysages">Paysages</a><a href="/art/">Art</a><a href="/#contact" class="nav-cta">Contact</a>
  </nav>
  <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" data-menu-btn><span></span><span></span><span class="sr">Menu</span></button>
</header>
<div class="menu" id="menu" data-menu hidden>
  <nav aria-label="Menu">
    <a href="/#projets">Projets</a><a href="/#approche">Approche</a><a href="/#apropos">À propos</a><a href="/#paysages">Paysages</a><a href="/art/">Art</a><a href="/#contact">Contact</a>
  </nav>
  <p class="menu-foot"><a href="tel:{PHONE_INTL}">{PHONE}</a><br><a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div>
<main id="contenu">
{body}
</main>
{footer()}
<div class="lightbox" data-lightbox hidden>
  <button class="lb-close" type="button" data-lb-close aria-label="Fermer">Fermer</button>
  <figure class="lb-figure"><img alt="" data-lb-img><figcaption data-lb-cap></figcaption></figure>
  <button class="lb-prev" type="button" data-lb-prev aria-label="Photo précédente"><span aria-hidden="true">←</span></button>
  <button class="lb-next" type="button" data-lb-next aria-label="Photo suivante"><span aria-hidden="true">→</span></button>
  <p class="lb-count" data-lb-count></p>
</div>
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


def footer():
    return f"""<footer class="foot" id="contact">
  <div class="foot-inner">
    <p class="eyebrow">Contact</p>
    <h2 class="foot-title reveal">Parlons de votre<br><em>appartement.</em></h2>
    <div class="foot-grid">
      <div class="reveal"><p class="label">Téléphone</p><a class="big-link" href="tel:{PHONE_INTL}">{PHONE}</a></div>
      <div class="reveal"><p class="label">E-mail</p><a class="big-link" href="mailto:{EMAIL}">{EMAIL}</a></div>
      <div class="reveal"><p class="label">Atelier</p><p class="addr">{E(ADDRESS[0])}<br>{ADDRESS[1]}</p></div>
    </div>
    <div class="foot-legal">
      <p>© {date.today().year} Maria Aiach, architecte DPLG · SIRET {SIRET}</p>
      <p><a href="/mentions-legales/">Mentions légales</a></p>
    </div>
  </div>
</footer>"""


def meta_row(p):
    cells = [("Lieu", p["place"]), ("Surface", p["surface"]), ("Année", p["year"])]
    if p.get("duration"):
        cells.append(("Chantier" if "mois" in p["duration"] or "semaine" in p["duration"] else "Mission", p["duration"]))
    if p.get("kind"):
        cells.append(("Type", KINDS[p["kind"]]))
    return '<dl class="facts">' + "".join(f"<div><dt>{a}</dt><dd>{E(b)}</dd></div>" for a, b in cells) + "</dl>"


def gallery_html(items):
    """Editorial rhythm: a wide landscape photo alone, portraits side by side."""
    photos = [i for i in items if not i["plan"]]
    out, row = [], []
    for it in photos:
        landscape = it["w"] / it["h"] > 1.25
        if landscape:
            if row:
                out.append(row)
                row = []
            out.append([it])
        else:
            row.append(it)
            if len(row) == 2:
                out.append(row)
                row = []
    if row:
        out.append(row)
    html_rows = []
    for r in out:
        cls = "g-row one" if len(r) == 1 else "g-row two"
        if len(r) == 1 and r[0]["w"] / r[0]["h"] <= 1.25:
            cls = "g-row single-portrait"
        figs = "".join(
            f'<figure class="g-fig reveal"><button class="g-open" type="button" data-lb-item>{img(it, "(max-width: 760px) 100vw, 50vw" if len(r) == 2 else "100vw")}</button>'
            + (f"<figcaption>{E(it['cap'])}</figcaption>" if it["cap"] else "") + "</figure>"
            for it in r)
        html_rows.append(f'<div class="{cls}">{figs}</div>')
    return "\n".join(html_rows)


def plans_html(items):
    plans = [i for i in items if i["plan"]]
    if not plans:
        return ""
    figs = "".join(
        f'<figure class="plan reveal"><button class="g-open" type="button" data-lb-item>{img(it, "(max-width: 760px) 100vw, 50vw")}</button>'
        + (f"<figcaption>{E(it['cap'])}</figcaption>" if it["cap"] else "") + "</figure>" for it in plans)
    return f'<section class="plans" aria-labelledby="plans-t"><div class="wrap"><p class="eyebrow" id="plans-t">Plans et dessins</p><div class="plans-grid" data-lb-group>{figs}</div></div></section>'


def cropped_cover(slug, it, box):
    """A cover cut out of a photo montage (keeps the photo, drops the captions written on it)."""
    import base64, io
    from PIL import Image
    im = Image.open(SITE / "img" / f"{it['file']}-2000.webp").convert("RGB")
    w, h = im.size
    im = im.crop((round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h)))
    name = f"cover-{slug}"
    for width in (1000, 2000):
        out = im if im.width <= width else im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        out.save(SITE / "img" / f"{name}-{width}.webp", "WEBP", quality=86, method=6)
    tiny = im.resize((24, max(1, round(im.height * 24 / im.width))))
    buf = io.BytesIO(); tiny.save(buf, "WEBP", quality=40)
    return dict(it, file=name, w=im.width, h=im.height, lqip="data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode())


# ------------------------------------------------------------------ pages
for p in PROJECTS:
    p["items"] = items_of(p["key"])
    photos = [i for i in p["items"] if not i["plan"]] or p["items"]
    p["cover_item"] = next((i for i in p["items"] if i["idx"] == p["cover"]), photos[0] if photos else None)
    if p.get("crop") and p["cover_item"]:
        p["cover_item"] = cropped_cover(p["slug"], p["cover_item"], p["crop"])
for g in GARDENS:
    g["items"] = items_of(g["key"])
    g["cover_item"] = next((i for i in g["items"] if not i["plan"] and i["w"] >= i["h"]), g["items"][0] if g["items"] else None)


def write(path, text):
    f = SITE / path.strip("/") / "index.html" if not path.endswith(".html") else SITE / path.strip("/")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, "utf-8")


def card(p, i, base="/projets/"):
    c = p["cover_item"]
    pic = img(c, "(max-width: 760px) 92vw, (max-width: 1200px) 46vw, 30vw", vt=f"c-{p['slug']}", alt=f"{p['name']}, {p['place']}") if c else ""
    return f"""<li class="card reveal" data-kind="{p.get('kind','')}" style="--i:{i % 3}">
  <a href="{base}{p['slug']}/" data-preview="/img/{c['file']}-1000.webp" >
    <div class="card-media">{pic}</div>
    <div class="card-text">
      <p class="card-place">{E(p['place'])}<span>{E(p['year'])}</span></p>
      <h3 class="card-name">{E(p['name'])}</h3>
      <p class="card-sum">{E(p['summary'])}</p>
      <p class="card-facts">{E(p['surface'])}{' · ' + E(KINDS[p['kind']]) if p.get('kind') else ''}</p>
    </div>
  </a>
</li>"""


def row(p, i):
    c = p["cover_item"]
    return f"""<li class="row reveal" data-kind="{p['kind']}"><a href="/projets/{p['slug']}/" data-preview="/img/{c['file']}-1000.webp">
  <span class="row-year">{E(p['year'])}</span><span class="row-name">{E(p['name'])}</span><span class="row-place">{E(p['place'])}</span><span class="row-surface">{E(p['surface'])}</span><span class="row-kind">{E(KINDS[p['kind']])}</span><span class="row-arrow" aria-hidden="true">→</span>
</a></li>"""


# ---- home
hero_slides = []
for n, (slug, idx) in enumerate(HERO):
    p = next(x for x in PROJECTS if x["slug"] == slug)
    it = next(i for i in p["items"] if i["idx"] == idx)
    hero_slides.append(
        f'<a class="slide{" is-on" if n == 0 else ""}" href="/projets/{slug}/" data-slide data-label="{E(p["name"])} · {E(p["place"])}" tabindex="{0 if n == 0 else -1}">'
        + img(it, "100vw", eager=n == 0, alt=f"{p['name']}, {p['place']}") + "</a>")

filters = '<div class="filters" role="group" aria-label="Filtrer les projets">' + "".join(
    f'<button type="button" class="chip{" is-on" if k == "all" else ""}" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{v}<sup>{n}</sup></button>'
    for k, v, n in [("all", "Tous", len(PROJECTS))] + [(k, v, sum(1 for p in PROJECTS if p["kind"] == k)) for k, v in KINDS.items()]
) + "</div>"

home_body = f"""
<section class="hero" aria-label="Projets récents">
  <div class="slides" data-slides>{''.join(hero_slides)}</div>
  <div class="hero-shade" aria-hidden="true"></div>
  <div class="hero-text">
    <p class="eyebrow light">Architecte DPLG · Paris</p>
    <h1 class="hero-title"><span class="line"><span>Rénover,</span></span><span class="line"><span><em>sans perdre</em></span></span><span class="line"><span>un centimètre.</span></span></h1>
  </div>
  <div class="hero-foot">
    <a class="hero-label" href="/projets/{HERO[0][0]}/" data-slide-label>{E(next(x for x in PROJECTS if x['slug']==HERO[0][0])['name'])}</a>
    <div class="hero-dots" data-dots>{''.join(f'<button type="button" aria-label="Photo {n+1}"{" class=is-on" if n == 0 else ""}><i></i></button>' for n in range(len(HERO)))}</div>
    <a class="hero-scroll" href="#intro">Découvrir <span aria-hidden="true">↓</span></a>
  </div>
</section>

<section class="intro wrap" id="intro">
  <p class="eyebrow reveal">L'atelier</p>
  <p class="statement reveal">Je conçois et je mène la rénovation de votre appartement, <em>clé en main</em> : du plan idéal au choix des matériaux, de la lumière aux placards sur mesure, jusqu'à la remise des clés.</p>
  <div class="numbers">
    <div class="reveal"><p class="num">20<small> ans</small></p><p class="num-label">en agence d'architecture</p></div>
    <div class="reveal"><p class="num">82</p><p class="num-label">projets menés en agence</p></div>
    <div class="reveal"><p class="num">6<small> ans</small></p><p class="num-label">architecte indépendante</p></div>
    <div class="reveal"><p class="num">20</p><p class="num-label">projets menés en indépendante</p></div>
  </div>
</section>

<section class="ba wrap" aria-labelledby="ba-t">
  <div class="section-head">
    <h2 class="section-title reveal" id="ba-t">Avant, <em>après.</em></h2>
    <p class="section-intro reveal">Rue de Heyrault, Boulogne-Billancourt : 62 m² entièrement rénovés, cuisine ouverte sur double séjour. Faites glisser pour voir la transformation.</p>
  </div>
  <div class="ba-frame reveal" data-ba style="aspect-ratio:{{BA_W}}/{{BA_H}};--ar:{{BA_AR}}">
    <img class="ba-img" src="/img/ba-after-2000.webp" alt="Après travaux : cuisine ouverte et double séjour" loading="lazy" decoding="async">
    <div class="ba-before"><img class="ba-img" src="/img/ba-before-2000.webp" alt="Avant travaux" loading="lazy" decoding="async"></div>
    <div class="ba-handle"><span>Glisser</span></div>
    <p class="ba-tag l">Avant</p><p class="ba-tag r">Après</p>
    <input class="ba-range" type="range" min="0" max="100" value="50" aria-label="Comparer avant et après" data-ba-range>
  </div>
  <p class="ba-link reveal"><a class="text-link" href="/projets/boulogne-rue-de-heyrault/">Voir le projet <span aria-hidden="true">→</span></a></p>
</section>

<section class="projects" id="projets" aria-labelledby="projets-t">
  <div class="wrap">
    <div class="section-head">
      <h2 class="section-title reveal" id="projets-t">Projets</h2>
      <div class="tools">
        {filters}
        <div class="views" role="group" aria-label="Affichage">
          <button type="button" class="view is-on" data-view="grid" aria-pressed="true">Galerie</button>
          <button type="button" class="view" data-view="list" aria-pressed="false">Liste</button>
        </div>
      </div>
    </div>
    <ul class="grid" data-grid>{''.join(card(p, i) for i, p in enumerate(PROJECTS))}</ul>
    <ul class="list" data-list hidden>{''.join(row(p, i) for i, p in enumerate(PROJECTS))}</ul>
  </div>
  <div class="cursor-preview" aria-hidden="true" data-cursor><img alt=""></div>
</section>

<section class="approach" id="approche" aria-labelledby="approche-t">
  <div class="wrap">
    <p class="eyebrow reveal">Approche</p>
    <h2 class="section-title reveal" id="approche-t">Une seule interlocutrice, <em>du premier croquis aux clés.</em></h2>
    <ol class="steps">
      <li class="reveal"><span class="step-n">01</span><h3>Le plan idéal</h3><p>Relevé de l'existant, puis plusieurs versions du plan jusqu'à la bonne : chaque mètre carré trouve son usage.</p></li>
      <li class="reveal"><span class="step-n">02</span><h3>La conception détaillée</h3><p>Matériaux, éclairage, cuisine, salle de bains, placards dessinés sur mesure, plans d'électricité.</p></li>
      <li class="reveal"><span class="step-n">03</span><h3>Les entreprises</h3><p>Consultation des artisans, analyse et négociation des devis. Je connais les prix justes : vous réalisez des économies importantes.</p></li>
      <li class="reveal"><span class="step-n">04</span><h3>Le chantier</h3><p>Direction des travaux, compte rendu chaque semaine, relations avec le syndic et la copropriété. Les délais sont tenus.</p></li>
    </ol>
    <div class="promise reveal">
      <p class="promise-title">Je dépense votre argent comme si c'était le mien.</p>
      <p class="promise-text">Chaque devis est relu, discuté et négocié : pas de supplément injustifié, pas de travaux superflus. Sur de nombreux chantiers, cette vigilance a permis des économies importantes.</p>
    </div>
  </div>
</section>

<section class="about" id="apropos" aria-labelledby="apropos-t">
  <div class="wrap about-grid">
    <div class="about-media reveal">{img(next(p for p in PROJECTS if p['slug']=='paris-15-rue-de-l-amiral-roussin')['items'][0], '(max-width: 760px) 100vw, 40vw', alt="Porte coulissante en métal découpée au laser, dessinée par Maria Aiach")}<p class="media-cap">Porte coulissante en métal découpée au laser, dessinée d'après l'horloge de la cathédrale de Milan. Rue de l'Amiral Roussin, 2013.</p></div>
    <div class="about-text">
      <p class="eyebrow reveal">À propos</p>
      <h2 class="section-title reveal" id="apropos-t">Maria Aiach</h2>
      <p class="reveal">Je travaille comme architecte depuis 2001 en agence d'architecture, principalement sur la conception de logements neufs, du permis de construire aux plans d'exécution.</p>
      <p class="reveal">Parallèlement, j'ai rénové une quinzaine d'appartements. J'aime le chantier, l'échange avec les artisans et les clients. Je suis organisée, rapide, réactive, rigoureuse et à l'écoute de chacun.</p>
      <p class="reveal">Depuis fin 2020, je suis installée à mon compte. Je pratique des prix raisonnables et je m'assure que les délais soient tenus.</p>
      <p class="reveal"><a class="text-link" href="#contact">Me contacter <span aria-hidden="true">→</span></a></p>
    </div>
  </div>
</section>

<section class="gardens" id="paysages" aria-labelledby="paysages-t">
  <div class="wrap">
    <div class="section-head">
      <h2 class="section-title reveal" id="paysages-t">Espaces <em>paysagers</em></h2>
      <p class="section-intro reveal">Conseils de jardinage et accompagnement sur mesure : ensemble, nous choisissons les végétaux qui égaieront votre extérieur.</p>
    </div>
    <ul class="grid gardens-grid">{''.join(card(g, i, base='/paysages/') for i, g in enumerate(GARDENS))}</ul>
  </div>
</section>
"""

ART_ITEMS = items_of("copie-de-je-me-presente-1")
if ART_ITEMS:
    strip = "".join(f'<li>{img(it, "(max-width:760px) 60vw, 22vw", alt="Œuvre de Maria Aiach")}</li>' for it in ART_ITEMS[:14])
    home_body += f"""
<section class="art-teaser" aria-labelledby="art-t">
  <div class="wrap section-head">
    <h2 class="section-title reveal" id="art-t">L'art, <em>à côté</em></h2>
    <p class="section-intro reveal">Dessin, peinture, céramique, bois, aquarelle, photographie. Un moment où le temps s'arrête.</p>
  </div>
  <ul class="strip" data-strip>{strip}</ul>
  <div class="wrap"><a class="text-link reveal" href="/art/">Voir les œuvres <span aria-hidden="true">→</span></a></div>
</section>"""

LD_BUSINESS = {
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "name": "Maria Aiach, architecte DPLG",
    "description": "Architecte DPLG à Paris : rénovation d'appartements clé en main, conception de plans, direction de travaux.",
    "url": DOMAIN + "/",
    "telephone": PHONE_INTL,
    "email": EMAIL,
    "address": {"@type": "PostalAddress", "streetAddress": ADDRESS[0], "postalCode": "75015", "addressLocality": "Paris", "addressCountry": "FR"},
    "areaServed": ["Paris", "Hauts-de-Seine", "Val-de-Marne"],
    "founder": {"@type": "Person", "name": NAME, "jobTitle": "Architecte DPLG"},
    "knowsAbout": ["Rénovation d'appartement", "Architecture d'intérieur", "Rénovation énergétique", "Direction de travaux"],
}

def before_after():
    """Cut the Heyrault before/after montage into two equal photos for the slider."""
    from PIL import Image
    p = next(x for x in PROJECTS if x["slug"] == "boulogne-rue-de-heyrault")
    it = next(i for i in p["items"] if i["idx"] == 1)
    im = Image.open(SITE / "img" / f"{it['file']}-2000.webp").convert("RGB")
    w, h = im.size
    left = im.crop((0, 0, round(.502 * w), round(.945 * h)))
    right = im.crop((round(.512 * w), 0, w, round(.945 * h))).resize(left.size, Image.LANCZOS)
    left.save(SITE / "img" / "ba-before-2000.webp", "WEBP", quality=88, method=6)
    right.save(SITE / "img" / "ba-after-2000.webp", "WEBP", quality=88, method=6)
    return left.size


BA_W, BA_H = before_after()
home_body = home_body.replace("{BA_W}", str(BA_W)).replace("{BA_H}", str(BA_H)).replace("{BA_AR}", f"{BA_W / BA_H:.4f}")

write("/", layout(
    title="Maria Aiach, architecte DPLG à Paris · Rénovation d'appartements",
    description_text="Maria Aiach, architecte DPLG à Paris 15e : rénovation d'appartements clé en main, du plan idéal à la remise des clés. Studios, familles, cabinets.",
    path="/", body=home_body, cls="home over-dark", jsonld=LD_BUSINESS, image=PROJECTS[0]["cover_item"]["file"]))

# ---- project pages
def detail_page(p, base, idx, collection, label):
    prev_p = collection[idx - 1] if idx > 0 else collection[-1]
    next_p = collection[(idx + 1) % len(collection)]
    c = p["cover_item"]
    paras = description(p["key"])
    nxt = next_p["cover_item"]
    body = f"""
<article class="project">
  <header class="p-hero">
    <div class="p-hero-media">{img(c, '100vw', eager=True, vt=f"c-{p['slug']}", alt=f"{p['name']}, {p['place']}") if c else ''}</div>
    <div class="p-hero-text wrap">
      <p class="eyebrow light"><a href="{'/#projets' if base == '/projets/' else '/#paysages'}">{label}</a> · {E(p['place'])}</p>
      <h1 class="p-title">{E(p['name'])}</h1>
    </div>
  </header>
  <div class="wrap p-intro">
    {meta_row(p)}
    <div class="p-text">
      <p class="lede reveal">{E(p['summary'])}</p>
      <div class="prose reveal">{paragraphs_html(paras)}</div>
    </div>
  </div>
  <section class="gallery wrap" aria-label="Photos" data-lb-group>
    {gallery_html(p['items'])}
  </section>
  {plans_html(p['items'])}
  <nav class="next" aria-label="Projet suivant">
    <a href="{base}{next_p['slug']}/" class="next-link">
      <div class="next-media">{img(nxt, '100vw', vt=f"c-{next_p['slug']}", alt=f"{next_p['name']}, {next_p['place']}") if nxt else ''}</div>
      <div class="next-text wrap"><p class="eyebrow light">Projet suivant</p><p class="next-title">{E(next_p['name'])}</p><p class="next-place">{E(next_p['place'])}</p></div>
    </a>
    <div class="wrap next-bar"><a href="{base}{prev_p['slug']}/">← {E(prev_p['name'])}</a><a href="{'/#projets' if base == '/projets/' else '/#paysages'}">Tous les projets</a></div>
  </nav>
</article>"""
    ld = {"@context": "https://schema.org", "@type": "CreativeWork", "name": f"{p['name']}, {p['place']}",
          "creator": {"@type": "Person", "name": NAME, "jobTitle": "Architecte DPLG"},
          "dateCreated": re.sub(r"\D.*", "", p["year"]) or None, "description": p["summary"], "locationCreated": p["place"]}
    write(f"{base}{p['slug']}/", layout(
        title=f"{p['name']}, {p['place']} · Maria Aiach, architecte",
        description_text=f"{p['summary']} {p['surface']}, {p['year']}. Un projet de Maria Aiach, architecte DPLG à Paris.",
        path=f"{base}{p['slug']}/", body=body, cls="page-project over-dark", jsonld=ld, image=c["file"] if c else None))


for i, p in enumerate(PROJECTS):
    detail_page(p, "/projets/", i, PROJECTS, "Projets")
for i, g in enumerate(GARDENS):
    detail_page(g, "/paysages/", i, GARDENS, "Espaces paysagers")

# ---- art page
art_figs = "".join(f'<figure class="m-item reveal"><button class="g-open" type="button" data-lb-item>{img(it, "(max-width:760px) 50vw, 25vw", alt="Œuvre de Maria Aiach")}</button></figure>' for it in ART_ITEMS)
write("/art/", layout(
    title="L'art · Maria Aiach, architecte",
    description_text="Dessin, peinture, sculpture, céramique, aquarelle et photographie : les œuvres de Maria Aiach, architecte DPLG à Paris.",
    path="/art/", cls="page-art", body=f"""
<section class="art-head wrap">
  <p class="eyebrow">L'art</p>
  <h1 class="p-title dark">Un besoin, <em>une joie.</em></h1>
  <div class="prose">
    <p>À 24 ans, j'ai été acceptée à deux écoles : l'École d'architecture Paris-Conflans et les Beaux-Arts. J'ai choisi l'architecture, pour un métier sûr, des connaissances techniques et une culture générale précieuse.</p>
    <p>Depuis, je n'ai jamais cessé : dessin, peinture, sculpture, bois, céramique, aquarelle, photographie, montages. Un moment privilégié et précieux, où le temps s'arrête et où le plaisir s'installe.</p>
    <p class="quote">« L'extraordinaire se trouve sur le chemin des gens ordinaires. » <span>Paulo Coelho</span></p>
  </div>
</section>
<section class="masonry wrap" data-lb-group aria-label="Œuvres">{art_figs}</section>
"""))

# ---- legal notice
write("/mentions-legales/", layout(
    title="Mentions légales · Maria Aiach, architecte", description_text="Mentions légales du site de Maria Aiach, architecte DPLG.",
    path="/mentions-legales/", cls="page-art", body=f"""
<section class="art-head wrap legal">
  <p class="eyebrow">Informations</p>
  <h1 class="p-title dark">Mentions légales</h1>
  <div class="prose">
    <h3>Éditrice du site</h3>
    <p>Maria Aiach, architecte DPLG, entreprise individuelle. SIRET {SIRET}.<br>{E(ADDRESS[0])}, {ADDRESS[1]}. Tél. {PHONE}. {EMAIL}</p>
    <h3>Hébergement</h3>
    <p>À compléter avec le nom, l'adresse et le téléphone de l'hébergeur choisi.</p>
    <h3>Photographies et contenus</h3>
    <p>Les photographies, plans et textes sont la propriété de Maria Aiach. Toute reproduction sans autorisation est interdite.</p>
    <h3>Données personnelles</h3>
    <p>Ce site ne dépose aucun cookie et ne collecte aucune donnée. Les polices de caractères sont hébergées sur le site lui-même.</p>
  </div>
</section>"""))

# ---- robots + sitemap
urls = ["/", "/art/", "/mentions-legales/"] + [f"/projets/{p['slug']}/" for p in PROJECTS] + [f"/paysages/{g['slug']}/" for g in GARDENS]
(SITE / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{DOMAIN}{u}</loc></url>\n" for u in urls) + "</urlset>\n", "utf-8")
(SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", "utf-8")
print("built", len(urls), "pages")
