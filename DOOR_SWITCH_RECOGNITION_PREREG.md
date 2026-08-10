# PREREG — THE COMPETENT-MAN JABBERWOCK RECOGNISES DOORS/SWITCHES ON SIGHT (block 209000)

*Committed ALONE, before any result number. Seed block **209000–209999**
(`scripts/seed_claim.py 209000 209999` → `CLEAN`). Off `main` HEAD
**`e8105953e4`**. Engine canonical **`793ce09ed498a749abb79aeaea44b92e`**
(`runners/dsl/python/substrate_rs/_native.abi3.so`; the `.pth`/symlink engine
resolves to the shared checkout). NO Rust: `term.rs` + whole `runners/dsl`
diff EMPTY. Seed + adapter + existing Terms only.*

## 0. What this is — PERCEPTION + RECOGNITION + INVESTIGATION, not rediscovery

The Jabberwock is a COMPETENT ADULT. It **already HOLDS the concepts `door` and
`switch`** — seeded as graph data (a legitimate competent-man domain bootstrap),
each carrying a SIGNATURE (differing framed/recessed geometry + distinct surface
texture) and an AFFORDANCE (door gates passage / operable; switch is a marked
surface whose operation changes a REMOTE sector). This block does NOT rediscover
"door" from affordance-poking (an earlier framing, rejected). It does three
things, all as graph RULES over the HELD concepts:

1. **PERCEIVE** — the eye sees REAL rendered Doom pixels + SEEN depth-from-motion
   and registers, per azimuth region, TWO salience channels:
   - **GEOMETRY difference** — a region that breaks the wall's depth regularity
     (a recess/frame/opening in the SEEN depth-from-motion profile) is
     under-compressed → salient.
   - **TEXTURE difference** — the rendered wall-surface appearance
     (luma + vertical-structure pattern) sampled from REAL Doom frames; a
     door/switch surface differs from plain wall → under-compressed → salient.
   BOTH channels jointly drive salience.
2. **RECOGNISE** — a RULE matches the salient region's (geometry-feature,
   texture-feature) against the HELD `door`/`switch` prototype signature
   (descriptor-vector nearest-prototype, the `figure_geometric_shape` idiom:
   `Lt(Magnitude(VecSub(region_feat, held_sig)), θ)`) and recognises it AS a
   door/switch.
3. **INVESTIGATE** — because the held concept carries the affordance, recognition
   mints an investigation Goal (orient/approach/attempt-use) at the recognised
   region.

## 1. Setting (declared PRIMARY, honest boundary)

Real E1M1 (Ultimate Doom `DOOM.WAD`), RGB24 320×240. A short scripted forward
approach gives parallax so depth-from-motion (158000) yields SEEN per-column
depth; the texture channel samples the current frame's rendered RGB luma. The
VizDoom **depth buffer** and **sectors geometry** are a SCORING ORACLE ONLY
(per-column structural-anomaly labels for precision/recall); the **labels buffer
/ any texture NAME is NEVER read** by the eye (161000/203000 discipline).

Honest scope, pre-declared: autonomous live operation of a DR door in E1M1 (USE →
ceiling rises) was probed and does NOT reliably trigger under scripted/​autonomous
navigation of the open start area (measured: 0 door-open events over 600+1200
USE-spammed tics). Therefore the HEADLINE is **RECOGNITION + INVESTIGATION**
(orient/approach/attempt-use); a live door OPEN is reported as the confirming
step **where feasible** (a deterministically-posed USE attempt), and named as a
residual otherwise — never faked. Switch's NON-LOCAL effect (operate here → remote
sector opens) is the harder credit-assignment piece and is scoped as a follow-on;
doors/openings (local, framed geometry) are the core.

## 2. GATES (pre-registered; numbers land in the RESULTS file only)

- **G-salient (both channels).** A structural door/opening/frame region on real
  E1M1 is flagged SALIENT by the eye WITHOUT being told. Show BOTH channels
  contribute: a geometry-only difference and a texture-only difference each raise
  salience above a plain-wall region; together higher. A plain uniform wall is
  NOT flagged (false-positive control). Report the salience numbers (per-region
  geometry-residual, texture-residual, combined) and the wall-vs-anomaly
  separation.
- **G-recognise.** The salient region is matched to the HELD `door`/`switch`
  concept and recognised. **Concept-scramble control:** corrupt the held concept
  signature (descriptor_vec) and recognition MUST fail — proving the held concept
  does the work, not a hardcoded detector. Report recognition precision/recall
  over a labelled set of door/opening regions vs non-door salient regions (label
  source = depth-buffer/sectors oracle + builder eyeball verification on the
  saved PNGs — never a texture name to the eye).
- **G-no-oracle (load-bearing).** Source-audit + a runtime assertion that the
  texture/appearance signal derives ONLY from rendered RGB pixels the eye
  sampled; the pipeline never reads a WAD texture name or the labels buffer.
  State EXACTLY what the eye samples (per-column RGB luma band + vertical
  gradient), and that the depth buffer / sectors are scoring-only.
- **G-investigate.** Recognition triggers the investigation (a graph-native
  Goal: orient/approach/attempt-use at the recognised region). Where feasible,
  a deterministically-posed USE attempt at a real door is shown to OPEN it
  (sector ceiling rises); otherwise the attempt is shown and non-opening named.
- **G-discipline.** Integer-native where the substrate is; **default-OFF
  byte-identical** (a `context`-gated params node; absent it every existing path
  unchanged); canonical `.so` md5 **`793ce09e…` UNCHANGED**; `term.rs` + whole
  `runners/dsl` diff EMPTY; oracle `bash scripts/rung7_vision_bench.sh`
  BEFORE==AFTER; 34-file `bash scripts/per_area_settlement_regression.sh`
  BEFORE==AFTER (failing-id SET, not a count); `source_match` reported.

## 3. Pre-registered abandon / narrow conditions (honesty)

- If depth-from-motion is too noisy to separate geometry anomalies on real frames
  (the genuine hard part), REPORT the number and LEAN on the texture channel,
  naming depth-from-motion geometry as the residual — a partial, honestly-measured
  result beats a faked full one.
- If texture-on-real-pixels does not reliably resolve door/switch surfaces, report
  the straight number and narrow the claim to whichever channel separates.
- The concept-scramble control MUST kill recognition; if it does not, the
  "recognition" is a hardcoded detector and the G-recognise claim is WITHDRAWN.

## 4. What is graph-native vs adapter (architecture rule)

- **Graph (seed `door_switch_recognition.json`):** the held `door`/`switch`
  Concept+prototype nodes (signature + affordance); the salience rule
  (geometry-residual + texture-residual → SalientRegion score); the recognition
  rule (region-feature vs held prototype → `recognised_as`); the investigation
  rule (recognised + affordance → mint investigate Goal). Every DECISION is a
  rule/Term.
- **Adapter (`domains/doom_door_switch.py`, mechanical I/O only):** capture real
  frames; per-column SEE geometry (depth-from-motion) + texture (RGB luma band +
  vertical gradient); write Obs/Region nodes; `run_rules`; read recognition;
  score against the depth/sectors oracle. No conditionals over graph state.
