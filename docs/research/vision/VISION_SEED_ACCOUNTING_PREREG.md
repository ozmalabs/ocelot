# SEED ACCOUNTING AUDIT — PRE-REGISTRATION

**Written and committed BEFORE any measurement (§3).**

Branch actually seen: `worktree-agent-a17e760b79a2d8af0` (NOT the intended
`gamma-substrate/seed-accounting` — the eighth consecutive rung to run under an
auto-generated name). Base HEAD `c7a57ec8a0e532a9937906fcd00cd7805fce3d0e`.

My own seed block: **82000–82999**. A concurrent rung holds 81000–81999.

## 0. What this rung is

An AUDIT of the project's own bookkeeping, not a vision experiment. The
resolution-scale rung (`c7a57ec8`) mis-stated its own seed consumption; the
error was visible only by auditing FROM SOURCE rather than from the
`SEED_BLOCK` constant at the top of the file. This rung asks whether that was
a one-off or whether `VISION_PROTOCOL.md` §11's burned-seed ledger is
systematically unreliable.

**The ledger records DECLARED blocks. Every collision check ever performed in
this arc, including the supervisor's, has been against declarations rather
than measured draws.** That is the thing under test.

## 1. The measurement instrument

A static analyser (`scripts/seed_audit.py`) that extracts ACTUAL seed draws
from Python source by AST walk + abstract interpretation. It must resolve the
pattern the defect rung actually used, which no substring scan can see:

```python
SEED_BLOCK = 79000
...
for t in range(N_BASE):                      # N_BASE = 50, module constant
    rng = random.Random(SEED_BLOCK + 400 + t)      # -> 79400..79449
    probes = video_probes(qs, gs, t, rng, SEED_BLOCK)   # interprocedural
    seed = SEED_BLOCK + 200 + t                    # -> 79200..79249
...
def video_probes(qs, gs, t, rng, seed):
    for label, off in (("G2c", 700), ("G2t", 800)):
        r2 = np.random.RandomState(seed + off + t)  # -> 79700..79749, 79800..79849
```

So the analyser needs: module-level constant propagation, `range()` loop-
variable expansion, tuple-unpacking loop targets, integer arithmetic folding,
and INTERPROCEDURAL propagation of a seed passed as an argument.

**§12 applies: a selector that matches by substring is not a selector.**
Substring selectors have failed four times in this arc, once going red on
their own docstring. This instrument is an AST walk; it never greps for a
number.

## 2. Instrument validation — declared BEFORE results

**§1.1 / the dead-instrument rule: zero consumption is a LEGITIMATE result
(k-scope and block-unit rungs consumed none by design), so a tool that reports
zero everywhere and a clean tree LOOK IDENTICAL.** Two controls, both required
to pass before any ledger number is quoted:

- **V1 SELF-AUDIT (the headline validation).** Apply the tool to THIS rung's
  own script first. If it cannot report my own declared-vs-measured
  consumption correctly, it does not work and no other number is reported.
- **V2 POSITIVE CONTROL — PLANTED COLLISION.** Plant a script that draws a
  seed measurably inside another rung's consumed range. The tool MUST flag it
  as a genuine collision. Removing it MUST restore a clean report. A detector
  that has never been ABLE to fire has not been tested.
- **V3 RECOVERY OF THE KNOWN DEFECT.** The tool must independently recover the
  four scattered sub-ranges of the resolution rung — 79200–79249, 79400–79449,
  79700–79749, 79800–79849 — WITHOUT being told them.

## 3. Predictions (registered before measuring; §7 — I report these whether
they hold or not)

- **P1** — V3 holds: the tool recovers all four sub-ranges exactly, and
  recovers the K-arm collision (declared 79200–79399 vs consumed 79200–79249)
  without being told.
- **P2** — **OVER-DECLARATION IS THE DOMINANT CLASS.** Most declared blocks are
  1000 wide; I predict median measured consumption is under 10% of declared
  width, and that a majority of declared blocks measure ZERO consumption from
  static analysis (either genuinely unspent, or invisible to the tool — I must
  distinguish these and will not conflate them).
- **P3** — the supervisor's `default_rng(0)` lead resolves as **conventional
  low seeds OUTSIDE the ledger's addressable range entirely** (every declared
  block starts above 2000), i.e. they are deterministic-shuffle conveniences
  and NOT evidence that declared blocks are vestigial. I predict this lead is
  a red herring; if it is not, I report that instead.
- **P4** — **GENUINE COLLISIONS ARE RARE: I predict 0–3 tree-wide**, precisely
  BECAUSE over-declaration means measured sets are sparse inside wide blocks.
  The K-arm case is a declared-vs-consumed collision WITHIN one rung and I
  count it separately from cross-rung collisions.
- **P5** — at least one `measured ⊄ declared` case exists (a script drawing
  outside any declared block, beyond the conventional low seeds).

**Registered risk of the negative:** if P2 and P4 both hold, the honest
headline is "systematically over-declared, no real collisions" — a
reassuring-sounding result. **I pre-commit that over-declaration is itself the
defect being reported, not an all-clear**, because it is exactly what makes the
ledger unable to protect a successor claiming an apparently-free sub-range.

## 4. What the tool CANNOT see — declared in advance, not after

I pre-commit to reporting these as coverage limits rather than implying
completeness:

1. Seeds from CLI args, `os.environ`, or config files (runtime values).
2. Seeds derived from data (`hash(x)`, `len(pool)`, timestamps, file contents).
3. Seeds crossing a module boundary (imported constant used as a seed
   elsewhere) — I attempt intra-file interprocedural only.
4. Draws inside library/adapter code (`domains/`, `substrate/`) reached from a
   script, unless separately analysed.
5. Seeds consumed by CONSECUTIVE draws from one generator — `default_rng(S)`
   burns an unbounded stream downstream of S; the ledger's unit is the SEED
   INTEGER, and that is what I measure. A rung reserving 1000 integers and
   seeding once at the base draws ONE seed by this measure.
6. Non-Python seeds (shell scripts, Rust, notebooks).
7. Any expression whose abstract value exceeds an enumeration cap.

**Item 5 is the most important limit and I flag it now: it is a definitional
choice, not an oversight.** If the project's intent is "a block reserves an
integer range", measuring integers is right. Both readings are reported.

## 5. The gate to leave behind

A one-line, cheap assertion that **declared ⊇ measured**, runnable at
PRE-REGISTRATION time by a future rung, with a positive control proving it can
fail. That check, existing earlier, would have caught the K-arm collision
before the rung ran rather than at its end.

## 6. Protocol compliance

- §3 this document committed before any headline.
- §5 no metric surgery: the three mismatch classes are FIXED here and will not
  be redefined after seeing results.
- §7 negatives reported.
- §8 bounds on every claim.
- §12.3 provenance claims pinned to BOTH endpoints, never `HEAD`
  (`tests/test_provenance_endpoint_guard_migrated.py` fails any range ending
  at HEAD).
- Provenance gate run as its OWN step BEFORE any number.
- Oracle `bash scripts/rung7_vision_bench.sh` reported with the `data/`
  condition stated.
- I do NOT edit `VISION_PROTOCOL.md` (§11) — I am auditing it. The supervisor
  amends.

## 7. Blast radius scope (§8)

Phase 3 runs ONLY for genuine collisions. For each, I state whether any landed
result depended on the independence it breaks (control arm sharing a seed with
its test arm; a "replication" reusing the original's seed). **I name the
exposure and stop — I do not re-litigate those rungs.**
