#!/usr/bin/env python3
"""
build.py — generiert statisches HTML aus den Datenquellen.

Quellen:
  data/projects.json   -> index.html: Segmented-Switcher "Meine Arbeit" (Pill + Carousel)
                          projects.html: Tab-Liste "Alle Projekte"
  kunden-logos/        -> kunden-logos/manifest.json + Logo-Marquee (index.html)

Inhalte zwischen Marker-Kommentaren:
  <!-- PROJECTS:INDEX:START -->/<END>, <!-- PROJECTS:LIST:START -->/<END>, <!-- LOGOS:... -->

Alle Projekte stehen statisch im HTML (auch inaktive Tabs/Panels) -> SEO-lesbar.
Videos laden DSGVO-konform erst nach Klick (youtube-nocookie).
"""

import json
import os
import re
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# key, Button-Label, Ziel-/Nutzen-Satz
CATEGORIES = [
    ("imagefilm",  "ImageFilm",
     "Ein ImageFilm erzählt die Geschichte hinter der Marke, schafft Vertrauen und zeigt, wofür ein Unternehmen steht."),
    ("recruiting", "Recruiting",
     "Zeigt euch als Arbeitgeber von der besten Seite und spricht genau die Talente an, die zu euch passen."),
    ("social",     "Social Media",
     "Kurze, schnelle Inhalte für Reichweite und Präsenz im Feed — plattformoptimiert produziert."),
]
DEFAULT_CAT = "imagefilm"

# ---------------------------------------------------------------- helpers
def yt_id(url: str) -> str:
    url = url.strip()
    m = (re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
         or re.search(r"/shorts/([A-Za-z0-9_-]{6,})", url)
         or re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
         or re.search(r"/embed/([A-Za-z0-9_-]{6,})", url))
    if not m:
        raise ValueError(f"Keine YouTube-ID erkannt in: {url}")
    return m.group(1)

def esc(s: str) -> str:
    return html.escape(s or "", quote=True)

def replace_between(text, marker, content, indent="    "):
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"Marker {marker} nicht gefunden.")
    return pattern.sub(f"{start}\n{content}\n{indent}{end}", text)

def pretty_name(filename):
    stem = os.path.splitext(filename)[0]
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", stem) if w)

PLAY_SVG = ('<span class="video-play" aria-hidden="true">'
            '<svg viewBox="0 0 24 24" width="24" height="24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>'
            '</span>')

EMPTY = ('<p class="work-empty">Hier entsteht gerade das erste Beispiel. '
         'Du hast ein Recruiting-Projekt? <a href="#anfragen">Schreib mir.</a></p>')

# ---------------------------------------------------------------- load data
with open(os.path.join(ROOT, "data", "projects.json"), encoding="utf-8") as f:
    projects = json.load(f)
by_cat = {key: [p for p in projects if p.get("category") == key] for key, _, _ in CATEGORIES}

# ---------------------------------------------------------------- index: segmented switcher + carousel
def video_card(p):
    vid = yt_id(p["youtubeUrl"])
    note = f'{esc(p["label"])} · {esc(p["customer"])}'
    return (
f'''            <div class="video-card">
              <button class="video-embed" type="button" data-id="{vid}" data-title="{esc(p["title"])}"
                      aria-label="Video abspielen: {esc(p["title"])}"
                      style="background-image:url('https://img.youtube.com/vi/{vid}/maxresdefault.jpg')">
                {PLAY_SVG}
              </button>
              <p class="video-card-title">{esc(p["title"])}</p>
              <p class="video-card-note">{note}</p>
            </div>''')

def index_block():
    # Switch
    parts = ['      <div class="switch" role="tablist" aria-label="Leistungen">',
             '        <div class="switch-pill" aria-hidden="true"></div>']
    for i, (key, label, _) in enumerate(CATEGORIES):
        active = " is-active" if i == 0 else ""
        sel = "true" if i == 0 else "false"
        parts.append(
            f'        <button class="switch-btn{active}" type="button" role="tab" '
            f'data-i="{i}" aria-selected="{sel}"><span>{esc(label)}</span></button>')
    parts.append('      </div>')
    switch = "\n".join(parts)

    # Carousel
    panels = []
    for key, _, goal in CATEGORIES:
        items = by_cat[key]
        if not items:
            body = EMPTY
        else:
            cards = "\n".join(video_card(p) for p in items)
            body = f'<div class="video-grid">\n{cards}\n          </div>'
        panels.append(
            f'        <div class="work-panel" role="tabpanel">\n'
            f'          <p class="work-goal">{esc(goal)}</p>\n'
            f'          {body}\n'
            f'        </div>')
    carousel = ('      <div class="work-carousel">\n'
                '        <div class="work-track">\n'
                + "\n".join(panels) + "\n"
                '        </div>\n'
                '      </div>')
    return switch + "\n" + carousel

# ---------------------------------------------------------------- projects.html: ruhiges Kategorie-Raster
def list_block():
    blocks = []
    for key, label, goal in CATEGORIES:
        items = by_cat[key]
        if not items:
            body = EMPTY
        else:
            cards = "\n".join(video_card(p) for p in items)
            body = f'<div class="video-grid">\n{cards}\n      </div>'
        blocks.append(
            f'  <section class="work-cat">\n'
            f'    <p class="work-cat-label" data-reveal>{esc(label)}</p>\n'
            f'    <p class="work-cat-goal" data-reveal>{esc(goal)}</p>\n'
            f'    {body}\n'
            f'  </section>')
    return "\n".join(blocks)

# ---------------------------------------------------------------- logos
logo_dir = os.path.join(ROOT, "kunden-logos")
exts = (".svg", ".png", ".jpg", ".jpeg")
logos = sorted(f for f in os.listdir(logo_dir) if f.lower().endswith(exts) and not f.startswith("."))
with open(os.path.join(logo_dir, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(logos, f, ensure_ascii=False, indent=2)
logos_html = "\n".join(
    f'        <img class="marquee-logo" src="kunden-logos/{esc(fn)}" alt="Kunde: {esc(pretty_name(fn))}" loading="lazy" />'
    for fn in logos)

# ---------------------------------------------------------------- write
index_path = os.path.join(ROOT, "index.html")
idx = open(index_path, encoding="utf-8").read()
idx = replace_between(idx, "PROJECTS:INDEX", index_block(), indent="    ")
idx = replace_between(idx, "LOGOS", logos_html, indent="      ")
open(index_path, "w", encoding="utf-8").write(idx)

proj_path = os.path.join(ROOT, "projects.html")
pr = open(proj_path, encoding="utf-8").read()
pr = replace_between(pr, "PROJECTS:LIST", list_block(), indent="  ")
open(proj_path, "w", encoding="utf-8").write(pr)

counts = ", ".join(f"{k}={len(by_cat[k])}" for k, _, _ in CATEGORIES)
print(f"Build OK: {len(projects)} Projekte ({counts}), {len(logos)} Logos.")
