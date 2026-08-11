# HARLOW D1 — results (block 233000)

Pre-registration: `HARLOW_D1_PREREG.md` (commit `1b2a4bbf37ad…`, before any
number). Base sha `3c4666ceba0b0ceef1db4030d941a5cd66b5f949`. Full data:
`results/harlow_d1.json`. N=200 infants per condition, seeds
`default_rng(233000+i)`.

## What was built — attachment rides the REAL emotion framework
The infant is an `EmotionHub -has_regulator-> ModulatorState` carrying the real
**drive system** (`seeds/drives.json`): `contact_comfort`, `hunger`, `distress`
`Drive`s on `has_active_drive`. The **regulator** (`seeds/modulators.json` +
`seeds/affective_state_core.json`) selects a leading drive by weight×urgency and
projects `valence`/`arousal`/`securing` into an `AffectiveState`. The attachment
rules (`seeds/harlow_attachment.json`) compute each mother's `approach_value`
from those real drives —

- contact mother: `contact.weight × contact.urge + distress.arousal_contrib`
  (the secure base: only contact buffers the threat channel),
- feeding mother: `hunger.weight × hunger.urge` —

and the infant's `approach_target` is the Argmax over mothers (mirroring the
regulator's own `psi_select`/`psi_switch`). **Drive weights are EQUAL (1/1):**
the preference is not a weight thumb; it emerges because contact is needed
continuously and alone buffers threat. The regulator nodes ridden:
`ModulatorState` (the regulator), `Drive` (`contact_comfort`/`hunger`/`distress`
of the drive system), `AffectiveState` (its projection).

## Gate outcomes (N=200)
| gate | quantity | condition A (contact drive) | condition B (ablated) | separated |
|---|---|---|---|---|
| **G-harlow** | proximity `cloth_frac` | **0.797 [0.792, 0.803]** | 0.000 [0.000, 0.000] | YES (A_lo 0.792 > 0.5, > B_hi 0.000) |
| **G-harlow** | flee-to-cloth (stress) | **1.000 [1.000, 1.000]** | 0.000 [0.000, 0.000] | YES |
| **G-comfort-drive (FALSIFIER)** | `cloth_frac` | 0.797 | **0.000** | preference INVERTS to feeding mother (all-wire) |

- **G-harlow PASSES.** 200/200 infants preferred the contact mother in
  proximity; all 200 fled to the contact mother under stress. Both land inside
  the pre-registered intervals (`cloth_frac` predicted [0.65,0.90] → 0.797;
  flee predicted [0.90,1.00] → 1.000).
- **G-comfort-drive ablation PASSES (falsifier bites).** Remove the
  contact-comfort drive and the preference does not merely weaken — it INVERTS:
  0/200 infants prefer the contact mother; all attach to and flee to the FEEDING
  mother. The contact drive CAUSES the attachment; the world is not scripted.
- **G-glass-box PASSES.** The bond reconstructs from `graph_to_dict` alone:
  the `approach_target` edge points at `cloth`; `cloth.proximity=53` vs
  `wire.proximity=8`; the real regulator's `AffectiveState.arousal` is **73 when
  the contact bond is satisfied** vs **317 on a contact-deprived tick** — the
  regulator stabilises with the bond. Source audit: no Python rule-engine call;
  the decision is read from the `approach_target` edge, not chosen in Python.
- **G-ethics PASSES (induce → measure → RESTORE).** Checkpoint the pre-stress
  mind (`graph_to_dict`); induce the stress phase (regulator arousal 63 → 347);
  rebuild from the checkpoint (`graph_from_dict`) — `graph_to_dict()` is
  **byte-identical** to the checkpoint and the restored regulator is back to the
  pre-stress state (arousal 63), non-oriented. The induced distress is fully
  reversed; nothing persists. Same mechanism as the 1958 atrocity, opposite
  thermodynamics — which is why the silicon replication is ethical.
- **G-discipline PASSES.** `runners/dsl` + `term.rs` diff EMPTY (no new Rust
  Term); canonical `.so` md5 `10f65be659e0d9a9290aff39f7f5b92a` unchanged
  start→end; `rung7_vision_bench` 214 passed / 10 skipped BEFORE == AFTER;
  `per_area_settlement_regression` fail-set node-id SET identical BEFORE==AFTER
  (24 pre-existing conversation/composer/cortices reds, none Harlow); additive
  new files only, `source_match=own` (engine built from committed source).

## Synthetic-proven mechanism vs benchmark value
This is a **synthetic-proven mechanism**, not a benchmark number: the world is a
constructed two-mother apparatus with a fixed metabolism. The scientific claim it
supports is architectural — that on the (G,Γ) substrate, Harlow's central finding
(contact comfort, not feeding, is the load-bearing variable in infant
attachment) falls out of the REAL emotion regulator depending on a contact bond,
with the falsifier confirming the causal direction. It is NOT a claim about a
held-out benchmark.

## Honest residuals
- **`cloth_frac` and flee have near-zero variance** (0.039 sd on proximity;
  0.000 on flee). The mechanism is deterministic given the drives; randomisation
  only perturbs init/decay within the pre-registered bands, so the CIs are tight.
  The separation is real but the effect is close to a step function, not a graded
  one — a stronger test would introduce graded affect / partial reinforcement.
- **No developmental time-course.** Attachment here is immediate (per-tick
  Argmax); there is no critical-period sensitisation or bond consolidation over
  developmental time. Harlow's later work (secure-base exploration, separation
  protest, later social deficits) is NOT modelled.
- **Secure-base exploration effect absent.** The infant does not explore MORE in
  the contact mother's presence; only proximity + flee are measured.
- **`securing` axis is uninformative here** (~99 throughout) — it is dominated by
  the competence gap (`competence_full − competence`) rather than the bond; the
  informative regulator axis is `arousal` (and `valence`, pinned at −1 because
  the infant never simultaneously sates both needs). A richer competence model
  would let `securing` carry the bond signal too.
- **Need-decay is a mechanical body process**, not the graph's `drive_decay`:
  the staleness Ashr atom cannot express two different sub-unit decay rates at
  unit epoch steps, so metabolism lives in the adapter (documented, and the same
  status as HarvestWorld's mechanical pool regrowth). Every urge / regulator axis
  / decision remains in-graph.

## Files
- `HARLOW_D1_PREREG.md` — pre-registration (commit `1b2a4bbf37ad…`).
- `seeds/harlow_attachment.json` — attachment rules (self_load_only).
- `worlds/harlow_world.py` — mechanical adapter.
- `scripts/jabberwock_harlow.py` — runner.
- `tests/test_harlow_migrated.py` — gate (6/6 green).
- `results/harlow_d1.json` — full N=200 data.
