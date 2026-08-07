# Profile Console Engine

Il `README.md` in questa cartella **è generato**. Non modificarlo a mano: viene
sovrascritto alla build successiva.

```
data/profile.yml          contenuto (l'unica cosa che tocchi di solito)
        │
scripts/build.py          engine
        ├──> assets/readme/*.svg    24 pannelli (dark/light × desktop/mobile)
        ├──> assets/icons/*.svg     icone dei canali (dark/light)
        └──> README.md              composto da templates/README.md.j2
```

## Aggiornare i contenuti

Modifichi solo `data/profile.yml` e lasci ricompilare alla CI:

```powershell
git add data/profile.yml
git commit -m "content: aggiorna ..."
git push
git pull            # <<< IMPORTANTE, vedi sotto
```

**Il `git pull` finale non e' opzionale.** Dopo il push, GitHub Actions
rigenera SVG e README e fa un proprio commit. Se non lo recuperi, la volta
successiva il tuo push viene rifiutato perche' il locale e' indietro.

Se preferisci evitare del tutto il commit del bot, rigenera in locale e
committa tutto insieme:

```powershell
.\.venv\Scripts\python.exe scripts\build.py
git add . && git commit -m "content: aggiorna ..." && git push
```

In questo caso la CI trova zero differenze e non scrive nulla.

### Impostazioni richieste su github.com

Perche' il bot possa committare serve **Settings → Actions → General →
Workflow permissions → Read and write permissions**.

Non apre il repository a nessun altro: il token esiste solo dentro il
workflow, che parte unicamente su `push` a `main` e su `workflow_dispatch` —
entrambi richiedono gia' accesso in scrittura. Una pull request da un fork non
riceve quel token, perche' non usiamo `pull_request_target`. In piu' il job ha
una condizione `github.actor == github.repository_owner`.

Igiene consigliata nella stessa pagina:

- **Allow select actions** invece di consentirle tutte: qui servono solo
  `actions/checkout` e `actions/setup-python`, gia' pinnate a SHA;
- lasciare **disattivata** l'opzione che permette ad Actions di creare e
  approvare pull request.

## Uso quotidiano

```powershell
# 1. anteprima con rebuild automatico  ->  http://localhost:6419
.\.venv\Scripts\python.exe scripts\preview.py

# 2. modifica data\profile.yml e guarda il browser aggiornarsi
```

Build singola, senza anteprima:

```powershell
.\.venv\Scripts\python.exe scripts\build.py
```

Primo setup:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Non serve altro: niente Pillow, niente font di sistema, niente `fontconfig`,
niente WSL o Docker. L'engine produce testo, non pixel, quindi gira identico su
Windows, macOS, Linux e sul runner di GitHub Actions.

## Cosa modificare, e dove

| Vuoi cambiare | File |
|---|---|
| Testi, missioni, punteggi, timeline, contatti | `data/profile.yml` |
| Struttura del README, sezioni `<details>`, ordine | `templates/README.md.j2` |
| Palette, font stack | `scripts/engine/theme.py` |
| Layout di un pannello | `scripts/engine/panels.py` |
| Cornice, header, rail, tag | `scripts/engine/components.py` |

Nel 90% dei casi è solo la prima riga.

## I tre vincoli che governano tutto il design

Questi non sono preferenze: sono i limiti di GitHub. Violarne uno produce un
profilo che **si vede in locale e si rompe online** — è quello che era successo
ai tentativi archiviati in `old/`.

1. **Mai `<foreignObject>` negli SVG.**
   GitHub serve le immagini tramite il suo proxy, quindi ogni SVG arriva dentro
   un tag `<img>`. In quella modalità Chrome e Safari non renderizzano l'HTML
   dentro `foreignObject`: il pannello risulta vuoto. Solo primitive native
   (`rect`, `line`, `path`, `circle`, `text`).

2. **Mai font esterni.**
   In modalità immagine il caricamento di risorse esterne è bloccato: niente
   `@font-face`, niente Google Fonts. Si usano solo stack di font di sistema
   (`scripts/engine/theme.py`). È il motivo per cui `scripts/engine/text.py`
   stima le larghezze con le metriche di Helvetica invece di misurare un font
   reale.

3. **Mai CSS o JavaScript nel Markdown.**
   GitHub li rimuove dal README. L'unico posto dove il CSS sopravvive è
   *dentro* il file SVG — ed è lì che stanno le animazioni.

Quello che invece **funziona** ed è usato: le `@keyframes` CSS dichiarate dentro
l'SVG girano regolarmente in modalità immagine. Da qui il LED che pulsa, il
radar che ruota e le barre di telemetria — senza una singola GIF.

## Canali di contatto

I canali vivono in `data/profile.yml` sotto `channels:`. Ognuno produce tre
cose: due icone (`assets/icons/<key>-dark.svg` e `-light.svg`), una voce
cliccabile nel README e un box nel pannello COM-01.

**Un canale con `url` vuota è invisibile ovunque.** È così che il digital garden
resta nascosto finché non gli dai un indirizzo: nessun link morto pubblicato per
sbaglio.

Per aggiungere un canale nuovo serve anche la sua icona in
`scripts/engine/icons.py`. Le icone sono nostre, non di shields.io: un servizio
esterno sul pezzo più visibile del profilo è lo stesso rischio del banner di
terze parti che avevamo scartato.

Attenzione a una cosa: **dentro un SVG servito come immagine i link non
funzionano.** Gli `<a>` vengono ignorati. Per questo le icone sono file separati
richiamati da `<a><picture><img></picture></a>` nel Markdown, e non disegni
dentro un pannello.

## Accessibilità e movimento ridotto

Ogni SVG contiene:

```css
@media (prefers-reduced-motion: reduce) { * { animation: none !important } }
```

È la dichiarazione corretta, ma **non è stata verificata**: in locale la media
query `prefers-color-scheme` posta dentro un SVG non ha effetto quando l'SVG è
caricato come immagine, ed è per questo che le icone usano due file e
`<picture>` invece di una media query interna. È plausibile che
`prefers-reduced-motion` si comporti allo stesso modo.

Se dovesse contare davvero, il rimedio è lo stesso meccanismo verificato:
generare una variante `-static` senza `<style>` e selezionarla con
`<source media="(prefers-reduced-motion: reduce)">`. Non l'ho fatto perché il
moto qui è minimo (un LED che pulsa, un radar lento, barre morbide) e
raddoppierebbe i file.

Il `README.md` mantiene inoltre due livelli sovrapposti: il pannello visivo e,
sotto, lo stesso contenuto in Markdown dentro un `<details>`. Il secondo serve
a chi usa uno screen reader, a chi ha le immagini disattivate, alla ricerca di
GitHub e al copia-incolla. **Non rimuoverlo** perché "è già nell'immagine".

## Verifica

`scripts/build.py` fallisce se un elemento esce dal `viewBox` del pannello —
è la classe di bug più comune quando si allunga un testo. Non sa però dire se
due elementi si sovrappongono *dentro* il pannello: per quello serve l'occhio,
cioè `scripts/preview.py`.

Nell'anteprima i punti da controllare sono:

- larghezza **599 vs 601 px** — è il breakpoint tra asset mobile e desktop;
- **dark e light** — pulsanti in alto, perché `prefers-color-scheme` non è
  pilotabile da JavaScript;
- che nessun testo tocchi il footer rail di un pannello.

I limiti di lunghezza dei campi sono documentati in testa a `data/profile.yml`.

## Automazione

`.github/workflows/build-profile.yml` ricompila e committa **solo** quando
cambia qualcosa in `data/`, `templates/`, `scripts/` o `requirements.txt`.

Non c'è nessun `schedule:`. L'output è deterministico — non contiene timestamp
di build — quindi un cron produrrebbe zero modifiche utili e, con un timestamp,
due commit al giorno di rumore nella history e nel grafico dei contributi.

Le action sono pinnate al commit SHA, non al tag: un tag è un riferimento
mobile.

## Note

- **Cache delle immagini.** Le URL degli asset nel README portano un
  `?v=<hash>` calcolato sul contenuto di tutti gli SVG. Serve a invalidare la
  cache del proxy immagini di GitHub dopo un aggiornamento.
- **App mobile di GitHub.** Il breakpoint `max-width: 600px` funziona nel
  browser; l'app nativa può ignorarlo e mostrare la variante desktop scalata.
  È una limitazione della piattaforma, non del template.

## Riferimento visivo

`reference/README.md` è la versione a PNG che definisce il risultato da
ottenere, con i suoi asset in `reference/assets/readme/`. È conservata solo come
metro di paragone: non viene pubblicata e non fa parte della build.

## Archivio

`old/` contiene i tentativi precedenti, tenuti per storia:

| Cartella | Cos'era | Perché è stato abbandonato |
|---|---|---|
| `01-attempts-readme` | Cinque varianti di README + note di fattibilità | Contenuto placeholder, nessuna sorgente dati |
| `02-attempts-gif` | Card JSX renderizzate in GIF, SVG con `foreignObject` | Gli SVG non renderizzano su GitHub; le GIF pesano ~100 KB l'una e il testo non è selezionabile |
| `03-png-engine` | Engine Pillow che generava i PNG del reference | Richiede WSL/Docker e font di sistema; 2.6 MB di asset binari |
| `04-react-dashboard` | Dashboard React (Vite) | Non pubblicata. Candidata naturale per un layer su GitHub Pages |

`node_modules/` e `.venv/` non sono stati archiviati: si rigenerano con
`npm ci` e `pip install -r requirements.txt`.
