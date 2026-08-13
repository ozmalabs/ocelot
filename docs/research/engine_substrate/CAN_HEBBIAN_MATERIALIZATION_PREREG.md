# Unblocking Blocker B for its three consumers — PREREG

Base `main @ 299ace3` ("Merge can-consumer-migration: 1/7 migrated (Bigville),
6/7 honestly blocked, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-hebbian-materialization`, branch
`can-hebbian-materialization`. One of three parallel primitive-building rungs
unblocking `CAN_CONSUMER_MIGRATION_RESULTS.md`'s named "Blocker B"
(consumers 2, 4, 6 — `insight_detection.py::consolidate_insight`,
`insight_propagation.py::propagate_insight`, `self_improvement_loop.py::
maybe_hebbian`).

---

## 0. The question, stated precisely

`Blocker B`, quoted from `CAN_CONSUMER_MIGRATION_RESULTS.md` §1 row 2: *"the
native log-odds render is intentionally non-materializing
(`LOGODDS_GENERATOR_RESULTS.md` §2/§4(b): confirmed live, never writes graph
state); nothing wires it back to `causal_influence.weight`."* Two candidate
resolutions, registered before reading the callers closely enough to decide
between them:

- **(A) Genuine materialization is required** — some caller reads a STORED
  weight value back, across ticks, that the native mechanism does not
  currently produce in a way that respects the frame/continuum invariant.
- **(B) On-demand reading suffices** — every caller only ever consumes the
  RETURN VALUE of `mt_hebbian_update_J` (an edge count) for control flow /
  telemetry, never a stored weight, so the already-built v1.1.0 evidence-count
  mechanism (`LOGODDS_GENERATOR_RESULTS.md`) is already the correct native
  analog and the only genuine gap is elsewhere.

## 1. Investigation, done before this document — findings

Read in full: `domains/insight_detection.py` (`consolidate_insight`,
`:153-167`), `domains/insight_propagation.py` (`propagate_insight`,
`:56-157`), `domains/self_improvement_loop.py` (`mt_allows`/`maybe_hebbian`,
`:44-77`, and `self_improvement_step`'s call site, `:‌266-289`).

**`consolidate_insight`'s only externally-visible effect is its return
value** — an `int` (edges updated), forwarded verbatim from
`substrate.mt_hebbian_update_J(mt, eta)`. It does not read any edge's
`weight` attr itself.

**Every caller of `consolidate_insight`/`maybe_hebbian` uses that `int`
exactly two ways, never as a float coupling strength:**

1. **Truthy control flow** — `self_improvement_step` (`:286-289`):
   `if edges_hebbian or edges_decayed or fields_decayed or identity_updated:
   relax(substrate, mt)` — re-relax only if SOMETHING changed.
   `propagate_insight` (`:129-132`): `if consolidation: substrate.
   mt_relax_to_marginal(other_mt); new_audit = substrate.mt_audit_basin
   (other_mt)`. Both branches ask "did anything change," never "by how
   much," and the re-relax that follows is the CONTINUOUS mechanism's own
   subsequent read of `causal_influence.weight` — a can_ops.rs-internal
   concern, out of this rung's scope to touch or replace.
2. **Telemetry** — stashed verbatim into `insight["consolidation_edges"]`
   (`self_improvement_loop.py:266`) / `cascade_event["consolidation_edges"]`
   (`insight_propagation.py:133`), never read back arithmetically by
   anything else in the two files searched.

**Grep confirms no Python file outside `can_migration.py` (a one-time
`refers_to`→`causal_influence` migration shim, unrelated) and
`worlds/bigville_can_beliefs.py` (edge-schema construction, not a read of a
previously-Hebbian-updated weight) ever reads `causal_influence`'s `weight`
attr as a VALUE.** The only consumer of the weight VALUE anywhere in Python
is `can_ops.rs` itself (via PyO3, opaque to grep) during
`mt_relax_to_marginal`/`mt_mean_field_marginal`.

**Registered finding, going in: (B) — on-demand reading suffices for what
these three callers actually need.** No caller reads a stored weight value
back across ticks; every caller wants (i) a real mutation to have happened
to SOME persistent, in-frame state (satisfied already by v1.1.0's
`evidence_confirm`/`evidence_disconfirm`/`evidence_tick` integer counters on
the `Coactivation` ledger node, `LOGODDS_GENERATOR_RESULTS.md` §3) and (ii)
an integer-shaped "how much happened" signal to gate control flow and to
report (satisfiable by counting Coactivation ledger entries touched this
tick — a mechanical graph query, not a new write).

**The genuine, confirmed gap is narrower than "build a materializing
write": it is that `can_native_hebbian_mint`/`can_native_hebbian_reweight`
(`seeds/can_native_reimplementation.json`) fire UNCONDITIONALLY today — no
`update_policy` check, no `plasticity_override` transient path — while their
continuous twin (`mt_hebbian_update_J`, called only through `mt_allows`-gated
`consolidate_insight`/`maybe_hebbian`) is always policy-gated.** This is
Blocker B's OWN task item 3 ("build the policy gate"), and on inspection it
is the load-bearing piece, not an add-on to a bigger missing mechanism.

## 2. What will be built

1. **No new materializing write.** The v1.1.0 evidence-count mechanism
   (already built, `LOGODDS_GENERATOR_RESULTS.md`) is confirmed and reused
   as-is as the native Hebbian analog. Zero changes to
   `can_native_note_coactivation`'s or the counters' own semantics.
2. **A policy gate**, added to `can_native_hebbian_mint`'s and
   `can_native_hebbian_reweight`'s `where` clauses (seed bump 1.1.0 →
   1.2.0, via a `tools/`-style builder script that loads, patches, and
   rewrites the JSON — matching this codebase's own precedent for
   in-place seed edits), mirroring `mt_allows`'s three-way policy switch
   (frozen/adaptive/hybrid) OR'd with a `plasticity_override > 0` transient
   rescue, expressed purely as `Eq`/`IfThenElse`/`Or`/`Gt`/`Not` Term
   composition — zero new Rust, zero new Term kinds (all confirmed already
   used elsewhere in this seed or `logodds_generator`'s own build).
   **One registered, deliberate divergence from `mt_allows`'s own default**:
   `mt_allows` defaults an Mt with NO `update_policy` attr to `frozen` (deny)
   — a Python-side safety default. The existing regression file
   (`tests/test_can_native_reimplementation.py`) builds its Hebbian-test Mts
   WITHOUT setting `update_policy` at all, and that file is required to stay
   green UNCHANGED (house discipline). The native gate's default for a
   POLICY-ABSENT Mt is therefore registered as ALLOW (legacy/opt-in
   behavior — an Mt that has never been classified by the policy system
   behaves exactly as the pre-gate rule always did), while an Mt carrying an
   EXPLICIT `update_policy` attr (`frozen`/`adaptive`/`hybrid`) is gated
   identically to `mt_allows`. This is flagged here, before writing the
   gate, as a genuine behavioral divergence from the continuous mechanism's
   own default, not discovered after the fact.
3. **A thin, no-decision Python bridge module** (new file, NOT one of the
   three explicitly-out-of-scope files), exposing: (a) a mechanical
   traversal to find the `Coactivation` ledger node for a given `(mt, a, b)`
   pair (the same `a -coactivated_with-> co -coactivation_of-> b` walk the
   seed's own rules already match on — reused, not reinvented); (b) an
   on-demand log-odds render for that node, evaluated live via
   `Substrate.evaluate`, the exact idiom `LOGODDS_GENERATOR_RESULTS.md` §2
   already proved; (c) a mechanical "how many ledger entries were touched
   this tick" count (comparing `evidence_tick == mt.can_tick` across the
   Mt's Coactivation nodes) as the drop-in analog of `mt_hebbian_update_J`'s
   returned edge count. All three are pure queries/renders over already-held
   graph state — no `if`/`else` deciding what to WRITE, matching the
   world-adapter "Emit" role CLAUDE.md carves out.

## 3. Live demonstration, registered

One isolated 2-Concept Mt per policy condition (mirroring
`tests/test_can_native_reimplementation.py`'s own `discrete_mode="static"`
isolation idiom so item-3's relaxation rules never interfere), driven through
several `can_tick` steps:

- **adaptive**: co-activation across ticks 0→1 mints the edge (tick 1),
  further same-sign co-activation (ticks 2-3) increments `evidence_confirm`,
  a disconfirming tick (4) increments `evidence_disconfirm` — log-odds render
  moves accordingly (up then down), matching v1.1.0's own already-proven
  trajectory.
- **frozen, no override**: identical co-activation sequence — mint/reweight
  MUST NOT fire at all (no edge minted OR, if pre-seeded, no evidence counter
  changes) at any tick.
- **frozen + `plasticity_override > 0`**: identical sequence — mint/reweight
  DOES fire, exactly as under `adaptive`.
- **hybrid, `allow_Hebbian_J: false`**: denied, same shape as frozen.
- **hybrid, `allow_Hebbian_J` attr absent** (mt_allows' own documented
  default-True-for-unlisted-axis): allowed.
- **no `update_policy` attr at all** (the legacy/regression-file shape):
  allowed — this IS `tests/test_can_native_reimplementation.py`'s own two
  existing Hebbian tests, expected to pass byte-identically, unmodified.

**Invariant check, registered**: for every scenario, `dict(node.attrs)` on
every `Coactivation`/`Concept`/`Microtheory` node is compared before and
after every `evaluate()` call of the log-odds render Term — predicted
identical every time, and a direct grep/attribute-key scan across all node
attrs after the full demonstration is predicted to show no `log_odds` (or
any other float-render) key on any node, ever — only the pre-existing
integer `evidence_confirm`/`evidence_disconfirm`/`evidence_tick` keys.

## 4. What this rung will NOT do

- No edit to `domains/insight_detection.py`, `domains/insight_propagation.py`,
  `domains/self_improvement_loop.py` (explicitly out of scope — a later,
  coordinated migration rung's job).
- No change to `can_ops.rs` or the log-odds render Term composition itself.
- No new Rust Term. If the investigation above turns out to be wrong and a
  genuine materializing write IS required in a way the existing Term algebra
  cannot express, this document will be updated BEFORE any Rust is written,
  and the RESULTS doc will say so plainly.
- No claim about the counterfactual-predictor (Blocker A) or decay/identity
  dynamics blockers — untouched, not this rung's territory.
- No resolution of whether graded reweighting ever reaches the NATIVE
  discrete propagation's own local-field computation
  (`can_native_update_3state`/`_2state`, item 3) — that rule reads a literal
  `EdgeAttr(e,"weight")` hardcoded to `1.0` at mint time and is UNCHANGED by
  this rung; if the investigation surfaces this as a real residual it will be
  reported honestly in the RESULTS doc, not silently fixed by touching item
  3's rules (which is a materially different, unscoped question — whether
  the CONTINUOUS consumers this rung targets need that fixed is a separate
  claim from whether the NATIVE propagation path needs it).
