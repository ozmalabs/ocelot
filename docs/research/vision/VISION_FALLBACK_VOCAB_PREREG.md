# FALLBACK VOCABULARY — PRE-REGISTRATION

*Written and committed BEFORE any implementation (§3). Branch
`gamma-substrate/fallback-vocabulary`, base **`0257eef6`** (the redundancy-audit
merge). Seed block **62000–62999**, verified free (ledger high-water 59002).
Engine at pre-registration: **`11ee213dfd46`**, `own` build in this worktree,
`data/` symlinked (§10.2), §9 reference baseline **200 passed / exit 0**.*

---

## 0. WHAT THIS RUNG IS FOR

`VISION_REDUNDANCY_RESULTS.md` Arm 4 measured observability **0/2** and found
**the marker inventory EMPTY in all 26 probe runs, baseline included**. Its own
conclusion: *"the finding is not 'the markers didn't fire', it is 'there are
none to fire'."* Ablating `vision_lateral` drives `channels_on` **51.976 →
0.000** and every learned gain to exactly **0.0**, leaving **no trace in graph
state**.

The deliverable is a **graph-resident vocabulary that records degraded
operation**, plus a reader. The reason it matters is not instrumentation:

> **A layer is only a layer if it has defined behaviour in the absence of its
> neighbours AND DECLARES IT.** Without a declared fallback, "layer B is
> independent of A" is indistinguishable from "nothing in B was running" — which
> is exactly the vacuous result the audit hit in Arm 5.

It is also a precondition for the named-not-built **self-stabilization** arm:
you cannot distinguish *recovers* / *persists* / *diverges* if degraded
operation is indistinguishable from healthy operation in the graph.

---

## 1. THE MECHANISM — where a fallback ACTUALLY is, structurally

### 1.1 The engine already has the disease §1.1 and §12 name

`runners/dsl/src/term.rs:3501`, the `Attr` evaluator, verbatim:

```rust
TermNode::Attr { node, key } => {
    let v = evaluate(arena, *node, env, ctx);
    match v {
        Value::Node(nid) if ctx.graph.has_node(nid) => ctx
            .graph
            .node(nid)
            .attrs
            .get(key)
            .cloned()
            .unwrap_or(Value::None),
        _ => Value::None,
    }
}
```

**`.get(key).cloned().unwrap_or(Value::None)` is `.get('Name','')` in the
engine core.** A rule that reads an attribute **no rule ever wrote** gets a
silent `Value::None` — numerically clean, well-formed, and indistinguishable
from a real value that happens to be absent. This is the mechanism by which
`vision_lateral`'s ablation produces a confident **0.000** with no evidence:
`lat_pool` never writes `h1`/`h2`, and every downstream consumer reads the
default without complaint.

**So the structural signature of a fallback in this architecture is: a rule
COMPUTED ON AN ATTRIBUTE THAT NOBODY WROTE.** That is derived from the engine's
own evaluation, not hand-annotated — it satisfies §13 (nothing goes in; the
marker falls out of the `.get()` miss the engine already performs).

### 1.2 The two hypotheses, tested HEAD-TO-HEAD

**H1 — DEFAULTED READ (this rung's proposal).** A fallback is an `Attr`
evaluation on a **live node** whose **key is absent**. Counted per
`(rule, key)`.

**H2 — ABSENCE-BRANCH (the hypothesis offered to this rung, tested not
adopted).** A fallback is a rule firing because a `Not(Exists(...))` guard
matched on an **empty source** — i.e. the rule took its absence-branch.
Counted per `(rule, term-site)`.

Both are instrumented, both are measured on the same runs, and both face the
same conjunction gate. **H2 is the offered hypothesis and it gets a fair,
pre-registered test with its own counter — not a strawman.**

---

## 2. THE VOCABULARY (graph-resident, structural, not string-matched)

Three typed node types. **Requirement 1 (structural, not string-matched) is met
by construction: these are node TYPES and numeric attrs, so the audit's own
`MARKER_RE` prose false-positive is impossible** — there is no prose to match,
and `redundancy_observability.py`'s existing `MARKER_TYPES` detector picks them
up for free once they exist.

| type | attrs | minted by |
|---|---|---|
| `RuleActivity` | `rule` (str), `progress` (int), `count` (int) | adapter, from `rule_costs_report()` |
| `DefaultedRead` | `rule` (str), `key` (str), `hits` (int) | adapter, from the NEW engine tally |
| `AbsenceBranch` | `rule` (str), `hits` (int) | adapter, from the NEW H2 tally |
| `LayerStatus` | `seed` (str), `status` (str) | **SEED RULES** — see §2.1 |

### 2.1 The DECISION is a rule, never Python (architecture rule)

The adapter does **mechanical translation only**: engine counter → node attrs.
It contains no conditional over graph state. **The three-way classification is
made by seed rules** in `seeds/fallback_vocabulary.json` (block 62000):

- `fv_status_silent` — a `RuleActivity` with `progress == 0` → `status='silent'`
  (**nothing ran**).
- `fv_status_degraded` — `progress > 0` AND `Exists` a linked `DefaultedRead`
  → `status='degraded'` (**ran, on values nobody wrote**).
- `fv_status_healthy` — `progress > 0` AND `Not(Exists(...))` a linked
  `DefaultedRead` → `status='healthy'` (**ran, on real inputs**).

*(Note `fv_status_healthy` uses the `Not(Exists)` idiom — used where it
genuinely belongs, which is the contrast H2 is being tested against.)*

### 2.2 THE SEPARABILITY CLAIM this makes measurable

The audit could not distinguish these two, and pooled them:

| engine reading | meaning | audit saw |
|---|---|---|
| `progress > 0`, `D == 0` | layer ran on real inputs — **genuinely independent** | "no effect" |
| `progress > 0`, `D > 0` | layer ran on **defaults** — degraded, silently | "no effect" |
| `progress == 0` | **nothing ran** — inert, says nothing about redundancy | "no effect" |

**All three are "no test loss" to an ablation harness.** The vocabulary splits
them. That split is the deliverable, and `vision_waves`' **non-monotone** curve
(a partially-ablated pipeline scoring *worse* than a more deeply ablated one —
"a component that keeps firing after its preconditions vanished") is the
pre-registered place row 2 should appear.

---

## 3. STATISTIC, EXACTLY

For a probe run `X` (baseline or one whole-seed ablation), the engine yields per
rule `r`:

- `P_X(r)` = `rule_cost_progress[r]` (existing counter, unmodified)
- `D_X(r)` = Σ over keys of the NEW defaulted-read tally for `r` (H1)
- `A_X(r)` = the NEW absence-branch tally for `r` (H2)

Define, for hypothesis `H ∈ {D, A}`:

- **`FIRE_H(s)`** = the set of rules `r` with `H_s(r) > 0` and `H_base(r) == 0`
  — markers that are **NEW under ablation of seed `s`**.
- **`FP_H`** = the number of rules with `H_base(r) > 0` — markers firing in
  **healthy baseline**.

---

## 4. THE CONJUNCTION GATE (requirement 3 — the crux)

*A marker that always fires and a marker that never fires both score perfectly
on one half. Both halves are pre-registered, and BOTH must pass.*

A hypothesis `H` **PASSES** iff:

- **(a) FIRES:** for **both** `vision_lateral` and `vision_waves` — the two
  ablations the audit measured as **degraded, non-crashing, and SILENT** —
  `|FIRE_H(s)| > 0`. *(These two are named in advance because they are the
  audit's only two degraded points; the denominator is 2 and stays 2.)*
- **(b) DOES NOT FIRE:** `FP_H == 0` in healthy baseline.

**Both, or the hypothesis fails.** Reported per hypothesis, in a 2×2, never
pooled.

### 4.1 THE STRICT/RELATIVE FORK, DECLARED IN ADVANCE (§5)

I do not know that baseline `D` is exactly zero. Declared **now**, before
looking, so that reporting the weaker form later is not metric surgery:

- **STRICT PASS** — `FP_H == 0`. The marker is an **absolute** signal.
- **RELATIVE PASS** — `FP_H > 0` but `|FIRE_H(s)| > 0` for both seeds. The
  marker is a **delta** signal and is **strictly weaker**: it needs a baseline
  to compare against, so it cannot announce a cliff on its own.
- **FAIL** — `|FIRE_H(s)| == 0` for either named seed.

**If STRICT fails I report the number and label the result RELATIVE. I do not
redefine the gate.** A RELATIVE-only result is reported as a **partial**
deliverable, because requirement 3's "does not fire in healthy baseline" is
literally the strict form.

---

## 5. OVERHEAD (requirement 2 — no hand-set threshold, §13)

Measured in **counted** terms, per the `ENGINE_WINNER_VALUE_RESULTS.md`
precedent (which measured 60M counted firings and refused wall-clock after
finding 1.66× variation from load alone):

- `N_attr` — total `Attr` evaluations on the probe workload.
- `N_default` — of those, how many missed (the increment count = the instrument's
  entire dynamic cost).
- `N_fire` — total rule firings.
- **The reported overhead statistic is `N_default / N_attr`** — the fraction of
  `Attr` evaluations that pay anything at all.

**The hit path costs exactly zero extra work**: the existing code already
branches on `.get()` returning `None` (`unwrap_or`), so the instrument occupies
a branch that is already taken. Only the miss path pays.

Wall-clock A/B is reported **only** alongside the concurrent-load state, and is
**not** the headline. **No threshold for "too expensive" is set in advance**
(§13) — the number is reported with its tradeoff and the design follows it.

---

## 6. COVERAGE AND SELECTION RULE (requirement: scope honestly)

**Selection rule, stated in advance:** exactly the **25 seeds** the redundancy
audit already characterised (its `TARGETS` — blast radius ≥ 2 on the rung-7
bench). No others. They are chosen because **they are the only seeds with a
measured before/after**, which is what makes a conjunction gate possible at all.

- Coverage: **25 / 573 seeds = 4.4%**.
- The probe is the audit's own 3-seed pipeline (`vision_waves` + `vision_lateral`
  + `vision_onoff`), RNG **62002** (the audit used 59002; a fresh seed from my
  own block, same construction).
- The FIRES half rests on **2 degraded points** — the same denominator the audit
  had, and it does not grow.

---

## 7. PREDICTIONS, STATED IN ADVANCE (§3.7)

1. **H2 (the offered absence-branch hypothesis) FAILS half (b) — loudly.** The
   `Not(Exists)` guards in the vision seeds are **clock barriers**
   (`vision_onoff.oo_sunit_activate`: *"no presynaptic bipolar is still behind
   the clock"*; `vision_waves.bh_sum_weights`, same idiom over `post`/`touched`).
   A barrier **passes on every healthy step** — that is its job. So `A_base > 0`
   heavily, and absence-branch firing marks **normal synchronisation**, not
   degradation. *Proviso: if the vision seeds' barriers turn out to evaluate
   their source non-empty in the healthy case, H2 could pass; I predict they are
   empty, because a barrier's whole purpose is to wait for an empty
   behind-the-clock set.*

2. **H1 passes half (a) on both named seeds.** Ablating `vision_lateral`
   removes the only writers of `h1`/`h2`/`resid`/gain attrs, so every downstream
   consumer's read must miss.

3. **H1's half (b) is the one at risk, and I am NOT confident.** Rules
   legitimately read optional attributes (first-step initialisation, absent
   config). I predict `FP_D > 0` — i.e. **RELATIVE, not STRICT** — and that the
   baseline false positives concentrate in **first-step/initialisation** reads
   rather than being spread uniformly. If that concentration holds it is a real
   finding about where the architecture's implicit defaults live.

4. **The separability split is non-degenerate**: at least one ablation produces
   a rule in row 2 (`progress > 0, D > 0` — ran on defaults). Predicted site:
   `vision_waves`' non-monotone region.

5. **Overhead `N_default / N_attr` is small but NOT negligible** — I predict
   between 1% and 20%, and I state the range in advance so that landing outside
   it is informative rather than absorbable.

---

## 8. WHAT A NULL MEANS (§3.5, §7)

- **H1 fails (a)** ⇒ defaulted reads are not the mechanism of the vision cliffs.
  That would be a **strong negative** and is reported as the headline: it would
  mean the cliffs are produced by rules **not firing at all**, and the honest
  conclusion is that a fallback vocabulary must be built on rule *absence*, not
  on read *defaults*.
- **H1 fails (b) strictly but passes relatively** ⇒ reported as a **partial**
  deliverable with the false-positive count quoted, per §4.1.
- **Both H1 and H2 fail** ⇒ **fallbacks are NOT structurally identifiable in
  this architecture**, reported as loudly as a success would be. This is a live
  possible outcome and it is the most valuable one if true, because it says the
  separability the layering story depends on has no structural witness.

---

## 9. BYTE-IDENTITY (§9) — what must not move

The engine change is a **pure counter**: it writes to a thread-local tally and
is **never read by any Term**, so it cannot change any verdict. Proven, not
asserted:

| check | requirement |
|---|---|
| `scripts/rung7_vision_bench.sh` | **200 passed, exit 0** |
| sd orbit law | `{2:1,3:2,4:2,6:2,12:4}` **unmoved** |
| landed vision artifacts | re-run identical |
| `seeds/` git status | clean apart from the ONE new seed file |

**The graph-MINTING is a separate facility and ships OFF by default** (§9) — it
adds nodes, which moves `node_count()`, so it must be opt-in. **The engine
counter is always-on** and its always-on-ness is the claim requirement 2 asks
about.

**If any verdict moves, I STOP and report — that is itself a finding.**

## 10. EXACTLY THE LISTED MEASUREMENTS. NO SWEEPS.

26 probe runs (baseline + 25 whole-seed ablations), one process each, BLAS
threads pinned (the audit's instrument-stability rule). The conjunction gate is
evaluated once, on those runs. **No re-runs, no parameter search, no post-hoc
arm.** A further attempt needs a new pre-registration with a new
mechanism-level hypothesis.
