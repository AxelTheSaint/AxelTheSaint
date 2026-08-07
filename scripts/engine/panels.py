"""I pannelli della console, in SVG nativo.

Porting di `old/03-png-engine/scripts/generate_profile_assets.py`. Proporzioni,
palette e gerarchia tipografica sono le stesse del riferimento in
`reference/README.md`; cambiano il formato di output (vettoriale invece di
raster) e il fatto che il moto e' dichiarativo invece che sfogliato in una GIF.
"""
from __future__ import annotations

from . import theme as T
from .components import footer_rail, panel, register_motion, status_led, tags
from .svg import Canvas
from .text import fit_size, measure, wrap

# Dimensioni di ogni pannello: (desktop_w, desktop_h, mobile_w, mobile_h).
# Le altezze sono dimensionate sul contenuto peggiore consentito dai limiti
# documentati in `data/profile.yml`; `scripts/build.py` verifica a ogni build
# che nulla sfori (vedi `check_overflow`).
SIZES = {
    "01-hero": (1600, 740, 800, 960),
    "02-doctrine-telemetry": (1600, 700, 800, 1220),
    "03-engineering": (1600, 800, 800, 1450),
    "04-missions": (1600, 800, 800, 1340),
    "05-flight-signal-comms": (1600, 1370, 800, 2210),
}

MARGIN_D = 42
MARGIN_M = 28


def _new(name: str, theme_name: str, mobile: bool) -> tuple[Canvas, float]:
    dw, dh, mw, mh = SIZES[name]
    w, h = (mw, mh) if mobile else (dw, dh)
    c = Canvas(w, h, T.THEMES[theme_name], theme_name, grid=56 if mobile else 84)
    c.background()
    register_motion(c)
    return c, (MARGIN_M if mobile else MARGIN_D)


def _spin_class(c: Canvas, cx: float, cy: float, dur: float) -> str:
    """Rotazione attorno a un punto esplicito in coordinate view-box."""
    name = c.uid("sp")
    c.css(f".{name}{{transform-box:view-box;transform-origin:{cx}px {cy}px;"
          f"animation:spin {dur}s linear infinite}}")
    return name


def _sweep_class(c: Canvas, distance: float, dur: float) -> str:
    """Linea di scansione che attraversa il pannello."""
    name = c.uid("sw")
    c.keyframes(f"k{name}",
                "0%{transform:translateX(0);opacity:0}"
                "12%{opacity:.5}88%{opacity:.5}"
                f"100%{{transform:translateX({int(distance)}px);opacity:0}}")
    c.css(f".{name}{{animation:k{name} {dur}s linear infinite}}")
    return name


# =============================================================================
#  01 // HERO — CMD-00
# =============================================================================
def hero(data: dict, theme_name: str, mobile: bool) -> str:
    c, m = _new("01-hero", theme_name, mobile)
    t, W, H = c.t, c.w, c.h
    ident, sysc = data["identity"], data["system"]

    # --- topbar -------------------------------------------------------------
    bar_h = 82 if mobile else 74
    c.rect(m, m, W - 2 * m, bar_h, fill=t["surface2"], opacity=0.92,
           stroke=t["blue"], stroke_opacity=0.47, stroke_width=2)
    c.rect(m, m, 8, bar_h, fill=t["blue"])

    c.rect(m + 22, m + 15, 46, 46, fill=t["blue"], opacity=0.11,
           stroke=t["blue"], stroke_opacity=0.7, stroke_width=2)
    c.text_mid(m + 45, m + 38, "AS", 24, t["blue"], bold=True)

    c.text(m + 84, m + 15, "PERSONAL SYSTEMS CONSOLE", 24 if mobile else 21,
           t["text"], bold=True, letter_spacing="0.5")
    c.text(m + 84, m + 44, f"ENGINEERING PROFILE / {sysc['revision']}",
           13, t["muted"], mono=True)

    right = W - m - 26
    if mobile:
        c.text(right, m + 24, "● LINK ACTIVE", 13, t["green"], mono=True, bold=True,
               anchor="end", cls="blink")
    else:
        # Due <text> separati invece di uno solo con spazi multipli: SVG
        # collassa gli spazi consecutivi, quindi la spaziatura larga va
        # ottenuta con la geometria, non con i caratteri.
        mode = f"MODE {sysc['mode']}"
        c.text(right, m + 20, mode, 13, t["muted"], mono=True, anchor="end")
        c.text(right - measure(mode, 13, mono=True) - 40, m + 20,
               f"SECTOR {sysc['sector']}", 13, t["muted"], mono=True, anchor="end")
        c.text(right, m + 46, "● LINK ACTIVE", 13, t["green"], mono=True, bold=True,
               anchor="end", cls="blink")

    # --- pannello principale ------------------------------------------------
    box = (m, m + bar_h + 18, W - m, H - m)
    x0, y0, x1, y1 = panel(c, box, t["command"], "CMD-00",
                           "FLIGHT DIRECTOR IDENTIFICATION", ident["name"])

    if mobile:
        c.text(x0, y0, ident["role"].upper(), 30, t["blue"], letter_spacing="0.5")
        yy = y0 + 52
        for line in wrap(ident["statement"], 22, x1 - x0, mono=True):
            c.text(x0, yy, line, 22, t["text"], mono=True)
            yy += 31
        yy += 10
        for label, value in (("PRIMARY VECTOR", ident["primary_vector"]),
                             ("MISSION TYPE", ident["mission_type"])):
            c.rect(x0, yy, x1 - x0, 64, fill=t["blue"], opacity=0.09)
            c.rect(x0, yy, 5, 64, fill=t["blue"])
            c.text(x0 + 18, yy + 9, label, 13, t["muted"], mono=True, bold=True)
            c.text(x0 + 18, yy + 30, value,
                   fit_size(value, x1 - x0 - 36, 19, 13, mono=True),
                   t["text"], mono=True)
            yy += 76
        tags(c, x0, yy, ident["domains"], t["command"], x1, size=14)
        _orbit(c, (x0 + x1) / 2, y1 - 118, 100, data["capabilities"])
    else:
        split = x0 + 920
        c.text(x0, y0, ident["role"].upper(), 38, t["blue"], letter_spacing="0.5")
        yy = y0 + 62
        for line in wrap(ident["statement"], 30, 850, mono=True):
            c.text(x0, yy, line, 30, t["text"], mono=True)
            yy += 42
        yy += 20
        for i, (label, value) in enumerate((("PRIMARY VECTOR", ident["primary_vector"]),
                                            ("MISSION TYPE", ident["mission_type"]))):
            bx = x0 + i * 430
            c.rect(bx, yy, 410, 68, fill=t["blue"], opacity=0.09)
            c.rect(bx, yy, 6, 68, fill=t["blue"])
            c.text(bx + 20, yy + 10, label, 13, t["muted"], mono=True, bold=True)
            c.text(bx + 20, yy + 33, value,
                   fit_size(value, 410 - 40, 19, 13, mono=True),
                   t["text"], mono=True)
        tags(c, x0, yy + 92, ident["domains"], t["command"], split - 40, size=15)
        _orbit(c, (split + x1) / 2, (y0 + y1) / 2 + 10, 150, data["capabilities"])

    # Su mobile la rail ha meno di meta' larghezza: si accorcia il testo invece
    # di lasciare che le due estremita' si tocchino.
    if mobile:
        footer_rail(c, box, t["command"],
                    f"{ident['callsign']} / {sysc['operating_since']}",
                    f"CLEARANCE: {sysc['clearance']}")
    else:
        footer_rail(c, box, t["command"],
                    f"CALLSIGN: {ident['callsign']} / OPERATING SINCE "
                    f"{sysc['operating_since']}",
                    f"PROFILE CLEARANCE: {sysc['clearance']}")
    return c.render()


def _orbit(c: Canvas, cx: float, cy: float, r: float, caps: list) -> None:
    """Diagramma orbitale: cerchi concentrici, crosshair, due ellissi inclinate."""
    t = c.t
    accent = t["blue"]
    for radius, opacity in ((r, 0.31), (r * 0.66, 0.18), (r * 0.35, 0.14)):
        c.circle(cx, cy, radius, stroke=accent, stroke_opacity=opacity, stroke_width=2)
    c.line(cx - r - 20, cy, cx + r + 20, cy, stroke=accent, opacity=0.18, width=2)
    c.line(cx, cy - r - 20, cx, cy + r + 20, stroke=accent, opacity=0.18, width=2)

    # Le orbite sono tratteggiate come nell'originale, dove erano approssimate
    # con segmenti calcolati punto per punto: qui basta una dasharray.
    for tilt_deg, rx, ry, opacity in ((-26, r * 1.05, r * 0.44, 0.7),
                                      (47, r * 0.88, r * 0.31, 0.58)):
        c.ellipse(cx, cy, rx, ry, stroke=accent, stroke_opacity=opacity,
                  stroke_width=3, dash="14 10",
                  transform=f"rotate({tilt_deg} {cx:.0f} {cy:.0f})")

    c.circle(cx, cy, 9, fill=accent)

    # Satellite in orbita: rotazione attorno al centro del diagramma.
    spin = _spin_class(c, cx, cy, 14)
    with c.group(cls=spin):
        c.circle(cx + r * 0.92, cy, 8, fill=t["cyan"])

    # Le due etichette leggono la competenza piu' alta e la piu' bassa: erano
    # cablate su punteggi che poi sono cambiati, e mentivano in silenzio.
    top = max(caps, key=lambda c_: c_["score"])
    low = min(caps, key=lambda c_: c_["score"])
    for cap, dy in ((top, -r - 42), (low, r + 24)):
        tag = cap["label"].split()[0].upper()
        c.text(cx, cy + dy, f"{tag} / {cap['score']:03d}", 14, accent, mono=True,
               bold=True, opacity=0.75, anchor="middle")


# =============================================================================
#  02 // DOCTRINE + TELEMETRY — TRM-17 / TLM-04
# =============================================================================
def doctrine_telemetry(data: dict, theme_name: str, mobile: bool) -> str:
    c, m = _new("02-doctrine-telemetry", theme_name, mobile)
    t, W, H = c.t, c.w, c.h
    doctrine, readout = data["doctrine"], data["telemetry"]

    if mobile:
        boxes = [(m, m, W - m, m + 570), (m, m + 594, W - m, H - m)]
    else:
        boxes = [(m, m, 760, H - m), (784, m, W - m, H - m)]

    # --- manifesto ----------------------------------------------------------
    x0, y0, x1, y1 = panel(c, boxes[0], t["green"], "TRM-17", "ENGINEERING DOCTRINE",
                           "SYSTEM MANIFESTO", fill=t["surface_green"])
    size = 19 if mobile else 21
    yy = y0 + 6
    for statement in doctrine["statements"]:
        c.text(x0, yy, ">", size, t["green"], mono=True, bold=True)
        lines = wrap(statement.upper(), size, x1 - x0 - 45, mono=True)
        for j, line in enumerate(lines):
            c.text(x0 + 34, yy + j * (size + 10), line, size, t["text"], mono=True)
        yy += max(46, len(lines) * (size + 10) + 13)

    alert_h = 78 if mobile else 66
    c.rect(x0, yy + 8, x1 - x0, alert_h, fill=t["red"], opacity=0.09,
           stroke=t["red"], stroke_opacity=0.59, stroke_width=2)
    alert = doctrine["alert"].upper()
    alert_size = fit_size(alert, x1 - x0 - 40, 21, 14, mono=True, bold=True)
    c.text_mid(x0 + 20, yy + 8 + alert_h / 2, alert, alert_size, t["red"],
               mono=True, bold=True, anchor="start")
    c.text(x0, yy + alert_h + 26, "█", 21, t["green"], mono=True, cls="blink")
    footer_rail(c, boxes[0], t["green"], "INPUT: EXPERIENCE", "OUTPUT: DURABLE SYSTEMS")

    # --- telemetria ---------------------------------------------------------
    x0, y0, x1, y1 = panel(c, boxes[1], t["cyan"], "TLM-04", "LIVE PROFILE READOUT",
                           "TELEMETRY")
    cell_gap = 14
    cell_w = (x1 - x0 - cell_gap) / 2
    cell_h = 118 if mobile else 128
    for i, item in enumerate(readout):
        bx = x0 + (i % 2) * (cell_w + cell_gap)
        by = y0 + (i // 2) * (cell_h + cell_gap)
        c.rect(bx, by, cell_w, cell_h, fill=t["cyan"], opacity=0.06,
               stroke=t["cyan"], stroke_opacity=0.28, stroke_width=2)
        c.text(bx + 18, by + 13, item["label"], 13, t["cyan"], mono=True, bold=True,
               opacity=0.75)
        c.text(bx + 18, by + 40, item["value"], 52 if mobile else 58, t["cyan"],
               bold=True)
        c.text(bx + 18, by + 96, item["unit"], 13, t["muted"], mono=True)

    _wave(c, x0, x1, y1 - 28, count=42, color=t["cyan"])
    return c.render()


def _wave(c: Canvas, x0: float, x1: float, base: float, *, count: int,
          color: str) -> None:
    """Istogramma di attivita' con animazione sfalsata."""
    c.keyframes("bar", "0%,100%{transform:scaleY(.32)}50%{transform:scaleY(1)}")
    c.css(".bar{transform-box:fill-box;transform-origin:center bottom;"
          "animation:bar 2.6s ease-in-out infinite}")
    step = (x1 - x0) / count
    for i in range(count):
        h = 18 + ((i * 17) % 70)
        c.raw(f'<rect class="bar" style="animation-delay:-{i * 0.11:.2f}s" '
              f'x="{x0 + i * step:.1f}" y="{base - h:.1f}" width="4" height="{h}" '
              f'fill="{color}" fill-opacity=".6"/>')


# =============================================================================
#  03 // ENGINEERING — SYS-94 / EQP-23
# =============================================================================
def engineering(data: dict, theme_name: str, mobile: bool) -> str:
    c, m = _new("03-engineering", theme_name, mobile)
    t, W, H = c.t, c.w, c.h

    if mobile:
        boxes = [(m, m, W - m, m + 677), (m, m + 701, W - m, H - m)]
    else:
        boxes = [(m, m, 960, H - m), (984, m, W - m, H - m)]

    # --- capability matrix --------------------------------------------------
    x0, y0, x1, y1 = panel(c, boxes[0], t["blue"], "SYS-94", "CAPABILITY MATRIX",
                           "ENGINEERING RANGE")
    yy = y0 + 4
    row_gap = 114 if mobile else 110
    for cap in data["capabilities"]:
        c.text(x0, yy, cap["label"].upper(), 23 if mobile else 24, t["text"])
        c.text(x0, yy + 33, cap["note"], 13, t["muted"], mono=True)
        c.text(x1, yy + 1, f"{cap['score']:03d}", 21, t["blue"], mono=True, bold=True,
               anchor="end")
        _segment_bar(c, x0, yy + 64, x1 - x0, cap["score"], t["blue"])
        yy += row_gap
    footer_rail(c, boxes[0], t["blue"], "CALIBRATION: SELF-ASSESSED",
                "BIAS: SYSTEMS / BACKEND")

    # --- technical loadout --------------------------------------------------
    x0, y0, x1, y1 = panel(c, boxes[1], t["amber"], "EQP-23", "OPERATIONAL EQUIPMENT",
                           "TECHNICAL LOADOUT", fill=t["surface_amber"])
    yy = y0
    slots = 0
    for idx, group in enumerate(data["loadout"], 1):
        h = 146 if mobile else 152
        c.rect(x0, yy, x1 - x0, h, fill=t["amber"], opacity=0.06,
               stroke=t["amber"], stroke_opacity=0.22, stroke_width=2)
        c.rect(x0, yy, 64, h, fill=t["amber"], opacity=0.11)
        c.text(x0 + 32, yy + 24, f"{idx:02d}", 32, t["amber"], bold=True, anchor="middle")
        c.text(x0 + 84, yy + 16, group["code"], 13, t["amber"], mono=True, bold=True)
        c.text(x0 + 84, yy + 40, group["label"].upper(), 23, t["text"])
        tags(c, x0 + 84, yy + 80, group["items"], t["amber"], x1 - 15,
             size=13, pad=10, gap=7)
        slots += len(group["items"])
        yy += h + 15
    footer_rail(c, boxes[1], t["amber"], f"SLOTS: {slots} ACTIVE",
                "WEIGHT: PRODUCTION-GRADE")
    return c.render()


def _segment_bar(c: Canvas, x: float, y: float, width: float, score: int,
                 color: str) -> None:
    """Barra segmentata a 10 tacche: `score` decide quante sono accese."""
    segments, gap = 10, 7
    sw = (width - gap * (segments - 1)) / segments
    active = score / 10
    for i in range(segments):
        lit = i < active
        c.rect(x + i * (sw + gap), y, sw, 21, fill=color,
               opacity=0.78 if lit else 0.11,
               stroke=color, stroke_opacity=0.27, stroke_width=1)


# =============================================================================
#  04 // MISSION CONTROL — MSN-04
# =============================================================================
def missions(data: dict, theme_name: str, mobile: bool) -> str:
    c, m = _new("04-missions", theme_name, mobile)
    t, W, H = c.t, c.w, c.h

    box = (m, m, W - m, H - m)
    x0, y0, x1, y1 = panel(c, box, t["orange"], "MSN-04", "SELECTED ACTIVE SYSTEMS",
                           "MISSION CONTROL")
    items = data["missions"]
    gap = 18
    if mobile:
        ch = (y1 - y0 - gap * (len(items) - 1)) / len(items)
        for i, mission in enumerate(items):
            _mission_card(c, (x0, y0 + i * (ch + gap), x1, y0 + i * (ch + gap) + ch),
                          mission)
    else:
        cw = (x1 - x0 - gap) / 2
        ch = (y1 - y0 - gap) / 2
        for i, mission in enumerate(items):
            bx = x0 + (i % 2) * (cw + gap)
            by = y0 + (i // 2) * (ch + gap)
            _mission_card(c, (bx, by, bx + cw, by + ch), mission)

    footer_rail(c, box, t["orange"], f"{len(items)} DOSSIERS LOADED",
                "PRIORITY: BUILD / OPERATE / LEARN")
    return c.render()


def _mission_card(c: Canvas, box, mission: dict) -> None:
    x0, y0, x1, y1 = box
    t = c.t
    accent = t["orange"]
    c.rect(x0, y0, x1 - x0, y1 - y0, fill=t["surface2"], opacity=0.93,
           stroke=accent, stroke_opacity=0.39, stroke_width=2)

    rail = 84
    c.rect(x0, y0, rail, y1 - y0, fill=accent, opacity=0.09)
    c.text(x0 + rail / 2, y0 + 22, mission["code"], 13, accent, mono=True, bold=True,
           anchor="middle")

    colour = T.status_color(t, mission["status"])
    status_led(c, x0 + rail / 2, y0 + 68, 7, colour)
    c.text(x0 + rail / 2, y0 + 86, mission["status"], 12, colour, mono=True, bold=True,
           anchor="middle")

    cx = x0 + rail + 24
    c.text(cx, y0 + 20, mission["name"], 27, t["text"], bold=True)
    c.text(cx, y0 + 55, mission["kind"], 13, accent, mono=True, bold=True, opacity=0.78)

    yy = y0 + 90
    for line in wrap(mission["description"], 17, x1 - cx - 30, mono=True, max_lines=3):
        c.text(cx, yy, line, 17, t["text"], mono=True)
        yy += 25

    tags(c, cx, y1 - 55, mission["stack"], accent, x1 - 20, size=12, pad=9, gap=6)
    c.text(x1 - 26, y0 + 20, "↗", 24, accent, bold=True, anchor="end")


# =============================================================================
#  05 // FLIGHT LOG + SIGNAL FILTER + COMMS — LOG-09 / SIG-02 / COM-01
# =============================================================================
def flight_signal_comms(data: dict, theme_name: str, mobile: bool) -> str:
    c, m = _new("05-flight-signal-comms", theme_name, mobile)
    t, W, H = c.t, c.w, c.h
    gap = 24

    if mobile:
        flight = (m, m, W - m, m + 914)
        signal = (m, flight[3] + gap, W - m, flight[3] + gap + 644)
        comms = (m, signal[3] + gap, W - m, H - m)
    else:
        flight = (m, m, 970, 790)
        signal = (994, m, W - m, 790)
        comms = (m, 814, W - m, H - m)

    # --- flight log ---------------------------------------------------------
    x0, y0, x1, y1 = panel(c, flight, t["violet"], "LOG-09", "CAREER TRAJECTORY",
                           "FLIGHT LOG")
    entries = data["flight_log"]
    step = 190 if mobile else 145
    yy = y0 + 10
    for idx, entry in enumerate(entries, 1):
        node_x = x0 + 32
        c.circle(node_x, yy + 12, 15, fill=t["violet"], opacity=0.16,
                 stroke=t["violet"], stroke_opacity=0.7, stroke_width=2)
        c.text_mid(node_x, yy + 12, f"{idx:02d}", 12, t["violet"], mono=True, bold=True)
        if idx < len(entries):
            c.line(node_x, yy + 29, node_x, yy + step - 16, stroke=t["violet"],
                   opacity=0.31, width=3)

        c.text(x0 + 70, yy, entry["year"], 27, t["violet"], bold=True)
        tx = x0 + 172
        c.text(tx, yy + 2, entry["title"],
               fit_size(entry["title"], x1 - tx, 24, 18), t["text"])
        detail_size = 17 if mobile else 16
        ydesc = yy + 36
        for line in wrap(entry["detail"], detail_size, x1 - tx, mono=True):
            c.text(tx, ydesc, line, detail_size, t["muted"], mono=True)
            ydesc += 24
        yy += step
    footer_rail(c, flight, t["violet"], "TRAJECTORY: CONTINUOUS", "MODE: COMPOUNDING")

    # --- signal filter ------------------------------------------------------
    x0, y0, x1, y1 = panel(c, signal, t["red"], "SIG-02", "COLLABORATION PROTOCOL",
                           "SIGNAL FILTER")
    lanes = (("ACCEPT", t["green"], data["signal"]["accept"]),
             ("REJECT", t["red"], data["signal"]["reject"]))
    lane_h = (y1 - y0 - 18) / 2
    for i, (label, colour, items) in enumerate(lanes):
        by = y0 + i * (lane_h + 18)
        c.rect(x0, by, x1 - x0, lane_h, fill=colour, opacity=0.05,
               stroke=colour, stroke_opacity=0.31, stroke_width=2)
        c.text(x0 + 20, by + 15, label, 18, colour, mono=True, bold=True,
               letter_spacing="1")
        status_led(c, x1 - 32, by + 27, 8, colour)
        yy = by + 56
        row = 38 if mobile else 34
        for item in items:
            c.text(x0 + 22, yy, "▸", 16, colour, mono=True, bold=True)
            c.text(x0 + 48, yy, item, 17 if mobile else 16, t["text"], mono=True)
            yy += row
    footer_rail(c, signal, t["red"], "CHANNEL: DIRECT", "NOISE REJECTION: HIGH")

    # --- comms --------------------------------------------------------------
    x0, y0, x1, y1 = panel(c, comms, t["green"], "COM-01", "OPEN COMMUNICATION CHANNEL",
                           "ESTABLISH CONTACT")
    size = 21 if mobile else 20
    yy = y0 + 5
    status_led(c, x0 + 8, yy + 15, 8, t["green"])
    for line in wrap(data["availability"]["headline"], size, x1 - x0 - 40, mono=True):
        c.text(x0 + 30, yy, line, size, t["text"], mono=True)
        yy += 30
    yy += 22

    # Griglia dei canali. Un canale senza url e' assente dai dati per scelta
    # dell'autore: non si disegna un box vuoto.
    active = [ch for ch in data["channels"] if ch["url"]]
    cols = 2
    gap = 18
    cw = (x1 - x0 - gap * (cols - 1)) / cols
    for i, ch in enumerate(active):
        bx = x0 + (i % cols) * (cw + gap)
        by = yy + (i // cols) * 70
        colour = t[ch["color"]]
        c.rect(bx, by, cw, 58, fill=colour, opacity=0.07,
               stroke=colour, stroke_opacity=0.41, stroke_width=2)
        c.text(bx + 18, by + 10, ch["label"], 13, colour, mono=True, bold=True)
        c.text(bx + 18, by + 29, ch["value"],
               fit_size(ch["value"], cw - 36, 19, 12, mono=True), t["text"], mono=True)

    footer_rail(c, comms, t["green"], "RESPONSE WINDOW: 48H",
                f"STATUS: {data['availability']['status']}")
    return c.render()


# =============================================================================
#  STRISCIA DI TELEMETRIA ANIMATA (sostituisce activity-loop.gif, 380 KB)
# =============================================================================
def telemetry_strip(data: dict, theme_name: str, mobile: bool) -> str:
    W, H = (800, 150) if mobile else (1200, 190)
    c = Canvas(W, H, T.THEMES[theme_name], theme_name, grid=56 if mobile else 84)
    c.background()
    register_motion(c)
    t = c.t

    c.rect(8, 8, W - 17, H - 17, fill=t["surface2"], opacity=0.93,
           stroke=t["blue"], stroke_opacity=0.47, stroke_width=2)
    c.rect(8, 8, 7, H - 17, fill=t["blue"])

    c.text(32, 24, "AS-CONSOLE // LIVE TELEMETRY", 20 if mobile else 24, t["text"],
           bold=True)
    c.text(32, 56, "LINK ACTIVE", 14, t["green"], mono=True, bold=True, cls="blink")

    radar_cx = W - 150
    bars_x0 = 300 if not mobile else 180
    bars_x1 = radar_cx - 110

    _wave(c, bars_x0, bars_x1, H - 33, count=44 if not mobile else 26, color=t["cyan"])

    # Sweep di scansione sopra l'istogramma.
    sweep = _sweep_class(c, bars_x1 - bars_x0, 5.5)
    with c.group(cls=sweep):
        c.rect(bars_x0, 20, 3, H - 42, fill=t["green"], opacity=0.45)

    # Radar con lancetta rotante.
    radar_cy = H / 2
    for r in (25, 45, 65):
        c.circle(radar_cx, radar_cy, r, stroke=t["blue"], stroke_opacity=0.26,
                 stroke_width=2)
    spin = _spin_class(c, radar_cx, radar_cy, 4)
    with c.group(cls=spin):
        c.line(radar_cx, radar_cy, radar_cx + 62, radar_cy, stroke=t["blue"],
               opacity=0.75, width=3)
        c.circle(radar_cx + 49, radar_cy, 5, fill=t["cyan"])

    return c.render()


PANELS = {
    "01-hero": hero,
    "02-doctrine-telemetry": doctrine_telemetry,
    "03-engineering": engineering,
    "04-missions": missions,
    "05-flight-signal-comms": flight_signal_comms,
}
