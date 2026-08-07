"""Chrome condiviso dei pannelli: cornice, header, rail, tag, animazioni.

Porting fedele di `panel()`, `footer_rail()` e `tags()` dell'engine PNG, con le
proporzioni originali mantenute in modo che il risultato coincida con
`reference/README.md`.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from .svg import Canvas
from .theme import CHROME
from .text import fit_size, measure

# Altezza della fascia header dentro un pannello.
HEADER_H = 100
# Padding orizzontale del corpo rispetto al bordo del pannello.
PAD_X = 34
# Spazio riservato in basso al footer rail.
FOOTER_H = 82

Box = tuple[float, float, float, float]


def panel(c: Canvas, box: Box, accent: str, code: str, eyebrow: str, title: str,
          *, fill: str | None = None) -> Box:
    """Disegna la cornice di un pannello e restituisce il box del corpo."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    fill = fill or c.t["surface"]

    chrome = CHROME[c.theme_name]
    c.rect(x0, y0, w, y1 - y0, rx=5, fill=fill, opacity=chrome["panel_fill"],
           stroke=accent, stroke_opacity=chrome["panel"], stroke_width=2)

    # Barra di accento in alto a sinistra (42% della larghezza).
    c.line(x0, y0, x0 + w * 0.42, y0, stroke=accent, width=4)

    _corner_brackets(c, box, accent)

    c.line(x0, y0 + HEADER_H, x1, y0 + HEADER_H, stroke=accent, opacity=0.22, width=2)
    c.text(x0 + PAD_X, y0 + 22, eyebrow.upper(), 15, accent, mono=True, bold=True,
           opacity=0.73, letter_spacing="1")

    title_size = fit_size(title.upper(), w - 240, 40, 26, bold=False)
    c.text(x0 + PAD_X, y0 + 50, title.upper(), title_size, c.t["text"],
           letter_spacing="0.5")

    # Badge del codice pannello, in alto a destra.
    bx, by, bw, bh = x1 - 150, y0 + 26, 120, 42
    c.rect(bx, by, bw, bh, fill=accent, opacity=0.07,
           stroke=accent, stroke_opacity=0.43, stroke_width=2)
    c.text_mid(bx + bw / 2, by + bh / 2, code, 16, accent, mono=True, bold=True)

    return (x0 + PAD_X, y0 + HEADER_H + 28, x1 - PAD_X, y1 - FOOTER_H)


def _corner_brackets(c: Canvas, box: Box, accent: str, inset: float = 10,
                     size: float = 20) -> None:
    x0, y0, x1, y1 = box
    for cx, cy, sx, sy in (
        (x0 + inset, y0 + inset, 1, 1),
        (x1 - inset, y0 + inset, -1, 1),
        (x0 + inset, y1 - inset, 1, -1),
        (x1 - inset, y1 - inset, -1, -1),
    ):
        c.path(f"M {cx + sx * size} {cy} L {cx} {cy} L {cx} {cy + sy * size}",
               stroke=accent, stroke_opacity=CHROME[c.theme_name]["bracket"],
               stroke_width=2)


def footer_rail(c: Canvas, box: Box, accent: str, left: str, right: str) -> None:
    x0, y0, x1, y1 = box
    y = y1 - 52
    c.line(x0, y, x1, y, stroke=accent, opacity=0.18, width=2)
    c.text(x0 + 30, y + 19, left, 13, accent, mono=True, opacity=0.65)
    c.text(x1 - 30, y + 19, right, 13, accent, mono=True, opacity=0.65, anchor="end")


def tags(c: Canvas, x: float, y: float, values: Iterable[str], accent: str,
         max_x: float, *, size: float = 15, pad: float = 13, gap: float = 9) -> float:
    """Riga di tag con a-capo automatico. Restituisce la y dell'ultima riga."""
    start_x = x
    h = size + 17
    for value in values:
        w = measure(value, size, mono=True, bold=True) + pad * 2
        if x + w > max_x and x > start_x:
            x = start_x
            y += h + gap
        c.rect(x, y, w, h, fill=accent, opacity=0.07,
               stroke=accent, stroke_opacity=0.39, stroke_width=2)
        c.text_mid(x + w / 2, y + h / 2, value, size, accent, mono=True, bold=True,
                   anchor="middle")
        x += w + gap
    return y + h


def tags_height(values: Sequence[str], max_width: float, *, size: float = 17,
                pad: float = 14, gap: float = 10) -> float:
    """Altezza che occuperebbe `tags()`, per riservare lo spazio prima di disegnare."""
    h = size + 20
    rows, x = 1, 0.0
    for value in values:
        w = measure(value, size, mono=True, bold=True) + pad * 2
        if x + w > max_width and x > 0:
            rows += 1
            x = 0.0
        x += w + gap
    return rows * h + (rows - 1) * gap


# --- animazioni --------------------------------------------------------------

def register_motion(c: Canvas) -> None:
    """Registra le keyframe usate dai pannelli.

    Solo CSS: `transform-box: fill-box` rende `transform-origin: center`
    prevedibile sugli elementi SVG, e un'unica media query di reduced-motion
    (emessa da `Canvas.render`) le spegne tutte.
    """
    c.keyframes("blink", "0%,100%{opacity:1}50%{opacity:.25}")
    c.keyframes("breathe", "0%,100%{opacity:.35}50%{opacity:.9}")
    c.css(".blink{animation:blink 2.4s ease-in-out infinite}")
    c.css(".breathe{animation:breathe 4s ease-in-out infinite}")
    c.css(".spin{transform-box:fill-box;transform-origin:center;"
          "animation:spin 12s linear infinite}")
    c.keyframes("spin", "to{transform:rotate(360deg)}")


def status_led(c: Canvas, cx: float, cy: float, r: float, color: str,
               *, animated: bool = True) -> None:
    """LED di stato con alone pulsante."""
    if animated:
        c.circle(cx, cy, r * 2.1, fill=color, opacity=0.22, cls="breathe")
    c.circle(cx, cy, r, fill=color)
