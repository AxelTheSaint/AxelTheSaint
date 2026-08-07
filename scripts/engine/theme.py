"""Design system: palette, font stack e costanti di layout.

Le palette sono portate 1:1 dall'engine PNG precedente (`old/03-png-engine/`)
in modo che il risultato visivo resti quello di `reference/README.md`.
"""
from __future__ import annotations

# --- Palette -----------------------------------------------------------------
# Due temi. Non e' un vezzo: chi visita GitHub in tema chiaro vedrebbe altrimenti
# un blocco scuro piantato in mezzo a una pagina bianca. Ogni tema espone gli
# stessi ruoli semantici, cosi' i pannelli non sanno quale stanno disegnando.
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#03070c", "bg2": "#06101a", "surface": "#09131e", "surface2": "#040b11",
        "text": "#e6edf1", "muted": "#82929e", "line": "#243746", "command": "#dfeaf0",
        "blue": "#61b7ff", "cyan": "#6be7f2", "green": "#6df5be", "amber": "#ffbd62",
        "orange": "#ff7849", "red": "#ff4f5f", "violet": "#a69cff",
        # tinte di superficie specifiche per pannello
        "surface_green": "#03100e", "surface_amber": "#100c07",
    },
    # Light non e' "il tema scuro schiarito": e' la stessa console vista in
    # pieno giorno. Il fondo e' azzurrino e non bianco, i pannelli sono piu'
    # chiari del fondo (cosi' sembrano accesi invece che stampati) e gli accenti
    # restano saturi. Testo e muted restano scuri: la leggibilita' viene prima.
    "light": {
        "bg": "#e6f0f7", "bg2": "#d2e4f0", "surface": "#f7fcff", "surface2": "#e9f3fa",
        "text": "#0a1e2b", "muted": "#4a687a", "line": "#9dbdd1", "command": "#12303f",
        "blue": "#0067cc", "cyan": "#007b8a", "green": "#06795a", "amber": "#8f5a00",
        "orange": "#bc3d14", "red": "#b81f31", "violet": "#5643bd",
        "surface_green": "#f2fbf8", "surface_amber": "#fdf8f0",
    },
}

# --- Intensita' del "chrome" -------------------------------------------------
# Griglia, scanline e bordi vanno tarati per tema. Gli stessi valori che sul
# fondo scuro sono un velo, sul chiaro sparirebbero del tutto — ed e' proprio
# quel reticolo tecnico a dire "strumento" invece che "documento".
#  panel_fill: quanto e' coprente la superficie di un pannello. Sul chiaro resta
#  volutamente traslucida: il reticolo che traspare e' cio' che fa leggere il
#  pannello come una lastra illuminata invece che come un foglio stampato.
CHROME: dict[str, dict[str, float]] = {
    "dark": {"grid": 0.07, "scan": 0.035, "panel": 0.59, "bracket": 0.75,
             "panel_fill": 0.95},
    "light": {"grid": 0.28, "scan": 0.100, "panel": 0.80, "bracket": 0.95,
              "panel_fill": 0.60},
}

# --- Scala tipografica -------------------------------------------------------
#  I pannelli hanno viewBox 1600px ma su GitHub vengono mostrati in una colonna
#  di circa 1000px: ogni corpo va quindi moltiplicato per ~0.63 per sapere come
#  appare davvero. Un 40 qui e' un 25 sullo schermo.
#
#  MIN_BODY e' il pavimento per il testo che si legge davvero (descrizioni,
#  elenchi): 19px qui = ~12px reali, il minimo sotto cui non si scende.
#  MIN_CHROME vale per le etichette decorative — rail, eyebrow, sigle — che si
#  scorrono, non si leggono: 13px qui = ~8px reali.
MIN_BODY = 19
MIN_CHROME = 13

# --- Tipografia --------------------------------------------------------------
# Un SVG servito come immagine (via il proxy camo di GitHub) NON puo' caricare
# font esterni: niente @font-face, niente Google Fonts, nessuna URL. Si usano
# solo stack di font gia' presenti sul sistema di chi guarda, e le metriche in
# `text.py` sono tarate su queste stack.
#
# Il monospace regge quasi tutto il testo: e' cio' che da' alla console il suo
# carattere da terminale. Il display resta ai soli titoli, dove serve una
# proporzionale per non sembrare un tabulato.
FONT_DISPLAY = (
    "'Helvetica Neue',Helvetica,'Segoe UI',Roboto,'DejaVu Sans',Arial,sans-serif"
)
FONT_MONO = (
    "ui-monospace,'SF Mono','DejaVu Sans Mono',Consolas,'Liberation Mono',monospace"
)

# --- Colori di stato delle missioni ------------------------------------------
STATUS_COLOR = {
    "ACTIVE": "green",
    "ONLINE": "green",
    "DELIVERED": "blue",
    "STABLE": "green",
    "BUILD": "amber",
    "RESEARCH": "violet",
}

# --- Geometria ---------------------------------------------------------------
DESKTOP_WIDTH = 1600
MOBILE_WIDTH = 800

# Breakpoint usato dal <picture> nel README.
MOBILE_BREAKPOINT = 600


def status_color(theme: dict[str, str], status: str) -> str:
    """Colore del LED di stato di una missione, con fallback prudente."""
    return theme[STATUS_COLOR.get(status.upper(), "violet")]
