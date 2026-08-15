# `Mod`/`Sqrt` call-site-scoped fix — PREREG

**Date:** 2026-08-16. Base `main @ 9c3e73f` ("Merge
progsyn-budget-exhausted-survey: reframing landed, Mod/Sqrt
built-measured-reverted, NO-GO"), verified fresh via
`git log --oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-modsqrt-scoped-fix`, branch
`progsyn-modsqrt-scoped-fix`.

---

**HEADLINE, stated up front: the predecessor document's own diagnosis of
WHICH call site causes the cross-lane regression was WRONG, and this
document corrects it with a live trace before building anything.**
`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_RESULTS.md` §5.2 names
`domains/prog_moves.py::intermediate_candidates`/`_run_synth_enumerate`
(the ARC5 structural-moves/decomposition probe) as the mechanism that
"widens what THAT probe proposes... and its proposal feeds into which
candidate the `retrieved_exemplar` construction lane ultimately accepts."
**A live call-site trace (§2, this document) on all four named regressions
(59, 135, 138, 406) shows this is not what happens.** Every one of the four
traces to exactly ONE call site, and it is not in `prog_moves.py` at all:
`domains/prog_retrieval.py:583-586`, inside `run_retrieval_ladder`'s rung
(d) ("retrieved-as-skeleton" — the masked-final-statement SynthEnumerate
call). `prog_moves.py`'s own `_run_synth_enumerate` call sites never fire
for any of these four tasks (confirmed: zero `SynthEnumerate` calls
attributed to `prog_moves.py` anywhere in the four traces) — `orbit_
candidates` requires arity 2-4 (three of the four tasks are arity 1) and
`intermediate_candidates`'s own `factor_candidates` gate finds no exact-
divisor decomposition for any of the four (none of these four specs is an
integer-multiple-of-a-sub-problem shape). The predecessor's own structural
reasoning — "prog_moves.py's call also omits an explicit `ops` key, so it
also reaches the widened typed default" — is TRUE as a general statement
(§3 confirms it independently), but it was never the operative mechanism
for the specific regression it was cited to explain.

**This changes where the fix goes.** The scoped fix in this document
excludes `Mod`/`Sqrt` from `prog_retrieval.py`'s rung-(d) SynthEnumerate
call ONLY — not from `prog_moves.py`, which the live trace shows had no
causal role in the four known regressions. `prog_moves.py`'s own calls are
left untouched pending the RESULTS document's full-battery task-id diff
(§6 of this document's plan): if that diff surfaces a DIFFERENT regression
population attributable to `prog_moves.py`, this rung's scope will need to
widen — named as an open question here, not assumed closed.

**A new, minimal, additive Rust primitive was required to test the
hypothesis at all — there was no way to "hand-verify before writing any
Rust."** No existing mechanism lets one `SynthEnumerate` caller opt out of
two specific ops from an otherwise-unchanged typed default: the only
existing lever is the caller's own explicit `ops` list, which replaces the
ENTIRE inventory — using it would require `prog_retrieval.py` to
reimplement `synth_enumerate.rs`'s typed-default branch selection in
Python (exactly the "Python re-implementing a Rust routing decision"
CLAUDE.md forbids). The task brief's own §3 anticipated this ("a genuinely
new, narrower typed-default op-list variant... mirroring `SynthEnumerate`'s
own existing `exclude` argument precedent"); this document builds that
variant — a new optional `exclude_ops` field on the `SynthEnumerate` Term,
applied as a post-filter at the single point (`op_list`'s construction in
`eval_synth_enumerate`) where the typed-default and explicit-`ops` paths
already converge — BEFORE writing the actual Python-side scoping edit, so
the mechanism could be hand-verified in isolation (§4) ahead of the real
fix.

---

## 1. What the predecessor established (re-read in full, cited directly)

`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_RESULTS.md` built `Mod`
(`OpKind::Binary`)/`Sqrt` (`OpKind::Unary`) — both pre-existing, fully
evaluated `TermNode` variants absent from `OP_TABLE` — scoped to the
bare-scalar `else` branch of `eval_synth_enumerate`'s typed-default
construction. Measured, full battery, real task-id set diff against the
73/72/101 baseline:

```
full/content_stripped: gained {92, 171, 246, 435}, regressed {59, 135, 138, 406} — churn, net 0
official: gained {246, 435, 441, 479}, regressed {14, 138, 164, 406, 455, 464} — net -2
```

Two regression mechanisms were named:

- **(a) search-cost inflation within the SAME bare-scalar branch** —
  adding two ops to a 12-op inventory increases per-size branching enough
  to push an already-in-budget formula (task 14, `a*b*c/2`) out of the
  200,000-candidate budget. This is intrinsic to widening the TOP-LEVEL
  bare-scalar default itself — no call-site scoping can fix it, because
  the top-level `run_enumerate` path is exactly the path this whole arc
  wants Mod/Sqrt exposed to.
- **(b) cross-lane reach** — a SECOND `SynthEnumerate` caller that also
  omits an explicit `ops` key reaches the SAME widened typed default on a
  DIFFERENT (sub-)spec, changing what IT proposes, which changes which
  candidate a `retrieved_exemplar`-labeled accept ultimately uses. The
  predecessor attributed this to `prog_moves.py`; §2 below shows the
  correct attribution is `prog_retrieval.py`.

The task brief for this rung asks to price and, if clean, build "a
call-site-scoped fix... excluding `Mod`/`Sqrt` from the decomposition
probe's own op list while keeping them for top-level enumerate" — this
document treats "the decomposition/retrieval probe" as an empirical
question to re-answer, not a given, because the predecessor's own
attribution turns out not to hold under a live trace.

## 2. Live trace: which call site actually produces the regressed candidate

**Method.** A thin proxy substituted for `sub._inner` (the PyO3 native
substrate's own wrapper attribute — the same substitution technique
`BUDGET_EXHAUSTED_SURVEY_PREREG.md` §"Reproduce" documents) intercepts
every `evaluate()` call whose term `type == "SynthEnumerate"`, and records
the Python call stack frame (file/line/function) that issued it, before
`domains.prog_synthesis.synthesize_from_request` runs to completion for
each of the four named regressions (59, 135, 138, 406), booted via the
SAME `boot_full` sequence `scripts/mbpp_endgame_battery.py` uses
(`ensure_program_synthesis` + `install_mined_chunks` +
`ensure_mbpp_train_diet`). Full reproduce script in §"Reproduce" below.

**Result — all four tasks, one call site, byte-identical shape:**

```
task 59  (nth octagonal number, n_revealed=2):
  SYNTH_CALL caller=domains/prog_retrieval.py:586 (run_retrieval_ladder)
    has_ops=False has_exclude_ops=False n_rows=2 -> found=True tested=67223
  RESULT status=accepted construction=retrieved_exemplar

task 135 (nth hexagonal number, n_revealed=2):
  SYNTH_CALL caller=domains/prog_retrieval.py:586 (run_retrieval_ladder)
    has_ops=False has_exclude_ops=False n_rows=2 -> found=True tested=67310
  RESULT status=accepted construction=retrieved_exemplar

task 138 (can-be-represented-as-sum check, n_revealed=2):
  SYNTH_CALL caller=domains/prog_retrieval.py:586 (run_retrieval_ladder)
    has_ops=False has_exclude_ops=False n_rows=2 -> found=True tested=851
  RESULT status=accepted construction=retrieved_exemplar

task 406 (parity check, n_revealed=2):
  SYNTH_CALL caller=domains/prog_retrieval.py:586 (run_retrieval_ladder)
    has_ops=False has_exclude_ops=False n_rows=2 -> found=True tested=257
  RESULT status=accepted construction=retrieved_exemplar
```

**Zero `SynthEnumerate` calls are attributed to `prog_moves.py` for any of
these four tasks** — the proxy logs EVERY `SynthEnumerate` call
regardless of caller, so an absence in the trace is a genuine absence, not
a gap in the instrumentation. This is consistent with the module's own
gating: `orbit_candidates` (`domains/prog_moves.py:459-521`) requires
`2 <= n <= 4` (task 59/135/406 are all `n=1`, single-argument specs —
structurally excluded); `intermediate_candidates`
(`domains/prog_moves.py:524-580`) requires `1 <= n <= 3` (all four pass
this gate) but only calls `_run_synth_enumerate` per `arg` when
`factor_candidates` (`domains/prog_moves.py:270-318`) finds an EXACT
integer-divisor decomposition (`expected % v == 0` for every revealed
row) — none of the four specs is an integer-multiple-of-a-sub-problem
shape (an octagonal-number formula, a hexagonal-number formula, a
sum-representable-as check, and a parity check are none of them "some
argument times an inner function"), so `factor_candidates` returns empty
and `intermediate_candidates`'s own loop body — the only place
`_run_synth_enumerate` is called from that function — never executes.

**Every one of `run_retrieval_ladder`'s accepts is labelled uniformly.**
`seeds/program_synthesis.json`'s `pr_ladder_accept` rule
(confirmed by direct read of its `where` clause) sets
`ps_construction := "retrieved_exemplar"` whenever
`status=='retrieve_ladder' AND pr_ladder_done==1.0 AND pr_rung_reached !=
'none'` — i.e. for EVERY successful rung, (a) as-is, (b) bounded arg
permutation, (c) bounded single-leaf edit, OR (d) retrieved-as-skeleton,
with no distinction recorded in the construction label itself. Rungs (a),
(b), and (c) never call `SynthEnumerate` at all — they reuse a stored
exemplar body verbatim, permute its argument order, or substitute one leaf
from a small fixed catalog (`_CANDIDATES_FOR`/`_ARITH_OPS`,
`prog_retrieval.py:102-106`, itself already including `"Mod"` in its own
LOCAL leaf-edit catalog — a separate, pre-existing, unaffected mechanism,
confirmed not implicated in any of the four traces above since none of
them reach rung (c) with a Mod-shaped edit). Only rung (d)
(`prog_retrieval.py:542-613`) runs a real search, at
`domains/prog_retrieval.py:583-586`:

```python
spec = {"type": "SynthEnumerate",
       "examples": {"type": "Lit", "value": derived_rows},
       "max_size": 7, "max_candidates": 0, "saturate_k": 0, "field": ""}
out = sub._inner.evaluate(spec, {})
```

No `"ops"` key — confirmed by reading the literal dict — so this call
reaches the SAME Rust-internal typed-default routing
`domains/prog_synthesis.py::run_enumerate`'s own top-level call reaches
when `ps_enum_ops` is empty. **This is the actual, sole, empirically
confirmed cross-lane call site for the four named regressions.**

## 3. `prog_moves.py`'s own calls also reach the typed default — a separate, unexercised risk

Independent of §2's finding, `domains/prog_moves.py`'s five
`_run_synth_enumerate` call sites (`prog_moves.py:468, 505, 532, 559,
736`) ALL construct their `SynthEnumerate` spec with no `"ops"` key
(confirmed by reading `_run_synth_enumerate`'s own body,
`prog_moves.py:332-349` — the dict literal has no `"ops"` entry), so they
too reach the widened bare-scalar typed default whenever their own
sub-spec is bare-scalar-shaped. **This is a real, structurally identical
exposure to what §2 found for `prog_retrieval.py` — it is simply not what
caused the four regressions this rung is charged with fixing**, because
(per §2) none of the four ever reaches `prog_moves.py`'s code at all. This
document does not assume `prog_moves.py` is risk-free for the WIDER
corpus (Group A's 20-task population from `BUDGET_EXHAUSTED_SURVEY_
RESULTS.md` §4 — "finds a cheap spurious candidate, excluded, retries" —
is exactly the shape a widened `prog_moves.py` probe could produce for
some OTHER task not in the four named regressions); the full-battery
task-id diff in the RESULTS document is what actually answers this, not
this section's reasoning alone.

## 4. The `exclude_ops` mechanism — built and hand-verified before the real fix

**Design.** A new optional field `exclude_ops: Option<TermIdx>` on
`TermNode::SynthEnumerate` (`term.rs`), threaded through `jsonio.rs`
(serialize/parse), `reflect.rs` (structural reflection), and
`eval_synth_enumerate`'s signature (`synth_enumerate.rs`). Evaluated
exactly like `ops`/`consts` (a `Lit` of strings, or absent/`None`), and
applied as a POST-FILTER immediately after `op_list` — the single point
where the typed-default path (`ops_t == None`) and the caller's-own-
explicit-`ops` path already converge — is constructed:

```rust
let op_list: Vec<(String, OpKind)> = match exclude_ops_t {
    Some(t) => {
        let xv = evaluate(arena, t, env, ctx);
        match items_of(&xv) {
            Some(items) => {
                let names: Vec<String> =
                    items.iter().filter_map(|v| value_str(v, ctx.interner)).collect();
                op_list.into_iter().filter(|(n, _)| !names.iter().any(|x| x == n)).collect()
            }
            None => op_list,
        }
    }
    None => op_list,
};
```

**Why this shape and not a second typed-default table**: a caller that
never sets `exclude_ops` (every existing call site, before this rung)
is byte-unchanged — `exclude_ops_t == None` falls straight to the
identity arm. This mirrors `exclude`'s own already-documented discipline
("a soft refutation hint, not part of the spec contract... unrecognized
names silently skipped") for op NAMES instead of candidate TERMS — the
same idiom, not a new one. It also means the SAME mechanism works
regardless of which typed-default branch (bare-scalar, list-shaped,
string-shaped, dict-shaped) a given call's spec happens to route through,
without `prog_retrieval.py` (or any future caller) needing to know or
duplicate that routing logic in Python.

**Mod/Sqrt exposure itself is unchanged from the predecessor's build**:
`OP_TABLE` gains `("Mod", OpKind::Binary)`/`("Sqrt", OpKind::Unary)`;
`build_op` gains the two match arms; the bare-scalar `else` branch of the
typed-default construction pushes `"Mod"`/`"Sqrt"` onto its OWN local `v`
vector (never onto the shared `DEFAULT_OPS` constant the list-shaped
branch also consumes — task 132 remains structurally unreachable by
construction, exactly as the predecessor's own scoping already
established); `term_json` (the module's own LOCAL candidate-JSON
renderer) gains the two missing match arms for `TermNode::Mod`/
`TermNode::Sqrt` — the SAME `unreachable!()`-avoidance fix
`DictFromPairs_RESULTS.md` §2 already made once for `TermNode::MkDict`,
needed again here for the identical reason (a search-built candidate can
now embed either op).

**Hand-verification, isolated from the real Python-side fix** (no
`prog_retrieval.py` edit yet at this point):

```
no exclude_ops                    -> found: True  term: Mod(a, (5+5))
exclude_ops=["Mod", "Sqrt"]       -> found: False term: None
```

confirms the filter suppresses `Mod` from being proposed at all when
requested, and changes nothing when absent (every pre-existing caller's
own behavior, including `prog_retrieval.py`'s rung (d) BEFORE this rung's
Python-side edit, is confirmed unaffected in §2's own trace: `has_
exclude_ops=False` for all four, since the edit had not yet been applied
when that trace was captured).

**Rust build discipline for this infrastructure change, already
completed**: genuine from-source rebuild (`cargo build --release`,
touched `synth_enumerate.rs` first, confirmed non-cached — 2m 21s),
`bash scripts/engine_build.sh` installed, `cargo test --lib --release --
--test-threads=1` (with the documented `RUSTFLAGS`/`LD_LIBRARY_PATH`
pairing) — **778 passed, 0 failed, 4 ignored**, byte-identical to the
778-baseline this arc's task brief cites. `record_build()` +
`pytest tests/test_engine_provenance_migrated.py` both green (9 passed,
1 skipped), confirming the installed engine matches this worktree's
source.

## 5. The actual fix, not yet applied at the time of writing this document

One line at `domains/prog_retrieval.py:583-585`, adding `"exclude_ops":
{"type": "Lit", "value": ["Mod", "Sqrt"]}` to rung (d)'s `spec` dict —
the ONLY call site §2's live trace implicates in the four named
regressions. `prog_moves.py` is left untouched per §3's reasoning (no
causal role found for the four named tasks; the full-battery diff is what
would surface a wider need, not assumed here). The top-level
`domains/prog_synthesis.py::run_enumerate` path is untouched by
construction (`exclude_ops` is a new, additive field nothing existing
sets) — Mod/Sqrt stay fully available to it, so tasks 92/171/246/435
(the predecessor's own measured conversions) are expected to still
convert.

## 6. What this document does NOT yet establish — the RESULTS document's job

1. Whether the one-line `prog_retrieval.py` edit, applied and measured
   through the REAL full battery (not just the isolated hand-check in
   §4), actually restores all four of 59/135/138/406 to their pre-
   regression `pass` outcome, and whether 92/171/246/435 still convert.
2. Whether the official-arm §1(a) mechanism (search-cost inflation
   WITHIN the bare-scalar branch itself, tasks 14/164) is unaffected by
   this fix — it is architecturally NOT a cross-lane issue, so this
   call-site-scoped fix is not expected to resolve it; this is named
   here as a predicted, not yet measured, partial limitation of this
   rung's own scope.
3. Whether `prog_moves.py`'s own (unscoped) `_run_synth_enumerate` calls
   cause ANY regression across the FULL 257-task corpus, beyond the four
   tasks this document traced — the exact task-id set diff is what
   answers this, not this document's structural reasoning about
   `factor_candidates`'s own gating.
4. Whether the named 9-file regression suite and the Rust suite stay
   green after the real Python-side edit (only the INFRASTRUCTURE change
   — `exclude_ops` itself, unused by any caller yet — has been verified
   against them so far).

## 7. GO/NO-GO criterion for this rung

**GO** iff the full paired battery, run after applying §5's edit,
restores 59/135/138/406 to `pass` on `full`/`content_stripped`, keeps
92/171/246/435 as `pass`, and produces **zero other task-id changes**
beyond what the predecessor's own build already produced (i.e. the
`official`-arm task-14/164 mechanism, if it recurs, is a NAMED, not a
disqualifying, limitation — see §6 item 2 — but any NEW regression
outside the predecessor's own measured set is disqualifying). **NO-GO**
otherwise, with the exact task-id diff reported honestly, matching this
arc's own repeated discipline.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-modsqrt-scoped-fix
git log --oneline -1   # on top of main @ 9c3e73f
```

`exclude_ops` hand-check (§4):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
rows = [{'inputs':{'a':123},'output':3}, {'inputs':{'a':25},'output':5}]
spec = {'type':'SynthEnumerate','examples':{'type':'Lit','value':rows},
        'max_size':9,'max_candidates':50000,'saturate_k':0,'field':''}
print('no exclude_ops:', s._inner.evaluate(spec, {}).get('found'))
spec2 = dict(spec); spec2['exclude_ops'] = {'type':'Lit','value':['Mod','Sqrt']}
print('exclude_ops=[Mod,Sqrt]:', s._inner.evaluate(spec2, {}).get('found'))
"
```

Call-site trace (§2) — the proxy-substitution method (a thin wrapper
class assigned to `sub._inner`, logging every `SynthEnumerate`-typed
`evaluate()` call's caller frame) applied to `boot_full()` +
`domains.prog_synthesis.synthesize_from_request` for tasks
`{59, 135, 138, 406}`, sourced from `mbpp_zero_shot_baseline.split_tasks`'s
own `"test"` split of `tests/fixtures/mbpp/sanitized-mbpp.json`.

Rust suite:
```bash
cd runners/dsl && RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
```

Battery:
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```
(Note: `results/mbpp_zero_shot_baseline.json`, `results/prog_construction_
scan.json`, and `results/prog_chunk_mine.json` are gitignored and must be
copied from the canonical tree into a fresh worktree's `results/` before
this script or `boot_full()` will run — not previously documented as a
worktree-setup step in this arc's prior PREREG/RESULTS docs; recorded here
since it cost real time to discover.)
