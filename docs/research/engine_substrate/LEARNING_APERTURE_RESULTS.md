# THE LEARNING HALF — results (block 366500)

Pre-registration: `STRESS_COMPRESSES_APERTURE_PREREG.md` addendum, committed before
`seeds/learning_aperture_gate.json` existed (`1fc534b`), base sha `6bf8687`. Measure:
`scripts/learning_aperture_measure.py`, over the **shipped** `learning_progress_curiosity` seed,
unmodified.

**Headline: stress does not remove the learning signal. It FORGES one.** A compressed learner is
dropped from attention with exactly the profile of an item it has mastered, and nothing in the
learning pipeline can tell the two apart.

## The three arms

Same seed, same params, same item; `d1` is the dimension stress removes.

| arm | `residual` | `learning_progress` | `interest` | `attended` | `obs_established` |
|---|---|---|---|---|---|
| LEARNABLE (regulated) | 6.0 | −5.0 | 1024.0 | 1.0 | 1.0 |
| **COMPRESSED** (stressed) | **0.0** | **0.0** | **0.0** | **0.0** | **0.0** |
| **MASTERED** (regulated) | **0.0** | **0.0** | **0.0** | **0.0** | **1.0** |

All five registered predictions hold. **P2 is the finding**: COMPRESSED and MASTERED are identical
on *every* field the seed computes — `residual`, `fast_res`, `slow_res`, `learning_progress`,
`smoothed_progress`, `interest`, `attended` — and differ only in `obs_established`, which the gate
writes and **nothing in `learning_progress_curiosity` reads**.

`learning_progress` is −5.0 rather than positive on the learnable arm: the residual is still rising
over this window, so the item is mid-learning. What matters is that it is non-zero; it is reported
as measured rather than described as "progress".

## P4 — exposure is inert

| ticks | 24 | 48 | 96 | 192 |
|---|---|---|---|---|
| `max_residual` | 0.0 | 0.0 | 0.0 | 0.0 |
| `max_progress` | 0.0 | 0.0 | 0.0 | 0.0 |

Eight times the exposure changes nothing, matching the manifold half. A gain is a thing more
exposure overcomes; an aperture is not.

## Why this is the same defect one layer up

`loss` and `information_loss` were the same number at the manifold until two rungs ago — *left the
tube* and *could not be assessed* were indistinguishable. Here, in a shipped seed, **residual-zero-
because-mastered and residual-zero-because-blind are the same number today.** Third occurrence of
one shape, and the first found in code that was already in service rather than in code written to
test the idea.

The consequence is worse here than at the manifold, because the collapse is not merely uninformative
— it is actively misdirecting. A zero residual does not read as "no information". It reads as
**success**, and drives the curiosity gate to *withdraw attention*. An agent under stress therefore
stops attending to exactly the things it has gone blind to, and its own learning signal reports that
it has mastered them.

**Fixed below**, in `learning_progress_curiosity` v1.1.0. The table above is the defect as measured
in v1.0.0 and is retained as the before-state.

## A confound caught before it was reported

The first run of this measurement was wrong and would have produced the same headline table. The
gate's guard compared `obs` to its gated value; in the compressed arm the gated value is `held`,
which already equalled `obs`'s initial value, so **the rule never fired** and the residual-zero
result reproduced with no gate present at all. `obs_established` came back `1.0` — the witness that
exposed it.

The guard now covers both outputs, and `test_the_gate_actually_fires` asserts the witness
specifically, so a regression cannot make the suite pass while measuring nothing. A second, smaller
instance of the same class: this file's first version copied a `matplotlib` optional-dependency skip
from the sibling suite, which silently skipped the entire file — the measure imports numpy, not
matplotlib.

Gates: `tests/test_learning_aperture_migrated.py` 9/9.

## THE FIX — `learning_progress_curiosity` v1.1.0, two guards

An observation that did not arrive must not enter the chain that produces a mastery verdict. Two
rules now carry an assessability guard, and **only two**:

* `lp_residual` — an unassessable tick writes no residual, so a zero is never *fabricated* from an
  observation that never came;
* `lp_interest` — interest does not decay on a tick that established nothing. Decay asserts *"this
  item has stopped repaying attention"*, which such a tick cannot support.

**Polarity is load-bearing.** The flag is `obs_unassessable == 1`, the MARKED case — not a positive
`established` flag. An absent numeric attr compares EQUAL to `0.0` in this engine, so a positive flag
would read as *unestablished* on every item that never heard of it, i.e. every existing caller. Absent
means assessable, and byte-identity is preserved.

Measured after:

| arm | `residual` | `progress` | `interest` | `attended` |
|---|---|---|---|---|
| LEARNABLE | 6.0 | −5.0 | 1024.0 | 1.0 |
| **COMPRESSED** | 0.0 | 0.0 | **1024.0** | **1.0** |
| MASTERED | 0.0 | 0.0 | 0.0 | 0.0 |
| **GOES_BLIND** (learns 12 ticks, then compressed) | **3.0 — preserved** | −5.0 | 256.0 | 1.0 |

Blindness and mastery are now distinguishable, and an agent that goes blind mid-learning **keeps what
it established** instead of having it overwritten with zero.

### What mutation testing removed, and it was most of what I wrote

The first version of this fix had **six** guards and a new rule. Mutation testing dismantled it:

* **`lp_hold_unassessable` — DELETED.** A new rule freezing the interest clock, justified in its own
  comment by a delayed-decay failure that *does not occur*: traced with and without it across a blind
  window and a reopening, the interest and residual series are **byte-identical**. The rationale was
  plausible and confabulated.
* **Guards on `lp_fast`, `lp_slow`, `lp_progress`, `lp_gate` — REMOVED.** With `lp_residual` guarded
  the residual is frozen and these recompute to the same values from it. Identical over a 68-tick
  blind period, guarded or not.
* **The measurement itself was reproducing the defect.** Every original arm started from a zero
  residual, so a *fabricated* zero and a *preserved* zero were the same number — the exact collapse
  under test, inside the instrument. Dropping the pipeline guards changed nothing until the
  `GOES_BLIND` arm existed. That arm is why any guard here is falsifiable at all.

Final mutation state: unguarding `lp_residual` fails 1 test, unguarding `lp_interest` fails 3. No
surviving change is undetectable.

### Regression on the shipped seed

`scripts/learning_progress_measure.py`'s full criteria set — G1 noisy-TV, G2 leave-the-unresolved,
G3 commit-net, G4 integer-native / default-off byte-identity / source audit — is **identical before
and after**, all 15 true. Run directly with figure rendering stubbed (it needs `matplotlib`, absent
here; the criteria do not).

## Honest bounds

One item, one dimension, deterministic arms, n=1, no CI. The compression is **stipulated**, as in the
manifold half: nothing explains why stress should remove `d1`, the fixture supplies that. What is
demonstrated is that the affect gate and the shipped curiosity pipeline **compose**, and that the
composition exposes a live collapse in the pipeline's own signal.

`ever_attended` is 1.0 in all three arms and is not a discriminator: `interest` initialises at 1024,
so every item attends on the first tick before anything decays. Reported so the column is not read
as evidence.
