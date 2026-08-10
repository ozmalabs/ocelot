# PRE-REGISTRATION — GENUINE texture recognition (pattern + colour), block 214000

Committed ALONE, before any measurement. Off `main` HEAD **`e4cf1dc239`**.
Seed block **214000–214999** (`python scripts/seed_claim.py 214000 214999` → verbatim below).

```
SEED CLAIM 214000-214999: CLEAN -- no collision DETECTED.
  Scope: 914 files with seed sinks; 617 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

## The honest null this attacks (blocks 209000 / 210000)

The 209000/211000 "texture" channel (`domains/doom_pattern_eye.py::col_texture_level`) is a CRUDE
SCALAR: per-column vertical luma-gradient ENERGY `Σ|Δluma|`, quantised 0..8. It answers only "is
this surface busier than the plain wall?". It gets the edge-DENSE doors (sec26/sec69 read level 8,
≈60× plain wall) but MISSES the texture-FAINT doors — 210000's measured residual: **sec83 reads
level ~2, sec85 reads level ~4 on their openable faces → never recognised, `n_use=0`, 0 opens/10**
— which a human recognises easily. It misses them because ONE energy number DISCARDS:

- **(a) PATTERN** — the ARRANGEMENT of edges (panels / frame-lines) collapsed to one magnitude.
- **(b) COLOUR entirely** — the channel is luma-only `(77R+150G+29B)>>8`, so a door differing in
  HUE / material from its wall at similar edge-density is invisible. Luminance carries structure;
  **colour is a SIGN**, and there is NO colour sign today.

This block replaces the edge-density SCALAR with a richer, still-INTEGER texture DESCRIPTOR (pattern
+ colour-as-sign), matched against the held door/switch concept, and MEASURES whether it recovers
the faint doors sec83/sec85 that the scalar missed.

## HARD CONSTRAINT (unchanged from 209000) — no oracle

Every descriptor value comes ONLY from SEEN rendered RGB pixels — integer luma AND the integer
colour channels (R, G, B). The VizDoom **depth buffer / sectors / labels buffer / texture names are
NEVER read by the eye** — they are a SCORING ORACLE only (labelling door vs wall columns for AUC).
AST-audited (new functions added to `_assert_no_oracle_in_eye`'s scope). Colour is a rendered-pixel
sign, not an oracle: `rgb[..., 0/1/2]` are channel indices, not `["depth"]`/`["label"]`/`["texture"]`.

## The richer descriptor (integer, SEEN RGB only) — measured, not assumed

**1. COLOUR-as-a-sign** — `col_colour_level(rgb)`: per-column INTEGER CHROMA CONTRAST from the
frame's ambient wall. Per column, mean (R,G,B) over the central band → integer luma
`m=(77R+150G+29B)>>8` → chroma vector `(R−m, G−m, B−m)`. Ambient = per-channel MEDIAN chroma across
columns (the surrounding wall). `colour_level = min(K, L1(chroma_col − chroma_ambient) // COL_DIV)`,
0..8. A door whose material/hue differs from its wall reads high **even at matched luma-gradient**; a
plain wall IS the ambient → reads ~0. This is the sign the luma-only channel throws away. Ambient
subtraction is the same self-normalising idiom the 211000 geometry channel uses (contrast, not
absolute colour → no fixed door-colour is hard-coded; a door is "a region whose material contrasts
with its wall").

**2. PATTERN-as-arrangement** — `col_pattern_signature(rgb)`: per-column INTEGER 4-bin orientation
histogram of the luma gradient over the central band. Bins by dominant gradient direction
(horizontal-edge `|gx|>|gy|`, vertical-edge `|gy|>|gx|`, and the two diagonal signs), each bin the
quantised summed |gradient| magnitude. The ARRANGEMENT (ratio of horizontal frame-lines to vertical
edges) distinguishes a door's panel/frame structure from isotropic busy-ness AT MATCHED TOTAL
ENERGY. Matched against the prototype's held pattern signature by L1 over the histogram.

**Held concept.** The door/switch prototypes gain `colour_sig` and a `pattern_sig`, CALIBRATED from
the STRONG doors (sec26/sec69 — clear exemplars; the competent-man concept "knows what a door's
texture is"). The FAINT doors sec83/sec85 are the disjoint TEST set. Calibrating a concept from
clear positive exemplars is held knowledge, not an oracle leak (the strong and faint doors are
different sectors; the test never reads a door label into the descriptor).

**Match (graph-native).** A NEW seed `seeds/pattern_texture_signature.json` (self_load_only,
default-OFF on its own params gate) with its own `TextureLibrary` + prototypes carrying the richer
descriptor, and match RULES computing an L1 distance including colour (+ pattern) with a
colour-sufficient recognition path (a region matching the door's colour-contrast even at low tex).
The 209000 seed `pattern_recognition.json` and its 10 tests are UNTOUCHED → byte-identical. The
adapter only quantises pixels and reads recognition back; no Python decision picks the recognition.

## SCORING ORACLE (depth buffer — SCORING ONLY, never fed to the eye)

Door-vs-wall column labels for AUC come from the depth buffer: warped to a door's openable face and
oriented at it (210000's `DOORS` table, reproduced from WAD linedef specials), the door is the near
central surface. A column is labelled `door` iff its central-band median depth is within the door's
near-depth band (nearest occluding surface), `wall` on plain-wall frames (no door in view). Depth is
used ONLY to label; the descriptor sees pixels only.

## GATES (pre-registered bars)

- **G-faint (HEADLINE).** On sec83/sec85 openable-face approach frames vs plain-wall control frames:
  report (i) recognition rate on the faint-door frames, (ii) plain-wall FALSE-POSITIVE rate, (iii)
  AUC of the richer door-match score (door-face central columns vs plain-wall central columns) and
  the OLD scalar's AUC on the same columns, with bootstrap 95% CIs.
  - **Outcome 1 (RECOVER):** richer AUC > old-scalar AUC (CI-separated) AND faint-door recognition
    > 0 at a plain-wall FP rate ≤ the old scalar's. The scalar was throwing the signal away.
  - **Outcome 2 (CONTEXT-LIMITED):** if sec83/sec85 are genuinely near-identical to their wall in a
    single frame across ALL three channels (richer AUC ≈ old ≈ 0.5), report THAT with the number and
    name CONTEXT / MEMORY / expectation (a human knows a door is there) as the mechanism a
    single-frame eye lacks. NOT hidden as a failure; NO oracle leaked to fake recognition.

  Both outcomes are honest results. Whichever is true is reported straight.
- **G-colour.** Colour contributes independently: (i) colour-only AUC of door-face vs wall central
  columns > 0.5 (CI excludes 0.5) on the STRONG doors (a real door-vs-wall colour contrast exists);
  (ii) a synthetic region differing from its wall ONLY in colour at MATCHED luma-gradient is
  recognised by the colour channel and is INVISIBLE to the luma-only scalar.
- **G-pattern.** Pattern carries signal beyond energy: a synthetic control with two patches of EQUAL
  total |Δluma| energy but different ARRANGEMENT produces different pattern signatures → different
  recognition (energy matched, pattern separates).
- **G-no-oracle.** AST + runtime audit: the new descriptor functions (`col_colour_level`,
  `col_pattern_signature`) read ONLY rendered RGB (luma + channels 0/1/2); NO `depth_buffer` /
  `labels` / `sectors` attr, NO `["depth"]`/`["label"]`/`["texture"]` subscript, NO texture NAME.
  The prereg states exactly what each samples.
- **G-no-regression.** The 10 `test_pattern_recognition_migrated` stay GREEN under the shared-file
  change (the 209000 seed + `col_texture_level` are untouched; new functions are additive). 210000's
  strong-door opens (sec26/sec69) still work. The 34-file regression set BEFORE == AFTER.
- **G-discipline.** Integer-native (no float reaches the graph). Default-OFF byte-identical (new
  seed self_load_only + params gate; new functions imported by nothing existing). Canonical `.so`
  md5 stays **`793ce09ed498a749abb79aeaea44b92e`** (NO Rust — `term.rs` + whole `runners/dsl` diff
  EMPTY). Oracle `rung7_vision_bench` BEFORE == AFTER. `source_match` reported.

## Scope discipline

This block owns ONLY the TEXTURE descriptor (`col_texture_level`'s successor: `col_colour_level` +
`col_pattern_signature`) and the held texture signature. It does NOT touch the 211000 geometry
feature (`col_structural_level` / `col_geometry_level`) nor the 210000 operate path
(`doom_operate.py` / `doom_operate.json`). It does NOT touch `VISION_PROTOCOL.md`. Committed to the
worktree branch; NOT merged to main.

## Honesty

Lead with: this replaces edge-density salience with genuine texture recognition (pattern +
colour-as-sign) against the held concept. Report the faint-door outcome STRAIGHT (recovered, or
context-limited) with the number. Named follow-ons: full colour-category grounding, learned texture
prototypes, and the context/memory channel if the faint doors need priors a single frame cannot
supply.
