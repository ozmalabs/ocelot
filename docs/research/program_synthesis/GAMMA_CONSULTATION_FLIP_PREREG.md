# Γ consultation flip — closing residual #41 — PREREG

Base `main @ de1845d` ("Merge mdl-occam-witness-pricing: witness-priced
literals, the Occam-ordering metric fix -- +1 (task 451), zero
regressions"), verified via `git log --oneline -1 main` immediately before
creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/gamma-consultation-flip`, branch
`gamma-consultation-flip`. MBPP baseline reconfirmed live from the
worktree's own copy of `results/mbpp_endgame.json` (`head:
de1845d47381523e7c967c5152aa5c7bbf9c0922`, exact task-id `pass` lists
saved to scratchpad before any change): **88/257 full, 87/257
content_stripped, 114/257 official** — matches the task brief exactly.

**Headline (predicted, not yet measured): this rung closes residual #41
by flipping `run_enumerate`'s op-list construction to consult Γ
(`admissible_moves`) when the caller passes no explicit `ops`, but ONLY
after extending the Γ table with two small, previously-uncovered evidence
sites that landed AFTER the bulk-transcription rung
(`ZipWith`, `zip-elementwise` rung; `GroupCount`-inside-the-list-shaped-
branch, `ceiling-reassessment-6` rung) — both confirmed missing by reading
current source directly, not assumed. The `DICT_DEFAULT_OPS` bucket
(7 ops, widened 5→7 in the SAME `ceiling-reassessment-6` rung) is
confirmed to remain genuinely, deliberately out of Γ's covered scope
today, and the flip's own fallback rule (`Γ admits nothing → leave
spec["ops"] unset, defer to Rust's own internal default`) is designed to
handle that branch correctly WITHOUT extending Γ to cover it, matching the
task brief's own scope framing. A genuine, structural op-list ORDER
concern is found and named honestly below (§4) — not fixable with a
single static candidate order — and is treated as a measured, not
assumed, question for the battery to answer.**

---

## 1. What is being flipped, precisely

`domains/prog_synthesis.py::run_enumerate` (`prog_synthesis.py:1278`
onward), the P4-A seam that hands a `SynthEnumerate` spec dict to
`sub._inner.evaluate`. Currently (as landed by
`OPLIST_ADMISSIBILITY_GRAMMAR_SLICE1_RESULTS.md`, unchanged by
`PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_RESULTS.md` per that
document's own §10.4):

```python
spec_shape_flags = _synth_spec_shape_flags(raw_rows)
spec_shape_node = sub.add_node("SynthSpecShape", spec_shape_flags)
gamma_sortby_admitted = bool(sub._inner.is_edge_admissible(
    spec_shape_node, "admits_op", "SynthOp", {"name": "SortBy"}))
sub.set_attr(g, "ps_enum_gamma_sortby_admitted", gamma_sortby_admitted)
...
graph_ops = _plain(sub.node(msg)["attrs"].get("ps_enum_ops")) ...
if graph_ops:
    spec["ops"] = {"type": "Lit", "value": [_text(op) for op in graph_ops]}
# else: spec["ops"] is left UNSET -- the Rust ladder's own internal
# default (eval_synth_enumerate's if/else-if chain) decides.
```

`graph_ops` is the NL-classifier-driven explicit op selection
(`ps_select_synthesis_operator_shape`) — when present, it ALREADY wins and
is untouched by this rung (out of scope; the task brief's own framing is
"when the caller passes no explicit `ops`"). The flip targets exactly the
`else` branch: when `graph_ops` is falsy, instead of leaving `spec["ops"]`
unset (which defers to Rust's own hand-written ladder,
`runners/dsl/src/synth_enumerate.rs:2359-2711`), consult Γ
(`admissible_moves`, not another `is_edge_admissible` probe — see §3) and,
if it admits a non-empty op set, use THAT as `spec["ops"]`.

## 2. Re-verified live: the Γ table's actual current coverage (not
   inherited from the bulk-transcription document's own count)

`OP_TABLE` (`synth_enumerate.rs:359-...`, counted programmatically via a
regex over the const's own body): **58 entries**, not the bulk
transcription's own "57" — `ZipWith` (`progsyn-zip-elementwise`,
`8f2c054`, merged AFTER `progsyn-gamma-bulk-transcription`, `38788ba`, per
`git log --oneline -- runners/dsl/src/synth_enumerate.rs`) is the 58th,
inserted between `DictMerge` and `Mod`. The `program_synthesis_opgrammar`
seed's own `SynthOp` node population is confirmed **57**, confirmed
missing `ZipWith` by direct membership check
(`'ZipWith' in [n['attrs']['name'] for n in seed['nodes'] if n['type']=='SynthOp']`
→ `False`).

Three concrete, source-verified gaps, all landed in the ladder AFTER the
bulk-transcription rung (`38788ba`):

1. **`ZipWith`** (`fe22e02`/`8f2c054`, `progsyn-zip-elementwise`) — a new
   evidence site inside the already-covered list-shaped branch:
   `spec_has_two_zippable_list_vars` (≥2 spec variables, each
   consistently list/tuple-shaped on every row, with EQUAL length on
   every row pairwise) → push `"ZipWith"` (`synth_enumerate.rs:2670-2679`).
   Zero Γ productions reference `ZipWith` today.
2. **`GroupCount` inside the list-shaped branch** (`45e987c`,
   GroupCount/DictMerge rung — landed BEFORE bulk-transcription, but
   correctly identified here as never having been given its own site
   despite living inside an already-Γ-covered branch): `spec_is_list_
   shaped && spec_output_is_dictlike` → push `"GroupCount"`
   (`synth_enumerate.rs:2667-2669`, task 88's own witness,
   `freq_count`). Re-read the bulk-transcription RESULTS document's own
   14-site table (§2) closely: this specific push is NOT one of the 14
   named sites (it is textually adjacent to site J's "has_dict_value"
   completion but keyed on the OUTPUT-shape flag `output_is_dictlike`, a
   distinct condition) — genuinely never covered, not merely
   deliberately excluded the way the full `DICT_DEFAULT_OPS` bucket was
   (next point). Zero Γ productions reference `GroupCount` today (grepped
   the seed's own production bodies directly).
3. **`DICT_DEFAULT_OPS` bucket widened 5→7 ops** (`aac3945`,
   `progsyn-ceiling-reassessment-6`, landed AFTER bulk-transcription):
   `&["Eq", "IfThenElse", "GroupCount", "DictMerge", "DictFromPairs",
   "DictItems", "FilterList"]` (`synth_enumerate.rs:602-603`) — was
   `["Eq", "IfThenElse", "GroupCount", "DictMerge", "DictFromPairs"]` (5
   ops) at bulk-transcription time. Confirmed via `git show aac3945 --
   runners/dsl/src/synth_enumerate.rs`: `DictItems`/`FilterList` were
   added specifically so `Fold(FilterList(DictItems(dict), item,
   predicate))` becomes constructible. **This ENTIRE branch remains
   correctly, deliberately out of Γ's covered scope** — the
   bulk-transcription document's own §1 named it explicitly ("Deliberately
   out of Γ scope (not one of the 14 named sites)"), and the task brief's
   own framing groups it with `exclude_ops`/`derived_ops` as things this
   rung does not touch. VERIFIED (not assumed, per the task brief's own
   instruction): grepped every production's `where` body in the seed —
   `"GroupCount"`, `"DictMerge"`, `"DictFromPairs"` never appear as an
   `Eq`/`In` member anywhere. Γ's admitted set for a spec landing in this
   branch (`¬is_string_shaped ∧ ¬output_is_setlike ∧ ¬is_list_shaped ∧
   output_is_dictlike`) is **exactly EMPTY** today — no existing
   production's `where` clause is satisfiable under that flag combination
   (every list-shaped-branch production requires `is_list_shaped=true`;
   the bare-scalar-fallback baseline and sites G/H explicitly conjunct
   `¬output_is_dictlike`). This EMPTY-verdict fact is the basis for the
   flip's fallback rule (§3.2) — it is not an assumption, it follows from
   reading all 15 productions' `where` bodies against this exact flag
   combination.

`item_mod_eq` (grepped per the task brief's own suggestion) is a
**template-pool** predicate family
(`synth_enumerate.rs:3114`, `map_templates_by_size`), not an op-list
evidence-gate site — already correctly out of scope per the bulk
transcription's own §10.5 ("Does not port the §1.2 template-pool
population"), unaffected by anything in this rung.

## 3. The flip's design

### 3.1 Consultation call: `admissible_moves`, not repeated
    `is_edge_admissible`

`Substrate::admissible_moves` (`substrate.rs:1887`, PyO3 exposed at
`py.rs:7958`) takes `(src, edge_type, candidates: Vec<(type, attrs)>)` and
returns the ADMITTED subset with weights, materialising one scratch node
per candidate — the same mechanism `is_edge_admissible`'s slow path uses,
batched. One call, `sub._inner.admissible_moves(spec_shape_node,
"admits_op", [("SynthOp", {"name": n}) for n in _GAMMA_OP_CANDIDATE_
ORDER])`, replaces the current single-op `SortBy` probe.

### 3.2 The fallback rule: empty Γ verdict → leave `spec["ops"]` unset

```python
if graph_ops:
    spec["ops"] = {...}                      # unchanged, explicit-ops path
elif gamma_ops:                                # non-empty admitted set
    spec["ops"] = {"type": "Lit", "value": gamma_ops}
# else: spec["ops"] stays unset -- Rust's own internal typed-default
# ladder decides, byte-identical to pre-flip behaviour for this call.
```

This is not a hidden branch-classification of "which Rust bucket is this"
— it is a direct, mechanical reading of Γ's own verdict, using the SAME
"empty means Γ has no opinion, defer to the substrate" idiom the rest of
this arc already uses for admissibility probes. It happens to coincide
exactly with the `DICT_DEFAULT_OPS` branch (§2, point 3) because that is
the one branch where the verdict is provably always empty today — proven
by exhaustive reading of all 15 (soon 17) productions' `where` clauses
against that flag combination, not by adding a second Python-side
flag check that duplicates the Rust ladder's own branch selection.

### 3.3 Extending Γ: 2 new productions + 1 new flag + 1 new `SynthOp` node

Closing gaps 1 and 2 from §2 (the two evidence sites that live INSIDE the
already-Γ-covered list-shaped branch) — same recipe as the bulk
transcription's own site I/L pattern (single-op `Eq(op.name, "X")`
production, gated on the exact real evidence flags, `¬output_is_setlike`
required per the seed's own standing invariant for every list-shaped-arm
production):

- `site_o_list_shaped_dictlike_output_groupcount`: `op.name="GroupCount"
  ∧ spec.is_list_shaped=true ∧ spec.output_is_dictlike=true ∧
  ¬spec.output_is_setlike`.
- `site_p_list_shaped_two_zippable_vars_zipwith`: `op.name="ZipWith" ∧
  spec.is_list_shaped=true ∧ spec.has_two_zippable_list_vars=true ∧
  ¬spec.output_is_setlike`.

New `SynthSpecShape` flag (12th): `has_two_zippable_list_vars` — a direct
port of `spec_has_two_zippable_list_vars`
(`synth_enumerate.rs:2395-2413`): at least two spec variables that are
EACH list/tuple/set/frozenset-shaped on every row, with some such PAIR
having equal length on every row. Added to `_synth_spec_shape_flags`
(the SAME documented-duplication idiom already covering the other 11
flags — fork (a) from the tracked tradeoff table, unchanged).

New `SynthOp` node: `ZipWith` (local_id 58). The `DICT_DEFAULT_OPS` bucket
itself is NOT extended (§2 point 3, §3.2) — no new productions for
`DictMerge`/`DictFromPairs`, no widening of the bare-scalar-fallback
baseline's exclusions (already correctly excludes `output_is_dictlike`).

### 3.4 Downstream consumers of the resolved `op_list`: confirmed
    source-agnostic

Read `eval_synth_enumerate` end to end for anything keyed on "was `ops`
explicit" rather than "what does the resolved `op_list` contain":

- `op_list` construction (`synth_enumerate.rs:2745-2775`): `ops_t=Some`
  evaluating to `Value::None` ALREADY falls back to `default_ops` — the
  exact same code path an explicit list takes is what Γ's output will
  take once passed as `spec["ops"]`; nothing distinguishes "explicit list
  from Γ" from "explicit list from the NL classifier" at this layer.
- `exclude_ops` (`synth_enumerate.rs:2776-2784`+): applied AFTER `op_list`
  converges "whether it came from the typed default above or a caller's
  own explicit `ops`" (the code's own comment) — confirmed source-
  agnostic, untouched by this rung, exactly per the task brief's
  instruction to leave it alone.
- `ZIP_MAX_CANDIDATES`/`DICT_FILTER_MAX_CANDIDATES` budget raises
  (`synth_enumerate.rs:2872-2897`): gated on `op_list.iter().any(name ==
  "ZipWith")` / `(contains "DictItems" ∧ contains "FilterList")` — reads
  the FULLY RESOLVED `op_list`, confirmed by the code's own comment
  ("`op_list` is fully resolved (typed default or explicit `ops`, post-
  `exclude_ops` filter) by this point") — **this is why extending Γ to
  cover `ZipWith` (§3.3) matters beyond op selection itself**: without
  it, a Γ-sourced op list missing `ZipWith` would ALSO silently fail to
  trigger the 300k-candidate budget raise for any zip-shaped spec,
  compounding a search-space regression on top of a missing-op
  regression. With the extension, Γ's output correctly includes
  `ZipWith` whenever the real ladder's default would, so the budget gate
  fires identically regardless of source.
- `derived_ops`/`Call` (`synth_enumerate.rs:2717-2731`): independent of
  `ops_t`, reads its own separate `derived_ops_t` term — untouched,
  confirmed, per the task brief's own scope note.

No hidden "was this explicit" flag exists anywhere else in the function
that this flip could silently trip.

## 4. A genuine, structural limitation, named honestly: `op_list` ORDER

The Rust ladder's own module doc (`LIST_EXTRA_OPS`'s comment) states
`op_list` ORDER is load-bearing for the search: "within one size the
growth loop walks `op_list` in order" — determines which of several
observationally-EQUIVALENT-on-revealed-rows candidates wins
signature-pruning at a given size, which can matter for a task's
correctness on HELD-OUT rows even when the ADMITTED SET is identical.

`admissible_moves` returns admitted candidates in the SAME relative order
as the candidate list supplied to it (confirmed by reading
`substrate.rs:1892-1920`'s `for (tgt_type, tgt_attrs) in candidates`
loop — straight iteration, no re-sort). So the flip's fidelity to the
real ladder's op ORDER depends entirely on the order of
`_GAMMA_OP_CANDIDATE_ORDER`, the Python-side candidate list this rung
must supply.

**Checked directly, not assumed: no single static candidate order can
reproduce every real branch's own internal push order simultaneously.**
Concrete, confirmed conflict: `DEFAULT_STR_OPS` (the string-shaped
branch) pushes `MapList` before `JoinList`
(`synth_enumerate.rs:644-647`); `LIST_EXTRA_OPS` (the list-shaped branch)
pushes `JoinList` before `MapList` (`synth_enumerate.rs:496-514`, indices
8 and 10). These two branches are mutually exclusive for any one spec
(`is_string_shaped` requires every value Str-typed; `is_list_shaped`
requires a listlike output/var — a `Value` cannot be both), so there is
no live spec where this conflict is directly observable as two different
correct answers being demanded of the SAME candidate list — but it DOES
mean a single fixed `_GAMMA_OP_CANDIDATE_ORDER`, fed once into one
`admissible_moves` call per `run_enumerate` invocation, is structurally
unable to preserve BOTH branches' real internal order at once. Re-
deriving a fully faithful per-branch order inside Python would require
re-implementing the branch classification itself from the flags — the
exact ladder-in-Python duplication this flip is trying to avoid
introducing a second copy of.

**Decision: proceed with ONE canonical order — the live `OP_TABLE`'s own
declaration order (re-derived programmatically from
`synth_enumerate.rs`, a well-defined existing engine artifact, not
hand-invented) — and treat order-fidelity as an EMPIRICAL question for
the paired battery and parity sweep to answer, not a property to assume.**
This is the same category of "documented, tracked liability" this rung's
own `_synth_spec_shape_flags`/`_GAMMA_OP_CANDIDATE_ORDER` duplication
already is (fork (a) from the SLICE1 tradeoff table) — a third instance
of the SAME accepted idiom in this file, not a new kind of risk. If the
paired MBPP battery (§6) comes back with an exact task-id-set match on
all three arms, that is strong, direct evidence order does not change any
CURRENTLY-MEASURED outcome; if it does not, the deviation is investigated
and reported precisely (house discipline), including checking whether a
mismatch is genuinely order-driven (same admitted SET, different winning
term) versus a genuine SET-coverage gap missed by this document's own
§2 audit.

## 5. What will be recorded on the Goal node

Replacing `ps_enum_gamma_sortby_admitted` (SLICE1's single-op probe,
superseded by full-set consultation) with:

- `ps_enum_gamma_ops_admitted`: sorted, comma-joined `gamma_ops` names (or
  empty string) — a fact, for inspection/debugging.
- `ps_enum_gamma_ops_used`: bool — true iff Γ's non-empty verdict was
  actually written into `spec["ops"]` this call (false when `graph_ops`
  won, or when Γ's verdict was empty and the Rust default was deferred
  to).
- `ps_enum_gamma_ops_error`: exception text (truncated), only set if the
  `admissible_moves` call itself raises — caught and recorded, never
  propagated, matching the SLICE1 precedent's own discipline (a Γ-path
  failure must never break a battery run; on error, falls back to the
  unset-`ops` path, i.e. treated the same as an empty verdict).

## 6. Verification plan (not yet run — this document precedes any code
   change)

1. Implement §3's flip + §3.3's two productions/flag/node.
2. Re-run `scripts/opgrammar_bulk_parity_sweep.py`, itself updated to
   match CURRENT source exactly (the existing oracle is stale — its
   `DICT_DEFAULT_OPS` constant has only 5 names, missing the
   `ceiling-reassessment-6` widening's `DictItems`/`FilterList`; it has no
   `ZipWith` branch at all). Expect 420/420 explained, with the two newly
   covered sites moving from "diff-but-explained (out-of-scope op)" into
   "exact set-agreement" where they apply.
3. Paired MBPP battery, exact task-id `pass` set diff on all 3 arms
   against the saved BEFORE state (88/87/114,
   `results/mbpp_endgame_BEFORE.json`) — expected empty added/removed,
   treating any non-empty diff as a bug to explain precisely (§4's own
   named risk is exactly what this gate exists to catch).
4. Named 9-file suite + `test_opgrammar_migrated.py` — expect exactly the
   3 known pre-existing pin-drift failures.
5. No `.rs` files are touched by this design (`admissible_moves`/
   `is_edge_admissible` are already PyO3-exposed) — no Rust rebuild
   required; will confirm `git diff --stat -- runners/dsl/src/` is empty
   throughout.

## 7. What this document does NOT establish

1. No code has been written yet — this PREREG precedes the implementation
   entirely, per house discipline.
2. Whether the battery is genuinely byte-identical after the flip is an
   open, measured question, not a foregone conclusion — §4's order
   concern is real and named, not dismissed.
3. Whether the `DICT_DEFAULT_OPS` branch should EVER be brought into Γ
   scope is explicitly left as a follow-on question, not decided here —
   this rung treats it as correctly out of scope, consistent with the
   task brief's own framing and the bulk-transcription rung's own
   deliberate exclusion.
4. The literal-pricing-as-Γ-evidence stretch goal (design doc's Slice 2
   framing) is out of scope for this rung unless the core flip lands
   cleanly with appetite remaining — not attempted in this document's own
   plan.
