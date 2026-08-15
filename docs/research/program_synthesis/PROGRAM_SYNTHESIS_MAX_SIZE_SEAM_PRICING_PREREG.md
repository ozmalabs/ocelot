# `run_enumerate`'s hardcoded `max_size: 9` — the shared-seam pricing named
   by `DICTFROMPAIRS_RESULTS.md` §3/§7 — PREREG (and the whole story: NO-GO)

**Date:** 2026-08-16. Base `main @ a3a9d4b` ("Merge progsyn-dictfrompairs:
DictFromPairs op (zero new Term) + engine bugfix, honest NULL on MBPP
conversion"), verified fresh via `git log --oneline -1 main` before creating
the worktree. Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-maxsize-seam`,
branch `progsyn-maxsize-seam` — **not merged to `main`**, left for the
orchestrator to independently verify (this session's explicit instruction:
never merge to `main`, never `git stash`, never push).

Investigation-only. This document is itself the only artifact this rung
produces — no code change survives in the worktree (a temporary one-line
edit, described in full in §4, was made to obtain the measurement and then
reverted; `git diff --stat` on the worktree is empty at the time of writing).

---

**HEADLINE, stated up front: NO-GO — not on risk, on measured yield. Raising
`run_enumerate`'s hardcoded `max_size` from 9 to 20, GLOBALLY, across the
real pipeline, all three MBPP battery arms, exact task-id-set diff (not a
sample, not a count): zero newly passing, zero regressed, zero outcome drift
of any kind on any of the 257 runnable rows in any arm, +2.1% wall-clock cost
(258.6s → 264.0s for the full three-arm battery). It is SAFE and CHEAP. It is
also, measured directly and exhaustively, of ZERO benefit — including to the
two tasks (277, 465) that motivated pricing this seam in the first place,
because their real blocker is `DICT_DEFAULT_OPS`'s missing `DictItems`/
`FilterList` (a SEPARATE, already-priced-and-rejected lever,
`DICTFROMPAIRS_PREREG.md` §4), not `max_size` alone. A narrower,
Dict-shape-scoped raise is measured even more starkly useless: the current
5-op `DICT_DEFAULT_OPS` bucket's search on both target specs SATURATES
(`halt_reason: 'saturated'`, distinct-behaviour count genuinely exhausted at
8/7) completely independent of `max_size` — raising the ceiling from 9 to 25
changes not one digit of `tested`/`distinct`/`halt_reason` for either task.
`max_size`, priced in isolation as this rung's single variable, is not the
lever that unblocks anything on `main` today. No code change is proposed.**

---

## 0. What was asked, and how this document answers each part

`DICTFROMPAIRS_RESULTS.md` §3/§7 named, but explicitly did NOT price, two
separate factors jointly required to convert tasks 277/465: (a) widening
`DICT_DEFAULT_OPS` with `DictItems`/`FilterList` (priced and REJECTED in the
PREREG on regression grounds, §4 there) and (b) raising `run_enumerate`'s
hardcoded `max_size: 9`. This document prices (b) alone, honouring the arc's
standing single-variable-rung discipline — it does NOT re-open (a), and every
finding below should be read with that scope in mind.

1. **Is `max_size: 9` derived from anything, or a bare literal?** §1 — bare
   literal, independent of the Rust-side `DEFAULT_MAX_SIZE` constant.
2. **What does search cost look like as `max_size` grows?** §2 — measured
   directly at three grains: a forced wide-op search (the exact composition
   `DICTFROMPAIRS_RESULTS.md` §1 found), the two live MBPP witness tasks
   under the CURRENT shipped 5-op bucket, and a full-corpus raw sweep.
3. **Global vs. per-spec/per-bucket raise — which is the right lever, and
   where would it live?** §3 — the Rust-side spec-shape branching that
   already exists (`spec_output_is_dictlike` et al., `synth_enumerate.rs`)
   is the ARCHITECTURALLY correct host for a narrower raise; a Python-side
   gate would violate this arc's own standing discipline. Moot for this
   rung's build decision because of §4's finding.
4. **Full population regression risk.** §4 — measured EXACTLY, all 257
   test-split tasks, all three arms, real pipeline, paired before/after,
   exact task-id-set diff (not sampled): zero regression, zero yield.

## 1. Where `9` comes from, read directly

`domains/prog_synthesis.py`, `run_enumerate` (current `main`, confirmed at
line 1338 in this worktree):

```python
spec: Dict[str, Any] = {
    "type": "SynthEnumerate",
    "examples": {"type": "Lit", "value": rows},
    "max_size": 9, "max_candidates": 0, "saturate_k": 0,
    "field": ""}
```

**Bare literal `9`, not derived from anything.** `runners/dsl/src/synth_enumerate.rs:229`
does carry `const DEFAULT_MAX_SIZE: i64 = 9`, but that constant is used
exactly once, at line 1991: `let max_size = (if max_size <= 0 {
DEFAULT_MAX_SIZE } else { max_size }) as usize;` — a fallback for when the
CALLER passes `<= 0` (i.e. "no opinion, use the engine default"). Python's
`run_enumerate` never passes `<= 0`; it always sends an explicit positive
`9`, so the Rust fallback path is NEVER exercised by the real pipeline — the
two `9`s currently agree by coincidence of two independently-chosen values,
not by derivation. Read directly, the module's own doc comment
(`synth_enumerate.rs:64-65`) states the contract neutrally: *"`max_size`
(≤0 → 9) bounds term size exactly as in generator.py"* — it does not imply
the CALLER must pick 9, only that omitting an opinion falls back to 9.

**A second, separate call site with its own separate hardcoded budget,
confirmed by reading the file, named here for completeness and explicitly
OUT OF SCOPE:** `_solve_arm` (`domains/prog_synthesis.py`, ~line 2106,
branch-arm derivation, `_derive_branch_arms`'s own direct
`SynthEnumerate` call for a THEN/OTHER row partition) hardcodes
`"max_size": 7` — a third, independent magic number, on a narrower,
unrelated construction lane (if-then-else branch splitting). This document
does not price it; it is unrelated to `DICTFROMPAIRS_RESULTS.md`'s own
naming of the seam, which cites `run_enumerate`'s `max_size: 9` specifically
(line ~1338, the seam every currently-failing Dict-shaped/list-shaped/
arithmetic-shaped/etc. spec passes through as its own primary search).

## 2. Search cost as `max_size` grows — measured directly, three grains

### 2.1 A forced wide op set on the exact DictFromPairs composition
   (reproducing, then extending, `DICTFROMPAIRS_RESULTS.md` §1)

Forcing `ops = ["DictItems","FilterList","DictFromPairs","Eq","IfThenElse",
"GroupCount","DictMerge"]` (the RESULTS doc's own forced set) directly via
`substrate_rs.Substrate()._inner.evaluate()` on task 277's two revealed
rows, sweeping `max_size` 9→22, `max_candidates: 400000`:

```
ms= 9  time=0.006s  found=False  tested=  2,729  distinct= 38  halt=max_size
ms=10  time=0.015s  found=False  tested=  5,401  distinct= 48  halt=max_size
ms=12  time=0.043s  found=False  tested= 11,948  distinct=128  halt=max_size
ms=14  time=0.151s  found=False  tested= 31,258  distinct=248  halt=max_size
ms=16  time=0.367s  found=False  tested= 76,186  distinct=448  halt=max_size
ms=18  time=0.920s  found=False  tested=154,434  distinct=856  halt=max_size
ms=19  time=0.952s  found=True   tested=158,531  distinct=868  halt=solved
ms=20  time=0.939s  found=True   tested=158,531  distinct=868  halt=solved
ms=22  time=0.923s  found=True   tested=158,531  distinct=868  halt=solved
```

**Combinatorial growth is real and large under a wide (7-op) inventory**:
tested candidates grow ~58× from `ms=9` to the solving size, wall time ~150×
(0.006s → 0.94s) — for ONE spec, ONE search call. (Minor, immaterial
discrepancy from `DICTFROMPAIRS_RESULTS.md`'s own report of "only `max_size:
20` succeeded" — this measurement finds the solution one step earlier, at
`ms=19`; both agree the threshold sits in the high-teens/20, and neither
changes any downstream conclusion here.)

### 2.2 The SAME growth, but under the bucket that is ACTUALLY shipped —
   `DICT_DEFAULT_OPS` (5 ops, no `DictItems`/`FilterList`) — zero effect

The same sweep, `ops = ["Eq","IfThenElse","GroupCount","DictMerge",
"DictFromPairs"]` — exactly `synth_enumerate.rs:497`'s current
`DICT_DEFAULT_OPS`, unchanged since the DictFromPairs rung — `max_size`
9→25, both tasks:

```
task 277: tested=566  distinct=8  halt=saturated   -- IDENTICAL at every max_size 9..25
task 465: tested=377  distinct=7  halt=saturated   -- IDENTICAL at every max_size 9..25
```

**`halt_reason` is `saturated`, not `max_size`, at every tested ceiling.**
The search's own saturation rule (`saturate_k` window, no NEW distinct
behaviour over the last few sizes) has already concluded there is nothing
left to find with these 5 ops, and that conclusion is INDEPENDENT of how
high `max_size` goes — raising the ceiling cannot rescue a search that has
already exhausted its representational capacity. This is the single most
important number in this document: **it means `max_size` alone, at ANY
value, converts neither target task under the op inventory that ships on
`main` today.** §2.1's wide-op result and this shipped-bucket result are not
in tension — they simply confirm, independently, `DICTFROMPAIRS_RESULTS.md`
§3's own finding that op-availability and size-budget are JOINTLY necessary,
neither sufficient alone.

### 2.3 Currently-PASSING tasks are provably unaffected, confirmed on the
   arc's own documented most-budget-fragile canary

The search is size-ordered and interleaved (production before registration,
`synth_enumerate.rs:95-100`) and returns the moment a target match is found
(`"TARGET match is checked FIRST on a new signature"`, same file, line 89).
**A spec whose accepted candidate is found at some size ≤ 9 today can NEVER
be affected by raising the ceiling — the ceiling is never even consulted.**
Confirmed directly, not just argued, on task 132 (`convert a tuple to a
string`, this codebase's own documented most-budget-fragile spec —
`synth_enumerate.rs:422-424`'s own comment: *"`distinct` already
1941/200,000 before this rung touched anything"*) and task 11 (a
currently-passing string-shaped spec), no explicit `ops` (typed default):

```
task 132: tested=38,864  distinct=186   -- BYTE-IDENTICAL at max_size 9, 12, 15, 18, 20 (time 0.014-0.017s, no trend)
task 11:  tested=69,691  distinct=5,028 -- BYTE-IDENTICAL at max_size 9, 12, 15, 18, 20 (time 0.021-0.033s, no trend)
```

### 2.4 A raw, no-explicit-`ops`, whole-corpus sweep — 257/257 test-split
   tasks, `max_size` 9 vs 20 — the cost driver identified directly

A lighter-weight approximation of the real pipeline (typed-default op
selection only — skips the real pipeline's `ps_enum_ops`/`consts`/`exclude`
machinery; §4 below supplies the REAL, full-fidelity number this
approximates) run against every runnable test-split task:

```
found@9:  166     found@20: 166     newly found: []     lost: []
total raw eval time @9: 13.62s   @20: 14.69s   (+1.07s, +7.9%, over 257 tasks)
halt reasons @9:  {solved: 166, budget: 73, max_size: 15, saturated: 2, None: 1}
halt reasons @20: {solved: 166, budget: 87, saturated: 3, None: 1}
```

**Zero newly-found, zero lost — matches §2.3's theoretical argument exactly,
now confirmed at whole-corpus scale.** The 15 tasks that halt via `max_size`
(genuinely still growing, not yet saturated) at `ms=9` mostly move to
`budget` at `ms=20` — i.e. they hit the SAME `max_candidates` (default
200,000, a COUNT budget per `synth_enumerate.rs:64-70`'s own "budgets are
COUNTS, never a wall clock" contract) ceiling that already exists today,
just later. **This is the actual mechanism that keeps a global raise's
worst-case cost bounded**: for any op inventory with real branching factor,
a spec that doesn't solve or saturate quickly will hit the pre-existing
200,000-candidate wall well before a `max_size` ceiling of 20 becomes the
binding constraint (task 87, for example, grows from 3,251 tested at `ms=9`
to 147,387 at `ms=20` — large, but still under the 200k floor that already
bounded it in spirit). The "top 15 growth" tasks (87, 97, 117, 237, 283,
290, 299, 301, 305, 412, 417, 462, 470, 475, 20) are exactly the
`max_size`-halted-at-9 population — none of them newly solves.

## 3. Global vs. narrow — which lever, and is there already a hook for a
   narrower one?

**Yes — `synth_enumerate.rs`'s own `eval_synth_enumerate` already computes
and branches on spec-shape flags** (`spec_is_list_shaped`,
`spec_output_is_dictlike`, `spec_output_is_setlike`, `spec_is_string_shaped`,
lines ~2074-2367) to pick a TYPED-DEFAULT op inventory when the caller
supplies none — this is the exact "does it already have per-spec-shape
branching that could host a narrower raise" infrastructure question asked.
It does — but only for the OP LIST, never for `max_size`, which is threaded
through as one caller-supplied scalar for the whole call regardless of which
typed-default branch is taken internally.

**A narrower raise would have to live in Rust, not Python.** `domains/
prog_synthesis.py` carries its own, independently-maintained mirror of these
shape predicates (`_synth_spec_shape_flags`, line 1153) — but that
function's own docstring and the call site's own comment
(`run_enumerate`, ~line 1322) are explicit: it is computed *"purely for
parity comparison against the existing hand-written Rust ladder — NEVER
consulted for `spec["ops"]` construction below"*. Gating `max_size` from a
FRESH Python `if is_dict_shaped: max_size = 20 else: 9` would be a NEW
Python decision over graph-derived shape evidence — precisely what
CLAUDE.md's architecture rule forbids ("Any `if`/`else` that reads graph
state and decides what to do next is a Rule, not Python") and precisely the
duplication-drift liability this codebase already flags for the `ops` case
one paragraph over. The only CLAUDE.md-compliant narrow design is a Rust
change inside `eval_synth_enumerate` itself, sizing `max_size` from the SAME
branch that already picks `DICT_DEFAULT_OPS` — architecturally sound, but a
genuine `.rs` change (not the near-zero-touch op-table exposure class this
arc has repeatedly favoured), requiring the full rebuild/Rust-suite
discipline.

**This entire question is moot for a build decision here.** §4 measures the
GLOBAL raise's regression risk directly at zero, so the risk-driven case for
preferring a narrow lever over a global one does not materialise. And §2.2
already shows a narrow, Dict-scoped raise (even if built the
CLAUDE.md-compliant Rust way) converts nothing, for the same reason a global
raise converts nothing: op-availability, not size, is the active constraint
on `main` today.

## 4. Full population regression risk — measured exactly, not sampled

**Method**: real pipeline (`domains.prog_synthesis.synthesize_from_request`,
unmodified except the ONE line under test), `scripts/mbpp_endgame_battery.py`
(unmodified — the arc's own standard three-arm measurement driver), all 257
MBPP test-split tasks, all three arms (`full`/`content_stripped`/`official`).
**Before**: this worktree, unmodified `main @ a3a9d4b`, freshly run.
**After**: `domains/prog_synthesis.py:1338` changed from `"max_size": 9` to
`"max_size": 20` (the ONLY line touched; reverted immediately after the
measurement — `git diff --stat` on this worktree is empty as of this
document), same battery, same worktree, same engine build (no `.rs` touched,
so no rebuild was needed or performed).

```
                    before (k/n)         after (k/n)          Δ elapsed
full:               71/257  p=0.276265   71/257  p=0.276265   71.70s -> 73.67s (+2.7%)
content_stripped:   70/257  p=0.272374   70/257  p=0.272374   71.32s -> 73.36s (+2.9%)
official:          100/257  p=0.389105  100/257  p=0.389105  115.60s -> 116.92s (+1.1%)
                                                     total:   258.6s -> 264.0s  (+2.1%)
```

**Exact task-id-set diff, all three arms** (direct set computation off
`results/mbpp_endgame_BEFORE_ms9.json` vs. `results/mbpp_endgame.json`,
both retained in this worktree — `results/` is gitignored per this arc's
own standing note, not part of any commit):

| arm | newly passing | regressed | ANY outcome drift (all runnable rows) | construction drift (still-passing) |
|---|---|---|---|---|
| `full` | `{}` | `{}` | `{}` | `{}` |
| `content_stripped` | `{}` | `{}` | `{}` | `{}` |
| `official` | `{}` | `{}` | `{}` | `{}` |

**"ANY outcome drift" was checked over EVERY runnable row's `outcome`
string** (not just pass↔fail transitions — `gapped:*` reason changes,
`accepted_holdout_fail`, `runner_exception:*` type changes, all of it), for
all 257 rows × 3 arms = 771 comparisons: zero drift anywhere. Task 277 and
465 specifically, spot-checked: `outcome: gapped:enumerate_failed,
construction: None, gap_reason: enumerate_failed` — byte-identical before
and after, confirming §2.2's forced-probe finding (saturation, not size,
blocks them) holds under the real pipeline too.

**Verdict on regression risk: measured LOW to the point of zero** — not
"priced as probably safe," actually observed as exactly zero across the
complete population, both arms, every task, every field checked, not a
sampled subset.

## 5. Worktree/artifact housekeeping (not part of any commit)

This worktree's `results/` and `data/` (gitignored, per-tree) were empty on
checkout. Copied/symlinked from `main`'s own tree, verbatim, read-only
inputs, before any battery run would boot cleanly:
`results/mbpp_zero_shot_baseline.json`, `results/prog_construction_scan.json`,
`results/prog_chunk_mine.json` (copied, small, static); `data/` (39G,
SYMLINKED to `main`'s own `data/`, never copied, per this task's own disk-space
caution). None of this is a code change and none of it is committed —
`results/`/`data/` stay gitignored, matching `DICTFROMPAIRS_RESULTS.md`'s own
precedent for the identical housekeeping need.

## 6. What this document does NOT establish

1. Whether widening `DICT_DEFAULT_OPS` with `DictItems`/`FilterList` — the
   OTHER factor `DICTFROMPAIRS_RESULTS.md` §3 names as jointly necessary —
   would itself be safe and worth its own regression pricing. Explicitly out
   of scope for this single-variable rung; `DICTFROMPAIRS_PREREG.md` §4
   already priced and rejected it once, on grounds this document's own §2.2
   finding does not overturn (the rejection was about op-availability
   benefit given a fixed size budget; this document is about size budget
   given a fixed op set — the two questions are genuinely orthogonal, and a
   FUTURE rung that reconsiders BOTH together, bundled, is a real,
   un-costed candidate this document explicitly declines to build).
2. Whether raising `max_size` would unlock anything for a spec whose real
   `ops` come from an explicit `ps_enum_ops` graph fact (a curated,
   rule-selected list, `seeds/program_synthesis_grounding.json`'s
   `ps_select_synthesis_operator_shape`) rather than the typed default —
   §4's real-pipeline measurement covers this population exactly as it
   exists on `main` today (whatever `ops` each of the 257 tasks' own rules
   actually select), and found zero yield there too; §2.4's raw sweep is a
   supporting approximation only, not the authoritative number.
3. Whether `max_candidates`'s own default (200,000) is itself well-tuned —
   named only as the mechanism (§2.4) that bounds a global raise's
   worst-case cost; not itself priced or questioned here.
4. The `_solve_arm` `max_size: 7` seam (§1) — a separate, narrower,
   unrelated construction lane, not priced.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 7. GO/NO-GO

**NO-GO.** Not a risk-driven NO-GO — every risk question this document was
asked came back favourable: `max_size` is a bare, undependent literal (§1);
raising it globally 9→20 costs +2.1% wall-clock on the full three-arm
battery and, measured exhaustively (not sampled) across all 257 tasks × 3
arms, changes not one single outcome, construction, or `ir` field for any
currently-passing task (§4). This is a YIELD-driven NO-GO: the seam this
rung was asked to price, taken alone, converts **zero** MBPP tasks — not the
two witnesses that motivated pricing it, and not any other task in the
corpus either (§2.4, §4). The reason is precisely diagnosed, not merely
observed: `DICT_DEFAULT_OPS`'s current 5-op inventory SATURATES for both
target specs independent of `max_size` (§2.2) — the search has already
concluded there is nothing more to find with these ops, at any size, and a
bigger ceiling cannot rescue a search that has already exhausted its
representational capacity. Converting tasks 277/465 needs `max_size` raised
**and** `DictItems`/`FilterList` added to `DICT_DEFAULT_OPS`, together — a
bundled, two-variable change this rung's own single-variable scope
correctly declines to make. No code change is proposed by this document. The
worktree contains no diff from `main @ a3a9d4b` other than this PREREG file
itself.

## Reproduce

Forced wide-op sweep (§2.1, no code change needed — direct `evaluate()`):
```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-maxsize-seam
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs, time
def wire(v):
    if isinstance(v, dict): return {'__dict__': [[k, wire(x)] for k, x in v.items()]}
    return v
rows = [
    {'inputs': {'dict': wire({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Kierra Gentry': 165, 'Pierre Cox': 190}), 'n': 170},
     'output': wire({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Pierre Cox': 190})},
    {'inputs': {'dict': wire({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Kierra Gentry': 165, 'Pierre Cox': 190}), 'n': 180},
     'output': wire({'Alden Cantrell': 180, 'Pierre Cox': 190})},
]
ops = ['DictItems','FilterList','DictFromPairs','Eq','IfThenElse','GroupCount','DictMerge']
for ms in (9, 15, 19, 20):
    s = srs.Substrate()
    spec = {'type': 'SynthEnumerate', 'examples': {'type': 'Lit', 'value': rows},
            'max_size': ms, 'max_candidates': 400000, 'saturate_k': 0, 'field': '',
            'ops': {'type': 'Lit', 'value': ops}}
    t0 = time.time(); r = s._inner.evaluate(spec, {}); dt = time.time() - t0
    print(ms, dt, {k: r.get(k) for k in ('found','tested','distinct','halt_reason')})
"
```

Shipped-bucket saturation check (§2.2):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
def wire(v):
    if isinstance(v, dict): return {'__dict__': [[k, wire(x)] for k, x in v.items()]}
    return v
rows = [
    {'inputs': {'dict1': wire({'c1':'Red','c2':'Green','c3':None})}, 'output': wire({'c1':'Red','c2':'Green'})},
    {'inputs': {'dict1': wire({'c1':'Red','c2':None,'c3':None})}, 'output': wire({'c1':'Red'})},
]
ops = ['Eq','IfThenElse','GroupCount','DictMerge','DictFromPairs']
for ms in (9, 15, 20, 25):
    s = srs.Substrate()
    spec = {'type': 'SynthEnumerate', 'examples': {'type': 'Lit', 'value': rows},
            'max_size': ms, 'max_candidates': 0, 'saturate_k': 0, 'field': '',
            'ops': {'type': 'Lit', 'value': ops}}
    r = s._inner.evaluate(spec, {})
    print(ms, {k: r.get(k) for k in ('found','tested','distinct','halt_reason')})
"
```

Full paired battery (§4 — the ONE-line edit, run, then revert):
```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-maxsize-seam
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py    # BEFORE, unmodified main
cp results/mbpp_endgame.json results/mbpp_endgame_BEFORE_ms9.json
# edit domains/prog_synthesis.py:1338  "max_size": 9  ->  "max_size": 20
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py    # AFTER
git checkout -- domains/prog_synthesis.py    # revert
```
