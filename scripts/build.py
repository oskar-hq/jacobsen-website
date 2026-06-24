#!/usr/bin/env python3
"""
build.py — generiert statisches HTML aus den Datenquellen.

Quellen:
  data/projects.json   -> Projekt-Cards (index.html) + Projektliste (projects.html)
  kunden-logos/        -> kunden-logos/manifest.json + Logo-Marquee (index.html)

Die Inhalte werden zwischen Marker-Kommentaren eingesetzt, z. B.:
  <!-- PROJECTS:INDEX:START --> ... <!-- PROJECTS:INDEX:END -->

So bleibt alles statisch im HTML (SEO-freundlich). Beim Push regeneriert eine
GitHub Action diese Dateien automatisch (siehe .github/workflows/build.yml).
"""

import json
import os
import re
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- helpers
def yt_id(url: str) -> str:
    """YouTube-Video-ID aus den gängigen Link-Formaten ziehen."""
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

def replace_between(text: str, marker: str, content: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"Marker {marker} nicht gefunden.")
    return pattern.sub(f"{start}\n{content}\n      {end}", text)

def pretty_name(filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", stem) if w)

# ---------------------------------------------------------------- load data
with open(os.path.join(ROOT, "data", "projects.json"), encoding="utf-8") as f:
    projects = json.load(f)

# ---------------------------------------------------------------- projects -> index cards
index_cards = []
for p in projects:
    vid = yt_id(p["youtubeUrl"])
    label = f'{esc(p["category"])}&thinsp;·&thinsp;{esc(p["customer"])}'
    index_cards.append(
        f'''        <a class="portfolio-item" href="{esc(p["youtubeUrl"])}" target="_blank" rel="noopener noreferrer"
           aria-label="{esc(p["title"])} auf YouTube ansehen (öffnet in neuem Tab)">
          <div class="portfolio-thumb">
            <img src="https://img.youtube.com/vi/{vid}/maxresdefault.jpg" alt="{esc(p["title"])}" loading="lazy" width="640" height="360" />
            <span class="portfolio-arrow" aria-hidden="true">↗</span>
          </div>
          <p class="portfolio-label">{label}</p>
        </a>''')
index_html = "\n".join(index_cards)

# ---------------------------------------------------------------- projects -> list rows
list_rows = []
for p in projects:
    vid = yt_id(p["youtubeUrl"])
    parts = [p["category"], p["customer"]] + ([p["date"]] if p.get("date") else [])
    desc = esc(" · ".join(parts))
    list_rows.append(
        f'''    <a class="project-row" href="{esc(p["youtubeUrl"])}" target="_blank" rel="noopener noreferrer">
      <img class="project-thumb" src="https://img.youtube.com/vi/{vid}/mqdefault.jpg" alt="{esc(p["title"])}" loading="lazy" width="64" height="64" />
      <div>
        <p class="project-name">{esc(p["title"])}</p>
        <p class="project-desc">{desc}</p>
      </div>
      <span class="project-arrow">↗</span>
    </a>''')
list_html = "\n".join(list_rows)

# ---------------------------------------------------------------- logos -> manifest + marquee
logo_dir = os.path.join(ROOT, "kunden-logos")
exts = (".svg", ".png", ".jpg", ".jpeg")
logos = sorted(f for f in os.listdir(logo_dir)
               if f.lower().endswith(exts) and not f.startswith("."))

with open(os.path.join(logo_dir, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(logos, f, ensure_ascii=False, indent=2)

logo_tags = []
for fn in logos:
    logo_tags.append(
        f'        <img class="marquee-logo" src="kunden-logos/{esc(fn)}" '
        f'alt="Kunde: {esc(pretty_name(fn))}" loading="lazy" />')
logos_html = "\n".join(logo_tags)

# ---------------------------------------------------------------- write index.html
index_path = os.path.join(ROOT, "index.html")
with open(index_path, encoding="utf-8") as f:
    idx = f.read()
idx = replace_between(idx, "PROJECTS:INDEX", index_html)
idx = replace_between(idx, "LOGOS", logos_html)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(idx)

# ---------------------------------------------------------------- write projects.html
proj_path = os.path.join(ROOT, "projects.html")
with open(proj_path, encoding="utf-8") as f:
    pr = f.read()
pr = replace_between(pr, "PROJECTS:LIST", list_html)
with open(proj_path, "w", encoding="utf-8") as f:
    f.write(pr)

print(f"Build OK: {len(projects)} Projekte, {len(logos)} Logos.")
