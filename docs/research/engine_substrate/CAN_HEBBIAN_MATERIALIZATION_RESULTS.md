# Unblocking Blocker B for its three consumers — RESULTS

Prereg: `CAN_HEBBIAN_MATERIALIZATION_PREREG.md`, same worktree/branch, base
`main @ 299ace3` ("Merge can-consumer-migration: 1/7 migrated (Bigville),
6/7 honestly blocked, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-hebbian-materialization`, branch
`can-hebbian-materialization`. One of three parallel primitive-building
rungs unblocking `CAN_CONSUMER_MIGRATION_RESULTS.md`'s named "Blocker B".

**Verdict, up front: (B) confirmed — on-demand reading suffices; no new
materializing write was needed.** The v1.1.0 evidence-count mechanism
(`LOGODDS_GENERATOR_RESULTS.md`) is confirmed, by direct read of every
caller, to already be the correct native Hebbian analog. The one genuine gap
was exactly what the PREREG named it as: a missing POLICY GATE, now built
(`seeds/can_native_reimplementation.json` v1.1.0 → v1.2.0). **A second,
unregistered, real defect was found and fixed live while testing the
gate**: `can_native_hebbian_mint`'s twin, `can_native_note_coactivation`,
carried a pre-existing (not introduced by this rung — reproduced on an
untouched v1.1.0 checkout, §2.3 below) dedup-guard bug that silently
double-counted evidence for a co-activating pair. GO.

---

## 1. The materialization-vs-on-demand finding, confirmed

Read in full (PREREG §1, reproduced and confirmed here): `domains/
insight_detection.py::consolidate_insight` (`:153-167`), `domains/
insight_propagation.py::propagate_insight` (`:56-157`), `domains/
self_improvement_loop.py::mt_allows`/`maybe_hebbian` (`:44-77`) and its
call site in `self_improvement_step` (`:266-289`).

**`consolidate_insight`'s only externally-visible effect is its return
value** — the raw `int` from `substrate.mt_hebbian_update_J(mt, eta)`
(edges updated). It never itself reads a `causal_influence` edge's
`weight` attr.

**Every caller of that return value uses it exactly two ways, confirmed
by direct read, never as a stored float coupling strength:**

1. **Truthy control flow.** `self_improvement_step:286-289`: `if
   edges_hebbian or edges_decayed or fields_decayed or identity_updated:
   relax(substrate, mt)`. `insight_propagation.py:129-132`: `if
   consolidation: substrate.mt_relax_to_marginal(other_mt); new_audit =
   substrate.mt_audit_basin(other_mt)`. Both ask "did anything change,"
   never "by how much" — and the re-relax that follows reads
   `causal_influence.weight` only inside `can_ops.rs` (out of scope to
   touch or replace here).
2. **Telemetry.** Stashed verbatim as `insight["consolidation_edges"]`
   (`self_improvement_loop.py:266`) / `cascade_event["consolidation_
   edges"]` (`insight_propagation.py:133`) — never read back
   arithmetically anywhere else in either file.

**Grep confirms no Python file outside `can_migration.py`** (a one-time
`refers_to`→`causal_influence` migration shim) **and `worlds/
bigville_can_beliefs.py`** (edge-schema construction, not a post-Hebbian
read) **ever reads `causal_influence`'s `weight` attr as a value.** The
only consumer of the weight VALUE anywhere is `can_ops.rs` itself (via
PyO3, opaque to grep) inside `mt_relax_to_marginal`/`mt_mean_field_
marginal` — an internal continuous-mechanism concern this rung does not
touch.

**Conclusion, exactly as registered: no caller reads a stored weight value
back across ticks.** The genuine requirement is (i) a real, persistent,
in-frame mutation to have happened (satisfied already, unmodified, by
v1.1.0's `evidence_confirm`/`evidence_disconfirm`/`evidence_tick` integer
counters on the `Coactivation` ledger — `LOGODDS_GENERATOR_RESULTS.md` §3)
and (ii) an integer-shaped "how much happened" signal for control flow and
telemetry (built here, §3). **The genuine, confirmed gap was narrower than
"build a materializing mechanism": `can_native_hebbian_mint`/
`can_native_hebbian_reweight` fired UNCONDITIONALLY through v1.1.0 — no
`update_policy` check, no `plasticity_override` path — while their
continuous twin is always policy-gated.** This is the task's own item 3
("build the policy gate"), and it is the load-bearing piece, not an add-on.

---

## 2. What was built

### 2.1 The policy gate

`tools/patch_can_hebbian_policy_gate.py` (new, this rung), a one-shot
patch script following this codebase's own builder-script convention
(`tools/build_*.py`'s `T()`/helper-function pattern), loads, patches, and
rewrites `seeds/can_native_reimplementation.json` in place (1.1.0 → 1.2.0).
`can_native_hebbian_mint` and `can_native_hebbian_reweight`'s `where`
clauses each gain one appended item:

```
Or(
  IfThenElse(Eq(policy,"frozen"), False,
    IfThenElse(Eq(policy,"adaptive"), True,
      IfThenElse(Eq(policy,"hybrid"),
        Not(Eq(Attr(mt,"allow_Hebbian_J"), False)),   -- default True when unset
        True))),                                       -- no policy at all -> allow
  Gt(Attr(mt,"plasticity_override"), 0.0)
)
```

Zero new Rust, zero new Term kinds — `Eq`/`IfThenElse`/`Or`/`Gt`/`Not`/
`Attr` all pre-exist and are reused verbatim (confirmed: `git diff --stat
main -- '*.rs'` is empty, §5).

**This mirrors `self_improvement_loop.py::mt_allows` + `maybe_hebbian`'s
own override fallback exactly, with ONE registered, deliberate
divergence**, named in the PREREG before any code was written: `mt_allows`
defaults an Mt with no `update_policy` attr to `"frozen"` (a Python-side
safety default). The pre-existing regression file
(`tests/test_can_native_reimplementation.py`) builds its two Hebbian tests'
Mts WITHOUT ever setting `update_policy`, and house discipline requires
that file to stay green, unmodified. The gate's default for a
policy-absent Mt is therefore ALLOW (legacy/opt-in — an Mt nobody has
classified behaves exactly as the pre-gate rule always did), while an Mt
carrying an EXPLICIT `update_policy` (`frozen`/`adaptive`/`hybrid`) is
gated identically to `mt_allows`. Confirmed measured, not merely claimed:
§4 below runs the EXACT unpatched regression file byte-identically, and
separately measures both directions of the divergence.

`can_native_note_coactivation` (the pure "noted a co-activation" bookkeeping
rule — no edge, no evidence-count mutation) is deliberately left UNGATED,
matching `self_improvement_loop.py::relax`'s own precedent: *"Reading
equilibrium isn't policy-gated; only J/h mutations are."* Confirmed by a
dedicated test (`test_seed_bumped_to_1_2_0_and_gate_present_on_both_rules`,
§4) that it carries no `Or(...)` gate item, and by the frozen-Mt
demonstration (§3.2) that noting still happens on a frozen Mt while
mint/reweight do not.

### 2.2 The bridge module

`domains/can_native_hebbian_bridge.py` (new, this rung) — a thin,
no-decision Python query/render layer, NOT wired into any of the three
explicitly-out-of-scope files:

- `find_coactivation(substrate, a, b)` — the mechanical
  `a-coactivated_with->co-coactivation_of->b` traversal, reused (not
  reinvented) from the same shape the seed's own rules match on.
- `causal_strength(substrate, coact)` / `causal_strength_between(substrate,
  a, b)` — the on-demand log-odds render (`Log(Div(Plus(confirm,1),
  Plus(disconfirm,1)))`), evaluated live via `Substrate.evaluate`, the
  EXACT formula and idiom `LOGODDS_GENERATOR_RESULTS.md` §2 proved. Never
  stored.
- `hebbian_signal(substrate, a, b)` — the full inspectable signal for one
  direction: edge existence, raw evidence counts, the on-demand render.
- `hebbian_ledger_entries_touched_this_tick(substrate, mt)` — the drop-in
  analog of `mt_hebbian_update_J`'s own returned "edges updated" `int`: a
  mechanical count of this Mt's Coactivation ledgers whose `evidence_tick`
  equals the Mt's current `can_tick` AND that carry nonzero evidence (the
  nonzero-evidence clause is load-bearing — it excludes a ledger's own
  first-sight INITIALIZATION, where `evidence_tick` trivially equals
  `noted_tick` at creation, from being misread as a real mint/reweight
  event).

Every function is a pure query or pure render over already-decoded graph
state — no `if`/`else` deciding what to WRITE. The actual decision (whether
to mint/reweight) lives entirely in the graph, in §2.1's `Or(...)`
predicate; this module only reads what that predicate already decided.

### 2.3 A genuine, pre-existing defect found and fixed live

While building the ledger-touch-count demonstration (§3.4), an isolated
2-Concept pair driven through 3 ticks produced **4** touched ledger entries
where exactly **2** were expected (one per direction). Direct inspection
found `can_native_note_coactivation`'s own "already noted" dedup guard:

```
Not(Exists(Edges(a,"coactivated_with"), e2, Eq(Nth(e2,2), Var("b"))))
```

`Nth(e2,2)` is the `coactivated_with` edge's TARGET — a `Coactivation`
node — compared directly against `b`, a `Concept` node. **These can never
be equal; the guard is vacuous.** Within one `run_rules()` cold-path pass,
this let `note_coactivation` re-fire for a pair that had already been
noted on an earlier tick — specifically the exact tick `can_native_
hebbian_mint` mints the edge in the SAME pass (the "no `causal_influence`
edge yet" guard's window is still open at the moment `note_coactivation`
is evaluated) — minting a SECOND, independent `Coactivation` ledger for
the same direction, which `can_native_hebbian_reweight` then advances in
parallel, silently doubling the evidence count.

**Confirmed pre-existing, not introduced by this rung**: reproduced on an
untouched `seeds/can_native_reimplementation.json` v1.1.0 (`git stash` on
this branch, before the policy-gate patch existed):

```
tick0 a.coactivated_with [#3]
tick1 a.coactivated_with [#3, #5]     <- duplicate minted here
tick2 a.coactivated_with [#3, #5]
#3 {'evidence_confirm': 2, 'evidence_tick': 2, ...}   <- original, correct trajectory
#5 {'evidence_confirm': 1, 'evidence_tick': 2, ...}   <- spurious duplicate
```

**Not caught by the existing regression file** because neither Hebbian
test there ever counts Coactivation nodes — `test_hebbian_mint_on_
recurrence_not_on_first_sight` checks edge cardinality only, `test_
hebbian_reweight_end_to_end...` reads counts off ONE node returned by
`_coact_between` (first-match iteration order, always the original `#3`,
whose own trajectory is unaffected by `#5`'s existence) — so the
duplicate was invisible to every existing assertion.

**Fixed, in the same patch script**, to the correct two-hop existence
check (matching `can_native_hebbian_mint`'s own match pattern
`[a,coactivated_with,coact],[coact,coactivation_of,b]`, expressed as a
where-guard):

```
Not(Exists(Edges(a,"coactivated_with"), e2,
  Exists(Edges(Nth(e2,2),"coactivation_of"), e3,
    Eq(Nth(e3,2), Var("b")))))
```

Zero new Rust, zero new Term kinds — nested `Exists`/`Edges`/`Nth`/`Eq`,
already used elsewhere in this exact rule. `Edges`'s `node` argument
accepts any node-valued Term (confirmed by reading `term.rs:6442-6446`
before writing this fix — `Nth(e2,2)` composes directly, no new plumbing
needed).

**Was fixing this in scope?** It touches `can_native_note_coactivation`,
not the three explicitly-forbidden Python files, not `can_ops.rs`, not the
log-odds render Term composition — none of the PREREG's out-of-scope
items. It is small, well-scoped, zero-Rust, directly relevant to this
rung's own subject (a duplicated ledger silently inflates the exact
"graded coupling strength" signal this rung is building), and matches this
codebase's own standing precedent (`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md`
§3/§0.0.2: found-and-fixed-live, reported honestly, not smoothed over).
Fixed.

---

## 3. Live demonstration — real numbers, real engine

All four registered scenarios (PREREG §3), reproduced verbatim
(`_isolated_pair`, `discrete_mode="static"`, the same isolation idiom
`test_can_native_reimplementation.py`'s own Hebbian tests use):

### 3.1 Adaptive — mint, reinforce, disconfirm

```
tick0 (note):                edge=False touched=0
tick1 (confirm, mint):       edge=True  touched=2  causal_strength=0.6931
tick2 (confirm):             edge=True  touched=2  causal_strength=1.0986
tick3 (confirm):             edge=True  touched=2  causal_strength=1.3863
tick4 (b flips, disconfirm): causal_strength=0.6931
  signal = {edge_exists: True, evidence_confirm: 3, evidence_disconfirm: 1,
            evidence_tick: 4, causal_strength: 0.6931471805599453}
```

Graded signal rises with confirming evidence, falls on disconfirmation —
exactly the shape `LOGODDS_GENERATOR_RESULTS.md` §4(c) already proved for
the ungated mechanism, now reproduced through the gate.

### 3.2 Frozen, no override — denied at every tick

```
tick1: edge=False touched=0
tick2: edge=False touched=0
tick3: edge=False touched=0
```

`note_coactivation` still fires (confirmed by a dedicated assertion,
`test_frozen_policy_denies_mint_and_reweight`: the Coactivation ledger
exists with `evidence_confirm=evidence_disconfirm=0` throughout) — only
the gated mint/reweight are denied.

### 3.3 Frozen + `plasticity_override` — allowed, then correctly stops when
the override decays

```
tick1 (override=0.5, active): edge=True   causal_strength=0.6931
tick2 (override=0.5, active): causal_strength=1.0986
tick3 (override set to 0.0, still frozen): causal_strength=1.0986  (unchanged)
```

The transient rescue works exactly like `maybe_hebbian`'s own override
fallback, AND stops working the instant the override is withdrawn while
the underlying policy stays frozen — the same shape `correction_raise_
plasticity.py::decay_plasticity_override` relies on for the continuous
mechanism.

### 3.4 Hybrid — per-axis default

```
hybrid, allow_Hebbian_J=False:  edge=False   (denied)
hybrid, allow_Hebbian_J absent: edge=True    (default True, matches mt_allows)
```

### 3.5 Legacy — no `update_policy` at all (the regression-file shape)

`test_no_update_policy_attr_still_mints_and_reweights_unconditionally`:
identical trajectory to §3.1 — mints on recurrence, reaches
`evidence_confirm=3` after 3 confirming ticks. Byte-identical to the
pre-gate v1.1.0 behaviour these Mts always had.

---

## 4. Regression

**New test file, 12/12 passed** (`tests/test_can_hebbian_materialization.py`):
seed-shape sanity, legacy/no-policy parity, adaptive/frozen/override/hybrid
(both axis states) policy demonstrations, the bridge's graded-signal and
ledger-touch-count behaviour, the never-coactivated `None` case, and the
frame/continuum invariant scan.

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_hebbian_materialization.py -q -s
............
12 passed in 0.22s
```

**`tests/test_can_native_reimplementation.py`, UNCHANGED (not edited),
11/11 passed, output byte-identical to `LOGODDS_GENERATOR_RESULTS.md` §4's
own printed tables** (oscillation counts, frustration means, basin
classification, evidence trajectory, log-odds ranking, item-4 reweighting
numbers, polarization sweep table, Bigville IN/OUT-neighbour check — every
printed line matches, confirmed by direct comparison, not by re-reading
the doc from memory):

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_native_reimplementation.py -q -s
[... same 11 demonstrations, byte-identical printed output ...]
11 passed in 0.61s
```

**Full named scoped CAN regression set (the `CAN_CONSUMER_MIGRATION_
RESULTS.md` §6 set, plus this rung's new file), one run, 163/163 passed**
(151 pre-existing + 12 new, exactly accounting for every test):

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_self_improvement_loop.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_can_crossover_point.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_native_migration.py \
  tests/test_can_hebbian_materialization.py -q
163 passed in 9.18s
```

No paired failing-node-id lists to report — zero failures, before or after,
every file in the set (confirmed: `tests/test_can_native_reimplementation.py`
was 11/11 before this rung touched anything, per `LOGODDS_GENERATOR_
RESULTS.md`'s own §6, and 11/11 now).

**Full boot regression** (`load_all_seeds` on a fresh `WorldAdapter`):
identical **8 pre-existing failures** to the documented baseline
(`acoustic_cue_vocab`, `character_tom`, `reading_constructions`,
`conceptual_categories`, `cue_investigator`, `named_compound_heads`,
`reading_skeleton`, `vision_change`, all `ValueError: seed node missing
local_id`), **0 rules_skipped** — `can_native_reimplementation.json`
stays `self_load_only: true`, excluded from the sweep as before.

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch.

---

## 5. The invariant, verified directly

`test_invariant_render_never_appears_as_a_stored_attr_anywhere` +
a standalone manual dump (both run, both agree): after driving a pair
through mint, three confirmations, and one disconfirmation, then calling
`causal_strength`/`causal_strength_between` five more times:

```
#0 (mt) {'update_policy': 'adaptive', 'can_tick': 3, 'temperature': 1.0, 'discrete_mode': 'static'}
#1 (a)  {'identity_field': 0.0, 'state': 1.0, 'external_field': 0.0, 'name': 'a'}
#2 (b)  {'identity_field': 0.0, 'state': 1.0, 'external_field': 0.0, 'name': 'b'}
#3 (co) {'evidence_disconfirm': 0, 'noted_tick': 0, 'evidence_confirm': 3, 'evidence_tick': 3}
#4 (co) {'evidence_disconfirm': 0, 'noted_tick': 0, 'evidence_confirm': 3, 'evidence_tick': 3}
```

No `log_odds`/`render`/`causal_strength` key anywhere, on any node, ever —
confirmed by direct attribute-dict comparison before/after every
`evaluate()` call (`dict(node.attrs)` byte-equal every time) AND by a
full-attrs key scan across every node touched. Every value that IS stored
(`evidence_confirm`/`evidence_disconfirm`/`evidence_tick`) is a genuine
Python `int`, never a `float`, confirmed by `isinstance` assertion. Exactly
one `Coactivation` ledger per direction (`#3` for a→b, `#4` for b→a) —
confirmed by the same dump that the §2.3 dedup fix holds under this exact
scenario (no `#5` duplicate).

---

## 6. What this rung does NOT establish

1. **No claim about Blocker A** (the counterfactual predictor) or the
   decay/identity-dynamics blockers — untouched, a different rung's
   territory, confirmed by `git diff --stat` touching only files this
   rung's own scope names.
2. **`domains/insight_detection.py`, `domains/insight_propagation.py`,
   `domains/self_improvement_loop.py` are UNCHANGED** (confirmed:
   `git diff --stat main -- domains/insight_detection.py domains/
   insight_propagation.py domains/self_improvement_loop.py` is empty) —
   this rung builds the native-side primitive; wiring these three files to
   actually CALL it (replacing `consolidate_insight`/`maybe_hebbian`'s
   `mt_hebbian_update_J` call with the bridge + gated rules) is explicitly
   a later, coordinated migration rung's job, per `CAN_CONSUMER_
   MIGRATION_RESULTS.md`'s own finding about shared-Mt coherence risk
   (running the continuous relax and the native discrete update on the
   same Mt across different code paths without joint validation).
3. **Graded reweighting still does not reach the NATIVE discrete
   propagation's own local-field computation.** `can_native_update_
   3state`/`_2state` (item 3, unchanged by this rung) reads a literal
   `EdgeAttr(e,"weight")` hardcoded to `1.0` at mint time — the evidence
   counts and their on-demand render are invisible to that Sum, exactly as
   they were before this rung (item 3 was DESIGNED this way from v1.0.0,
   before the reweighting mechanism existed at all — not a regression this
   rung introduces). Whether the native discrete propagation SHOULD read a
   quantized/rendered graded strength instead of a flat mint-time weight
   is a real, separate, unscoped design question this rung does not
   adjudicate — named here, per the PREREG's own registered boundary,
   rather than silently left unmentioned.
4. **The "legacy allow" default is a real, permanent divergence from
   `mt_allows`'s own conservative default, not a temporary shim.** Any Mt
   that a future migration rung wants gated defensively MUST carry an
   explicit `update_policy` attr — an Mt with none is, by this rung's own
   deliberate design, treated as unrestricted for native mint/reweight.
5. **The `hebbian_ledger_entries_touched_this_tick` count is PER-DIRECTION**
   (unchanged v1.0.0/v1.1.0 convention: a pair co-activating gets two
   independent `Coactivation` ledgers, one per direction) — a caller
   wanting a single "did this PAIR learn" signal must divide by 2 or dedupe
   by `coactivation_of` target itself; this function does not do that for
   them.
6. **The §2.3 dedup fix was found and fixed for THIS specific guard**; it
   is not a general audit of every other guard in this seed or the wider
   corpus for the same "compare a derived intermediate node directly
   against the wrong final target" shape. Named as a reusable lesson
   (the SAME shape as `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md`'s own §3
   starvation finding and §0.0.2 `ShapeDecode` scoring property — found
   live while building something else, not swept for elsewhere).
7. **Whether any of this reflects real human causal-strength or Hebbian
   learning cognition** remains exactly as open as `LOGODDS_GENERATOR_
   RESULTS.md`/`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` left it — this
   rung is a design-debt closure on this substrate's own mechanism.

---

## 7. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-hebbian-materialization
git log --oneline -1 main   # 299ace3, verified before branching

# The policy-gate + dedup-fix patch (idempotent guard: refuses a second run)
python3 tools/patch_can_hebbian_policy_gate.py

# New test file — policy gate both ways, override, bridge, invariant
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_hebbian_materialization.py -q -s

# Existing regression file, UNCHANGED, byte-identical printed output
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py -q -s

# Full named scoped CAN regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_self_improvement_loop.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_can_crossover_point.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_native_migration.py \
  tests/test_can_hebbian_materialization.py -q

# Full boot regression (8 pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"

# Zero Rust touched
git diff --stat main -- '*.rs'
```
