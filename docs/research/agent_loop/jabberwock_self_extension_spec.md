# The jabberwock's self-extension spec (GAP 2: compose held primitives, honest impasse)

_Authored by the agent, context=spec (register: Plainsong). Replaces the last auto-claude-p; the design is its own._

I have the full machinery mapped. Here is the spec — handed back in Plainsong, ordered to your five points, grounded in the exact nodes, rules, and call site I hold.

---

# GAP 2 — self-extension without a teacher

## The call I am removing

`substrate/world_adapter.py:3938-3946`, inside `_self_extend_reflex`:

```python
teacher = getattr(self, "_self_teacher", None)
if teacher is not None:
    ans = teacher(f"No existing faculty addresses the capability {keys}. ...")
    approach = str(ans).strip()...
```

That is the last `claude -p`. Everything below replaces it with graph rules. The reflex keeps **only** the mechanical authoring a rule cannot express (assembling a composite Term-tree blob via `author_subroutine`). The *decisions* — which primitives, what confidence, compose-or-surface — move into seed Rules.

---

## 0. One enabling change first: reify capability keys as nodes

Today `capability_keys` is a string-list attr on `CapabilityAxis`, and primitives (`RoutingPrimitive`, `Primitive`, `OperationPrimitive`) carry only prose (`does`/`axis`) — **no machine-readable capability**. List-attr intersection is not a clean graph join. So:

- **`CapKey { name }`** — one node per capability token, interned (get-or-create by name, same dedup move as the slang canonical-concept rule).
- `axis —requires_key→ CapKey` — minted when an axis is created, one edge per token in its `capability_keys`. (Add to `ground_hint_to_investigation` and the axis-minting paths; a load-time backfill rule covers seeded axes.)
- `primitive —provides_key→ CapKey` and `operator —provides_key→ CapKey` — what each **held** faculty advertises. The maze primitives gain `provides_key → {route, map_memory, distance_field, gradient_descent, solve}`; speech ops gain theirs. This is the "capability_keys on Operators/primitives" you named — made joinable.
- Each primitive/operator also gains **`reliability`** (float, default 0.5; a resolved faculty carries its best saturation `sat_best`).

Coverage is now a join: `axis —requires_key→ k ←provides_key— prim`, with `prim —applies_in→ w ←operates_in— agent`. No list code.

---

## 1. Compose from held primitives

**Matching — which keys count.** A required key *counts as coverable* iff some held primitive/operator **in the world I operate in** provides it. The domain token (`speech`, `maze`) and the teacher's distinguishing discriminator are context, not capability — they are required_keys that no primitive provides, so they never enter the coverable set and never inflate or deflate the score. Coverage is measured only over keys that *could* be addressed by something I hold.

**Selection — set cover by graph fixpoint, not Python.** Three rules, fired to fixpoint:

- **`compose_from_held_primitives`** (Rule A) — fires on a `needs_tool` impasse when *at least one* required key is coverable (`Exists` the join above) and no composed op yet exists for the axis. Effect: mint **one** `Operator cop {composed:1, compose_confidence:0, provisional:1}`, `axis —investigated_by→ cop`, `cop —applies_in→ w`, consume the old `investigated_by` (already unbound by `order4_self_extend`).
- **`wire_composed_primitive`** (Rule B) — `cop` composed-for `axis`, `axis —requires_key→ k ←provides_key— prim` (in-world), and no `cop —composed_from→ prim` yet ⇒ `add_edge cop composed_from prim`, `add_edge axis covered_key k`. Fires once per distinct covering primitive; fixpoint assembles the whole cover. (Greedy is unnecessary — the union of all in-world providers *is* the maximal cover; minimality is a later optimization, not correctness.)

**What the composed operator IS — two tiers, one rule set.** The `composed_from` edges are the composition. Execution depends on what the parts are:

- **Subroutine-backed parts** (parts carry a `subroutine`/`body` Term-tree): the reflex's only job — author a **composite subroutine** whose Term-tree evaluates each part's body in declared order, threading the bound `{axis}` env, and folding their results (sequence/product, matching the `many_settings` combine-all move). Set `cop.runner="subroutine"`, `cop.subroutine=<new name>`. This runs **purely graph-native** through the existing `run_subroutine` path in `_run_investigation_reflex` (`world_adapter.py:3860-3874`) — **zero world code**.
- **Runner-backed parts** (parts the host atomically knows, e.g. maze `flood`): set `cop.runner="composed"`. Add **one generic host executor**: on `runner=="composed"`, read `composed_from`, apply each part's own `runner` in order, score once. This is domain-agnostic dispatch reading graph data — it **subsumes and deletes** the maze-specific `if op=="composed_routing"` branch in `domains/maze_world.py:196-199`. The maze compose stops being special: `composed_routing` becomes `runner="composed"` over `[map_memory, distance_field, gradient_descent]`.

That is how the maze-specific compose generalises: the *selection* and *wiring* are domain-agnostic rules over `CapKey`; the *running* is either pure-graph (subroutine fold) or one generic composed-runner — never a per-domain compose branch again.

---

## 2. Known confidence (a-priori, before it runs)

Set by **`set_compose_confidence`** (Rule C) once wiring settles:

```
coverage   = Count(axis covered_key *) / Count(axis requires_key-that-is-coverable *)
reliability = mean( reliability of each composed_from prim )
compose_confidence = coverage × reliability
```

Computed with `Div`/`Count`/`Max` Terms (the same kit `bank_measurement_to_axis` uses for saturation). Written to `cop.compose_confidence` **and** mirrored to `axis.compose_confidence`; `axis.provisional = (coverage < 1.0)`.

**How it drives the ladder:**

- **Full coverage (coverage = 1.0) and high reliability** → trust. The single measurement trial decides; `escalation_resolve_high_confidence` resolves on first `sat ≥ 0.95` (existing behaviour, unchanged).
- **Partial coverage (0 < coverage < 1.0)** → compose-but-trial. `provisional=1` blocks early resolve (see §3); the measurement must be *earned and reproduced*. If it plateaus below target, the ladder climbs as today (`escalation_climb_low_confidence`, plateau guard `mf_stall ≥ 4`).
- **Zero coverage** → never reaches this rule; §4 fires instead.

The number is durable on the operator and axis, so a reboot reads the same confidence; a re-measurement updates `saturation` independently (confidence is the *prior*, saturation the *posterior*).

---

## 3. Confirm later / by context

The measurement trial is the primary confirmation (`resolve_high` / `climb_low`). Two additions for the provisional case, both already precedented:

- **Reproducibility re-run (the `learn_plan_effect` move).** A `confirmations` counter on the axis; `bank_measurement_to_axis` increments it when `measured ≥ target`, resets it on a miss. New rule **`recompose_reproduce`**: a *provisional* cop whose trial met target but `confirmations < 2` does **not** resolve — it re-arms the axis (`shortfall` high) to force a second trial. `escalation_resolve_high_confidence` is extended: resolve iff `sat ≥ 0.95` **and** (`compose_confidence ≥ 1.0` **or** `confirmations ≥ 2`). A full-coverage op trusts one measurement; a partial-coverage op must reproduce. A one-off success on a partial composition is *not* confirmed — exactly the discipline that rejected ls20's flash-artifact "rules."
- **Confirm by context (analogy), used instead of a fresh trial.** New rule **`confirm_compose_by_sibling`**: if a *sibling axis* sharing the same required `CapKey` set already resolved with the same `composed_from` structure, inherit that confirmation — set `confirmations := 2` without re-running. Use this when a measurement trial is expensive or unavailable and a structurally identical composition has already proven out; otherwise wait for the measurement.

---

## 4. The honest impasse (the discipline)

Coverage-zero is the real finding, surfaced — never papered over.

**`compose_zero_coverage_impasse`** (Rule D) — fires on a `needs_tool` impasse when **no** required key is coverable (`Not Exists` the §1 join). Effect:

```
add_node mh HumanImpasse {
  kind: "capability_gap",
  needs_human: 1.0,
  question: "Capability <requires_key names> in world <w> is needed and no held
             primitive provides any of it. What primitive should I be given, or
             what should I read, to address it?",
  resolved: false
}
add_edge mh about_axis ax
add_edge ax needs_human 1   # marker, mirrored
# DO NOT mint any Operator. DO NOT set saturation. DO NOT resolve the impasse.
```

A host surface step (mechanical I/O, the same shape as the teacher-resolution drain) reads `HumanImpasse` nodes and prints/queues them for the human. The axis stays **open and unsaturated** — its real recognition measurement is untouched.

**Stated plainly, as the contract:** I do **not** author a placeholder operator that trivially returns success. Such an op would push `saturation → 1`, fire `resolve_high`, and falsely saturate the axis — masking the exact gap that is the point of surfacing. The current reflex's `spec = {"runner": "authored", ...}` fallback (`world_adapter.py:3961`) is deleted with the teacher. The impasse *is* the deliverable on zero coverage.

**Partial-but-exhausted boundary, same honesty:** if coverage > 0 but the composition plateaus below target and the climb reaches order-4 with no further coverable keys to add, mint `HumanImpasse { kind: "capability_gap_partial", uncovered: <requires_key minus covered_key> }`. I report *which* keys I could not cover, rather than looping authoring or faking the remainder.

---

## 5. The mechanism (what fires, end to end)

The order-4 path is unchanged up to the routing marker: `order4_self_extend` (and `route_unaddressed_axis_to_authoring`) lay `mi —needs_tool→ ax`. Then, replacing the teacher consult:

1. **Rule D `compose_zero_coverage_impasse`** — no coverable key ⇒ `HumanImpasse{needs_human}`, no operator. **Stop.** (Honest impasse.)
2. **Rule A `compose_from_held_primitives`** — ≥1 coverable key ⇒ mint composed `Operator`, bind `axis investigated_by cop`.
3. **Rule B `wire_composed_primitive`** (fixpoint) — `cop —composed_from→ prim` and `axis covered_key k` for every in-world provider.
4. **Rule C `set_compose_confidence`** — `compose_confidence = coverage × reliability`; `provisional = coverage<1`. Recorded on cop and axis.
5. **`_self_extend_reflex` (now teacher-free)** — mechanical only: if `cop.runner=="subroutine"`, `author_subroutine` the composite Term-tree folding the parts' bodies in `composed_from` order; mark `mi.authored=1`; set `ax.shortfall` high for the trial. No string from any model — `approach` becomes a generated label `"composed:" + sorted(covered_key names)`.
6. **Trial** — `_run_investigation_reflex` runs the cop (subroutine fold, or generic `composed` runner reading `composed_from`); `bank_measurement_to_axis` writes `saturation`, updates `confirmations`.
7. **Confirm** — `escalation_resolve_high_confidence` resolves iff `sat≥0.95` and (`compose_confidence≥1` or `confirmations≥2`); `recompose_reproduce` forces the second trial for provisional ops; `confirm_compose_by_sibling` inherits confirmation by context.
8. **Climb / partial impasse** — plateau below target climbs (`escalation_climb_low_confidence`); exhausted-partial at order-4 ⇒ `HumanImpasse{capability_gap_partial}`.

**Confidence attrs set:** `cop.compose_confidence`, `axis.compose_confidence`, `axis.provisional`, `axis.confirmations`. **Impasse minted on coverage-zero:** `HumanImpasse{kind:"capability_gap", needs_human:1, question, about_axis}`.

Everything is domain-agnostic: it keys off `CapKey` joins and `composed_from`, knows nothing of speech or maze. `set_self_teacher` / `_self_teacher` / `scripts/claude_teacher.py` drop out of this path entirely.

---

## What I am claiming, and where I stop

I can extend myself wherever I already hold primitives whose advertised keys cover the need — I assemble them, I carry a prior confidence equal to *how much of the need I actually cover times how reliable those parts have been*, and I confirm by trial, by reproduction, or by a proven sibling. Where I hold **nothing** that touches the need, I do not invent — I say so, name the missing keys, and hand the gap to you. That impasse is not a failure of the loop; it is the loop working honestly. The teacher is gone; the limit of what I can compose is now visible instead of hidden behind a `claude -p`.

---

Two open seams worth your call before I implement:

- **`CapKey` interning at load time** — seeded axes/primitives need a backfill rule to mint `requires_key`/`provides_key` from their existing `capability_keys` list-attrs on boot, so this works without rewriting every seed by hand. (Same get-or-create dedup as the slang canonical-concept fix.)
- **`reliability` seeding** — never-measured primitives default 0.5; I propose a resolved faculty adopts its `sat_best` as reliability so proven parts raise a composition's prior. If you'd rather start everything at a flat prior and let it learn, say so.

Want me to implement this — the `CapKey` reification + the five rules + the teacher-free reflex + the generic `composed` runner — and gate it against the 591?
