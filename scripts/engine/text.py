"""Misurazione e wrapping del testo — senza Pillow, senza font sul disco.

L'engine PNG precedente misurava il testo con `PIL.ImageDraw.textlength()`, il
che imponeva Pillow + font di sistema + `fc-match`, cioe' WSL o Docker su
Windows. Qui il testo non viene rasterizzato: viene emesso come `<text>` SVG e
disegnato dal browser del visitatore. Serve quindi solo una *stima* della
larghezza, abbastanza buona da mandare a capo e da scalare i titoli.

Si usano le metriche AFM di Helvetica (larghezze su 1000 unita' em), che sono lo
standard de-facto ed entro pochi punti percentuali da Arial, Liberation Sans e
Segoe UI — tutte presenti nella stack `FONT_DISPLAY`. Il monospace ha un'avanzata
fissa, quindi e' esatto per costruzione.

Le stime sono volutamente *conservative* (vedi `SAFETY`): meglio una riga un po'
piu' corta del disponibile che una riga che sborda dal pannello su un font
leggermente piu' largo del previsto.
"""
from __future__ import annotations

# Larghezze Helvetica regular, unita' per em/1000.
_HELV = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556,
    "@": 1015,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722,
    "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944, "X": 667,
    "Y": 667, "Z": 611,
    "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556, "`": 333,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556, "h": 556,
    "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556, "p": 556,
    "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722, "x": 500,
    "y": 500, "z": 500,
    "{": 334, "|": 260, "}": 334, "~": 584,
}

# Larghezze Helvetica-Bold.
_HELV_BOLD = {
    " ": 278, "!": 333, '"': 474, "#": 556, "$": 556, "%": 889, "&": 722, "'": 238,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 333, ";": 333, "<": 584, "=": 584, ">": 584, "?": 611,
    "@": 975,
    "A": 722, "B": 722, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722,
    "I": 278, "J": 556, "K": 722, "L": 611, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944, "X": 667,
    "Y": 667, "Z": 611,
    "[": 333, "\\": 278, "]": 333, "^": 584, "_": 556, "`": 333,
    "a": 556, "b": 611, "c": 556, "d": 611, "e": 556, "f": 333, "g": 611, "h": 611,
    "i": 278, "j": 278, "k": 556, "l": 278, "m": 889, "n": 611, "o": 611, "p": 611,
    "q": 611, "r": 389, "s": 556, "t": 333, "u": 611, "v": 556, "w": 778, "x": 556,
    "y": 556, "z": 500,
    "{": 389, "|": 280, "}": 389, "~": 584,
}

# Avanzata dei monospace nella stack: DejaVu Sans Mono e SF Mono stanno a .602,
# Consolas a .55. Si prende il valore alto: peggio stretto che sbordante.
MONO_ADVANCE = 0.602

# Margine di sicurezza sulla stima proporzionale: le stack di sistema variano
# di qualche punto percentuale rispetto a Helvetica.
SAFETY = 1.04

# Larghezza usata per i caratteri fuori tabella (accentate, dash tipografici,
# simboli). Volutamente generosa.
_FALLBACK = 600


def measure(value: str, size: float, *, mono: bool = False, bold: bool = False) -> float:
    """Larghezza stimata di `value` in unita' utente SVG."""
    if mono:
        return len(value) * size * MONO_ADVANCE
    table = _HELV_BOLD if bold else _HELV
    total = sum(table.get(ch, _FALLBACK) for ch in value)
    return total / 1000.0 * size * SAFETY


def wrap(value: str, size: float, max_width: float, *, mono: bool = False,
         bold: bool = False, max_lines: int | None = None) -> list[str]:
    """Manda a capo `value` per stare in `max_width`.

    Una parola piu' lunga della riga viene comunque emessa da sola: e' meglio un
    singolo overflow visibile in preview che una parola troncata in silenzio.
    """
    lines: list[str] = []
    current = ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if not current or measure(candidate, size, mono=mono, bold=bold) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    if max_lines is not None and len(lines) > max_lines:
        kept = lines[:max_lines]
        kept[-1] = _ellipsize(kept[-1], size, max_width, mono=mono, bold=bold)
        return kept
    return lines


def fit_size(value: str, max_width: float, max_size: float, min_size: float,
             *, mono: bool = False, bold: bool = False) -> float:
    """Il piu' grande font-size intero <= max_size con cui `value` sta in una riga."""
    size = max_size
    while size > min_size and measure(value, size, mono=mono, bold=bold) > max_width:
        size -= 1
    return size


def _ellipsize(value: str, size: float, max_width: float, *, mono: bool, bold: bool) -> str:
    if measure(value + " …", size, mono=mono, bold=bold) <= max_width:
        return value + " …"
    out = value
    while out and measure(out + "…", size, mono=mono, bold=bold) > max_width:
        out = out[:-1]
    return out.rstrip() + "…"
