# LS20 FLASH-ONSET-GUIDED MECHANIC DISCOVERY — PRE-REGISTRATION (block 223000)

**The owner's claim under test:** *"The flash when the avatar goes to the shape
in the map is a salience indicator of what the rules are."* The transient flash
on avatar↔shape contact is ls20's OWN supervision signal: it LOCALISES (where a
rule matters) and TIMES (which action-step fired it) the mechanic. This attacks
222000's measured LIVE residual: 222000's blind per-cell model did NOT converge
live because the avatar is multi-colour and NOT colour-separable from static
structure, with a move+trail/consume dynamic — the flash is exactly what separates
the moving/interacting avatar from the static field and marks the consume event.

Block `223000` claimed via `python scripts/seed_claim.py 223000 223999` →
**"SEED CLAIM 223000-223999: CLEAN -- no collision DETECTED."** (927 files with
seed sinks; 630 unresolved sinks tree-wide). Verbatim `check_claim` re-run and
asserted in `tests/test_ls20_flash_migrated.py`.

## THE MECHANISM (assembled; graph-native; NO new Rust)

Flash-guided discovery = the SAME sd-loop `TransformDecode`/`DimInfer` discovery
as 222000, but curiosity/ATTENTION is routed by the **flash onset** (which region
+ which action-step) instead of by blind mode-colour. The flash only changes
WHERE/WHEN the agent probes first; the transform itself is STILL DISCOVERED by the
identical sd-loop. **The flash is a POINTER (salience + timing), DISTINCT from the
persistent TRANSFORM it announces — the flash is TRANSIENT (it reverts), the
rule's effect PERSISTS.**

- **Flash detection = the EXISTING onset stream** (blocks 135000/171000/191000):
  the 2-D `retinal_onset_2d` seed + `photon_transduce_onset` Rust kernel mint
  `RetinalOnsetEvent{column_index,row_index,magnitude_db,epoch}` when a cell's
  transduced drive departs its OWN adapting floor by a dB threshold. A flash is a
  bright transient → a strong onset. NO new flash detector. The general onset
  machinery that serves Doom / the photon eye.
- **Flash-guided attention = a graph RULE** (`fg_pick_flash`, new seed
  `seeds/ls20_flash.json`): Argmax(`magnitude_db`) over the onset cues copied into
  the agent graph → the attended flash location. (The DECISION "which onset to
  attend" is a rule, exactly like 222000's `pc_probe_pick` Argmin curiosity.)
- **The transform = the identical sd-loop** (222000's `_recognise_transform`);
  the ONLY difference between arms is the REGION-SELECTOR fed to it: blind =
  mode-colour over ALL changed cells; flash = mode non-bg-non-flash colour among
  changed cells WITHIN a window around the attended flash onset.

## HOW CIRCULARITY IS AVOIDED (the fatal trap — stated explicitly)

The flash is a REALISTIC transient, co-located with rule-firing but transient, and
it does **NOT encode the transform**:

1. **Identical appearance for all 10 actions.** The flash is a fixed-colour
   (`FLASH_COLOUR`) transient blob at the rule object's contact location. Given
   ONLY the flash you cannot tell move_up from rotate — you must read the object
   geometry. The flash carries WHERE + WHEN, never WHAT.
2. **Both arms DISCOVER the transform via the IDENTICAL sd-loop.** The flash only
   changes which region the sd-loop is pointed at first (attention order).
3. **The blind arm ALSO converges** (222000 proved offline F1 1.0). The
   comparison is SAMPLE-EFFICIENCY (probes-to-converge), not can-converge.
4. **Anti-rig control:** the flash advantage is measured across a CLUTTER sweep
   `n_distractors ∈ {0,1,2,3}`. At `n_distractors=0` (a clean world like 222000)
   the flash is pre-registered to give NO advantage (blind's mode-colour already
   localises) — if flash won even there, the flash would be rigged. The advantage
   must GROW with clutter, grounded in 222000's measured real-ls20 reality (52
   changed cells/action, avatar a minority, not colour-separable).

If flash-guided does NOT beat blind under clutter, the owner's claim is
**FALSIFIED** and the null is reported STRAIGHT.

## THE METRIC TRAP (inherited from 222000)

Score on the CHANGE-SET (strict changed-cell F1 + value-accuracy), NEVER raw
per-cell accuracy (persistence aces raw ~99%).

## GATES (pre-registered thresholds)

- **G-flash-detects.** On a persistent arena whose static field is adapted, a
  FLASH frame produces onset events that (a) LOCALISE to the flash cells and (b)
  have `magnitude_db` CI-separated ABOVE both the ambient/distractor-motion
  onsets AND the (silent) static field. Pre-registered: flash-cell mean onset
  `magnitude_db` bootstrap-CI lower bound > distractor-motion onset upper bound,
  over ≥ 30 random arenas; and the Argmax-`magnitude_db` onset localises to a
  flash cell in ≥ 90% of arenas. The real `GraphEye` 2-D onset stream, no
  bespoke detector.
- **G-sample-efficiency (HEADLINE — FALSIFIABLE).** Observations (world
  queries/probes) until the learned model reaches held-out change-set strict-F1
  ≥ `τ = 0.9`, flash-guided vs blind (222000's mode-colour control), at clutter
  `n_distractors = 2`, over ≥ 30 seeds, 1000-resample bootstrap 95% CI.
  Pre-registered PASS: flash-guided mean observations-to-converge CI-separated
  BELOW blind (flash upper < blind lower). Reported alongside the full clutter
  sweep {0,1,2,3}. **This gate CAN FAIL** (if the cell-diff already localises as
  well as the flash → null reported straight).
- **G-pointer-vs-content.** A CONFLATE arm that treats the flash cells AS the
  transform (decodes the object INCLUDING the transient flash + predicts the
  flash as a persistent change) scores WORSE held-out change-set strict-F1 than
  the SEPARATE arm (flash = pointer only; decode the persistent object EXCLUDING
  the transient flash). Pre-registered: conflate F1 CI-separated BELOW separate
  F1 — the transient/persistent separation is load-bearing, not decorative.
- **G-live (HONEST, bounded n).** On real ARC-AGI-3 ls20 (`--game ls20-9607627b`,
  budget ≤ 60 steps; auth verified BEFORE measuring, key from
  `/home/matt/ozma/internal/.env`, NEVER printed/committed): does flash-onset
  attention separate the moving avatar from static structure / mark the consume
  event and IMPROVE live change-set F1 over 222000's blind live NULL (0.0)?
  Report the REAL number. If it still does not converge in budget, report the
  null STRAIGHT + what the flash DID localise. If the API is
  unreachable/rejected/rate-limited, STOP and report — NEVER fabricate.
- **G-graph-native + SOURCE-AUDIT.** Flash detection = the onset stream
  (existing); flash-guided attention = the `fg_pick_flash` rule; the adapter is
  mechanical (perceive → onset → attend → sd-loop discover → apply → measure).
  Source-audit: the agent's prediction/transform functions reference NO
  ground-truth `_MOVE`/`_XFORM`/flash-transform table — the mechanic is minted
  from observation. PASS = empty.
- **G-discipline.** Integer-native in-frame (the `Transform` is the cross-frame
  map). Default-OFF byte-identical: 222000/221000/220000/218000 ls20 tests
  unchanged with the flag off. Canonical `.so` md5 `793ce09e…` UNCHANGED (no
  Rust). `term.rs` + whole `runners/dsl` diff EMPTY. Oracle `rung7_vision_bench`
  BEFORE==AFTER. 34-file regression BEFORE==AFTER. `source_match` reported.

## FILES (to be created — NO 222000 file touched)

- `worlds/arc_ls20_flash.py` — the flash world: clutter arena + transient flash
  (fixed colour, all actions) + the onset-eye driver + the three region-selectors
  (blind / flash-separate / flash-conflate). Reuses 222000's
  scene/physics/discovery/apply/metrics unchanged.
- `seeds/ls20_flash.json` — `fg_pick_flash` (Argmax-magnitude attention rule) +
  the flash-guided attend wiring; depends on `ls20_percell`. Default-OFF
  (`flash_on==1`).
- `scripts/arc_ls20_flash_measure.py` — G-flash-detects + G-sample-efficiency
  (clutter sweep, powered) + G-pointer-vs-content + source-audit.
- `scripts/arc_ls20_flash_live.py` — the bounded LIVE half.
- `tests/test_ls20_flash_migrated.py` — the gate tests + claim re-check +
  default-OFF byte-identity.
- `results/arc_ls20_flash_{powered,live}.json` — the measured numbers.

## LEAD

Lead with SAMPLE-EFFICIENCY vs the 222000 blind baseline — that is the test of
the owner's claim. The flash detector is the GENERAL onset stream; the attention
is discovered routing; the win must be MEASURED (the claim can fail).
