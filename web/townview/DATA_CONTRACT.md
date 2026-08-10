# TownView data contract

The SPA consumes ONE unified schema, normalised in `js/schema.js` from three real
producers. Nothing here is invented — every field cites the code that emits it.

## Producers

| source | schema | producing code |
|---|---|---|
| **simple replay** (`results/*/play.json`) | flat | `scripts/living_town_play_run.py`, `scripts/conduct_play_run.py` |
| **rich replay** (`play_doc`) | nested `map`/`paper`/… | `worlds/bigville_play_world.py::BigvillePlayWorld.play_doc` → `worlds/bigville_integ3_state.py::export_townstate3` → `bigville_integ2_state.py::export_townstate2` |
| **live stream** (SSE) | rich, one msg/tick | `server/app.py` over `worlds/bigville_living_town_world.py::BigvilleLivingTownWorld.integ_step` |

The live stream and the rich replay emit the **same** shape, so the SPA renders both
identically. The simple replay is a subset the normaliser upgrades (procedural map).

## Unified document (what the SPA holds after `normalizeDoc`)

```jsonc
{
  "schema": "townview/1",
  "title": "living_town_play",
  "grid": [w, h],                 // cells. simple: doc.grid; rich: [map.w, map.h]
  "square": [x, y],               // town-square anchor (simple: doc.square; rich: townhall)
  "map": {                        // present for rich docs; SYNTHESISED for simple docs
    "w": w, "h": h,
    "tiles": [[ "grass"|"path"|"square"|"floor"|"wall"|"tree"|"water"|"dirt", ... ], ...],
    "buildings": [ { "id", "type", "x","y","w","h", "owner", "name" } ],   // integ2 _coherent_buildings
    "features":  [ { "type": "crop|forest|rocks|orchard|water|well", "x","y","w","h" } ] // integ2 _features
  },
  "shops": { "bakery": [x,y], "fishmonger": [x,y] },   // rich only (play_doc.shops)
  "residents": [
    {
      "id": "v00",                // simple: name; rich: id
      "name": "Marjorie Dough",   // display name (rich); == id for simple
      "face": "🍞",               // emoji glyph (both)
      "role": "baker",            // rich (_villager_entry.role); simple: "villager"
      "cls":  "middle",           // rich; simple: "middle"
      "home": [x, y],             // both
      "health": 88,               // both
      "coin": 36,                 // rich only
      "held": "wellbeing=100; spite=0.03; …",   // rich only (deep_held, real graph read)
      "journal": "Day 2. I have 36 coin. …",    // rich; may be null; simple: absent
      "predicts": ["v01","v04"],  // who they expect to meet (simple + rich-derived)
      "rels": [                   // UNIFIED relationships (normaliser merges both forms)
        { "who": "v01", "feeling": "warm|hostile|neutral",
          "affection": 3.0, "resentment": 0.0, "kind": "hates|kin|owes" }
      ]
    }
  ],
  "paper":  [ { … } ],            // rich: export_townstate3 -> world.papers (Newspaper printings)
  "council_board": [ { … } ],    // rich: world.council_log (posted decisions / notices)
  "collective_action": {         // rich: informed-share series vs the 3.5% Chenoweth threshold
    "chenoweth_threshold": 0.035, "printings": [...], "coalitions_formed": 0
  },
  "institutions": { "bank": {"reserves","rate_bp"}, "church": {"funds"}, "council": {…}, … },
  "frames": [
    {
      "t": 0, "day": 0,
      "pos": { "v00": [x,y], … },            // per-resident cell this frame (both)
      "events": [                             // conduct / located happenings (UNIFIED)
        { "actor": "v05", "act": "help|give|harm|greet",
          "target": "v01", "text": "v05 helps v01", "kind": "kindness|violence|gift",
          "at": [x,y] }                        // 'at' present for rich says/acts
      ]
    }
  ],
  "ticks": 40,
  "days": 1
}
```

## Normalisation rules (`js/schema.js`)

1. **Grid / square** — simple: `doc.grid`, `doc.square`. rich: `[map.w, map.h]`, townhall.
2. **Map** — rich carries `map.tiles`. Simple docs have none, so the SPA **synthesises**
   a tilemap from `grid` + `square` (grass field, a plaza around the square, a ring path,
   scattered trees) so both modes look like a town. Buildings for a simple doc are placed
   at the square + resident homes.
3. **Residents** — `id = name ?? id`. Relationships come from either
   `rels:[{who,feeling,affection,resentment}]` (simple) **or** `rel:[{to,kind}]` (rich
   `_rel`: hates/kin/owes) — both are merged into the unified `rels` list, keyed by the
   other resident, so the inspector shows warmth AND structural ties (kin/owes/hates).
4. **Frames.events** — a simple frame has `events:[{actor,act,target,text}]`. A rich
   `play_doc` frame has `says:[…]` + `acts:[…]` with `{id,at,kind,text}`; the normaliser
   folds both into one `events` list (map `id→actor`, keep `at`, derive `act` from `kind`).
   The **live** stream emits the simple `events` form directly (from `conduct_events`),
   already unified.
5. **Act → colour** — `help`=green, `give`/`transfer`/`gift`=blue, `harm`/`violence`=red,
   everything else neutral. `kind ∈ {drama,council,paper,loud}` renders as a speech bubble;
   the rest as a floating action popup at `at` (or the actor's cell).

## Live protocol (SSE, `GET /api/live`)

`text/event-stream`, one JSON object per message with a `type`:

| `type` | payload | when |
|---|---|---|
| `meta` | `{ grid, square, map, residents, institutions, shops, cast, seed }` | first message |
| `frame` | `{ t, day, pos, events }` | one per sim tick (~0.5–1.2 s at cast 8) |
| `paper` | `{ paper, council_board, collective_action, institutions }` | when the town's boards change |
| `end` | `{ reason, ticks }` | stream closed (max ticks / client gone) |

The SPA appends every `frame` to the same timeline the replay uses, so LIVE is scrubbable
back through everything that has streamed. `meta` seeds the map + roster exactly as a
replay's top-level fields do.
