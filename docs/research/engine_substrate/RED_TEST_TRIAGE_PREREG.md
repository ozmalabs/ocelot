# Red-test triage — pre-registration

**Posture:** MEASURE-THEN-TRIAGE. The creator's directive, verbatim: *"The
pre-existing red tests are causing huge amounts of wasted time and effort.
Start an agent to fix them if required or retire them if they are no longer
relevant."* Over twenty rungs today each re-verified the same red baseline to
prove they added nothing new — a real, repeated cost, paid every time.

This doc registers the bars **before** the sweep is run, per this folder's own
house discipline (`GAMMA_REFLECTION_WIRING_PREREG.md`,
`RULE_SIGNATURE_SLICE_PREREG.md`) and per CLAUDE.md's standing rule from the
2026-07-21 retraction:

> **A BASELINE MUST BE A LIST OF NODE IDS, NEVER A COUNT OR A
> CHARACTERISATION — a count can be held; a list has to be read.**

Because the population is potentially hundreds of node ids that have never
been read individually, this doc pre-registers the **categorisation
methodology and the evidence standard**, not a per-node verdict. Pre-committing
a verdict per node before reading it would be exactly the substring-selector
defect this tree is 0-for-6 on.

---

## 0. Environment — stamped, because the red count is condition-dependent

CLAUDE.md's own conditioned note measures the same tree at **144–145 red node
ids** with `data/` symlinked and **565** with `data/` absent — a 3.9× spread on
one engine at one commit. **Every number this rung emits carries its
condition.**

| item | value |
|---|---|
| worktree | `/home/matt/ocelot-red-test-triage`, branch `red-test-triage` |
| detached from | `main` @ `d239b7c` (verified `git log --oneline -1 main`) |
| engine | `runners/dsl/python/substrate_rs/_native.abi3.so`, sha256 `62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f` — **this worktree's own tracked artifact**, not the canonical `.pth` fallback (`substrate_rs.__file__` resolves inside the worktree) |
| coherence probe | `add_node("T", {"lst":[1,2,3],"tup":(1,2,3)})` reads back `[1,2,3]` (list) / `(1,2,3)` (tuple), distinct — PASS |
| Rust rebuild | **none planned.** The `.so` is git-tracked and arrives with the worktree; a Rust fix is out of scope unless a category-(a) defect proves to be engine-resident, in which case it is NAMED, not rushed. |
| `chess` | INSTALLED, 1.11.2 |
| `data/` | **SYMLINKED** to the canonical tree (`data -> /home/matt/ozmadev/ocelot/data`) |
| `results/` | per-entry symlinks to the canonical tree's artifacts, EXCEPT `results/failure_baseline.json`, which is a **copy** so this rung's rewrite never mutates the canonical tree |
| the prior list | `results/failure_baseline.json`, measured 2026-07-21T02:38:59 @ head `0e61f60e`, condition *"no data/ symlink; own engine build; per-file subprocess"*, **543 entries / 147 red files** |

**The prior list is therefore NOT comparable node-for-node to this rung's
measurement**, and this rung does not pretend otherwise: it was measured in the
WORSE of the two documented conditions. That is precisely the re-measurement
AR1 requires.

**Sweep discipline:** `scripts/failure_baseline_sweep.py`, per-file subprocess,
`COLUMNS=250` (its own docstring records that a captured pipe's 80-column
truncation once amputated every diagnosis in an entire sweep), workers capped
explicitly (never `-n auto`), memory-bounded under `systemd-run --scope`.

---

## 1. The bars

### AR1 — a fresh, enumerated, environment-stamped baseline
A full `tests/test_*.py` per-file sweep at `d239b7c` under the stamped
condition above, producing a **list of node ids**, not a count. PASS iff the
artifact is list-shaped by its own gate
(`tests/test_failure_baseline_migrated.py::check_is_a_list_not_a_count` returns
`[]`) and its `coverage` block declares every file that did not complete as
`NOT_ESTABLISHED` (never red, never silently green).

**Registered in advance:** the fresh red set will be reported as a
three-way diff against the prior list — HELD / STALE (listed, now passes) /
NEW (fails, not listed) — because a bare new number would destroy exactly the
information the list exists to carry. A STALE entry is not an error to be
hidden; per the gate's own docstring it is the payoff.

### AR2 — every node id assigned to exactly one bucket, with evidence
Buckets, fixed in advance:

- **(a) genuine fixable bug** — test correct, behaviour wrong. Evidence
  required: the failing assertion read, and the responsible code path
  identified by reading it.
- **(b) environment / optional-dependency gap** — the test would pass with a
  legitimately-optional dependency or gitignored artifact present. Evidence
  required: the missing thing NAMED, and a demonstration that the test is not
  currently guarded (`importorskip` / `skipif` / a data-presence guard). The
  fix for (b) is **the guard**, never installing the dependency — an unguarded
  optional dep is a real process bug even when the capability gap is not being
  closed, because it forces every future rung to re-diagnose it.
- **(c) stale / no-longer-relevant** — the tested claim, mechanism or API was
  superseded, deleted or deliberately changed. Evidence required: **the
  superseding commit, doc section, or deletion, named**. Retirement is by
  DELETION (CLAUDE.md prefers clean deletion to compatibility shims), never by
  an unconditional skip.
- **(d) ambiguous — needs the creator** — real evidence on both sides. Named
  precisely, neither fixed nor retired.

**Batching is permitted and expected**, but only by *shared root cause proven
once and shown to apply*: a batch must name its root cause, show the evidence
for it, and list every node id it covers. A batch whose members were assigned
by message-substring similarity alone is exactly the substring selector this
tree keeps failing on, and is NOT admissible.

**Registered in advance (a bar this rung can fail):** the *pre-declared
prohibition* on retirement-by-convenience. A node may enter (c) only with a
named superseding artifact. "I could not work out why it fails" is (d), never
(c). Any node retired without a named superseder is a FAILURE of this bar even
if the number improves.

### AR3 — fixes applied for (a) and (b), with before/after evidence
Per fix or per proven batch: the node ids, red before, green after, both
measured in the stamped condition. A fix must not weaken an assertion, add an
unconditional skip, or make a test tautological. (a)-class defects too large
for one rung are **named with their diagnosis and left red**, which this
folder's culture treats as a complete outcome, not a failure.

### AR4 — retirements applied for (c), with per-test (or per-batch) justification
Deleted, with the superseding artifact named in the commit message and in the
RESULTS doc.

### AR5 — the regenerated `results/failure_baseline.json`
Rebuilt from the post-fix sweep by the existing `scripts/failure_baseline.py
build` path, re-gated green by `tests/test_failure_baseline_migrated.py`
(all its structural checks AND its six positive controls). Every remaining
entry carries a class that a reader can act on — a (a)-too-big-for-this-rung
with its diagnosis, or a (d).

### AR6 — no regression beyond the baseline's own change
A post-fix sweep over, at minimum, every file this rung touched plus every
file that previously contained a listed node. PASS iff no node that was GREEN
in the AR1 sweep is RED in the AR6 sweep. A fix that greens one node by
reddening another is not a fix.

---

## 2. Constraints, registered so a violation is visible

1. **Architecture rule.** No Python agent-decision logic. If a fix would need a
   Python `if` that decides agent behaviour from graph state, the legal fix is
   Rust or a graph rule; if that is too large, the node is (a)-too-big and is
   NAMED, not shortcut.
2. **Files owned by concurrent threads — not touched, at all:**
   `domains/analogical_thinking.py`, `domains/reflective_faculty.py`,
   `domains/rule_signature.py`, `runners/dsl/src/py.rs`, and
   `substrate/world_adapter.py`'s checkpoint-load region. A red whose fix
   requires one of these is recorded as **BLOCKED — concurrent thread owns
   this file** inside its bucket, and skipped.
3. **Worktree isolation.** Every write resolves inside
   `/home/matt/ocelot-red-test-triage`. The canonical tree is read-only to this
   rung, `results/failure_baseline.json` explicitly de-symlinked to guarantee
   it.
4. **No push, no `main`.** Work is committed on branch `red-test-triage` in the
   worktree.

---

## 3. What would make this rung a null, stated before measuring

If the honest finding is *"the large majority of these are genuine defects
whose fixes are each their own rung; only a handful were cheaply fixable or
safely retirable"*, that is the result, reported as-is. The bars above are
passed by **reading every entry and assigning it with evidence**, not by the
size of the reduction. A number improved by unconditional skips, weakened
assertions or unjustified deletions fails AR2, AR3 and AR4 simultaneously,
regardless of how small the remaining list is.
