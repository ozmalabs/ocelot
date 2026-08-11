# BIGVILLE — survey + architecture + first scaffold (BUILD NOTES)

Scope: (A) a search-grounded survey of what to build ON, (B) the bigville
architecture, (C) a first minimal runnable SCAFFOLD wrapping the proven
small-cast drama (block 245000) in a Stardew-style top-down grid world with a
per-agent occlusion-gated observation query, a reporter + newspaper, and a
self-contained glass-box web viewer.

This is engineering scaffold, **not** a gated measurement rung. Base SHA
`b1b021f517`. Own engine built from committed Rust source (zero Rust added),
canonical shared `.so` never written through.

---

## A. Survey (search-verified, licenses checked)

**Search availability: YES** (WebSearch + WebFetch both live this session).

### Prior art (conceded up front)
- **Generative Agents / "Smallville"** (Park, O'Brien, Cai, Morris, Liang,
  Bernstein, UIST '23) — **25 agents**, each a **per-step LLM call**, a
  Sims-like sandbox; believable but **black-box / confabulated reasons /
  expensive**. Code Apache-2.0 (`github.com/joonspk-research/generative_agents`).
  This is the reference sim; our differentiator is orthogonal: **glass-box
  (reasons READ from graph state) + cheap + real-time + emergent**, and 200
  real-time glass-box agents is structurally out of reach for per-step-LLM.
  (Refs: dl.acm.org/doi/10.1145/3586183.3606763; arxiv.org/abs/2304.03442.)

### Web viewer / frontend — **BUILD-FRESH (self-contained HTML), thin**
- **PixiJS** (MIT, ~450 KB, WebGL 2D renderer) and **Phaser** (MIT, full game
  framework, v4 "Caladan" 2026) are both real and apt for a tilemap game — but
  both are **CDN/npm dependencies**, which the CSP-safe self-contained-HTML /
  Artifact path forbids (no external host). For the **first** viewer the
  simplest capable path is a **single self-contained HTML + `<canvas>`**: colored
  typed tiles + emoji sprites, zero dependencies, Artifact-publishable.
  **Recommendation:** ship the canvas viewer now; adopt **PixiJS** only if/when
  the hosted (FastAPI + websockets) live version needs sprite batching at scale.
  (Refs: pixijs.com / MIT; phaser.io / MIT; npm-compare pixi-vs-phaser.)

### Village visual assets — **BUILD-ON (Kenney CC0 first)**
- **Kenney** packs are **CC0 (public domain, no attribution required)** —
  *RPG Urban Pack* (~480 top-down tiles), *Roguelike Modern City* (~1036),
  *Roguelike/RPG Pack* (~1700). **Best fit for a Stardew-style top-down town,
  zero license friction.** (kenney.nl/assets/rpg-urban-pack, roguelike-modern-city.)
- **LPC / Liberated Pixel Cup** (OpenGameArt) — cohesive top-down character
  sprites + tiles, but **dual CC-BY-SA 3.0 / GPL-3.0**: **attribution +
  share-alike required**, per-contributor credits (`CREDITS.TXT`). Usable but
  heavier compliance. (opengameart.org LPC base assets; Universal-LPC generator.)
- **Recommendation:** start with emoji/canvas (in the scaffold — no assets to
  embed, fully self-contained); upgrade to **Kenney CC0** tiles/sprites embedded
  as data-URIs (keeps the page self-contained + CSP-safe) before any public
  build; treat LPC as an optional richer set only if its attribution is carried.

### Real-time multi-agent sim / persistence — **BUILD-FRESH host loop; substrate IS the agent engine**
- The substrate is already the agent engine (graph rules in Rust); durable JSON
  round-trips via `graph_to_dict`/`graph_from_dict` (persistence is solved). What
  bigville needs is only a **host sim loop + tick scheduler + a graph→viewer
  read-out** — **not** an external agent framework.
- **Mesa** (Apache-2.0, Python ABM, Solara browser viz) and **NetLogo** are real
  and mature, surveyed **as reference only / what-NOT-to-reuse**: they are
  agent-decision engines, and adopting one would put agent decisions in the host
  layer — a direct violation of this tree's architecture rule. We reuse their
  *idea* (spatial grid + scheduler) but the decisions stay graph-native.
  (Refs: mesa.readthedocs.io / Apache-2.0.)

---

## B. Architecture (adopted)

```
 substrate agents (block 245000 drama: John, Mary, villagers, +reporter)
        seeds/bigville_drama_social.json  ← decisions are graph RULES
                    │  run_rules() fixpoint (Rust)
                    ▼
 BigvilleSimWorld  (worlds/bigville_sim_world.py)  ← MECHANICAL host adapter
   • tile grid + affordances (office, church, square, houses) — Stardew top-down
   • PER-AGENT observation gate = a CHEAP GEOMETRIC GRAPH QUERY, not the pixel eye:
       - SIGHT: Chebyshev range + Bresenham line-of-sight, occluded by walls/trees
       - HEARING: proximity range, wall-muffled
       - observations injected as GRAPH FACTS (set_attr on observation counts)
       - unknown = absence (an agent knows only what it perceives)
   • proximity-LOCAL per agent  →  realized interaction ~O(N·k), NOT all-pairs
   • reporter observes through the SAME gate → its stance (the credibility rule)
     is the newspaper FRAME → newspaper node propagates to readers' beliefs
                    │  graph_to_dict + targeted queries
                    ▼
 dumped state JSON  (results/bigville_sim/bigville_state.json)
                    ▼
 self-contained HTML viewer (worlds/bigville_viewer_glassbox.html)
   • top-down canvas grid + emoji cast, tick scrubber, play
   • CLICK an inhabitant → read-off panel (held intent / belief / goal / backing)
     + WHAT IT CAN SEE & HEAR (perception overlay); + the in-world newspaper
```

**Chosen first-viewer path:** a single **self-contained `<canvas>` HTML file**
(no CDN, CSP-safe, Artifact-publishable). Rationale: simplest capable path,
zero dependency, and the state is inlined so the file is a standalone artifact.

**Why perception is the load-bearing core (three jobs):**
1. *Sparsity/scale* — an agent only perceives (→ interacts with) whoever is in
   sight/earshot; a bounded local neighborhood keeps interaction ~linear.
2. *Grounds the drama's epistemics* — John's benevolence is a **square** event
   (public, seen by all); his scheming is an **office** event (enclosed →
   occluded). The credibility asymmetry becomes a **perception fact**, not a
   `stated≠held` flag: villagers in the square *never witness* the hostility
   (`seen_hostile=0`), while the pastor (at the door) and reporter (on the beat)
   do — so Mary infers, the reporter exposes, and only they hold the private truth.
3. *Reuses the substrate's perception principles* — occlusion / line-of-sight /
   unknown-as-absence / proximity — as a **graph query** over already-symbolic
   typed tiles (skip the pixel→symbol eye stage; compute only the occlusion GATE).

**Delta vs the earlier "run the eye per agent" idea:** adopted the creator's
correction — the gate here is a cheap Bresenham+range query injecting graph
facts; the photon-eye is **not** run per agent.

---

## C. Scaffold (what runs)

Additive files (all `bigville_sim_` / `bigville_viewer_` / `BIGVILLE_BUILD_`):
- `worlds/bigville_sim_world.py` — the sim-loop world adapter (grid, perception
  gate, reporter+newspaper, glass-box read-off). Wraps `BigvilleDramaWorld`
  unchanged; **no agent decision in Python** (source-clean).
- `scripts/bigville_sim_run.py` — runs T=20 ticks, dumps `bigville_state.json`,
  and inlines it into a standalone copy of the viewer.
- `worlds/bigville_viewer_glassbox.html` — the self-contained clickable viewer.
- `results/bigville_sim/{bigville_state.json, bigville_viewer_glassbox.html}` —
  the dumped state + the standalone inlined viewer (open it in a browser).

**Run:** `python scripts/bigville_sim_run.py`
**View:** open `results/bigville_sim/bigville_viewer_glassbox.html`.

### Added per the creator's design directives (batches 3 & 4)

- **Nightly journals — the THREE glass-box layers.** Each night (a consolidation
  tick) every inhabitant writes a private `JournalEntry` graph node carrying
  **held (truth) / journal (inward self-story) / face (public)**. The three
  tokens are READ from graph state; `self_deception` = the presented token (out
  AND in) contradicting the held truth. For John this IS the `deception_gap`
  (states benevolence over held hostility) — his journal *rationalizes, it does
  not confess* — so the gap held≠journal falls out of the psychopath knobs, not
  a script. Honest characters' three layers agree. The viewer shows all three on
  a click. Prose is a template; the syntax-carrying composition is the sibling
  **244000/246000** faculty (seam marked, not depended on). The journal is
  `private` (a future plot hook: another agent could FIND one).
- **Seeded ONCE, with history.** `_seed_history()` runs a single time: a village
  that has already lived — pre-existing relationship edges (`allied_with` /
  `friend_of` / `rival_of` / `charmed`) and priors (John's charm has worked for
  years → each villager starts with a `seen_benevolent` prior ∝ its charm
  susceptibility; the pastor's standing already built). Sparse ties, NOT
  all-pairs.
- **Persistence: seed once → live → dump → resume.** `dump(path)` writes
  `graph_to_dict` + host meta; `resume(path)` rebuilds a fresh substrate (same
  seed manifests → rules present), overlays the saved graph, rebinds handles by
  type/name, and continues WITHOUT re-seeding — verified: dump@10 → resume →
  run to 20, no duplicate nodes, John's scheme continues. The runner exercises
  this every run.
- **Every entity is a full agent (no NPCs).** All five villagers + the reporter
  carry the same ToM/valuation/journal machinery; none is a hollow extra. Code
  does NOT special-case John/Mary — the three-layer read-out, journals, and
  perception gate are uniform across the cast. The seeded conflict is a **seed
  crystal**, not a privileged plot: the viewer surfaces any inhabitant's state,
  so an emergent story from elsewhere would show up the same way. (This raises
  the scale bar — no cheap bodies — which the scale-verification probe gates.)
- **A role-discovery instrument (in miniature).** The small cast already REVEALS
  a needed role: nobody in the seeded cast carries information to villagers who
  weren't present, so the **reporter/newspaper** role was required for the
  wide-public credibility channel to exist at all — the village showing what
  function it was missing. At larger scale the same instrument would surface
  missing roles (a mediator, a rumor-broker, kin ties) rather than us
  hand-authoring them. Noted, not hand-forced.

### Deltas vs the directives (honest)
- **Language composition** (journals + newspaper prose) is a **template** here,
  not the 244000/246000 syntax faculty — that block builds in parallel
  (`bigville_lang_`); its files are untouched and NOT depended on. The seam is
  marked so the composed prose drops in later.
- **Night = per-tick** in the scaffold (each tick is a "day"); a richer
  fresh→gist→latent demotion pass over the emotional residual is the upgrade —
  the JournalEntry is the readable trace hook for it.
- Relationship priors modestly shift villager `seen_benevolent` (history), which
  is why the numbers differ slightly from the pure 245000 drama — reported, not
  hidden.

**What emerges (read off the graph, not scripted):** John holds UNDERMINE while
stating benevolence (deception gap); the villagers in the square see only
benevolence (`seen_hostile=0`, office occluded); Mary at the office door
witnesses the harm → infers **hostile** → forms a goal → makes a claim; the
reporter on the office beat also witnesses it → its credibility stance flips →
the **Herald** prints an **EXPOSURE** frame → the wide-public channel carries the
accusation to villagers who were never in earshot, flipping the low-charm
villagers while the most-charmed still back John. The cascade falls out of the
geometry + the reused rules.

---

## Architecture-rule compliance & provenance
- **Own engine**, built in-worktree from committed Rust source (`cargo build
  --release`), md5 `10f65be659e0d9a9290aff39f7f5b92a` — **byte-identical** to the
  block-245000 own engine (this scaffold adds **zero Rust**). Canonical shared
  `.so` never written through.
- **No agent decision in host Python.** The scheme (ss_choose_burn), the public
  face (bd_john_public_face), the inference (bd_mary_infers), the backing and the
  reporter's frame (bd_villager_backs) are all **graph rules**, unchanged. The
  host does only ingest (geometry → observation facts) + emit (graph → JSON).
- **Reporter/newspaper**: the reporter is another `Villager` node, so the
  **same** credibility rule decides its stance; the frame is READ from that
  decision (mechanical emit). The composed article headline is a **template**
  here — the syntax-carrying composition is the sibling block **246000
  (`bigville_lang_`)**; that seam is marked and **not** depended on (its files
  are untouched; nothing merged).

## Honest boundary
- **Small-cast scaffold only.** The 200-scale live version needs the separate
  **scale-verification probe** (measure interaction-ops vs N, expect ~linear;
  per `ozma_village_north_star`) — **not** run or claimed here. The scaffold is
  structured proximity-local so scale stays linear, but that is a design
  property, not a measurement.
- **A synthetic MODEL** of a political-drama mechanism, not a claim about real
  politics and not new social science. Assets in the scaffold are emoji/canvas
  (self-contained); Kenney CC0 is the recommended real-asset upgrade path.
- Absence/novelty claims are weak-by-construction; the prior-art positioning
  (Smallville et al.) is conceded above.
