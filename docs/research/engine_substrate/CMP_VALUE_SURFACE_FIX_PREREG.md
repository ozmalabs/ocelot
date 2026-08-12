# ENGINE CORRECTNESS — `cmp_value` HAS NO `(Surface, Surface)` ARM — PRE-REGISTRATION

*Branch `cmp-value-surface-fix`, worktree `/home/matt/ocelot-cmp-value-surface-fix`,
based on `main` @ `a624375`. The engine is built in THIS worktree
(`scripts/engine_build.sh`), never in the canonical tree.*

*Committed BEFORE any measurement is run. No seed block is required — this rung
adds no seed data.*

---

## 0. WHAT THIS RUNG IS

An **engine-correctness rung**, sent at a defect that a different rung found
while building something else and explicitly declined to fix inside its own
scope (`RULE_SIGNATURE_TO_RUST_RESULTS.md` §5.1 / §5.2, merged `a624375`).
It registers **no hypothesis about any faculty, benchmark or domain**. The
deliverable is either:

- a **fix with a reproduction that is RED before it and GREEN after it**, both
  demonstrated live on the real engine; or
- an honest, precisely-scoped **NO-GO** with the blast radius that decided it.

A fix without a reproduction is untestable and will not be committed. A NO-GO
with real evidence is a complete result under this project's standing culture.

---

## 1. THE TWO DEFECTS, RESTATED FROM THE SOURCE

Quoted from `RULE_SIGNATURE_TO_RUST_RESULTS.md` §5, which is the pinned prior
evidence this rung starts from:

> 1. `cmp_value` has **no `(Surface, Surface)` arm**, so any two runtime-BUILT
>    strings compare `Equal` — and since `make_set` / `make_frozenset` dedup by
>    `cmp_value` and `Value::Dict` is a cmp-sorted vec, **a set or dict of
>    computed strings collapses to one element.** Measured:
>    `{f"a{i}" for i in range(3)}` → `frozenset({'a0'})`.
> 2. `cmp_value`'s `(Str, Str)` arm compares **interner symbol IDs**, so
>    `sorted`/`min`/`max`/`Lt` over strings are boot-history order, not
>    lexicographic — there is no lexicographic string order in the engine at
>    all.

**Defect 1 is an Ord/Eq INCONSISTENCY** — `PartialEq` has a correct
`(Surface, Surface)` arm; `cmp_value` does not, so two values that are `!=`
compare `Equal` for ordering. That is a violation of the total-order contract
every `Set`/`FrozenSet`/`Dict` in the substrate canonicalises through, and it
loses data silently.

**Defect 2 is NOT an Ord/Eq inconsistency** — `(Str,Str)` is self-consistent
(`Sym == Sym` under both), it is merely a *non-lexicographic* order. It is a
determinism/portability defect, not a data-loss defect. Whether those are the
same root cause is AR4's question, not an assumption of this prereg.

---

## 2. REGISTERED BARS

Registered before any code is read further or written. Every bar is
verdicted in the RESULTS doc whether it lands or not.

**AR1 — ROOT CAUSE, VERIFIED FROM THE CODE, NOT INFERRED.**
State the exact reason `cmp_value` and `PartialEq` disagree for `Surface`,
with file:line for both implementations, and the exact mechanism by which the
disagreement reaches a user-visible collapse (which constructor, which dedup
call). MET iff the mechanism is read off the source and each link in the chain
is cited, not asserted.

**AR2 — LIVE CONFIRMATION, BEFORE ANY FIX.**
Reproduce the collapse on the real engine as committed at `a624375`
(the engine artifact already in the tree, not a rebuild), for at least the
four cases §5.1 names: a set of computed strings, a dict keyed by computed
strings, a nested (tuple-wrapped) computed key, and the literal-string control
that must be CORRECT. MET iff the collapse is observed live and the control is
observed correct — the control matters, because a reproduction that fails the
same way for literals would mean the diagnosis is wrong.

**AR3 — THE `(Surface, Surface)` FIX, LIVE BEFORE/AFTER.**
The exact AR2 cases produce the correct number of distinct elements after the
fix (3, not 1), with the before/after transcript recorded. Additional required
properties, each asserted in a Rust unit test:

- **Ord/Eq consistency**: for Surface values, `cmp_value(a,b) == Equal` iff
  `a == b`. Both directions, including the two `SurfaceKind`s.
- **Antisymmetry / totality**: `cmp_value(a,b) == cmp_value(b,a).reverse()`.
- **Transitivity spot-check** on a three-element ladder.
- **`SurfaceKind` is part of the order** — a `Text` and a `Bytes` surface with
  identical payload are `!=` under `PartialEq`, so they must not be `Equal`
  under `cmp_value` either.

MET iff all of the above hold live AND the AR2 transcript inverts.

**AR4 — THE `(Str, Str)` INVESTIGATION: SAME ROOT CAUSE OR DIFFERENT, AND
GO/NO-GO WITH REASONING.**
Answer, from the code: are `Str` and `Surface` the same defect twice, or two
different defects that happen to both be about strings? Then a GO/NO-GO on
fixing `(Str,Str)` **in this rung**, decided on evidence:

- does `cmp_value` have access to the interner at all (it is a free function;
  the interner is per-Substrate) — i.e. is the fix even *local*?
- how many call sites would have to change if it is not local?
- what currently depends on the existing `Sym`-ID order?

**A NO-GO here is a legitimate outcome and is pre-registered as such.** The
registered decision rule: **GO only if the fix is local to `value.rs` (no
signature change to `cmp_value`) AND the blast-radius check finds no
dependent.** Anything else is NO-GO, named precisely as its own follow-on
rung. This is registered now so the verdict cannot be rationalised later.

**AR5 — BLAST-RADIUS CHECK, BEFORE SHIPPING.**
A real search — not a plausibility argument — for anything that depends on the
CURRENT (buggy) behaviour:

- every Rust call site of `cmp_value` (and of `make_set`/`make_frozenset`,
  which is how it reaches data);
- persisted graph data: does any committed seed or checkpoint contain a
  `Set`/`FrozenSet`/`Dict` holding `Surface` values whose stored order or
  membership would change?
- tests: does any test assert an outcome that only holds because of the
  collapse (the precedent is `test_galileo_migrated.py`, which deliberately
  relies on a DIFFERENT dedup quirk being present — so this is a real pattern
  in this tree, not a hypothetical);
- `PartialEq`/`Hash` consistency: does the fix make `cmp_value` agree with the
  hash, or introduce a new disagreement?

MET iff the search is enumerated (the list, not a count — CLAUDE.md's standing
rule) and each hit is dispositioned.

**AR6 — NO REGRESSION, PAIRED FAILING-NODE-ID LISTS, NEVER COUNTS.**
- `cargo test --lib` in `runners/dsl`, before and after, as **lists of failing
  test names**.
- Python: the suites most likely to exercise `Set`/`Dict` construction over
  computed strings, run before and after on the SAME engine-swap protocol,
  reported as paired **failing node-id lists**. `test_rule_signature_program_migrated.py`
  is named explicitly (it is the direct consumer that walked into this defect
  and routed around it), plus the Program-IR / ProgEval suites, plus a broad
  migrated sweep sized to fit the box.

MET iff the after-list is a subset of (or equal to) the before-list, with any
difference enumerated and explained.

---

## 3. WHAT WOULD FALSIFY THE FIX

Registered so the rung can lose:

1. **The AR2 reproduction does not reproduce.** Then §5.1's claim is
   environment-conditional and the rung reports that instead of a fix (the
   CLAUDE.md retraction note is the standing precedent: a claim quoted without
   its condition is the defect).
2. **AR5 finds a real dependent.** Then per the brief's constraint, it is
   named precisely and either fixed alongside (if small) or reported as a
   blocker requiring its own decision — NOT silently broken.
3. **AR6's after-list is not a subset of the before-list.** Any new red is a
   regression caused by this rung until proven otherwise, and the fix does not
   ship on "it's probably unrelated."

---

## 4. WHAT THIS RUNG WILL NOT DO

- It will not add a Term variant, a seed, or any Python agent logic.
- It will not "improve" `cmp_value` beyond the two registered defects — no
  reordering of the tag table (the source comment says renumbering would
  change the canonical order of every existing mixed-type Set, and that is
  correct), no new cross-type arms.
- It will not touch `main` or the canonical tree. Engine built and committed
  in this worktree only.

---

## 5. PROTOCOL

Engine build, per this box's standing note:

```
export PATH="/home/matt/.cargo/bin:$PATH"          # rustc 1.97.1
export RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"
CARGO_BUILD_JOBS=2 systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G -- \
    bash scripts/engine_build.sh
```

`--release`, verified by `sha256sum` that the committed artifact is the built
one, plus the list/tuple coherence probe after any rebuild.

The AR2 "before" measurement is taken on the engine artifact **as committed at
`a624375`**, saved aside by sha256 so the before/after pair is against a pinned
binary, not a memory of one.
