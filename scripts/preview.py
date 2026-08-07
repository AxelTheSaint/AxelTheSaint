#!/usr/bin/env python3
"""Anteprima locale del profilo, con rebuild automatico.

    python scripts/preview.py           ->  http://localhost:6419

Perche' esiste
--------------
Il ciclo "modifico -> rigenero -> committo -> guardo su GitHub" e' troppo lento
perche' un design converga: e' il motivo per cui in `old/` ci sono cinque README
diversi. Questo script chiude il ciclo in circa un secondo.

Cosa verifica davvero
---------------------
1. Gli SVG sono caricati con `<img>`, esattamente come fa GitHub tramite il suo
   proxy immagini. E' la differenza che conta: in modalita' immagine il browser
   NON renderizza `<foreignObject>` e NON carica font esterni. Se un pannello si
   vede qui, si vede su GitHub.
2. Sono usati i veri blocchi `<picture>` estratti da README.md, quindi le media
   query desktop/mobile e dark/light vengono valutate sul serio.
3. La larghezza del riquadro e' regolabile: il breakpoint a 600px si controlla
   spostandosi tra 599 e 601, e il tema con i pulsanti dark/light.
"""
from __future__ import annotations

import http.server
import re
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 6419
WATCH = [ROOT / "data", ROOT / "templates", ROOT / "scripts" / "engine"]

_state = {"rev": 0, "error": ""}


# --- rebuild -----------------------------------------------------------------

def snapshot() -> dict[str, float]:
    stamps: dict[str, float] = {}
    for folder in WATCH:
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".yml", ".j2"}:
                stamps[str(path)] = path.stat().st_mtime
    return stamps


def rebuild() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")],
                            capture_output=True, text=True, cwd=ROOT)
    _state["error"] = "" if result.returncode == 0 else (result.stderr or result.stdout)
    _state["rev"] += 1
    stamp = time.strftime("%H:%M:%S")
    if result.returncode == 0:
        print(f"[{stamp}] {result.stdout.strip().splitlines()[0]}", flush=True)
    else:
        print(f"[{stamp}] BUILD FALLITA\n{_state['error']}", file=sys.stderr)


def watcher() -> None:
    previous = snapshot()
    while True:
        time.sleep(0.6)
        current = snapshot()
        if current != previous:
            previous = current
            rebuild()


# --- pagine ------------------------------------------------------------------

PICTURE = re.compile(r"<picture>.*?</picture>", re.S)
ICON_STRIP = re.compile(r'<a href="[^"]+" title="[^"]+"><img src="\./assets/icons/.*?(?=</p>)', re.S)


def force_theme(block: str, theme: str) -> str:
    """Riscrive un blocco perche' mostri un tema preciso.

    Serve perche' `prefers-color-scheme` non e' pilotabile da JavaScript: per
    guardare la variante chiara senza cambiare le impostazioni del sistema
    bisogna riscrivere il markup. Le varianti sono distinguibili dal nome del
    file, quindi basta buttare le <source> dell'altro tema, togliere le media
    query di colore e puntare il fallback <img> al tema scelto.
    """
    other = "light" if theme == "dark" else "dark"
    block = re.sub(rf"<source[^>]*-{other}\.svg[^>]*>", "", block)
    block = re.sub(r" and \(prefers-color-scheme: \w+\)", "", block)
    block = re.sub(r'\s*media="\(prefers-color-scheme: \w+\)"', "", block)
    return re.sub(rf"(<img[^>]*?)-{other}\.svg", rf"\1-{theme}.svg", block)


def frame_html(theme: str | None) -> str:
    """Pagina interna: i blocchi <picture> reali estratti dal README, piu' la
    striscia di icone — che non e' un <picture> ma una fila di <img> in <a>."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    blocks = PICTURE.findall(readme) + ICON_STRIP.findall(readme)
    if theme:
        blocks = [force_theme(block, theme) for block in blocks]
    body = "\n".join(f'<section>{block}</section>' for block in blocks)
    return f"""<!doctype html><meta charset="utf-8">
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:16px; background:#0d1117; font-family:system-ui; }}
  @media (prefers-color-scheme: light) {{ body {{ background:#ffffff; }} }}
  section {{ margin: 0 0 18px; }}
  /* I pannelli si allargano; le icone dei canali no: si distinguono dal
     width="100%" che il template mette solo sui pannelli. */
  img {{ max-width:100%; height:auto; }}
  img[width="100%"] {{ width:100%; display:block; }}
  section:has(img:not([width="100%"])) {{ display:inline-block; margin:0 7px 18px; }}
</style>
{body}"""


def shell_html() -> str:
    widths = [390, 430, 599, 601, 768, 1280]
    buttons = "".join(f'<button data-w="{w}">{w}</button>' for w in widths)
    return f"""<!doctype html><meta charset="utf-8">
<title>AS-CONSOLE // preview</title>
<style>
  body {{ margin:0; font-family:ui-monospace,Consolas,monospace; background:#161b22;
         color:#c9d1d9; display:flex; flex-direction:column; height:100vh; }}
  header {{ padding:10px 14px; background:#0d1117; border-bottom:1px solid #30363d;
            display:flex; gap:14px; align-items:center; flex-wrap:wrap; }}
  button {{ background:#21262d; color:#c9d1d9; border:1px solid #30363d;
            padding:5px 11px; cursor:pointer; font:inherit; font-size:12px; }}
  button.on {{ border-color:#58a6ff; color:#58a6ff; }}
  .sep {{ color:#484f58; }}
  #err {{ background:#3d1418; color:#ffa198; padding:8px 14px; white-space:pre-wrap;
          font-size:12px; display:none; max-height:35vh; overflow:auto; }}
  #stage {{ flex:1; overflow:auto; display:flex; justify-content:center;
            padding:18px 0; background:#161b22; }}
  iframe {{ border:1px solid #30363d; background:#0d1117; height:100%;
            transition:width .12s; }}
</style>
<header>
  <strong style="color:#58a6ff">AS-CONSOLE</strong>
  <span class="sep">larghezza</span> {buttons}
  <span class="sep">|</span>
  <span class="sep">tema</span>
  <button data-t="">auto</button>
  <button data-t="dark">dark</button>
  <button data-t="light">light</button>
  <span class="sep">|</span>
  <span id="rev" class="sep"></span>
</header>
<div id="err"></div>
<div id="stage"><iframe id="f"></iframe></div>
<script>
  let width = 1280, theme = "", rev = null;

  function paint() {{
    document.getElementById("f").style.width = width + "px";
    document.querySelectorAll("[data-w]").forEach(b =>
      b.classList.toggle("on", +b.dataset.w === width));
    document.querySelectorAll("[data-t]").forEach(b =>
      b.classList.toggle("on", b.dataset.t === theme));
  }}
  function reload() {{
    document.getElementById("f").src =
      "/_frame?theme=" + theme + "&r=" + Date.now();
  }}
  document.querySelectorAll("[data-w]").forEach(b =>
    b.onclick = () => {{ width = +b.dataset.w; paint(); }});
  document.querySelectorAll("[data-t]").forEach(b =>
    b.onclick = () => {{ theme = b.dataset.t; paint(); reload(); }});
  setInterval(async () => {{
    const s = await (await fetch("/_rev")).json();
    document.getElementById("err").style.display = s.error ? "block" : "none";
    document.getElementById("err").textContent = s.error;
    document.getElementById("rev").textContent = "build #" + s.rev;
    if (rev !== null && s.rev !== rev && !s.error) reload();
    rev = s.rev;
  }}, 700);

  paint(); reload();
</script>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if path == "/":
            return self._send(shell_html(), "text/html")
        if path == "/_frame":
            forced = re.search(r"theme=(dark|light)", self.path)
            return self._send(frame_html(forced.group(1) if forced else None),
                              "text/html")
        if path == "/_rev":
            error = _state["error"].replace("\\", "\\\\").replace('"', '\\"')
            error = error.replace("\n", "\\n")
            return self._send(f'{{"rev":{_state["rev"]},"error":"{error}"}}',
                              "application/json")
        return super().do_GET()

    def _send(self, body: str, mime: str) -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args) -> None:
        pass  # il rumore delle richieste coprirebbe l'output della build


def main() -> None:
    rebuild()
    threading.Thread(target=watcher, daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as server:
        url = f"http://localhost:{PORT}"
        print(f"Anteprima su {url}  —  modifica data/profile.yml e guarda",
              flush=True)
        print("Ctrl+C per uscire.")
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nChiuso.")


if __name__ == "__main__":
    main()
