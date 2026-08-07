#!/usr/bin/env python3
"""Compila il profilo: `data/profile.yml` -> SVG vettoriali + `README.md`.

    python scripts/build.py            build completa
    python scripts/build.py --check    build in memoria, non scrive nulla (per la CI)

Nessuna dipendenza di sistema: niente Pillow, niente font installati, niente
fontconfig. Gira identico su Windows, macOS, Linux e sul runner di GitHub.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import PANELS, telemetry_strip  # noqa: E402
from engine import icons  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "profile.yml"
TEMPLATES = ROOT / "templates"
OUT = ROOT / "assets"
README = ROOT / "README.md"

THEMES = ("dark", "light")
VARIANTS = (("desktop", False), ("mobile", True))


# --- verifica ----------------------------------------------------------------

_SHAPE = re.compile(
    r'<(?P<tag>rect|circle|text|ellipse|line)\s(?P<attrs>[^>]*)>'
)
_ATTR = re.compile(r'([a-z-]+)="([^"]*)"')


def check_bounds(svg: str, name: str) -> list[str]:
    """Segnala elementi che escono dal viewBox.

    Cattura la classe di bug piu' insidiosa di un generatore di layout: il
    contenuto che sfora il pannello. Non sostituisce l'ispezione visiva (non sa
    dire se due testi si sovrappongono *dentro* il pannello), per quello c'e'
    `scripts/preview.py`.
    """
    head = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    if not head:
        return [f"{name}: viewBox mancante"]
    width, height = int(head.group(1)), int(head.group(2))
    problems: list[str] = []

    for match in _SHAPE.finditer(svg):
        attrs = dict(_ATTR.findall(match.group("attrs")))
        tag = match.group("tag")
        # Gli elementi dentro un gruppo animato si spostano per progetto.
        if "class" in attrs and attrs["class"] not in {"blink", "breathe", "bar"}:
            continue

        def num(key: str, default: float = 0.0) -> float:
            try:
                return float(attrs.get(key, default))
            except ValueError:
                return default

        if tag == "rect":
            bottom, right = num("y") + num("height"), num("x") + num("width")
        elif tag == "circle":
            bottom, right = num("cy") + num("r"), num("cx") + num("r")
        elif tag == "ellipse":
            bottom, right = num("cy") + num("ry"), num("cx") + num("rx")
        elif tag == "line":
            bottom, right = max(num("y1"), num("y2")), max(num("x1"), num("x2"))
        else:  # text: y e' la baseline, sotto restano i discendenti
            bottom, right = num("y") + num("font-size") * 0.22, num("x")

        if bottom > height + 1:
            problems.append(f"{name}: <{tag}> sfora in basso di {bottom - height:.0f}px")
        if right > width + 1:
            problems.append(f"{name}: <{tag}> sfora a destra di {right - width:.0f}px")
    return problems


# --- build -------------------------------------------------------------------

def render_assets(data: dict) -> dict[str, str]:
    """Genera tutti gli SVG. Restituisce {percorso sotto assets/: contenuto}."""
    assets: dict[str, str] = {}
    for name, draw in PANELS.items():
        for theme in THEMES:
            for suffix, mobile in VARIANTS:
                assets[f"readme/{name}-{suffix}-{theme}.svg"] = draw(data, theme, mobile)
    for theme in THEMES:
        for suffix, mobile in VARIANTS:
            assets[f"readme/telemetry-strip-{suffix}-{theme}.svg"] = telemetry_strip(
                data, theme, mobile
            )
    # Un'icona per canale attivo: sono i soli asset che devono restare
    # cliccabili, quindi vivono come file separati richiamati dal Markdown.
    for channel in data["channels"]:
        if channel["url"]:
            for theme in THEMES:
                assets[f"icons/{channel['key']}-{theme}.svg"] = icons.render(
                    channel["key"], channel["color"], theme
                )
    return assets


def render_readme(data: dict, revision: str) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,   # una chiave mancante rompe la build, non il profilo
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("README.md.j2")
    return template.render(**data, assets_rev=revision)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="non scrivere nulla, verifica soltanto")
    args = parser.parse_args()

    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    assets = render_assets(data)

    problems: list[str] = []
    for name, svg in sorted(assets.items()):
        problems.extend(check_bounds(svg, name))
    if problems:
        print("Layout fuori dai limiti:", file=sys.stderr)
        for problem in problems:
            print(f"  ! {problem}", file=sys.stderr)
        return 1

    # Revisione degli asset: sta in query string sulle URL delle immagini e
    # forza il proxy immagini di GitHub a rileggere il file dopo un aggiornamento.
    digest = hashlib.sha256()
    for name in sorted(assets):
        digest.update(name.encode())
        digest.update(assets[name].encode())
    revision = digest.hexdigest()[:8]

    readme = render_readme(data, revision)

    if args.check:
        total = sum(len(svg.encode()) for svg in assets.values())
        print(f"OK — {len(assets)} SVG ({total / 1024:.0f} KB), "
              f"README {len(readme.encode()) / 1024:.1f} KB, rev {revision}")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    # Un canale rimosso dal YAML deve sparire anche dal disco, altrimenti la sua
    # icona resterebbe committata per sempre senza che nulla la referenzi.
    for stale in OUT.rglob("*.svg"):
        if str(stale.relative_to(OUT)).replace("\\", "/") not in assets:
            stale.unlink()
    # Fine riga forzata a LF: su Windows Python tradurrebbe altrimenti ogni
    # avanzamento in CRLF, e l'output non sarebbe piu' identico byte per byte
    # a quello del runner Linux. Cosi' la build e' riproducibile ovunque,
    # senza dipendere da come e' configurato git sulla macchina di turno.
    for name, svg in sorted(assets.items()):
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8", newline="\n")
    README.write_text(readme, encoding="utf-8", newline="\n")

    total = sum(len(svg.encode()) for svg in assets.values())
    print(f"{len(assets)} SVG scritti in assets/ ({total / 1024:.0f} KB totali)")
    print(f"README.md compilato ({len(readme.encode()) / 1024:.1f} KB), rev {revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
