# Shape audit — Pattern C fixes — results

**Verdict: GO on all three (AR1, AR2, AR3). AR4 (regression) is clean: 7/7
identical failing-node-ids, paired against a from-scratch pristine baseline
in the same worktree, all pre-existing and environment-conditional
(`data/` absent — the population CLAUDE.md's own retracted note already
documents), zero attributable to this rung's diff.**

**The one thing worth reading if you read nothing else:** all three fixes are
the SAME shape — "an index or marker that lives OUTSIDE the graph decides
whether to mint, while the minted content lives INSIDE the graph" (the
generalisable Pattern C shape `SHAPE_AUDIT.md` §4.1 names) — but they needed
three DIFFERENT specific edits, confirmed by reading each function
independently rather than assumed from the audit's prose: AR1's index (the
`capability_keys` string) was never wrong to persist, it was wrong to
*compute* (order-dependent, truncated); AR2's index was never wired to
`save`/`load` AT ALL; AR3's index WAS wired to `save`/`load` correctly but
the mint path never *read* it. Two of the three (AR2, AR3) converge on the
exact same fallback discipline already established elsewhere in the same
file — `_concept_by_name` as the ground truth, matching `_ensure_concept`'s
existing precedent (CLAUDE.md: *"State lives in the substrate. Python may
cache for performance, but the substrate is the source of truth."*) — which
is why AR2's fix additionally survives a checkpoint saved BEFORE this fix
(missing the new persisted key entirely), not just checkpoints saved after.

---

## 0. Provenance

- Worktree: `/home/matt/ocelot-shape-audit-pattern-c`, branch
  `shape-audit-pattern-c-fixes`, detached from `main` at `4f24abb` (verified
  via `git log --oneline -1 main` immediately before worktree creation).
- No Rust rebuild performed. The pre-existing `.so` in this worktree already
  imports and passes the coherence probe (`add_node("T", {"lst":[1,2,3],
  "tup":(1,2,3)})` reads back `{'lst': [1, 2, 3], 'tup': (1, 2, 3)}`,
  list/tuple distinct) — confirmed before any edit. All three fixes are
  Python-level identity/dedup computations over existing, already-adequate
  Terms/rules; none required a new DSL primitive.
- PREREG:
  `docs/research/engine_substrate/SHAPE_AUDIT_PATTERN_C_FIXES_PREREG.md`,
  registered before any code was written; §1-§3's root-cause investigations
  there are not repeated in full here.
- Diff: `domains/reflective_faculty.py` (+9/-1, one line inside
  `induce_concern`'s key computation), `substrate/world_adapter.py`
  (+42/-3: `save`/`load` gain a `recursive_concepts` key pair;
  `learn_word`/`learn_recursive_concept` gain a find-or-create lookup
  before mint). No seed JSON touched — every fix is a Python identity/dedup
  computation, and the rules already treat `capability_keys` opaquely as an
  equality-tested value.

---

## 1. AR1 — `CapabilityAxis` identity

### Root cause (verified, not assumed)

`induce_concern` (`domains/reflective_faculty.py:1268-1390`) built the
mint/dedup identity as `"induced_" + "_".join(preds[:3])` — the observation's
own predicate-head list, in whatever order the caller supplied it, truncated
to the first three. Confirmed by reading:

- The 5 other `capability_keys` comparison sites in the same file
  (`:2807, :3027, :3960, :4145, :5877, :6421`) all compare it as an opaque,
  already-canonical string — none sort or truncate at their own end, so this
  ONE site (the writer) was the sole source of the inconsistency.
- `build_candidate` (`runners/dsl/src/shape_decode.rs:1589-1591`)
  canonically sorts both sides with `cmp_value` before comparing;
  `ShapeDecode`/`AntiUnify`/`FixedCount` all score over relation SETS —
  confirming the audit's "every other comparison here is canonically
  sorted" claim by direct inspection, not by citation.
- Both seed rules read in full (`seeds/shape_decode_loop.json`'s
  `sd_mint_quantum`/`sd_dedup_existing`): the guard is a literal
  `capability_keys == obs.key` equality test; `sd_dedup_existing`'s ONLY
  effect is `set_attr(obs, "status", "recognized_duplicate")`.
- No length constraint anywhere: grepped every `capability_keys`/`obs.key`
  read site in both the seed and the Python file — every one is an equality
  test or opaque string field, never sliced, never rendered with a
  length-dependent format. Truncation was never load-bearing.

### Fix

```python
key = name_hint or (("induced_" + "_".join(sorted(preds))) if preds else "induced_concern")
```

Sorted (fixes order-dependence), untruncated (fixes the dangerous
false-match/suppressed-mint direction), NOT deduplicated (a repeated
predicate head is real multiset information the join should not discard —
matches `build_candidate`'s own convention of sorting, not deduping).

### Live before/after evidence

Two genuinely different `induce_concern` calls (no `name_hint`, so the real
key-derivation path is exercised), sharing their first three predicate
heads in the same order but diverging at relation 4:

```
obs_a = [["zqA","1"],["zqB","2"],["zqC","3"],["zqX","4"]]
obs_b = [["zqA","1"],["zqB","2"],["zqC","3"],["zqY","5"]]
```

**BEFORE** (pristine `4f24abb`, run in this worktree via `git stash`):
```
r1: {'minted': True,  'capability_key': 'induced_zqA_zqB_zqC', 'axis_id': '#768'}
r2: {'minted': False, 'capability_key': 'induced_zqA_zqB_zqC', 'covered_by_existing_axis': '#768'}
axes minted total: 1   <- the growth failure: obs_b is genuinely novel and never mints
```

**AFTER** (this rung's fix):
```
r1: {'minted': True, 'capability_key': 'induced_zqA_zqB_zqC_zqX', 'axis_id': '#768'}
r2: {'minted': True, 'capability_key': 'induced_zqA_zqB_zqC_zqY', 'axis_id': '#770'}
axes minted total: 2   <- both correctly recognized as distinct
```

**Bonus check (not in the PREREG bar, verified because it was cheap and it
is the audit's OTHER failure direction):** the same relation SET in two
different observation orders now correctly dedups to ONE axis instead of
minting two:

```
obs_a = [["zrA","1"],["zrB","2"]];  obs_b = [["zrB","2"],["zrA","1"]]
r1: key='induced_zrA_zrB', minted=True,  axis_id='#768'
r2: key='induced_zrA_zrB', minted=False, covered_by_existing_axis='#768'
axes added: 1   <- correctly recognized as the SAME concern, was 2 before this fix
```

---

## 2. AR2 — `learn_recursive_concept`

### Root cause (verified, distinct from AR3)

`substrate/world_adapter.py:10113-10132` (pre-fix). Grepped
`_recursive_concepts` across the whole file: **3 occurrences, all inside
`learn_recursive_concept`/`recursive_concept` — none in `save()`
(`:6119-6143`) or `load()` (`:6146-6233`).** `load()` also bypasses
`__init__` via `cls.__new__(cls)`, so after a load the attribute is
genuinely ABSENT (not merely empty) — `getattr(self, "_recursive_concepts",
None)` returns `None`, a fresh dict is created, and the unconditional-mint
`else` branch fires for every name, known or not. **This is a different
defect from AR3: the index was never wired to persistence at all — there
was no "restore" step to fix, only "not persisted/restored" to add.**

### Fix

1. Persist `_recursive_concepts` in `save()` (mirrors `_concepts` exactly,
   `getattr(..., {})` so a WorldAdapter that never taught a recursive
   concept still saves) and restore it in `load()` (mirrors `_concepts`
   exactly, `.get(..., [])` so an OLD checkpoint without the new key still
   loads).
2. `learn_recursive_concept`'s lookup falls back to `_concept_by_name(name)`
   when the session index misses — covers checkpoints saved BEFORE this fix
   too, and backfills the index on a fallback hit so `recursive_concept()`/
   `eval_recursive()` keep working through the cheap path afterward.

Both edits are outside the checkpoint-load region a concurrent thread owns
(the Γ-mirror-replay loop, confirmed at `world_adapter.py:6174-6188` in
this worktree — the `_recursive_concepts` restore line sits at `:6208`,
well clear).

### Live before/after evidence

Teach `"factorial"`, save, load into a fresh `WorldAdapter`, teach
`"factorial"` again (the save/load-then-reteach trigger the audit names).

**BEFORE:**
```
taught #1, cid: #747
taught #2 (post-reload), cid: #749
Concept{name='factorial'} node count: 2   [#747, #749]
_concept_by_name resolves to:  #747   (STALE)
recursive_concept resolves to: #749   (NEW)
AGREE: False
```

**AFTER:**
```
taught #1, cid: #747
taught #2 (post-reload), cid: #747
Concept{name='factorial'} node count: 1   [#747]
_concept_by_name resolves to:  #747
recursive_concept resolves to: #747
AGREE: True
eval_recursive(factorial) = True   <- still functions correctly
```

**Additional check: a checkpoint saved BEFORE this fix** (simulated by
stripping the new `"recursive_concepts"` key from the saved blob before
loading — exactly the shape an in-flight production checkpoint would have):
`load()` restores an empty index (`{}`), and the `_concept_by_name`
fallback still finds the existing node on re-teach — `cid1 == cid2`, one
`Concept` node, no duplicate. The fix is not just forward-correct, it heals
existing checkpoints on their next re-teach.

---

## 3. AR3 — `learn_word`

### Root cause (verified, distinct from AR2)

`substrate/world_adapter.py:9987-9996` (pre-fix, line numbers before AR2's
edits shifted the file). `self._concepts` **IS** initialised in `__init__`
(`:70`), **IS** written by `save()` (`:6137`) and **IS** restored by
`load()` (`:6199`) — confirmed by reading both sites directly. The defect
is narrower than AR2's: the index survives a save/load round-trip intact,
but `learn_word` itself never calls `self._concepts.get(name)` before
unconditionally minting a new `Concept` + a new `definition` Term subgraph.
Unlike AR2, this defect doesn't even need a reload to trigger — two
same-session `learn_word("prime", ...)` calls already mint two nodes.

### Fix

Mirror the replace-on-reteach pattern `learn_recursive_concept` already
establishes in the same file: `cid = self._concepts.get(name) or
self._concept_by_name(name)`; if found, remove the old `definition` edge +
subgraph before attaching the new one; only mint a fresh `Concept` when
neither lookup finds one.

### Live before/after evidence

**BEFORE**, same-session re-teach (no reload needed):
```
taught #1, cid: #748
taught #2 (same session), cid: #750
Concept{name='prime'} node count: 2   [#748, #750]
_concept_by_name resolves to:     #748   (STALE)
self._concepts['prime'] resolves to: #750   (NEW)
AGREE: False
```
And the harder, AR2-matching trigger (save/load then re-teach) compounds it
further: **3** `Concept{name='prime'}` nodes after one reload + re-teach.

**AFTER**, same-session re-teach:
```
taught #1, cid: #747
taught #2 (same session), cid: #747
Concept{name='prime'} node count: 1   [#747]
_concept_by_name resolves to:      #747
self._concepts['prime'] resolves to: #747
AGREE: True
concept_holds still works: True
```
And the save/load-then-re-teach trigger: **1** `Concept{name='prime'}` node,
both resolution paths agree.

---

## 4. AR4 — no regression

Paired against a from-scratch pristine baseline in the SAME worktree
(`git stash` around this rung's diff, same interpreter, same `.so`), the
regression suite named in the PREREG:

```
tests/test_axis_mint_novelty.py tests/test_gap_awareness_migrated.py
tests/test_self_concern_promote_migrated.py tests/test_dimension_inference_migrated.py
tests/test_composer_driver_migrated.py tests/test_recursion_migrated.py
tests/test_persistence_migrated.py tests/test_groups_migrated.py
tests/test_procedure_migrated.py tests/test_structure_world_migrated.py
tests/test_rings_migrated.py tests/test_number_world_migrated.py
```

| run | result |
|---|---|
| pristine baseline (`git stash`) | `7 failed, 61 passed` (393.78s) |
| this rung's fix | `7 failed, 61 passed` (393.32s) |

**Failing node-id lists, both runs, byte-identical (`diff` empty):**

```
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
FAILED tests/test_composer_driver_migrated.py::test_question_driver_parity
FAILED tests/test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content
FAILED tests/test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once
FAILED tests/test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap
FAILED tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
FAILED tests/test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap
```

**All 7 are pre-existing and environment-conditional, not this rung's diff**
— confirmed two ways: (1) identical on the untouched pristine baseline in
this same worktree; (2) `test_question_driver_parity`'s failure is a direct
`FileNotFoundError: .../ocelot-shape-audit-pattern-c/data/hle_math.json` —
this worktree has no `data/` directory at all (`ls data` →
"No such file or directory"), and `test_resolved_topic_files_no_gap`'s
failure trace shows the same shape (a local-grounding lookup that needs
`data/` returning nothing, so no `answer_topic` goal is ever created to
assert against). This is exactly the `data/`-absent population CLAUDE.md's
own retracted optional-dep note documents (147 red files / 565 red node ids
under that condition) — not a new failure class this rung introduced.

Also checked (not part of the formal pair, sanity-only): grepped every test
file for a hardcoded `"induced_..."` literal that might assume the OLD
truncated/order-dependent key form. One hit
(`tests/test_composer_driver_migrated.py:304`,
`_mint_axis_and_ground("induced_multi_head", ...)`) — it passes an explicit
`name_hint`, which bypasses the computed-key path entirely and is therefore
unaffected by AR1's fix.

---

## 5. Everything that broke, and what didn't

- **Broke nothing** — 7/7 identical failing node-ids against a from-scratch
  pristine baseline in the same worktree, both pre-existing and traced to
  the same `data/`-absent environment condition.
- **AR1's fix changed the string VALUE of every auto-derived
  `capability_key`** (no more truncation, predicates now sorted) — this is
  the intended effect, not a side effect, and no test or seed rule depends
  on the specific old string form (checked directly, §1's investigation).
- **AR2/AR3's fixes change `save()`'s blob shape** (AR2 adds a new
  `"recursive_concepts"` key). Confirmed backward-compatible both
  directions: an OLD checkpoint (missing the key) loads cleanly via
  `.get(..., [])`, and `learn_recursive_concept`'s `_concept_by_name`
  fallback heals it on next re-teach (§2's "additional check").

---

## 6. Remaining uncertainties

- **AR1's fix is a mechanism proof, not a measured production-frequency
  claim.** Per CLAUDE.md's standing rule ("synthetic-proven mechanism ≠
  benchmark value, report both"): the live demonstration proves the
  collision is real and the fix resolves it; how often a genuine 4+
  predicate observation's first three heads collide with another's on the
  live daemon was not measured (the audit itself flagged this as
  unmeasured prevalence, and this rung does not change that).
- **`_concept_by_name`'s own first-match-wins semantics are unchanged.**
  All three fixes make re-teaching converge to ONE node instead of
  minting duplicates, but if a duplicate was ALREADY minted by prior
  (pre-fix) runs, `_concept_by_name` still returns the first one by node
  order — this rung does not retroactively clean up pre-existing
  duplicates (out of scope; the brief's charter is the mint-path fix, not
  a graph migration/cleanup pass, and no such cleanup was requested).
- **AR3's fallback to `_concept_by_name` means `learn_word` can now find
  and overwrite a `Concept` node minted by an unrelated path** (e.g. one
  `_ensure_concept` created for a different purpose under the same name) —
  this is the SAME shared-namespace characteristic `_ensure_concept`/
  `learn_recursive_concept` already have (all three write into one global
  `Concept{name}` space), not a new risk this rung introduces; flagged for
  completeness, not as a regression.
- **The `data/`-absent 7-failure population was not independently reduced
  or investigated further** — it was out of this rung's charter (the brief
  scopes exactly three findings), and CLAUDE.md's own standing rule is that
  such a population must be enumerated as a list, not summarised as a
  count; the list above is that enumeration for THIS test subset, not a
  claim about the whole corpus.

---

## 7. Reproduce

```bash
cd /home/matt/ocelot-shape-audit-pattern-c
git log --oneline -1                 # shape-audit-pattern-c-fixes, on top of 4f24abb
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs
s = srs.Substrate()
a = s.node(s.add_node('T', {'lst':[1,2,3], 'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst'] != a['tup'])"   # coherence probe

# AR1 live demo
PYTHONPATH=runners/dsl/python:. python3 - <<'PY'
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
s, ag = boot_core()
native = rf._native_eval2(s)
rf._ensure_shape_decode_loop(s, native, ag)
obs_a = [["zqA","1"],["zqB","2"],["zqC","3"],["zqX","4"]]
obs_b = [["zqA","1"],["zqB","2"],["zqC","3"],["zqY","5"]]
r1 = rf.induce_concern(s, obs_a); r2 = rf.induce_concern(s, obs_b)
print(r1["minted"], r1["capability_key"], "|", r2["minted"], r2["capability_key"])
PY

# AR2 live demo
PYTHONPATH=runners/dsl/python:. python3 - <<'PY'
import tempfile, os
from substrate.world_adapter import WorldAdapter
wa = WorldAdapter()
defn = {"type": "Lit", "value": True}
cid1 = wa.learn_recursive_concept("factorial", defn)
path = os.path.join(tempfile.mkdtemp(), "ckpt.json")
wa.save(path)
wa2 = WorldAdapter.load(path)
cid2 = wa2.learn_recursive_concept("factorial", defn)
nodes = [n for n in wa2.s.nodes("Concept") if wa2.s.node(n)["attrs"].get("name") == "factorial"]
print(cid1, cid2, len(nodes), wa2._concept_by_name("factorial") == wa2.recursive_concept("factorial"))
PY

# AR3 live demo
PYTHONPATH=runners/dsl/python:. python3 - <<'PY'
from substrate.world_adapter import WorldAdapter
wa = WorldAdapter()
defn = {"type": "Lit", "value": True}
cid1 = wa.learn_word("prime", defn); cid2 = wa.learn_word("prime", defn)
nodes = [n for n in wa.s.nodes("Concept") if wa.s.node(n)["attrs"].get("name") == "prime"]
print(cid1, cid2, len(nodes))
PY

# AR4 regression (paired against `git stash` on the same worktree)
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q \
  tests/test_axis_mint_novelty.py tests/test_gap_awareness_migrated.py \
  tests/test_self_concern_promote_migrated.py tests/test_dimension_inference_migrated.py \
  tests/test_composer_driver_migrated.py tests/test_recursion_migrated.py \
  tests/test_persistence_migrated.py tests/test_groups_migrated.py \
  tests/test_procedure_migrated.py tests/test_structure_world_migrated.py \
  tests/test_rings_migrated.py tests/test_number_world_migrated.py
```
