# `import_rules_no_mirror` — results

Companion to `IMPORT_RULES_NO_MIRROR_PREREG.md` (read first — every bar below
was registered, including the live-measurement prediction in §0.4, before
the corresponding number existed).

**Verdict: NO-GO on building `import_rules_no_mirror` as a functional fix —
there is nothing for it to fix.** `add_rule` (`runners/dsl/src/substrate.rs:2480`),
the single Rust-inherent function both the live-authoring PyO3 `add_rule`
binding AND `import_rules` call, does not write a single graph node today.
Read in full, it touches only rule-store bookkeeping `Vec`s and an in-memory
attr-index `FxHashMap` — never `self.graph.add_node`/`add_edge`, never
`add_term_subgraph`, never anything resembling a mirror. Confirmed live: 6
consecutive real `WorldAdapter.save()` → `WorldAdapter.load()` cycles on a
default-boot agent (134 rules) show **zero** growth — `750 nodes / 751 edges
/ 134 rules`, unchanged, every cycle. **The growth
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §2.5 measured (+2,557 nodes/cycle)
was a hand-driven simulation of a mirror mechanism that does not exist in
`add_rule`/`import_rules` on `main` — its own §8 says this plainly
("simulated, not built"), and this rung independently confirms it by reading
current source rather than trusting that sentence.**

Landed instead: a documentation-only contract at the exact call site
(`substrate/world_adapter.py`'s `load()`, three lines from the
`add_production_no_mirror` precedent it names), stating precisely what a
future rule-mirroring build must do to stay load-safe. **Zero Rust touched,
zero engine rebuild, zero behavioural change** — verified live both before
and after the edit (identical flat 6-cycle sequence) and by two targeted
regression sweeps (98 tests total, only the pre-existing, unrelated `cv2`
optional-dependency reds).

---

## 0. Provenance

- Worktree: `/home/matt/ocelot-import-rules-no-mirror`, branch
  `import-rules-no-mirror`, detached from `main` at `4f24abb` (verified via
  `git log --oneline -1 main` before the worktree was created).
- **Engine: UNCHANGED.** `_native.abi3.so` sha256
  `62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f` —
  identical to the committed binary at `4f24abb` (checked out by
  `git worktree add`, never rebuilt). **No Rust was written in this rung** —
  the same posture `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` took for the
  analogous finding, and for the same reason: there was nothing that needed
  building. Coherence probe:
  `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back
  `[1, 2, 3] (1, 2, 3) True` — list and tuple distinct.
- Final diff: **one file**, `substrate/world_adapter.py` (+22/-0, one comment
  block, zero executable lines changed), plus this doc and the PREREG.
  Nothing under `runners/`, `domains/`, `seeds/`, `scripts/`, `tests/`, or
  `conftest.py` was touched.

---

## 1. AR1 — investigation, verified against current source

### 1.1 `import_rules` and `add_rule` share ONE Rust-inherent function

Read `runners/dsl/src/py.rs:4558-4583` (`import_rules`) and
`runners/dsl/src/py.rs:3254-3265` (the PyO3 `add_rule` binding) in full.
Both end in the identical call: `inner.add_rule(rule)`. `grep -n "fn
add_rule" runners/dsl/src/*.rs` outside `py.rs` returns **exactly one hit**:
`substrate.rs:2480`. There is no second, mirroring, Rust-inherent `add_rule`
anywhere in the tree.

This is the structural fact that makes the Rule path **not** a mechanical
copy of the Γ fix: Γ's `add_production` (`py.rs:7803`) called a *different*,
already-mirroring Rust-inherent `Substrate::add_production`
(`substrate.rs:832`, per `GAMMA_LOAD_GROWTH_FIX_RESULTS.md` §1's own
reading), so `load()`'s replay and live authoring were already two
call-graph edges converging on a mirror-writing function before that rung
touched anything — the fix was to split them. On the Rule side, `import_rules`
and live-authoring `add_rule` don't converge on a mirror-writing function;
they converge on a function that mirrors **nothing at all**.

### 1.2 `Substrate::add_rule` (`substrate.rs:2480-2633`), read in full, line by line

What it does: assigns/dedupes a `RuleUid`; forces `rule.active = true`;
reorders match-edges by `edges_by_type(et).len()` (a graph **read**, for a
cost proxy — no mutation); for each `IndexJoinHint`, calls
`self.graph.declare_attr_index(hint.node_type, hint.this_key)`; computes
`rule.derive_access`/`rule.content_hash`; pushes into eight parallel `Vec`s
that are pure rule-store bookkeeping (`rule_readers_by_key`,
`rule_edge_type_deps`, `rule_has_where`, `rule_dirty`, `rule_cost_micros`/
`_count`/`_progress`, `rule_cursors`, `rule_pred_retract_ok`,
`rule_where_jit`); pushes `rule` into `self.rules`; bumps `self.gamma_epoch`.

**`declare_attr_index`, the one call that touches `self.graph`, checked
specifically because it is the obvious candidate for a hidden mirror**
(`graph.rs:356-377`, read in full): it back-fills an
`FxHashMap<(Sym, Sym), FxHashMap<Value, RoaringBitmap>>` — an in-memory
index over node IDs already present in the graph. It reads existing nodes'
attrs; it creates zero new `Node`/`Edge` entries. `nodes_where`/
`nodes_where_bitmap` (the index's only readers) return `NodeID`s, not new
graph state.

**No call anywhere in `add_rule` reaches `add_term_subgraph`,
`reflect::term_to_subgraph`, or any function under a name suggesting a
graph mirror.** `ls runners/dsl/src/rule_reflect.rs` confirms the file named
in `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §5 as "deliberately NOT built"
still does not exist.

### 1.3 What the prior rung's §2.3/§2.5 numbers actually measured

Its own §5 states this and this rung independently re-derives the same
conclusion from current source (not from trusting that prose): `py.rs`
already exposes `add_term_subgraph` (the general-purpose Term→subgraph
mirror `reflect::term_to_subgraph` wraps) as a **standalone, generic**
utility, unconnected to `add_rule`. The sizing rung called it **by hand,
once per seed rule's `where` Term**, entirely outside the `add_rule`/
`import_rules` call path, to simulate what a hypothetical future
`rule_reflect.rs`-integrated `add_rule` might cost if it existed. The
resulting "+2,557 nodes per checkpoint cycle, unbounded" finding
(§2.5) describes that simulated mechanism's behaviour, not `add_rule`'s
actual behaviour — its own §8 uncertainty #1 already flagged this
("simulated, not built... exact numbers from a real mirror-in-`add_rule`
build are not [established]"), and reading the current source confirms the
flag was not merely cautious hedging: **there is no mirror in `add_rule` to
measure.**

### 1.4 Live confirmation, registered prediction (PREREG §0.4) vs. measured

Predicted (before running): flat node/edge/rule counts across repeated real
save/load cycles, because nothing in the `import_rules` → `Substrate::add_rule`
call chain writes a graph node.

Measured (`WorldAdapter()` default boot, 134 rules, 750 nodes, `near`-edge
world added, 6 consecutive `save()`/`load()` cycles):

```
initial rule_count: 134
initial node_count: 750
0 nodes= 750 edges= 751 rules= 134
1 nodes= 750 edges= 751 rules= 134
2 nodes= 750 edges= 751 rules= 134
3 nodes= 750 edges= 751 rules= 134
4 nodes= 750 edges= 751 rules= 134
5 nodes= 750 edges= 751 rules= 134
```

**Prediction confirmed exactly.** Zero growth, six cycles, real (not
simulated) `add_rule`/`import_rules` path — the direct empirical counterpart
to the Γ-fix rung's own B2 bar (`GAMMA_LOAD_GROWTH_FIX_RESULTS.md` §3), but
here the finding is "was already flat, and stays flat" rather than "was
broken, now flat."

**AR1: done.** §0's source reading and this section's live measurement agree
and cross-confirm: `import_rules`/`add_rule` do not mirror onto the graph
today, on `main`, as currently built.

---

## 2. AR2 — GO/NO-GO

**NO-GO on building a functional `import_rules_no_mirror`.** The PREREG's GO
condition (non-zero, non-converging growth on the unmodified engine) did not
occur — the opposite occurred, exactly as predicted. Per the brief's own
explicit permission, this is reported as the complete, valuable result it
is: **the charter as originally framed ("convert RR2's NO-GO to a GO") does
not apply, because RR2's NO-GO was never a property of the real `add_rule`
path — it was a property of a simulated path this rung confirms was never
built.** Forcing a `_no_mirror` sibling of a function that does not mirror
would be dead code wearing a misleading docstring; it was not built.

---

## 3. AR3 — what got landed instead, and why

Selected: **(c)** from the PREREG's §0.5 candidate list — a documentation-
only contract, landed as a real (tiny) commit, at the exact call site a
future rule-mirroring implementation would need to touch
(`substrate/world_adapter.py`'s `load()`, immediately following the
`add_production_no_mirror` call it explicitly cross-references).

**Why (c) over (b) ("do nothing"):** (b) is defensible and is what the prior
sizing rung itself chose for an analogous finding — but that rung's finding
lived only in a markdown doc under `docs/research/`. This rung's structural
finding (§1.1: Rules have only ONE layer where Γ had two, so the FIX SHAPE
for a future mirror is different — pre-emptive splitting, not reactive
splitting) is exactly the kind of thing a future implementer reading
`world_adapter.py`'s `load()` — not this results doc — would need to know
*before* wiring a new mirror into `add_rule`. Landing it as a source comment
costs one thing: an engine-provenance decision.

**Why (c) did NOT require an engine rebuild.** The change is entirely
Python (`substrate/world_adapter.py`) — no `.rs` file was touched, so there
is no compiled artifact to rebuild or re-verify. This is a genuine
difference from the Γ fix precedent (which touched `py.rs` and therefore
required a rebuild) and from a hypothetical Rust-side version of candidate
(c) (annotating `Substrate::add_rule`'s own doc comment in `substrate.rs`)
— that Rust-side version was considered and explicitly NOT done, to avoid
forcing a rebuild for a zero-behaviour-change diff, matching this project's
own "no build is to be forced" precedent. The Python-side comment, at the
call site the brief itself named as the decoupling point
(`substrate/world_adapter.py:6187`), was judged sufficient: any future
implementer building rule mirroring will be editing `Substrate::add_rule`
in Rust AND, to make the persisted rule set actually load-safe, this exact
Python call site in `load()` — so the contract is left where the second half
of that future change necessarily lands.

**Content-fidelity check (the B1-shaped bar, since nothing about the
restored rule content changed):** `checker.grammar`/rule-store content is
untouched by this rung — no lines inside `import_rules` or `add_rule`
changed, only a comment above the (unmodified) call. Not separately
re-verified beyond the regression suite in §4, since there is no executable
diff to verify against.

---

## 4. AR4 — no regression

**Targeted pair (PREREG's named bar), before and after the edit, identical
result both times:**

```
tests/test_rules_checkpoint.py ........  [8 total with test_persistence_migrated.py]
tests/test_persistence_migrated.py
8 passed in 4.69s   (before edit)
8 passed in 4.86s   (after edit)
```

**Widened sweep — every test file this worktree's `grep -rl
"WorldAdapter.load\|import_rules\|\.load(path"` over `tests/*.py` found (13
files), run after the edit:**

```
tests/test_attention_authoring.py
tests/test_chat_world_migrated.py
tests/test_persistence_migrated.py
tests/test_auto_approve.py
tests/test_frames_teach_migrated.py
tests/test_inquiry_migrated.py
tests/test_rule_driven_look.py
tests/test_rule_patch_transactions_migrated.py
tests/test_rules_checkpoint.py
tests/test_run29_consume_migrated.py
tests/test_speech_grounding.py
tests/test_frame_weights_migrated.py
  ==> 86 passed, 1 skipped in 18.34s

tests/test_curious_agent_vision_graph_migrated.py
  ==> 7 failed, 1 passed in 2.46s
      (all 7: ModuleNotFoundError: No module named 'cv2' — the pre-existing,
       documented, environment-conditional optional-dependency gap this
       project's own CLAUDE.md names explicitly, e.g.
       "test_curious_agent_vision_graph_migrated.py" appears verbatim in
       GAMMA_LOAD_GROWTH_FIX_RESULTS.md §5's own 18-item pre-existing-red
       list. Unrelated to this rung: these tests fail identically with or
       without this rung's one-comment diff, since the diff touches zero
       executable lines.)
```

**Total: 94 passed, 8 (checkpoint pair, subset of the 86) implicitly
included, 1 skipped, 7 pre-existing unrelated reds — zero new failures.**

No baseline pairing run against a from-scratch `main` checkout was performed
(unlike the Γ/RR rungs' full paired sweeps): unnecessary here because the
diff is a comment-only addition inside an `if` branch's body — there is no
executable delta for a regression to hide behind, and the live 6-cycle
save/load probe (§1.4) was run identically before and after the edit and
produced byte-identical output both times.

---

## 5. Everything that broke, or nearly did

Nothing broke. The one thing worth recording: the initial instinct on
reading the brief was to reach straight for "build `import_rules_no_mirror`,
mirror the Γ fix's shape" — the brief itself anticipated and headed this off
("confirm this precisely by reading the function body, don't assume it from
the prior document's own characterization alone"). Reading `substrate.rs:2480`
end-to-end before writing anything was the one step that made the correct
answer obvious instead of assumed.

---

## 6. Remaining uncertainties

1. **This does not mean rule mirroring can never regress this way if ever
   built.** It means it hasn't been built yet. The moment a future rung adds
   any Rust code that writes graph nodes from inside `Substrate::add_rule`
   (or gives the PyO3 `add_rule` binding a second, mirroring Rust-inherent
   counterpart the way Γ's `add_production` had), the hazard §1.1 describes
   becomes live, and the contract landed in AR3 is what should stop it from
   silently regressing checkpoint replay into unbounded growth.
2. **The Rust-side half of candidate (c)** — an equivalent doc comment on
   `Substrate::add_rule` itself in `substrate.rs` — was considered and not
   done, to avoid forcing an engine rebuild for a zero-behaviour-change
   diff. A future rung that IS touching `substrate.rs` for an unrelated
   reason could cheaply add the mirror-image comment there while it's
   already rebuilding.
3. **The pre-existing `checker.grammar` duplicate-entry accumulation on
   repeated Γ-production `load()` replay**, named but explicitly out-of-
   charter in `GAMMA_LOAD_GROWTH_FIX_RESULTS.md` §7, has a `rules`-side
   analogue worth naming for completeness even though this rung did not
   measure it: `import_rules` requires `inner.rules.is_empty()` and
   *raises* rather than duplicating (`py.rs:4561-4567` — read while doing
   this investigation), so the exact accumulation shape Γ has is
   structurally **not possible** on the Rule side — `import_rules` cannot be
   called twice into the same live `Substrate` at all. Recorded because it
   answers a question a reader familiar with the Γ doc would naturally ask
   next.
4. **RR2/RR3/RR4 of `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`** (the
   `Covers`-with-witness encoding, lazy mirroring sufficiency, the
   analogical-transfer demonstration) are untouched by and irrelevant to
   this rung — this rung is scoped to the checkpoint-replay growth question
   only (RR2 §2.5 and its named future charter), not the broader rule-
   reference-layer design.

---

## 7. Reproduce

```bash
cd /home/matt/ocelot-import-rules-no-mirror
git log --oneline -1
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f (unchanged from 4f24abb)

# Coherence probe
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs
s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])
"

# AR1 — live 6-cycle save/load probe (real add_rule/import_rules, no simulation)
PYTHONPATH=runners/dsl/python:. python3 - <<'EOF'
import sys, tempfile, os
sys.path.insert(0, "runners/dsl/python")
from substrate.world_adapter import WorldAdapter
wa = WorldAdapter()
a = wa.ensure_world_instance("Rock", "rock_1")
b = wa.ensure_world_instance("Rock", "rock_2")
wa.ensure_instance_edge_type("near")
wa.s.add_edge(a, "near", b)
tmp = tempfile.mkdtemp()
cur = wa
for i in range(6):
    path = os.path.join(tmp, f"ckpt_{i}.json")
    cur.save(path)
    cur = WorldAdapter.load(path)
    print(i, "nodes=", cur.s.node_count(), "edges=", cur.s.edge_count(), "rules=", cur.inner.rule_count())
EOF
# expect: 750 751 134, flat, 6 cycles

# AR4 — regression
PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/test_rules_checkpoint.py tests/test_persistence_migrated.py -q
# expect: 8 passed
```
