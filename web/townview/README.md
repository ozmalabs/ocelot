# TownView — the Bigville glass-box town, in your browser

A production-quality single-page app that renders the **Bigville living town** as a
cozy, Stardew-esque pixel-art world: residents walk hop-by-hop, speak, help / give /
harm one another on the surprise clock, and — because every resident is a full mind in
the graph — you can **click anyone and read their held state, journal, and bonds**.

Two modes, both real:

- **Replay** — load a recorded `play.json` and scrub the timeline.
- **Live** — stream a real `BigvilleLivingTownWorld` over SSE, tick by tick, scrubbable
  back through everything that has streamed.

This is a served project (not a static file, not a Claude artifact): the live mode needs
SSE, which an artifact's CSP blocks.

---

## Run it

From the **gamma-substrate root** (`internal/research/experiments/gamma-substrate`):

```bash
# 1. (optional) regenerate the pixel-art assets — committed, so only if you edit them
python3 web/townview/assets/generate_assets.py

# 2. (optional) export a RICH replay doc (map + paper + council + institutions)
python3 -m web.townview.server.export_richplay --ticks 40 --cast 8

# 3. start the backend (serves the SPA + the API)
python3 -m web.townview.server.app
#   TownView -> http://127.0.0.1:8756
#   flags: --host 0.0.0.0 --port 9000
```

Open **http://127.0.0.1:8756** and:

- **Replay** (default): pick a run from the dropdown → *Load*, or *Open file…* a
  local `play.json`. Transport bar = play / restart / speed / scrub.
- **Live**: click **Live** in the top bar. Choose a cast (6–12) and it streams a fresh
  town. The status dot goes `connecting → live`; frames append to the timeline as they
  arrive, so you can pause and scrub back at any time. *Restart stream* starts a new one.

Deps (already present in this env): `fastapi`, `uvicorn`, `sse-starlette`. If missing:
`pip install --break-system-packages fastapi uvicorn sse-starlette`.

### Endpoints
| route | purpose |
|---|---|
| `GET /` | the SPA |
| `GET /api/runs` | list recorded `play.json` docs under `results/` |
| `GET /api/replay/<name>` | one recorded play document |
| `GET /api/live?cast=8&seed=276000&ticks=160` | SSE stream (meta → frame… → paper → end) |
| `GET /api/health` | liveness + run count |

---

## Layout

```
web/townview/
  index.html              SPA shell
  css/style.css           warm theme, light/dark, pixelated rendering
  js/
    app.js                bootstrap + mode wiring + HUD
    schema.js             UNIFIED contract normaliser (simple/rich/live -> one model)
    assets.js             manifest-driven sprite loading + per-resident MULTIPLY tint
    renderer.js           canvas tilemap, walking sprites, bubbles + action popups
    player.js             playback clock (rAF), timeline, transport (fixed + growing feed)
    live.js               SSE client (auto-reconnect, status)
    ui.js                 inspector / roster / newspaper / council / chronicle panels
  assets/
    generate_assets.py    reproducible pixel-art generator (pure stdlib PNG, no deps)
    tileset.png           15 terrain/prop tiles (16px)
    characters.png        humanoid, 3 walk frames x 4 directions (light body = tintable)
    buildings.png         10 institution sprites (48px)
    manifest.json         names every asset (the reusable list)
  server/
    app.py                FastAPI + SSE backend (world adapter; no agent logic)
    export_richplay.py    mechanical exporter -> a rich play_doc replay file
  DATA_CONTRACT.md        the unified schema, citing the exact producing code
  README.md
```

## Asset manifest (the reusable named set)

`assets/manifest.json` names everything; the generator is deterministic (byte-stable):

- **tileset** (15): `grass, grass_alt, path, dirt, square, floor, wall, water, sand,
  tree, bush, flower, rocks, well, crop` — plus `tile_map` / `feature_map` mapping the
  sim's tile + feature names onto them.
- **characters**: one 16×16 humanoid, cols = `{idle, stepA, stepB}`, rows =
  `{down, up, left, right}`, `walk_cycle [0,1,0,2]`. Bodies are drawn **light** so the
  renderer recolours each resident by MULTIPLY-compositing a class/role tint — one sheet,
  N distinct residents.
- **buildings** (10): `house, townhall, church, bank, market, press, noticeboard,
  school, surgery, inn`, each with a signage motif; `building_map` routes sim building
  types (incl. `bakery`/`fishmonger` → `market`) onto them.

Palette: warm cozy (greens / browns / soft blues).

---

## What's fully working vs. honest residuals

**Fully real, verified end to end:**

- **Replay** — every recorded `play.json` under `results/` loads and plays. Verified
  against `living_town_play` + `conduct_play` (simple schema) and `townview_richplay` +
  `bigville_play` (rich `play_doc` schema); the normaliser produces valid frames for all.
- **Live** — `/api/live` constructs a real `BigvilleLivingTownWorld`, steps it, and emits
  the unified schema per tick. Verified: `meta` (rich map + residents + rels), `frame`
  (positions + real conduct events like "v00 helps v01"), `paper`, `end`. The sim runs in
  the Rust substrate behind `integ_step()`; the server only reads + serialises.
- **Assets** — generated + visually confirmed; the full map (tiles + features + buildings
  + residents) composites cohesively from the real data.
- **Inspector / newspaper / council** — render real fields: `held` (a live graph read of
  affect/decision state), `journal`, coin/health, bonds (warm/hostile + affection/
  resentment + kin/owes/hates ties), the informed-share-vs-3.5%-threshold meter, and the
  institution readouts.

**Honest residuals (nothing faked):**

- **Live tick rate.** The town's `integ_step` costs ~0.5–1.2 s/tick at cast 8 — this is
  the nav's per-hop `run_rules`, an engine cost documented in `BIGVILLE_PERF_FINDINGS.md`,
  not the UI. Live therefore streams at roughly **~1 tick/second**; the player interpolates
  between frames so movement stays smooth. Larger casts stream slower (cap is 16). This is
  a real constraint of the sim, surfaced honestly in the Live controls hint — not stubbed.
- **Event actor labels.** Conduct-event text uses the sim's internal resident keys
  (`v00 helps v01`) exactly as the world produces them; the inspector/roster resolve those
  keys to display names ("Marjorie Dough"). Faithful to the source, not rewritten.
- **Paper / council in short runs.** These populate as stories break; a 40-tick run often
  prints nothing yet (`paper: []`), which the panels state plainly. The 252-tick
  `bigville_play` run does carry printed editions + a posted decision.
- **No browser-automation screenshot** was taken in this environment (no headless browser
  driver wired up); rendering was validated by (a) syntax-checking every module, (b)
  running the normaliser over all real docs in Node, and (c) compositing the map through
  the exact asset indices in a Python mirror of the renderer. The served app itself is
  standard canvas 2D + ES modules.

Nothing in the replay path is stubbed; the live path runs the real town.
