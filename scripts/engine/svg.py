"""Primitive SVG native per i pannelli mission-control.

VINCOLI NON NEGOZIABILI
-----------------------
1. Mai `<foreignObject>`. Un SVG servito come *immagine* (che e' l'unico modo su
   GitHub: il proxy camo lo consegna a un tag `<img>`) non renderizza l'HTML
   dentro foreignObject su Chrome e Safari. E' esattamente il motivo per cui i
   tentativi in `old/02-attempts-gif/assets-svg-foreignobject/` risultavano
   vuoti. Qui si usano solo rect / line / path / circle / text.

2. Mai font esterni. Nessun @font-face, nessuna URL: in modalita' immagine il
   caricamento di risorse esterne e' bloccato. Solo stack di font di sistema.

3. Mai JavaScript. Ignorato in modalita' immagine (e comunque strippato).

Cosa invece FUNZIONA e viene usato: le animazioni CSS `@keyframes` dichiarate
in un `<style>` interno all'SVG girano regolarmente in modalita' immagine
("secure animated mode"). E' lo stesso meccanismo per cui i banner animati
di terze parti funzionano su GitHub — solo self-hosted.

CONVENZIONE SULLE COORDINATE DEL TESTO
--------------------------------------
`<text y=...>` in SVG posiziona la *baseline*. Le API di disegno tipo Pillow
posizionano il *bordo superiore*. Per mantenere il porting leggibile rispetto
all'engine originale, i metodi qui accettano il bordo superiore e convertono
esplicitamente. Non si usa `dominant-baseline`: e' reso in modo incoerente tra
browser quando l'SVG e' un'immagine.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from .theme import CHROME, FONT_DISPLAY, FONT_MONO

# Distanza dal bordo superiore del box di testo alla baseline, in em.
ASCENT = 0.80
# Distanza dal centro ottico (meta' altezza maiuscole) alla baseline, in em.
MIDDLE = 0.355


def _fmt(value: float) -> str:
    """Numero compatto: gli SVG sono file di testo, ogni decimale inutile pesa."""
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _attrs(**kwargs) -> str:
    parts = []
    for key, value in kwargs.items():
        if value is None:
            continue
        key = key.replace("_", "-")
        parts.append(f'{key}="{_fmt(value) if isinstance(value, (int, float)) else value}"')
    return " ".join(parts)


class Canvas:
    """Accumula elementi SVG e li serializza in un documento completo."""

    def __init__(self, width: int, height: int, theme: dict[str, str],
                 theme_name: str, *, grid: int = 84):
        self.w = width
        self.h = height
        self.t = theme
        self.theme_name = theme_name
        self.grid = grid
        self._body: list[str] = []
        self._defs: list[str] = []
        self._keyframes: list[str] = []
        self._css: list[str] = []
        self._uid = 0

    # -- infrastruttura ------------------------------------------------------
    def uid(self, prefix: str) -> str:
        self._uid += 1
        return f"{prefix}{self._uid}"

    def raw(self, markup: str) -> None:
        self._body.append(markup)

    def defs(self, markup: str) -> None:
        self._defs.append(markup)

    def keyframes(self, name: str, body: str) -> None:
        self._keyframes.append(f"@keyframes {name}{{{body}}}")

    def css(self, rule: str) -> None:
        self._css.append(rule)

    def group(self, **kwargs) -> "_Group":
        return _Group(self, **kwargs)

    # -- forme ---------------------------------------------------------------
    def rect(self, x, y, w, h, *, fill=None, opacity=None, stroke=None,
             stroke_opacity=None, stroke_width=None, rx=None, cls=None) -> None:
        self.raw("<rect " + _attrs(
            x=x, y=y, width=w, height=h, rx=rx, fill=fill or "none",
            fill_opacity=opacity, stroke=stroke, stroke_opacity=stroke_opacity,
            stroke_width=stroke_width, **{"class": cls} if cls else {},
        ) + "/>")

    def line(self, x1, y1, x2, y2, *, stroke, opacity=None, width=1, cls=None,
             linecap=None) -> None:
        self.raw("<line " + _attrs(
            x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke, stroke_opacity=opacity,
            stroke_width=width, stroke_linecap=linecap,
            **{"class": cls} if cls else {},
        ) + "/>")

    def circle(self, cx, cy, r, *, fill=None, opacity=None, stroke=None,
               stroke_opacity=None, stroke_width=None, cls=None) -> None:
        self.raw("<circle " + _attrs(
            cx=cx, cy=cy, r=r, fill=fill or "none", fill_opacity=opacity,
            stroke=stroke, stroke_opacity=stroke_opacity, stroke_width=stroke_width,
            **{"class": cls} if cls else {},
        ) + "/>")

    def ellipse(self, cx, cy, rx, ry, *, fill=None, opacity=None, stroke=None,
                stroke_opacity=None, stroke_width=None, dash=None, transform=None,
                cls=None) -> None:
        self.raw("<ellipse " + _attrs(
            cx=cx, cy=cy, rx=rx, ry=ry, fill=fill or "none", fill_opacity=opacity,
            stroke=stroke, stroke_opacity=stroke_opacity, stroke_width=stroke_width,
            stroke_dasharray=dash, transform=transform,
            **{"class": cls} if cls else {},
        ) + "/>")

    def path(self, d, *, fill=None, opacity=None, stroke=None, stroke_opacity=None,
             stroke_width=None, dash=None, linecap=None, cls=None) -> None:
        self.raw("<path " + _attrs(
            d=d, fill=fill or "none", fill_opacity=opacity, stroke=stroke,
            stroke_opacity=stroke_opacity, stroke_width=stroke_width,
            stroke_dasharray=dash, stroke_linecap=linecap,
            **{"class": cls} if cls else {},
        ) + "/>")

    # -- testo ---------------------------------------------------------------
    def text(self, x, y_top, value: str, size: float, fill: str, *, mono=False,
             bold=False, anchor=None, opacity=None, letter_spacing=None,
             cls=None) -> None:
        """Testo con `y_top` = bordo superiore (non baseline)."""
        self._text(x, y_top + size * ASCENT, value, size, fill, mono=mono,
                   bold=bold, anchor=anchor, opacity=opacity,
                   letter_spacing=letter_spacing, cls=cls)

    def text_mid(self, x, cy, value: str, size: float, fill: str, *, mono=False,
                 bold=False, anchor="middle", opacity=None, letter_spacing=None,
                 cls=None) -> None:
        """Testo centrato verticalmente su `cy`."""
        self._text(x, cy + size * MIDDLE, value, size, fill, mono=mono, bold=bold,
                   anchor=anchor, opacity=opacity, letter_spacing=letter_spacing,
                   cls=cls)

    def _text(self, x, y_base, value, size, fill, *, mono, bold, anchor, opacity,
              letter_spacing, cls) -> None:
        self.raw("<text " + _attrs(
            x=x, y=y_base, fill=fill, fill_opacity=opacity,
            font_family=FONT_MONO if mono else FONT_DISPLAY,
            font_size=size, font_weight="700" if bold else None,
            text_anchor=anchor, letter_spacing=letter_spacing,
            **{"class": cls} if cls else {},
        ) + ">" + escape(value) + "</text>")

    # -- sfondo mission-control ---------------------------------------------
    def background(self) -> None:
        """Gradiente + griglia + scanline, tutto come pattern ripetuti.

        L'engine PNG disegnava migliaia di linee e punti singoli; qui bastano
        due `<pattern>`, che il browser tassella. E' il motivo principale per cui
        un pannello passa da ~100 KB a pochi KB.
        """
        t = self.t
        self.defs(
            f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{t["bg"]}"/>'
            f'<stop offset="1" stop-color="{t["bg2"]}"/>'
            f"</linearGradient>"
        )
        g = self.grid
        chrome = CHROME[self.theme_name]
        # Reticolo a due livelli: la maglia fine piu' un incrocio marcato ogni
        # quattro celle. E' il dettaglio che distingue una griglia tecnica da
        # una carta millimetrata.
        self.defs(
            f'<pattern id="grid" width="{g}" height="{g}" patternUnits="userSpaceOnUse">'
            f'<path d="M {g} 0 L 0 0 0 {g}" fill="none" stroke="{t["blue"]}" '
            f'stroke-opacity="{chrome["grid"]}" stroke-width="1"/></pattern>'
        )
        self.defs(
            f'<pattern id="grid4" width="{g * 4}" height="{g * 4}" '
            f'patternUnits="userSpaceOnUse">'
            f'<path d="M {g * 4} 0 L 0 0 0 {g * 4}" fill="none" stroke="{t["cyan"]}" '
            f'stroke-opacity="{chrome["grid"] * 1.5:.3f}" stroke-width="1"/></pattern>'
        )
        self.defs(
            f'<pattern id="scan" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<rect width="8" height="1" fill="{t["command"]}" '
            f'fill-opacity="{chrome["scan"]}"/>'
            f"</pattern>"
        )
        self.rect(0, 0, self.w, self.h, fill="url(#bg)")
        self.rect(0, 0, self.w, self.h, fill="url(#grid)")
        self.rect(0, 0, self.w, self.h, fill="url(#grid4)")
        self.rect(0, 0, self.w, self.h, fill="url(#scan)")

    # -- serializzazione -----------------------------------------------------
    def render(self) -> str:
        style = ""
        if self._keyframes or self._css:
            rules = "".join(self._css) + "".join(self._keyframes)
            # Un'unica riga disattiva TUTTO il moto per chi lo ha chiesto a
            # livello di sistema. Sostituisce il vecchio PNG statico separato.
            rules += "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            style = f"<style>{rules}</style>"
        defs = "".join(self._defs)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img">'
            f"<defs>{defs}</defs>{style}"
            + "".join(self._body)
            + "</svg>"
        )


class _Group:
    """Context manager per un `<g>` con attributi (usato per clip e transform)."""

    def __init__(self, canvas: Canvas, **kwargs):
        self.canvas = canvas
        cls = kwargs.pop("cls", None)
        if cls:
            kwargs["class"] = cls
        self.attrs = _attrs(**kwargs)

    def __enter__(self) -> Canvas:
        self.canvas.raw(f"<g {self.attrs}>" if self.attrs else "<g>")
        return self.canvas

    def __exit__(self, *exc) -> None:
        self.canvas.raw("</g>")
