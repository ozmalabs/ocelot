# Shape audit — Pattern C fixes — PREREG

**Registered before any code is edited.** Worktree
`/home/matt/ocelot-shape-audit-pattern-c`, branch `shape-audit-pattern-c-fixes`,
detached from `main` at `4f24abb` (verified via `git log --oneline -1 main`
immediately before worktree creation).

This rung fixes exactly three findings from `SHAPE_AUDIT.md`'s Pattern C
cluster (§3.1 and §4.2/§4.3 — "no dedup on mint", the family the audit's own
ranked list names as the pattern with *measured* production consequence, one
instance of which — the Γ checkpoint-reload growth bug — was already fixed in
`GAMMA_LOAD_GROWTH_FIX_RESULTS.md`). Nothing else in the audit's other 37
findings is touched.

---

## 0. Scope discipline

Three independent fixes, three independent investigations. The brief is
explicit that these must not be assumed to share one root cause, and reading
the code confirms they genuinely don't:

- **AR1** is a Python identity-string computation feeding a graph-resident
  mint guard (`seeds/shape_decode_loop.json`'s `sd_mint_quantum`/
  `sd_dedup_existing`). No persistence involved.
- **AR2** (`learn_recursive_concept`) is a Python session index
  (`self._recursive_concepts`) that is **never written to or read from**
  `WorldAdapter.save()`/`load()` at all.
- **AR3** (`learn_word`) is a Python session index (`self._concepts`) that
  **is** persisted and restored (`world_adapter.py:6137`, `:6199`) but the
  function that mints new `Concept` nodes never consults it before minting.

Files in scope: `domains/reflective_faculty.py` (only the `induce_concern`
region, ~1268-1390 — NOT `keywords_text`/`_pick_acting_rule`/`RuleSummary`
sites at 2691-4187, which a concurrent thread owns), `substrate/
world_adapter.py` (only `learn_word` ~9987-9996, `learn_recursive_concept`
~10113-10132, `recursive_concept` ~10134-10136, `save`/`load`'s index
read/write lines — explicitly NOT the Γ/Rule mirror replay block at
~6169-6194, which a concurrent thread owns). No Rust changes are anticipated
(confirmed: the existing `.so` already imports and passes the coherence
probe in this worktree; these are Python-level identity/dedup computations,
not new DSL primitives or graph operations).

---

## 1. AR1 — `CapabilityAxis` identity (`reflective_faculty.py:1286-1287`)

### 1.1 Root cause, read (not assumed)

`induce_concern` builds the mint/dedup identity key as:

```python
preds = [st[0] for st in obs if isinstance(st, list) and st and isinstance(st[0], str)]
key = name_hint or (("induced_" + "_".join(preds[:3])) if preds else "induced_concern")
```

`preds` is the ordered list of relation-head strings from the observation's
own `signature` (a relation-system: a list of `[predicate, *args]` lists, in
whatever order the caller supplied them — `induce_concern`'s docstring and
every call site confirm this is NOT already canonicalised before this point).
`key` becomes `obs.key` (`sub.add_node("Observation", {..., "key": [key], ...})`)
and is read downstream, unmodified, as `CapabilityAxis.capability_keys` by
BOTH `sd_mint_quantum`'s guard (mint only if
`Not(Exists(CapabilityAxis, induced==1 AND capability_keys==obs.key))`) and
its mirror `sd_dedup_existing` (fires when that Exists DOES hold, and its
only effect is `set_attr(obs, "status", "recognized_duplicate")` — verified
by reading both rules' full JSON in `seeds/shape_decode_loop.json`).

**Confirmed: every other comparison in this pipeline is over a canonically
sorted/order-independent form**, checked directly:

- `build_candidate` (`runners/dsl/src/shape_decode.rs:1589-1591`) sorts both
  sides with `cmp_value` before comparing.
- `ShapeDecode` is a set cover over the codebook; `AntiUnify`/`FixedCount`
  score over relation *sets*, not ordered sequences.
- The 5 other `reflective_faculty.py` call sites that read
  `capability_keys` (`:2807, :3027, :3960, :4145, :5877, :6421`) all compare
  it as `== [str(k) for k in keys]` against an ALREADY-CANONICAL `keys` list
  built the same way this one is (i.e. the inconsistency is that THIS one
  site is the only one that both (a) does not sort and (b) truncates).

**Confirmed: truncation was never load-bearing.** Grepped every
`capability_keys`/`obs.key`/`obs["key"]` read site in
`seeds/shape_decode_loop.json` and `reflective_faculty.py`: the key is used
ONLY for equality comparison (mint-guard, dedup-guard, 5 read sites above) —
never rendered with a length assumption, never sliced, never displayed with
a truncation-dependent format string. No test asserts a specific key length
or a specific 3-predicate form. Truncation is pure liability with no
offsetting benefit found.

**Confirmed, both failure directions, by reading the rule pair:**

1. *Missed match / duplicate axis:* `induced_concern(agent, [["contains",…],
   ["above",…]])` and the same relation system emitted `[["above",…],
   ["contains",…]]` key as `induced_contains_above` vs `induced_above_contains`
   — two nodes for what the decode treats as the same object.
2. *False match / suppressed mint (the dangerous direction):* two
   observations agreeing on their first three predicate heads and differing
   in relation 4+ collapse to the identical truncated key; the second one
   matches `sd_dedup_existing`'s guard and is marked
   `status="recognized_duplicate"` — the CapabilityAxis is never minted for a
   genuinely novel residual.

### 1.2 Fix shape

Match the established convention exactly (canonical form = sorted; keep the
full information, since truncation carried no benefit and only cost
collision-safety): `key = name_hint or ("induced_" + "_".join(sorted(preds))
if preds else "induced_concern")`. Not deduplicated (a repeated predicate
head is real multiset information the untruncated join should not discard;
sorting alone already fixes order-dependence — this mirrors `build_candidate`,
which canonically sorts, not dedups).

This is a pure identity-computation change — a "compute a canonical key"
mechanical pattern, explicitly sanctioned by CLAUDE.md's world-adapter rule.
No rule-JSON change needed (the rules already treat `capability_keys`
opaquely as an equality-tested list).

### 1.3 AR1 bar

- Root-cause investigation as above, verified by reading `induce_concern`,
  both seed rules in full, and the 5 other `capability_keys` comparison
  sites (not assumed from the audit's prose).
- The fix: sorted, untruncated key construction.
- **Live before/after evidence**, run in this worktree, git-stashed around
  the one-line change so the *same* code executes both runs: two
  `induce_concern` calls (no `name_hint`, so the buggy/fixed path is
  actually exercised) whose predicate lists share their first three heads
  but diverge afterward — BEFORE: the second collides with the first
  (`recognized_duplicate`, `minted=False`, axis count does not grow);
  AFTER: both mint distinct axes.

---

## 2. AR2 — `learn_recursive_concept` (`world_adapter.py:10113-10132`)

### 2.1 Root cause, read

```python
def learn_recursive_concept(self, name, definition_term_json):
    index = getattr(self, "_recursive_concepts", None)
    if index is None:
        index = {}
        self._recursive_concepts = index
    cid = index.get(name)
    if cid is not None:
        for tgt in list(self.inner.neighbours(cid, "definition")):
            self.inner.remove_edge_unchecked(cid, "definition", tgt)
            self.inner.remove_node(tgt)
    else:
        cid = self.s.add_node("Concept", {"name": name})
        index[name] = cid
    ...
```

Grepped `_recursive_concepts` across `world_adapter.py`: occurs at exactly
**3 lines — 10117, 10120, 10135 (`recursive_concept`'s reader) — and
nowhere else.** Not present in `save()`'s blob (`:6130-6141`, which writes
only `instances/concepts/body_types/mirrored_edge_types/sensed_types`) and
not restored in `load()` (`:6166-6233`, which also bypasses `__init__` via
`cls.__new__(cls)`, so the attribute is genuinely ABSENT after a load, not
merely empty). **Confirmed distinct from AR3**: this index was never wired
into persistence at all — there is no "restore" bug to fix, only an
"omitted from `save`/`load` entirely" bug.

Concrete failure: teach → save → load → re-teach the same name. `getattr`
returns `None` (fresh, empty dict), so the `else` (unconditional mint)
branch always fires post-load, minting a second `Concept{name}` node with
its own `definition` subgraph. `_concept_by_name` (`:1615-1621`) then
returns the FIRST node-order match — the STALE pre-reload node — to every
reader that resolves the concept by name, while `eval_recursive`
(`:10138-10152`, reading through `recursive_concept`/`self._recursive_concepts`)
resolves the NEW one. Silent divergence between two ways of finding "the"
concept.

### 2.2 Fix shape

Two changes, matched to the precedent already in the same file
(`_ensure_concept`, `:4308-4315`, is exactly `_concept_by_name(name) or
add_node`):

1. **Persist and restore the index**, mirroring exactly how `_concepts` is
   already handled (`save()` gains a `"recursive_concepts"` key parallel to
   `"concepts"`; `load()` restores `wa._recursive_concepts` parallel to
   `wa._concepts`, at the same restore site, NOT inside the
   out-of-scope 6169-6194 Γ-mirror-replay block).
2. **Fall back to `_concept_by_name(name)` when the session index misses**,
   so the fix is correct even for a checkpoint saved BEFORE this change
   (missing the new persisted key entirely) — the graph itself, not a
   Python cache, is the source of truth (CLAUDE.md: *"State lives in the
   substrate. Python may cache for performance, but the substrate is the
   source of truth."*). When the fallback finds an existing node, the index
   is backfilled so `recursive_concept()`/`eval_recursive()` keep working
   without a second lookup path.

This is a mechanical find-or-create + subgraph-replace — the exact shape
`_ensure_concept` already establishes as sanctioned, not a new decision.

### 2.3 AR2 bar

- Root-cause investigation as above (distinct from AR3 — no read omitted,
  the index was never wired to persistence in the first place).
- The fix: persist/restore `_recursive_concepts` + `_concept_by_name`
  fallback.
- **Live before/after evidence**: teach a recursive concept, `save()`,
  `load()` into a fresh `WorldAdapter`, teach the SAME name again. BEFORE:
  two `Concept{name:...}` nodes exist, `_concept_by_name` resolves the
  stale (pre-reload) one, `eval_recursive` resolves the other — measurable
  divergence. AFTER: exactly one `Concept` node, both resolution paths
  agree.

---

## 3. AR3 — `learn_word` (`world_adapter.py:9987-9996`)

### 3.1 Root cause, read

```python
def learn_word(self, name, definition_term_json):
    root = self.inner.add_term_subgraph(definition_term_json)
    cid = self.s.add_node("Concept", {"name": name})
    self.inner.add_edge_unchecked(cid, "definition", root)
    self._concepts[name] = cid
    return cid
```

`self._concepts` is initialised in `__init__` (`:70`), IS persisted
(`save()` `:6137`) and IS restored (`load()` `:6199`, confirmed present at
both sites by reading them directly) — **confirmed distinct from AR2**: the
index survives a save/load round-trip intact. The defect is narrower and
purely local: `learn_word` never reads `self._concepts.get(name)` before
unconditionally minting. Every re-teach (whether same-session or
post-reload) mints a second `Concept` + a second full `definition` Term
subgraph, and `self._concepts[name]` is overwritten to point at the NEW
node while the OLD node stays in the graph and wins `_concept_by_name`'s
first-match scan — same stale-node hazard as AR2, different mechanism
(unread index vs. unpersisted index).

### 3.2 Fix shape

Mirror the replace-on-reteach pattern `learn_recursive_concept` already
establishes in the same file (structurally consistent with the file's own
precedent, not an invented shape): look up `self._concepts.get(name) or
self._concept_by_name(name)` first; if found, remove the old `definition`
edge + subgraph before attaching the new one; only mint a fresh `Concept`
node when neither lookup finds one.

### 3.3 AR3 bar

- Root-cause investigation as above (distinct from AR2 — index persistence
  is intact; the read is what's missing).
- The fix: find-or-replace before mint, mirroring `learn_recursive_concept`.
- **Live before/after evidence**: `learn_word` the same name twice in one
  session (no reload needed — this defect doesn't require one, unlike AR2).
  BEFORE: two `Concept` nodes, two `definition` subgraphs, `_concepts[name]`
  points at the second while `_concept_by_name` returns the first (stale).
  AFTER: exactly one `Concept` node, both resolution paths agree, and a
  save/load round-trip (matching AR2's harder trigger) also confirmed
  clean.

---

## 4. AR4 — no regression

Regression suites gated (paired failing-node-id lists, not counts):

- `tests/test_axis_mint_novelty.py` — the existing CapabilityAxis
  novelty-guard regression test (uses `name_hint`, so it does not exercise
  AR1's bug directly, but is the closest existing gate on
  `sd_mint_quantum`/`sd_dedup_existing` and must stay green).
- `tests/test_gap_awareness_migrated.py`,
  `tests/test_self_concern_promote_migrated.py` — the self-improvement
  pipeline `induce_concern`/`CapabilityAxis` feeds.
- `tests/test_dimension_inference_migrated.py`,
  `tests/test_composer_driver_migrated.py` — other consumers of the
  `shape_decode_loop` seed and `capability_keys` reads (§1.1's 5 sites).
- `tests/test_recursion_migrated.py` — every `learn_recursive_concept`/
  `recursive_concept`/`eval_recursive` call site.
- `tests/test_persistence_migrated.py`, `tests/test_groups_migrated.py`,
  `tests/test_procedure_migrated.py`, `tests/test_structure_world_migrated.py`,
  `tests/test_rings_migrated.py`, `tests/test_number_world_migrated.py` —
  every `learn_word` call site found by grep across `tests/`.

Bar: paired before/after failing-node-id lists for this file set; zero net
new reds attributable to this rung's diff. Pre-existing reds (if any, e.g.
optional-dep gaps per CLAUDE.md's retracted-note discipline) are recorded as
a list, not summarised as a count.

---

## 5. Process notes

- No Rust rebuild anticipated or performed unless investigation proves one
  of the three fixes genuinely needs a new DSL primitive (not expected —
  confirmed by reading; these are Python-level identity/dedup computations
  over existing, already-adequate Terms/rules).
- Each fix's live demonstration is captured by git-stashing that one fix's
  diff, running the "before" script, popping the stash, running the "after"
  script — same interpreter, same worktree, same engine build, only the
  Python source differs, exactly as the demonstration discipline in
  `GAMMA_LOAD_GROWTH_FIX_RESULTS.md` §3's B2 uses (before/after under
  controlled, reproducible conditions).
- Constraints from the brief: do not touch `runners/dsl/src/py.rs`,
  `world_adapter.py`'s checkpoint-load region ~6180-6190, `domains/
  rule_signature.py`, `reflective_faculty.py`'s `keywords_text`/
  `_pick_acting_rule`/`RuleSummary` sites (~2691-4187), `seeds/
  variation_ops.json`, `seeds/composer_experiment_graph.json`. None of the
  three fixes above require touching any of these.
