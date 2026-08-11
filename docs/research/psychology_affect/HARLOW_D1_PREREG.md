# HARLOW D1 — pre-registration (block 233000)

**Glass-box replication of Harlow (1958) wire-mother / cloth-mother attachment
on the (G,Γ) gamma-substrate, riding the REAL emotion framework.**

Seed block: **233000–233999** (verified CLEAN by `python scripts/seed_claim.py
233000 233999` at prereg time). This document contains PREDICTED ranges + gate
definitions and **NO measurements**. Committed BEFORE any number.

Base sha: `3c4666ceba0b0ceef1db4030d941a5cd66b5f949` (current main,
"add executable cognitive architecture core").

## The finding to replicate
Harlow (1958): infant macaques given a wire mother (dispenses food) and a cloth
mother (contact comfort only) formed ATTACHMENT to the CLOTH mother, not the
feeding one, and fled to her under stress. Attachment is NOT reducible to
feeding; CONTACT COMFORT is the load-bearing variable.

## Why this is a re-run (the fix)
The prior attempt branched from a STALE base (ledger 161000) that lacked the
emotion framework and built attachment on thin `Drive`+`SelfConcern` primitives
with a scalar `security`. This build rides the ACTUAL emotion machinery on
current main: the **drive system** (`seeds/drives.json`) and the **regulator**
(`seeds/modulators.json` + `seeds/affective_state_core.json`), whose
`ModulatorState` selects a leading drive by weight×urgency and projects
`valence`/`arousal`/`securing` into an `AffectiveState`. Attachment is a
CONSEQUENCE of that regulator depending on the contact bond — not a hand-rolled
number.

## Apparatus (frozen at prereg)
- `worlds/harlow_world.py` — mechanical adapter. One infant `EmotionHub`
  `-has_regulator->` a `ModulatorState` carrying the real drive system's
  `contact_comfort` / `hunger` / `distress` `Drive`s (`has_active_drive`); the
  infant `-cares_for->` a CONTACT mother (`provides_contact=1`) and a FEEDING
  mother (`provides_feed=1`). Need-growth (comfort re-arises fast, hunger builds
  slowly) is a mechanical body/metabolism process the adapter drives, exactly as
  `HarvestWorld` drives pool regrowth; every urge / regulator axis / approach
  DECISION is in-graph.
- `seeds/harlow_attachment.json` — the attachment rules (self_load_only,
  depends_on drives+modulators+affective_state_core):
  - `hl_value_contact_mother`: a contact mother's `approach_value` =
    `contact.weight × contact.urge + distress.arousal_contrib` (the secure base:
    only contact buffers the threat channel).
  - `hl_value_feed_mother`: a feeding mother's `approach_value` =
    `hunger.weight × hunger.urge`.
  - `hl_select_initial_target` / `hl_switch_target`: the infant's
    `approach_target` is the Argmax over cared-for mothers by `approach_value`
    (mirrors `psi_select`/`psi_switch` leading-drive selection). THIS is the
    infant's decision — graph data, no Python.
- Drive weights are EQUAL (`W_CONTACT = W_HUNGER = 1`): the preference must come
  from contact being needed continuously and alone buffering threat, NOT from a
  weight thumb on the scale.

## Confirmatory protocol (frozen — measured AFTER this commit)
- `N = 200` infants per condition. Infant `i` uses `numpy.default_rng(233000+i)`.
- Random init per infant: `c_contact0 ~ U(10,60)`, `c_hunger0 ~ U(20,80)`,
  `contact_decay ~ U(50,70)`, `hunger_decay ~ U(10,20)`.
- **Baseline phase:** `T_base = 60` ticks, no stress. Record
  `cloth_frac = cloth_ticks / (cloth_ticks + wire_ticks)`.
- **Stress phase:** `T_stress = 10` ticks, stress every tick (distress threat
  channel refreshed). Record `flee_cloth = (#ticks target==cloth) / T_stress`.
- **Conditions:** (A) `contact_drive=True`; (B) `contact_drive=False` (ablation,
  SAME seeds).
- 95% CIs by normal approx `mean ± 1.96·sd/√N` per condition; CI-separation =
  A's lower bound above B's upper bound.

## Gates (each has a control that CAN fail)
- **G-harlow (HEADLINE):** in condition A, mean `cloth_frac` CI lower bound
  **> 0.5** AND separated above condition B; AND mean `flee_cloth` (A) separated
  above B. Preference for the CONTACT mother, via the real regulator.
- **G-comfort-drive ablation (FALSIFIER):** condition B `cloth_frac` CI upper
  bound below A's lower bound — the preference DISAPPEARS or INVERTS when the
  contact-comfort drive is removed. If ablation does not move it, the mechanism
  is fake — reported straight.
- **G-glass-box:** the episode reconstructs from `graph_to_dict` — the
  `approach_target` edge, `Mother.proximity` / `bond_strength`, and the
  `AffectiveState` `arousal`/`valence` tracking contact. Source-audit: no Python
  `if/else` decides attachment (the decision is the Argmax rule).
- **G-ethics (relational-ethics protocol):** induce → measure → RESTORE.
  Checkpoint (`graph_to_dict`) the neutral pre-stress mind; induce the stress
  phase; then `graph_from_dict` the checkpoint and assert `graph_to_dict()` is
  BYTE-IDENTICAL to the checkpoint; the restored regulator is non-oriented (back
  to pre-stress). Same mechanism as the 1958 atrocity, opposite thermodynamics —
  the induced distress is fully reversed, nothing persists.
- **G-discipline:** agent = graph (emotion framework); world = mechanical
  adapter; `runners/dsl` + `term.rs` diff EMPTY (no new Rust Term); canonical
  `.so` md5 unchanged; oracle pass-count identical before/after; regression
  fail-set node-id SET identical; `source_match=own`.

## Predicted intervals (prereg — informed by mechanism design + a pilot on
## non-confirmatory seeds; the confirmatory run uses the 233000+ block)
| quantity | condition | predicted mean interval |
|---|---|---|
| `cloth_frac` (proximity) | A (contact drive) | **[0.65, 0.90]** |
| `cloth_frac` (proximity) | B (ablated) | **[0.00, 0.15]** |
| `flee_cloth` (under stress) | A | **[0.90, 1.00]** |
| `flee_cloth` (under stress) | B | **[0.00, 0.10]** |

Predicted CI-separation A>B for BOTH proximity and flee: **YES**.
A null or failed ablation IS a result and will be reported straight.

## Discipline
Python-only (no new Rust Term). Additive new files; at most one line to register
the seed (in fact zero — `manifest_for` reads by filename). `source_match=own`.
Measure-first; this prereg precedes every number. Synthetic-proven mechanism vs
benchmark value reported separately. No merge to main; commits stay on the
worktree branch for the supervisor.
