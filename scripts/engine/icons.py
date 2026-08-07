"""Icone dei canali di contatto, self-hosted.

Perche' non shields.io / simple-icons via CDN
---------------------------------------------
Sarebbero una dipendenza da un servizio di terzi sul pezzo piu' visibile del
profilo: se il servizio e' lento, rate-limitato o sparisce, le icone spariscono.
Sono lo stesso genere di rischio del banner esterno che avevamo scartato. Qui
sono file nostri, ~1 KB l'uno.

Perche' un file per icona
-------------------------
Devono essere cliccabili. Un SVG servito come immagine non ha link attivi: gli
`<a>` interni vengono ignorati. Quindi il link vive nel Markdown
(`<a href><img src=icona></a>`) e ogni icona deve essere un file a se'.

Forma
-----
Ogni icona non e' un glifo nudo ma una *piastrella*: stessa superficie, stesso
bordo e stessa palette dei pannelli. Affiancate senza spazi nel Markdown
formano una striscia orizzontale continua, coerente con le tab e i tag del
resto della console — e ogni piastrella resta un link a se'.

Tema
----
Due file per piastrella, uno per tema, scelti da `<picture>` nel Markdown.
Non si usa una media query `prefers-color-scheme` *dentro* l'SVG: provata in
locale, non ha effetto quando l'SVG e' caricato come immagine. Il `<picture>`
invece e' verificato — e' lo stesso meccanismo con cui i pannelli scelgono la
loro variante.
"""
from __future__ import annotations

from .theme import THEMES

# Ogni icona e' (tipo, markup). "stroke" per il tratto tecnico line-art,
# "fill" per i marchi, che sono riconoscibili solo nella loro forma piena.
ICONS: dict[str, tuple[str, str]] = {
    "email": ("stroke",
              '<rect x="2.5" y="5" width="19" height="14" rx="2"/>'
              '<path d="M3.2 6.4 12 13.6l8.8-7.2"/>'),

    "website": ("stroke",
                '<circle cx="12" cy="12" r="9.2"/>'
                '<path d="M2.8 12h18.4"/>'
                '<path d="M12 2.8c2.5 2.6 3.8 5.7 3.8 9.2s-1.3 6.6-3.8 9.2'
                'c-2.5-2.6-3.8-5.7-3.8-9.2S9.5 5.4 12 2.8Z"/>'),

    "garden": ("stroke",
               '<path d="M12 21.5V10.5"/>'
               '<path d="M12 14.5C7.9 14.5 5.5 12 5.5 8.2 10 8.2 12 10.7 12 14.5Z"/>'
               '<path d="M12 12.2c0-3.8 2.4-6.3 6.5-6.3 0 3.8-2.4 6.3-6.5 6.3Z"/>'),

    "github": ("fill",
               '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 '
               '11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.'
               '042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.08'
               '4-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1'
               '.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.46'
               '6-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 '
               '1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .40'
               '5 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.8'
               '4 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.8'
               '1 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.09'
               '2 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'),

    "linkedin": ("fill",
                 '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.0'
                 '37-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c'
                 '.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286z'
                 'M5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125zm'
                 '1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 '
                 '1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 '
                 '22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'),

    "x": ("fill",
          '<path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 '
          '7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932zM17.61 20.644h2.039L6.486 '
          '3.24H4.298z"/>'),

    # Instagram: la glifo pieno sarebbe un tracciato enorme. Il marchio e'
    # ugualmente riconoscibile nella sua forma a contorno, che pesa 200 byte
    # invece di 2 KB e sta in coerenza con le altre icone a tratto.
    "instagram": ("stroke",
                  '<rect x="2.8" y="2.8" width="18.4" height="18.4" rx="5.2"/>'
                  '<circle cx="12" cy="12" r="4.2"/>'
                  '<circle cx="17.4" cy="6.6" r="1.2"/>'),

    "telegram": ("stroke",
                 '<path d="M21.5 4.3 2.9 11.4a.5.5 0 0 0 .04.94l4.7 1.4 1.8 5.5'
                 'a.5.5 0 0 0 .87.17l2.5-2.7 4.8 3.5a.5.5 0 0 0 .78-.3l3.7-15'
                 'a.5.5 0 0 0-.66-.58Z"/>'
                 '<path d="m7.6 13.8 11.6-7.6-8.3 8.5-.5 4.2"/>'),
}


# Geometria della piastrella. I bordi adiacenti di due piastrelle si sommano e
# leggono come un divisorio di segmento: e' voluto.
TILE_W = 74
TILE_H = 46
GLYPH = 24


def render(key: str, colour_role: str, theme_name: str) -> str:
    """Una piastrella cliccabile: superficie, bordo e glifo centrato."""
    kind, markup = ICONS[key]
    t = THEMES[theme_name]
    colour = t[colour_role]

    if kind == "fill":
        attrs = f'fill="{colour}"'
    else:
        attrs = (f'fill="none" stroke="{colour}" stroke-width="1.7" '
                 'stroke-linecap="round" stroke-linejoin="round"')

    dx = (TILE_W - GLYPH) / 2
    dy = (TILE_H - GLYPH) / 2

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TILE_W} {TILE_H}" '
        f'width="{TILE_W}" height="{TILE_H}" role="img">'
        f'<rect x="1" y="1" width="{TILE_W - 2}" height="{TILE_H - 2}" '
        f'fill="{t["surface2"]}" stroke="{colour}" stroke-opacity=".42" '
        f'stroke-width="2"/>'
        f'<g transform="translate({dx} {dy})">'
        f"<g {attrs}>{markup}</g></g></svg>"
    )
