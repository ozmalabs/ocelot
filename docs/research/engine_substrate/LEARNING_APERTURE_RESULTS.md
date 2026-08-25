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

**This document does not fix that.** `obs_established` exists only because the gate writes it. Making
the pipeline read it — so that an unestablished observation cannot decay interest — is a change to
`learning_progress_curiosity` and is not made here.

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

## Honest bounds

One item, one dimension, deterministic arms, n=1, no CI. The compression is **stipulated**, as in the
manifold half: nothing explains why stress should remove `d1`, the fixture supplies that. What is
demonstrated is that the affect gate and the shipped curiosity pipeline **compose**, and that the
composition exposes a live collapse in the pipeline's own signal.

`ever_attended` is 1.0 in all three arms and is not a discriminator: `interest` initialises at 1024,
so every item attends on the first tick before anything decays. Reported so the column is not read
as evidence.
