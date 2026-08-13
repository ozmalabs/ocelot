# The seven real CAN consumers — per-consumer audit, before any migration/removal code — PREREG

**Charter, verbatim:** *"remove the old can and replace it with the new one."*
Per `CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`'s own unhedged verdict (§7,
"replace"), this is the intended end state. This document is the Phase-1
audit required before touching any consumer's code, per this session's own
standing discipline against post-hoc rationalization: read every real
consumer's actual calling code, decide precisely what it needs, and only
migrate what can be honestly and fully migrated. A partial result — N of 7
consumers moved, M correctly left on the continuous mechanism, each blocker
named precisely — is the expected, valuable shape of this rung's outcome,
not a shortfall against the charter.

**Method.** `CLAUDE.md` in full, "SHAPE IS ACQUISITION, RULE IS EXECUTION"
and "SHAPES, NOT NUMBERS" re-read directly. The four docs this arc already
produced, read in full and quoted where load-bearing:
`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md` (design, verdict: replace),
`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` (items 1-3 built, item 4 partial),
`LOGODDS_GENERATOR_RESULTS.md` (item 4 completed — graded reweighting via a
separate evidence-count ledger, rendered on demand, never written back to
the edge), `LOGODDS_DIMINFER_RESULTS.md` (automatic recognition of the
evidence-count generator). Every one of the seven consumers named in the
orchestrating session's own pre-dispatch grep was opened and read in full
(not re-grepped), including the Rust functions it actually calls
(`runners/dsl/src/can_ops.rs`, `runners/dsl/src/py.rs`'s PyO3 bindings) and
the seed the native mechanism ships in (`seeds/can_native_reimplementation.
json`, `seeds/evidence_axis_infer.json`). One factual correction to the
pre-dispatch grep's own line attribution is reported below (§1, consumer 2)
— the grep matched a docstring mention, not the file's real call site; this
document reports what the code actually calls, confirmed by direct read.

---

## 0. Two blockers that recur across five of the six non-Bigville
consumers — named once here, cited by number below rather than re-derived
seven times

**Blocker A — no native non-mutating counterfactual ("what-if") predictor
exists.** `mt_mean_field_with_h_override` (`can_ops.rs:479`) and the pair
`mt_energy`/`mt_frustration_given_state` evaluated on an ARBITRARY predicted
marginal dict (never written to the graph) answer "what would the network's
state/energy/frustration be if this one node's field were X, without
touching the graph." This is a genuinely different computational object
from anything the native mechanism provides: `run_rules()` (item 3's
discrete-async update) always MUTATES real graph state — there is no
"simulate N rule-firings and report the result without committing" facility
anywhere in `rewrite.rs`/`term.rs` (grepped for `dry_run`/`speculative`/
`simulate` before writing this line: nothing). Building one is real,
unscoped design work (snapshot/restore semantics, or a pure functional
multi-step evaluator) — squarely the kind of "genuinely new machinery" the
task's own scope boundary reserves for a dedicated follow-on rung, not
attempted here.

**Blocker B — Hebbian graded reweighting's native half is intentionally
non-materializing, so nothing downstream of it can read a native strength.**
`LOGODDS_GENERATOR_RESULTS.md` §2 built the render
(`log_odds = ln((confirm+1)/(disconfirm+1))`) as a PURE comparator,
confirmed live to "never touch graph state" (§2, §4(b): `dict(node.attrs)`
identical before/after every `evaluate()` call) — a deliberate design
choice, not an oversight, matching the `cmp_value_lex`/`mt_mean_field_
marginal`-cross-check precedent of "pure comparator kept separate from
canonical storage." Nothing writes the log-odds value (or the raw
`evidence_confirm`/`evidence_disconfirm` counts) back onto the
`causal_influence` edge's `weight` attr, and `LOGODDS_GENERATOR_RESULTS.md`
§5 confirms by grep that no existing consumer reads `has_latent_dimension`
or the evidence counters at all. This means: wherever a Python consumer's
actual JOB is to make an edge's `weight` stronger so a SUBSEQUENT relaxation
(continuous OR native discrete) feels the reinforcement — i.e. `can_ops.rs
::hebbian_update_J`'s actual role — there is no native mechanism that does
that job today. Wiring the log-odds render into a `weight` write-back (or
into the discrete update rule's own local-field read) is a real, un-sized
integration DECISION (does every reweight event trigger a `set_attr`?
does this collide with the render's own deliberate non-materializing
design?) — not a small closing move, and not attempted here.

Both blockers are consequences of what was explicitly NOT built in the
three prior rungs, confirmed by direct re-reading of their own "what this
does NOT establish" sections, not new findings invented for this document.

---

## 1. The seven-consumer audit table

| # | Consumer | Actual can_ops call site(s) (file:line) | What it DOES with the output | Native equivalent exists? | Buildable this rung? | Verdict |
|---|----------|----------------------------|-------------------------------|---------------------------|----------------------|---------|
| 1 | `domains/drive_curiosity.py` | `probe_via_what_if` (`:76` `mt_mean_field_marginal`, `:77-78` `mt_mean_field_with_h_override`) | Non-mutating counterfactual: predicts network-wide σ change if one ambivalent concept's field were perturbed by a fixed delta; ranks candidates by total predicted change (info gain). `find_ambivalent_nodes` (`:43-62`) itself makes ZERO can_ops calls — pure `state`-attr threshold read, already representation-agnostic. | No (Blocker A) | No | **BLOCKED** — stays continuous. Blocker A. |
| 2 | `domains/insight_detection.py` | `consolidate_insight` (`:167` `mt_hebbian_update_J`) | Elevated Hebbian reweighting of `causal_influence.weight` on the newly-discovered basin, so the deepened basin resists a subsequent perturbation. **Correction to the pre-dispatch grep's own attribution**: `relax_to_marginal` appears only in this function's DOCSTRING (`:156`, describing what a CALLER already did), not as a call in this file — confirmed by `grep -n "relax_to_marginal" domains/insight_detection.py` returning exactly one hit, the docstring line. `detect_insight`/`read_previous_state`/`compute_delta_f_via_substrate` make no can_ops calls at all (pure Python + the substrate's generic Term-tree evaluator, already representation-agnostic). | No (Blocker B) | No | **BLOCKED** — stays continuous. Blocker B. |
| 3 | `domains/insight_seeking.py` | `find_hot_nodes` (`:53` `node_local_frustration`); `predict_perturbation_impact` (`:81` `mt_mean_field_marginal`, `:82` `mt_audit_basin`, `:85` `mt_mean_field_with_h_override`, `:98` `mt_energy`, `:108` `mt_frustration_given_state` — the LAST TWO evaluated on a hypothetical predicted marginal that is never written to the graph); `seek_insights` (`:157` `mt_relax_to_marginal`) | Sweeps 6 fixed h-perturbations per hot node, predicts ΔE/ΔF for each WITHOUT mutating the graph, ranks candidates by predicted energy drop. This is Blocker A's exact shape, compounded: even `mt_energy`/`mt_frustration_given_state` here are not reading real graph state, they are reading an UNGROUNDED hypothetical dict — something no native decode/rule path has any facility to evaluate (native classification only ever reads committed graph state). `node_local_frustration` (`:53`) is itself closed-form/non-iterative and reads REAL graph state, but it feeds directly into the counterfactual sweep — migrating it alone would not change this file's actual behavior or remove any real dependency. | No (Blocker A, compounded) | No | **BLOCKED** — stays continuous. Blocker A. |
| 4 | `domains/insight_propagation.py` | `propagate_insight` (`:108` `mt_relax_to_marginal`, `:109`/`:132` `mt_audit_basin`, `:129` calls `insight_detection.consolidate_insight` → Blocker B) | Cross-Mt cascade: re-relaxes every OTHER Mt sharing a flipped Concept, detects a secondary insight, and — when the target Mt's policy allows — consolidates it via the SAME Hebbian call as consumer 2. `find_shared_concepts`/`find_connected_mts` make no can_ops calls (pure neighbour-set Python). | Partial — the relax+audit half (`:108`-`:109`/`:132`) maps cleanly onto items 1-3 (discrete-async update + `ShapeDecode` classification), in isolation | No, not cleanly, for the WHOLE function | **BLOCKED** — stays continuous. The relax+audit half is individually migratable, but `propagate_insight` is one function that also calls `consolidate_insight` inline (Blocker B) on the SAME Mt whenever policy allows. Swapping only the relax+audit half while `mt_hebbian_update_J` still runs on the same Mt's `weight` attrs — and while `self_improvement_loop.py`'s OWN separate step (consumer 6) keeps relaxing this SAME Mt continuously every tick — would run two different, never-jointly-validated relaxation mechanisms against one shared Mt across different code paths. That is exactly the forced half-measure the task instructs against, not a clean bounded migration. |
| 5 | `domains/sparseness_signal.py` | **None, directly.** `detect_sparse_mt` (`:44-47`) reads `attrs["coverage"]` — an Mt-side attr written exclusively by `self_improvement_loop.py::_stash_post_state` (`:165`, `substrate.set_attr(mt, "coverage", int(post_audit["coverage"]))`), itself sourced from `mt_audit_basin` (consumer 6). | Streak-detects sustained low coverage from an attr it never itself computes. | N/A — the file is already representation-agnostic; it consumes whatever `coverage` upstream produces, continuous or native, unchanged. | N/A | **BLOCKED, transitively, via consumer 6 — zero code change needed in this file either way.** Its blocker is entirely inherited: as long as `self_improvement_loop.py` stays continuous (it does, §6), `coverage` keeps arriving from `mt_audit_basin`'s continuous marginal, and `sparseness_signal.py` reads it exactly as today. |
| 6 | `domains/self_improvement_loop.py` | `relax()` (`:97` `mt_relax_to_marginal`); `maybe_hebbian` (`:69`/`:76` `mt_hebbian_update_J` → Blocker B); `maybe_decay_J` (`:84` `mt_decay_J`); `maybe_decay_h` (`:91` `mt_decay_h`); `maybe_update_identity` (`:188` `mt_update_identity_dynamics`); `nudge_identity_on_flipped` (`:215-216` `concept_nudge_identity`); `self_improvement_step` (`:266`/`:286`/`:332` `mt_audit_basin`; `_stash_post_state` `:161` `mt_distance_to_target`) | The central per-tick orchestrator: relax → audit → detect/consolidate insight (Hebbian) → decay J → decay h → update identity → re-relax → re-audit → stash. ALL SEVEN of these run, in this order, on the SAME Mt, every step. | Partial — relax (item 3) and audit/classification (items 1-2) map cleanly in isolation; decay and identity dynamics map onto NOTHING (see below) | No, decay explicitly out of scope this rung (task's own instruction); identity dynamics were never designed by ANY of the three prior rungs (not one of the 5 mapped claims in the spike) | **BLOCKED** — stays continuous. Three independent, compounding blockers on the SAME step function: (a) `mt_decay_h`/`mt_decay_J` — `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §9 point 5 and `LOGODDS_GENERATOR_RESULTS.md` §7 point 3 both confirm, unchanged across three rungs, that decay/forgetting has NO proposed native analog anywhere in this arc, and the task explicitly reserves building one for a dedicated follow-on; (b) `mt_hebbian_update_J` — Blocker B, identical to consumer 2; (c) `mt_update_identity_dynamics`/`concept_nudge_identity` — identity dynamics (`h_id ← h_id + α·σ − β·h_id`) were never one of the five claims the spike mapped (basin, energy, multistability, evidence-propagation, Hebbian) and no native design exists for it at all, in any of the four docs. Even if relax+audit were swapped in isolation, `self_improvement_step` would still call `can_ops.rs` for 5 of its 7 real operations every tick — `can_ops.rs`'s decay/Hebbian/identity code paths could not be removed regardless, and this is the exact function consumer 4 is downstream of, so a partial swap here would propagate the same never-validated mixed-mechanism risk into every other consumer's shared Mt state. |
| 7 | `worlds/bigville_can_beliefs.py` | `build_resident_can_mt` (structural edges, identity fields); `apply_scenario_evidence` → `concept_apply_evidence` (`can_ops.rs::apply_evidence_h`) | Mechanically translates one resident's drawn params into a personal CAN belief network, then applies fixed scenario evidence. The demo script (`scripts/bigville_can_integration_demo.py`) separately calls `mt_relax_to_marginal`/`mt_audit_basin`/`mt_frustration_given_state`/`mt_energy` plus a Python-side multi-start `basin_count` enumeration loop (`multi_start_basin_count`, genuine enumeration, built entirely in Python on top of repeated relaxation calls — never inside `can_ops.rs` itself, confirming the spike's own §3.1 finding that `audit_basin` never does enumeration). | Yes, for the relaxation + classification/coherence half (items 1-3), ONCE the named schema fix is applied (`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §7's own verified-backward-compatible one-line fix) | **Yes — explicitly instructed and sized as ready** | **MIGRATE.** See §2. |

---

## 2. The Bigville migration — what will be built

`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §7 measured the ONE incompatibility
directly, not hypothetically: `worlds/bigville_can_beliefs.py:176-181`
(`STRUCTURAL_EDGES` loop) mints each structural coupling in ONE direction
only (`s.add_edge(concepts[a], "causal_influence", concepts[b], {"weight":
q_j})`); the native rule's local-field `Sum(Edges(c,"causal_influence"))`
reads OUT-edges only (§0.0.1 of `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md`),
so a Concept whose only coupling is an IN-edge (e.g. `claim_credible`'s
edge FROM `trust_mayor`) is invisible to the native local-field computation
— measured directly: `claim_credible` has 6 out-neighbours visible to the
native rule and 1 additional in-neighbour (`trust_mayor`) invisible to it.

**The fix** (verified backward-compatible on paper by the prior rung,
implemented here): change the `STRUCTURAL_EDGES` loop in
`build_resident_can_mt` to mint BOTH directions with the SAME weight. This
is additive-risk-only for the EXISTING continuous mechanism —
`build_couplings`'s own in-edge de-dup (`can_ops.rs:180-191`) and
`enumerate_couplings`'s own undirected-pair de-dup (`can_ops.rs:293-322`,
confirmed by direct re-read in this rung, not merely cited) both already
skip a neighbour already found via the other direction, so
`mt_mean_field_marginal`/`audit_basin`'s `coupling_count`/energy/frustration
arithmetic is BYTE-IDENTICAL before and after the fix — checked as a
regression, not assumed (§4 below).

**The native migration demo, precisely what will be measured**: for each of
the two demo residents (lowest/highest `resolution_bins`, the SAME pair
`pick_demo_residents` already selects), after the schema fix:

1. Build the resident's CAN belief Mt (`build_resident_can_mt`, symmetric
   edges) + apply the same scenario evidence (`apply_scenario_evidence`,
   UNCHANGED).
2. Set `Mt.discrete_mode = "3state"` and run the SEEDED
   `can_native_update_3state` rule to a fixpoint via `run_rules()` — this
   REPLACES `mt_relax_to_marginal`'s iterative mean-field relaxation with
   the native discrete-asynchronous Hopfield-style update (item 3), the
   actual mechanism this whole arc set out to replace (the oscillation-
   prone, synchronous-iteration one).
3. Read frustration on the RESULTING discrete state via
   `mt_frustration_given_state` — this function is closed-form, O(edges),
   confirmed NON-iterative by direct read in the spike (§3.2) and reused
   AS-IS by `tests/test_can_native_reimplementation.py`'s own `_frustration`
   helper to score native-produced states — it is not part of what needed
   replacing (no oscillation pathology, no Boltzmann ensemble, just a sum).
   Using it here to SCORE the native relaxation's output is the same
   established idiom the prior rung already used for its own item-3
   demonstration, not a new pattern invented for Bigville.

**Registered prediction**: the low-resolution resident's native-relaxed
state shows HIGHER frustration than the high-resolution resident's, on
identical scenario evidence — the same qualitative divergence
`BIGVILLE_CAN_INTEGRATION_RESULTS.md`'s continuous-mechanism demonstration
already established, now reproduced via the native relaxation mechanism.

**What this demo does NOT attempt, named up front**: the multi-start
`basin_count` ENUMERATION half of the existing demo script stays exactly
as it is (Python-side, built on repeated CONTINUOUS relaxation calls) —
per §3.1 of the spike, enumeration has no native analog and building one is
explicitly out of this rung's scope. `test_bigville_can_integration.py`'s
existing `multi_start_sweep`-based assertion is a regression on the
CONTINUOUS mechanism and is expected to keep passing unchanged (the fix is
additive-risk-only, per the de-dup argument above) — it is not something
this rung claims to have migrated.

---

## 3. What will be removed from `can_ops.rs`/`causal_attitude_networks.json`

**Nothing.** Every one of `mt_mean_field_marginal`, `mt_mean_field_with_h_
override`, `mt_energy`, `mt_frustration_given_state`, `node_local_
frustration`, `mt_audit_basin`/`audit_basin`, `mt_hebbian_update_J`,
`mt_decay_J`, `mt_decay_h`, `mt_update_identity_dynamics`, `concept_nudge_
identity`, `mt_relax_to_marginal`, `apply_evidence_h`/`concept_apply_
evidence`, `mt_distance_to_target` has at least one real, named, currently-
irreplaceable consumer per §1 above (six files) or is reused, unmodified,
as a closed-form scoring utility by the Bigville migration itself (§2).
Per the task's own instruction — remove only what has ZERO remaining real
consumers — Phase 3 is empty this rung. This is reported as the honest,
expected, non-forced outcome, not a shortfall: five of the six blocked
consumers are blocked on machinery this rung is explicitly told NOT to
build (a non-mutating counterfactual predictor; a decay mechanism; an
edge-weight write-back for the log-odds render), and the sixth
(`self_improvement_loop.py`) is blocked on the SAME three things at once
because it is the shared orchestrator every other consumer sits downstream
of.

---

## 4. Regression plan

All seven named test files
(`tests/test_can_ops.py`, `tests/test_can_migration.py`, `tests/
test_identity_field.py`, `tests/test_insight_seeking.py`, `tests/
test_self_improvement_loop.py`, `tests/test_can_belief_quantization.py`,
`tests/test_bigville_can_integration.py`), plus the directly-relevant ones
this audit surfaced and that the task's own file list did not name
(`tests/test_insight_detection.py`, `tests/test_insight_propagation.py`,
`tests/test_drive_curiosity.py`, `tests/test_sparseness_signal.py`,
`tests/test_can_native_reimplementation.py`, `tests/test_evidence_axis_
infer.py`, `tests/test_can_crossover_point.py`,
`tests/test_causal_attitude_networks.py`), run before and after the
Bigville fix, per-file, with paired failing-node-id lists if anything
regresses — never a bare count, per this session's own standing discipline.
Since §1's audit concludes zero code changes to `domains/drive_curiosity.py`,
`domains/insight_detection.py`, `domains/insight_seeking.py`,
`domains/insight_propagation.py`, `domains/sparseness_signal.py`, or
`domains/self_improvement_loop.py`, every test file exercising those
modules is expected to be BYTE-IDENTICAL before/after (a true regression
guard, not a formality) — only `tests/test_bigville_can_integration.py`
and the new Bigville native-migration test are expected to exercise
changed code.
