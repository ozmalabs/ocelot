# Substrate gap review — ocelot against *Graphic Equalisation* v22 and *Narrative Momentum* v2

Status: **measurement, not a plan.** This document reports what the ocelot substrate does and
does not implement of the two current theory papers. It proposes no work, prices no work, and
opens no rung. Where it names a build it names it as a gap with a location, not a recommendation.

## 0. Conditions on every claim below

- **Theory versions:** `~/law_of_graphic_equalisation_recursive_v22.tex` (944 lines) and
  `~/law_of_narrative_inertia_v2.tex` (800 lines). Both are moving documents; v22 is the
  twenty-second revision in a single session and v2 was edited to match it. **A verdict here is
  against those two files and no others.** Quoting a verdict without its theory version is the
  defect this repo's own retracted optional-dep note was about.
- **Code state:** working tree at `75427d0` with the same dirty files present throughout the audit.
  HEAD did not move during the review, so every delta reported against the earlier (v1-era) review
  is the theory's movement, not the code's.
- **Method:** four parallel delegated audits (boundary/input, decision/execution, identity/frames,
  narrativium/groundings), each briefed with the specific theory clauses and required to cite
  `file:line`. Two agent findings contradicted each other and were resolved by direct verification
  (§8). Two further agent recommendations were overridden and are recorded as overridden in §9.

---

## 1. The inversion — four gaps closed by the theory, not by the code

The first review of this substrate was run against an early version of the theory in which a graph
carried `g'`, a reference to its containing supergraph. Its headline finding was that ocelot has no
such field. **v22 now forbids that field.**

> *"No parent or supergraph reference is a primitive member of `G`."* — v22, §The graph and its world boundary
>
> Falsifier: *"**No parent reference primitive.** Falsified if a situated graph requires a direct parent
> or supergraph reference merely to receive boundary input or participate in world interaction."*

`TypedGraph` (`runners/dsl/src/graph.rs:171-260`) has no `parent`, `world`, `container`, or
`supergraph` field. What was the single largest gap in the earlier review is now **a passing
falsifier, with no line of code changed.**

Three more of the same kind:

| Earlier reading | v22 position | ocelot |
|---|---|---|
| No persistent attempt/request object → gap | v18 forbids one at substrate level | flat effect application, no substrate-level attempt object — **correct** |
| Faculties running with no valuation → incomplete | v18 capability layering makes deliberation optional | `run_rules_opts` (`rewrite.rs:2140`) references no valuation construct — **correct** |
| No RNG → unremarked | v12 requires a conforming executor be deterministic | no `rand` dependency in either Cargo.toml; `FxHashMap` throughout the match loop — **correct** |

**Consequence for how this document should be read.** The gap between ocelot and the theory is not
a backlog that has been accumulating. It is a distance between two things that have both been
moving, and in at least four places the theory moved *toward* the implementation. A gap list that
does not distinguish "not built" from "no longer required" will misprice everything downstream.

---

## 2. Scorecard

`HAS` = implemented and theory-conformant. `PARTIAL` = the shape exists somewhere, scoped or
unnamed. `LACKS` = no counterpart. `MOOT` = required by an earlier theory version, not by v22.

### Boundary and input

| Requirement | Verdict | Anchor |
|---|---|---|
| World boundary `B=(I,A)` as a typed relation | PARTIAL | `WorldAdapter` discipline; no `WorldBoundary` type (0 grep hits) |
| Input as `I=(d,ε,K)` | PARTIAL | `FovealTileAssessment` carries all three (`world_adapter.py:1113-1139`); general `ingest()` is `d`-only |
| Precision-bearing `Integrate` | **HAS** | `seeds/staleness_decay.json` — full Decay→gain→blend chain as graph rules |
| Γ does not gate inbound change; WF preserved | **HAS** | `ingest()` uses `add_edge_unchecked` at 4/4 edge sites; `insert_edge` still guards endpoints |
| `Expose` event-local, no persistent request | PARTIAL | `*Request{status}` lifecycle across 22 files |
| Vocabulary separation + handle publication | LACKS | `physics_world.py:183-184` copies external field names verbatim |
| Merge provenance witness | LACKS | `substrate.rs:3264-3271` *discards* colliding bindings |

### Decision and execution

| Requirement | Verdict | Anchor |
|---|---|---|
| Non-mutating proposal construction | LACKS | `rewrite.rs:2196-2207` apply-then-maybe-undo; `batch_apply_rule:2460` documents same-round visibility |
| Target-typed dependency graph | LACKS | flat `Vec<Effect>` in list order (`rewrite.rs:1494`) |
| Guarded proposal `π=νa.(P_G,P_B,D)` | PARTIAL | `RulePatch` CAS (`substrate.rs:2391-2470`) — real, scoped to rule self-edit |
| Feasible-set selection, SET-TIE | LACKS | zero hits for feasible-set/decision-coupling machinery |
| Atomicity | LACKS | `Transaction` is sequential-with-partial-rollback (`substrate.rs:5075-5124`) |
| Typed WF predicates | LACKS | zero named WF predicates; structural guard exists (`graph.rs:669-674`) |
| Determinism | **HAS** (see §7) | no `rand`; `FxHashMap` |
| Capability layering | **HAS** | decision machinery is opt-in per rule |

### Identity, frames, recursion

| Requirement | Verdict | Anchor |
|---|---|---|
| No parent pointer | **MOOT → CREDIT** | `graph.rs:171-260` |
| Node identity, retype-preserving | **HAS** | `graph.rs:849-869` in-place `type_` mutation, same NodeID |
| SELF identity, copyable | **HAS** | `seeds/jabberwock_identity.json:2-8`; copy demonstrated by child boot |
| SUPERGRAPH identity `ι_{W:G}` | **HAS** | `experiment_dispatch.py:206-264` — see §3 |
| Multi-frame concurrent individuation | LACKS | peer instances only (`test_multi_agent_migrated.py:126-153`) |
| Per-frame termination | PARTIAL | `gap_awareness.json` retire-not-delete |
| `Boundary(W,G_j,B_j)` as graph content | PARTIAL | shape present, not reified |
| Narrative held *about* another | PARTIAL | peer-level: `interlocutor_model.py`, `bigville_theory_of_mind.py` |

### Narrativium

| Requirement | Verdict | Anchor |
|---|---|---|
| Measurement vs expenditure distinction | LACKS as named; **shape exists** | `seeds/energy_ledger.json` + `surprise_promotion.json` gate |
| Conferral without transition | LACKS live | conferral-shaped seeds extracted (§8) |
| Selectable reachability over an action set | LACKS | both halves exist, never composed (§4) |
| Termination as reachable deformation | LACKS | `termination_code` is a status flag, not a magnitude |
| Fuel grounding | **HAS** | `energy_ledger.json`, `jsbsim_f16_paper_world.py:972-987` |
| Potential-energy grounding | **HAS** | `traditional_helicopter_world.py:381` — literal `mgh`, real PE↔KE |
| Social-capital grounding | EXTRACTED | §8 |
| Spoons grounding | PARTIAL/EXTRACTED | §8 |
| Momentum as domain grounding, not primitive | **HAS** | two independent groundings, no substrate Term |

---

## 3. The strongest credit: `ι_{W:G}` already exists, unnamed

`domains/experiment_dispatch.py:206-264` snapshots the parent's entire mind to `parent_snapshot.json`,
launches the child as a separate OS process, and writes the individuating record —
`status`, `run_dir`, `child_pid`, `result_path` — **onto an `Experiment` node in the parent's graph**.
The child holds no back-reference of any kind.

That is v22's identity split, running in production:

- internal content in the instance, individuation in the containing frame;
- the child boots a byte-identical copy of the parent's self-model, so **two live instances carry
  the same `SelfId` under different `ι`** — the copying case v22 built the distinction to handle;
- `domains/imagination.py:181-481` repeats the pattern at node granularity via `detached_id`.

Nothing in the codebase calls this identity individuation. It is the theory's mechanism arrived at
independently for operational reasons, which is the convergence signature this folder exists to record.

Second credit of the same kind: **precision-bearing integration is not merely present but present in
the right form.** `seeds/staleness_decay.json` implements decay, gain, and blend as ordinary graph
rules over node attrs that other rules match on — v22's `Λ_t^I ⊆ g_t^I` requirement satisfied
literally, rather than as a hidden numeric routine. Note two orphaned Kalman implementations
(`l3_kalman_nd.rs`, `l3_drives.rs:150-208`) are wired to nothing and should **not** be cited as the
compliant mechanism.

---

## 4. The single highest-leverage gap: two primitives that have never been composed

`N_{W:G}(𝒳,T) = μ_𝒳(ℛ^T_{W:G}(𝒳))` needs a deformation metric over an admissible action set.
Ocelot has both, natively, and no code path joins them:

- **`runners/dsl/src/future_manifold.rs`** audits **one** candidate trajectory against one target
  tube, returning retained width, loss, information loss, and an earliest-decisive-tick. Every
  call site is single-candidate (`seldon_manifold_viz_demo.py:48-72`, `speech.py:803`).
- **`Substrate::admissible_moves`** (`substrate.rs:1887-1935`) enumerates a Γ-admissible target set
  with additive weights — the natural `𝒜(𝓕)`. An exhaustive call-site sweep found **no site that
  composes it with any deformation metric**; every use is weighted selection among admitted moves.

Until they are composed, "an always-admissible but never-selected candidate contributes nothing" and
"termination is visible when the deformation class admits it" are not false in ocelot — they are
**not expressible**, because no reachable-deformation set exists to be true or false of.

---

## 5. Where the theory's own name appears, the math is the forbidden shape

`scripts/seldon_manifold_viz_demo.py:168-185` is the only occurrence of "narrativium" in the tree.
It computes cumulative deviation from the narrative's own momentum by **summing a per-tick term over
ticks** (`total += math.hypot(...)`, line 182).

v22, §Measurement and expenditure: *"no path integration ... a sequence of expenditures cannot be
summed to predict a later measurement."*

The script disclaims itself honestly (`:125-137`, "NOT native-audited fields... plain arithmetic
aggregates computed here, in Python"), so this is not a violation by a component claiming compliance.
It is worth recording precisely because the demo is the most likely thing for a later rung to
mistake for an implementation.

---

## 6. Bug-shaped finding, independent of the theory

`runners/dsl/src/rewrite.rs:1510`:

```rust
let _ = graph.insert_edge(s, *edge_type, t, attr_map);
```

The `Result` is discarded. If an earlier effect in the same rule firing removed an endpoint, the edge
is silently not created: no error, no `progressed` accounting for that effect, and no rollback of the
rule's already-committed effects. This is neither the theory's clean-failure semantics nor a reported
skip. It is worth fixing on its own merits regardless of any theory work.

---

## 7. A tension worth recording: determinism bought with semantic order

Ocelot passes v22's determinism falsifier — no `rand` crate, `FxHashMap` (unseeded, deterministic
iteration) throughout `rewrite.rs`/`substrate.rs`. It achieves this by making **enumeration order the
tie-breaker**: rules scan in insertion order (`substrate.rs:2582-2584`), and within a rule the first
binding that progresses wins (`rewrite.rs:2213`).

v22 requires determinism **and** non-semantic enumeration order simultaneously. Ocelot satisfies the
first *by means of* violating the second.

**Measured, 2026-08-21** (`docs/research/engine_substrate/ARGMIN_TIE_CENSUS_RESULTS.md`): on a
five-utterance conversational workload with the full seed set, **95 of 148 selector firings (64.19%)
are exact ties resolved by enumeration order**. Four distinct sites tie; one — `Argmax` over
`ranked_source.salience` in `default_mode_mint_episode_context` — accounts for 90 of the 95, and
ties on 90 of 90 firings because every message-derived episode is minted with a hardcoded
`salience: 1.0` (`memory_core.json::rule_episode_from_message`). An `Argmax` over a constant cannot
rank: it returns the first-encountered consolidated episode while presenting as a salience ranking.
(An earlier version of this paragraph named the wrong rule and reported the attribute as unset; both
errors are corrected and recorded in the results doc's §CORRECTION rather than silently edited.) So order is not
merely *how* determinism is achieved here — on this workload it is the primary decider in a majority
of firings and the only decider at the dominant site. Caveats in the results doc: one workload,
conversation paths only, and the instrument reaches `Argmin`/`Argmax` Terms but not rule-order
scanning or first-binding-wins, so the true order-dependence is at least this and probably more.

The engine had already measured a version of this on itself. `runners/dsl/src/argmin_tie.rs:5-15`
quotes a prior measurement verbatim: *"`Argmin` returned a winner from FIVE IDENTICAL CANDIDATES ...
on all 200 draws."* `ArgminUnique`/`ArgminRefusal` exist and refuse on exact non-uniqueness with no epsilon —
matching v22's exact-equality requirement — but they are opt-in per Term, default `MODE_OFF`, return
`Value::None` rather than a represented tied set, and the module header records that they cover
"185 CONFIGURATION reads and ZERO VERDICT reads." **The instrument exists and is not wired to the
decisions.**

---

## 8. Extraction changes what "missing" means for two groundings

Commit `5065fb8` ("Extract Bigville implementation from Ocelot", 2026-08-15) removed 481 files.
Verified: `seeds/bigville_loop_reputation.json` and `seeds/bigville_drama_social.json` were deleted
in that commit; 3 bigville seeds and 5 bigville modules remain live.

Two of v22's four narrativium groundings were **built here, then moved out**:

- **Social capital (conferral).** The reputation model in which another villager's backing or
  badmouthing changed a resident's standing — with no edit to that resident's own node — is exactly
  v22's conferral/revocation proposition. It is gone. What remains live under the name is
  `domains/epistemic_access.py:610-660`, a self-held, self-depleting, fixed-schedule-regenerating
  budget: **structurally fuel wearing the social-capital name**, and it regenerates unilaterally,
  which is precisely what v22 says social capital cannot do.
- **Spoons (recovery through cessation).** Bigville's allostatic-load model with `al_rest` geometric
  decay and a `recovery=0` control (`docs/research/bigville/BIGVILLE_STRESS_PREREG.md:5-42`) is
  documented but its seeds are extracted. What remains — `fatigue_recovery_per_second` in the
  embodied seed generators — is mechanical fatigue, not an unobservable source-typed capacity.

So the honest statement is not "ocelot lacks two groundings." It is that **ocelot built them,
validated them, and they now live elsewhere** — which matters both for where to look for prior art
and for what any future claim of novelty here would have to contend with.

---

## 9. Overridden agent findings, recorded

Two delegated recommendations were rejected on verification:

1. **"Retire the narrative-horizon apparatus as contradicting no-conservation."** Rejected.
   `α_t = N_avail(t)/C_rev` is a same-instant comparison of a fresh measurement against a cost —
   precisely the feasibility gate v22 endorses (`c ⪯ N`). The agent read "no conservation" as
   "no gate". The horizon survives; it needed typing, not removal.
2. **"Index every quantity in the inertia paper by frame."** Rejected as an edit strategy. Correct
   in substance — `𝒮`, `ℳ`, `N`, `𝒩`, `p` are all per frame — but re-indexing ~40 equations would
   have cost legibility for no gain. A single convention subsection plus explicit indexing where
   plurality is load-bearing was applied instead.

Recorded because a review that shows only its accepted findings hides its own error rate.

---

## 10. Terminology collisions

Three cases where ocelot already uses a theory word for an unrelated mechanism. These are the same
collision class corrected in the papers themselves this session, and will misroute searches:

| Word | ocelot meaning | theory meaning |
|---|---|---|
| `Supergraph` | per-resident valuation weight node (`worlds/bigville_ocelot_adapter.py:364-388`) | the identity relation under which a frame individuates an instance |
| `Frame` | physics-style reference frame, a weighted dimension set (`domains/frame.py:1-42`) | an individuating containing world |
| `narrative_*` | literary story grammar (Rumelhart) — `seeds/narrative_structure.json` | a frame's represented continuation of a situated graph |

---

## 11. Reproduce

```bash
# The inversion (§1)
rg -n "parent|supergraph|world_ptr" runners/dsl/src/graph.rs
rg -n "rand::|thread_rng" runners/dsl/ --type rust
# Identity individuation (§3)
sed -n '206,264p' domains/experiment_dispatch.py
# The uncomposed primitives (§4)
sed -n '1887,1935p' runners/dsl/src/substrate.rs   # admissible_moves
rg -n "admissible_moves" --type py --type rust      # every call site
# The forbidden shape (§5)
sed -n '168,185p' scripts/seldon_manifold_viz_demo.py
# Tie semantics (§7)
sed -n '1,60p' runners/dsl/src/argmin_tie.rs
# Extraction (§8)
git show --stat 5065fb8 | head -5
```
