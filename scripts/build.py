#!/usr/bin/env python3
"""
build.py — generiert statisches HTML aus den Datenquellen.

Quellen:
  data/projects.json   -> Tab-/Filter-System mit Projekt-Cards (index.html)
                          + Tab-/Filter-Liste (projects.html)
  kunden-logos/        -> kunden-logos/manifest.json + Logo-Marquee (index.html)

Inhalte werden zwischen Marker-Kommentaren eingesetzt:
  <!-- PROJECTS:INDEX:START --> ... <!-- PROJECTS:INDEX:END -->
  <!-- PROJECTS:LIST:START -->  ... <!-- PROJECTS:LIST:END -->
  <!-- LOGOS:START -->          ... <!-- LOGOS:END -->

Alle Projekte stehen statisch im HTML (auch inaktive Tabs => display:none),
damit Suchmaschinen den kompletten Inhalt lesen können.
"""

import json
import os
import re
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Reihenfolge + Beschriftung + Nutzen-Satz der drei Leistungs-Tabs
CATEGORIES = [
    ("imagefilm",  "Imagefilm",
     "Zeigt, wer ihr wirklich seid — für mehr Bindung zu euren Kunden."),
    ("recruiting", "Recruiting-Video",
     "Gibt den richtigen Leuten einen Grund, sich für euch zu entscheiden."),
    ("social",     "Social-Media-Content",
     "Kurzformate, die fürs jeweilige Format gemacht sind — nicht nur gekürzt."),
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

def replace_between(text: str, marker: str, content: str, indent: str = "    ") -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"Marker {marker} nicht gefunden.")
    return pattern.sub(f"{start}\n{content}\n{indent}{end}", text)

def pretty_name(filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", stem) if w)

# ---------------------------------------------------------------- load data
with open(os.path.join(ROOT, "data", "projects.json"), encoding="utf-8") as f:
    projects = json.load(f)

by_cat = {key: [p for p in projects if p.get("category") == key]
          for key, _, _ in CATEGORIES}

# ---------------------------------------------------------------- card / row templates
def index_card(p):
    vid = yt_id(p["youtubeUrl"])
    label = f'{esc(p["label"])}&thinsp;·&thinsp;{esc(p["customer"])}'
    return (
f'''            <a class="portfolio-item" href="{esc(p["youtubeUrl"])}" target="_blank" rel="noopener noreferrer"
               aria-label="{esc(p["title"])} auf YouTube ansehen (öffnet in neuem Tab)">
              <div class="portfolio-thumb">
                <img src="https://img.youtube.com/vi/{vid}/maxresdefault.jpg" alt="{esc(p["title"])}" loading="lazy" width="640" height="360" />
                <span class="portfolio-arrow" aria-hidden="true">↗</span>
              </div>
              <p class="portfolio-label">{label}</p>
            </a>''')

def list_row(p):
    vid = yt_id(p["youtubeUrl"])
    parts = [p["label"], p["customer"]] + ([p["date"]] if p.get("date") else [])
    desc = esc(" · ".join(parts))
    return (
f'''        <a class="project-row" href="{esc(p["youtubeUrl"])}" target="_blank" rel="noopener noreferrer">
          <img class="project-thumb" src="https://img.youtube.com/vi/{vid}/mqdefault.jpg" alt="{esc(p["title"])}" loading="lazy" width="64" height="64" />
          <div>
            <p class="project-name">{esc(p["title"])}</p>
            <p class="project-desc">{desc}</p>
          </div>
          <span class="project-arrow">↗</span>
        </a>''')

# ---------------------------------------------------------------- tabs (shared)
def tabs_html():
    btns = []
    for key, label, _ in CATEGORIES:
        active = " is-active" if key == DEFAULT_CAT else ""
        sel = "true" if key == DEFAULT_CAT else "false"
        btns.append(
            f'        <button class="tab{active}" type="button" role="tab" '
            f'id="tab-{key}" data-tab="{key}" aria-selected="{sel}" '
            f'aria-controls="panel-{key}">{esc(label)}</button>')
    return ('      <div class="tabs" role="tablist" aria-label="Leistungen">\n'
            + "\n".join(btns) + "\n      </div>")

EMPTY = ('<p class="tab-empty">Hier entsteht gerade das erste Beispiel. '
         'Du hast so ein Projekt? <a href="#anfragen">Schreib mir.</a></p>')

# ---------------------------------------------------------------- index: tabs + panels (cards)
def index_block():
    out = [tabs_html()]
    for key, _, benefit in CATEGORIES:
        items = by_cat[key]
        active = " is-active" if key == DEFAULT_CAT else ""
        if not items:
            body = EMPTY.replace("so ein Projekt", "ein Recruiting-Projekt") if key == "recruiting" else EMPTY
        else:
            single = " is-single" if len(items) == 1 else ""
            cards = "\n".join(index_card(p) for p in items)
            progress = ('\n        <div class="portfolio-progress" aria-hidden="true">'
                        '<span class="portfolio-progress-bar"></span></div>') if len(items) > 1 else ""
            body = (f'<div class="portfolio-hscroll{single}">\n'
                    f'          <div class="portfolio-track">\n{cards}\n          </div>\n'
                    f'        </div>{progress}')
        out.append(
            f'      <div class="tab-panel{active}" id="panel-{key}" data-panel="{key}" '
            f'role="tabpanel" aria-labelledby="tab-{key}">\n'
            f'        <p class="tab-benefit">{esc(benefit)}</p>\n'
            f'        {body}\n'
            f'      </div>')
    return "\n".join(out)

# ---------------------------------------------------------------- projects.html: tabs + panels (list)
def list_block():
    out = ['    <div class="tabs" role="tablist" aria-label="Leistungen">']
    for key, label, _ in CATEGORIES:
        active = " is-active" if key == DEFAULT_CAT else ""
        sel = "true" if key == DEFAULT_CAT else "false"
        out.append(f'      <button class="tab{active}" type="button" role="tab" id="ltab-{key}" '
                   f'data-tab="{key}" aria-selected="{sel}" aria-controls="lpanel-{key}">{esc(label)}</button>')
    out.append('    </div>')
    for key, _, benefit in CATEGORIES:
        items = by_cat[key]
        active = " is-active" if key == DEFAULT_CAT else ""
        if not items:
            body = EMPTY.replace("so ein Projekt", "ein Recruiting-Projekt") if key == "recruiting" else EMPTY
        else:
            rows = "\n".join(list_row(p) for p in items)
            body = f'<div class="projects-list">\n{rows}\n        </div>'
        out.append(
            f'    <div class="tab-panel{active}" id="lpanel-{key}" data-panel="{key}" '
            f'role="tabpanel" aria-labelledby="ltab-{key}">\n'
            f'      <p class="tab-benefit">{esc(benefit)}</p>\n'
            f'      {body}\n'
            f'    </div>')
    return "\n".join(out)

# ---------------------------------------------------------------- logos -> manifest + marquee
logo_dir = os.path.join(ROOT, "kunden-logos")
exts = (".svg", ".png", ".jpg", ".jpeg")
logos = sorted(f for f in os.listdir(logo_dir)
               if f.lower().endswith(exts) and not f.startswith("."))
with open(os.path.join(logo_dir, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(logos, f, ensure_ascii=False, indent=2)
logos_html = "\n".join(
    f'        <img class="marquee-logo" src="kunden-logos/{esc(fn)}" '
    f'alt="Kunde: {esc(pretty_name(fn))}" loading="lazy" />'
    for fn in logos)

# ---------------------------------------------------------------- write files
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
