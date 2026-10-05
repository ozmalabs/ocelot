# Mary's Room: quale-level access only — EXPLORATORY

Status: post-hoc and exploratory, not preregistered. No eye was built and no frozen
file changed. This corrects `marys-room-model-vs-know-exploratory.md`, which let
Mary read her own (RG, BY) values as numbers. Script:
`scripts/marys_room_quale_access.py`. Output:
`results/marys_room_quale_access_exploratory.json`. The prior is the same
population prior used there.

## What reaches cognition

Mary never reads coordinates. She reports only on her qualia:

- **Sign:** whether a light looks reddish or greenish, bluish or yellowish.
  Modelled as a probit on the opponent sign with internal noise 0.005.
- **Null:** the wavelength dial setting at which a light looks neither reddish nor
  greenish (unique yellow), or neither bluish nor yellowish. Setting SD 2 nm, at
  three intensities.
- **Match:** the dial settings at which two lights look the same.
  - Rayleigh-type: 545 + 670 nm mixture against 589 nm.
  - Moreland-type: 440 + 520 nm mixture against 480 nm.
  - Brightness matches between whites.
  - Ratio SD 0.01; intensity SD 0.01 log units.

The dial readings are numbers on the apparatus, not on her eye. This is how human
cone fundamentals were actually measured.

## Information gained (local Fisher, population prior)

| Access | Bits | RG-zero SD (prior 0.86 nm) |
|---|---|---|
| Room, E light + eyelid: sign reports | 2.6 | 0.86 |
| Room, E/D65/A + eyelid: sign reports + white brightness matches | 4.4 | 0.81 |
| Release: sign reports on 93 monochromatic lights | 4.9 | 0.79 |
| Release: unique-yellow null (3 settings) | 0.8 | 0.77 |
| Release: four nulls/matches, one setting each | 11.6 | 0.60 |
| All of the above | 14.9 | 0.51 |
| Four tasks × 10 / × 100 repeats | 18.2 / 26.7 | 0.30 / 0.12 |
| Numeric read-out (previous analysis), room + release | 37.6 | 0.08 |

## Findings

1. **Quale access carries far less about the eye than numeric access.** Inside the
   room, sign reports give 3–4 bits, against 17–23 bits with numeric read-out.
   That is mostly half-saturation and some L/M bandwidth. Where her cones sit
   stays at prior uncertainty. Release with signs alone adds about 5 bits. Even
   with four classic matching and nulling tasks, she reaches only 15 bits, and
   needs about 100 repeats of each task to approach the numeric read-out's
   precision on the zero.
2. **The first null is a surprise, not a refinement.** Her self-model predicts
   unique yellow at 538.3 ± 2.4 nm (prior predictive, including setting noise).
   Her actual setting is 547.85 nm, z = 4.0 (2.5 under the broad prior). The local
   Fisher bits (0.8) understate this: they assume her prior is right. What the
   first exposure tells her is mainly that her self-model is wrong.
3. **Relational quale data cannot tell red from green inside her eye.** Swapping
   her L and M cones leaves every null and match setting identical (max
   difference 0.0). All four tasks are symmetric in L and M. The swap flips the
   sign of every red–green signal, and the frozen decoder's labels agree on only
   9.9% of held-out stimuli. From nulls and matches alone, a red–green inverted
   Mary is indistinguishable. Only sign reports tied to public labels break the
   symmetry: "this is the quale I get from what everyone calls red light". That
   tie is an edge from quale to concept, made by co-occurring with labelled
   stimuli, not something the quale itself contains.
4. **Nonlinear self-fits from quale tasks failed.** MAP fits to the four tasks
   (1, 10 and 100 repeats; both priors) did not recover the eye. Held-out angle
   errors were 4.5–29°. Several fits landed on the L/M-swapped mode or on
   bandwidth–centre ridges. One fit got the zero right (547.80 nm) with L and M
   exchanged, so its decoder agreement was 0.11. The local Fisher figures above
   therefore overstate what she can actually work out.

## Bearing on the claim

With access limited to qualia, Mary's exposure tells her much less about her eye
than numeric read-out would. What it does tell her arrives first as a large
surprise against her self-model, and then slowly. Which of her qualia is "red"
is not fixed by any relational quale data. It is fixed by linking the quale to
publicly labelled light. In this model, qualia are a lossy, relational format
that hides the coordinates and an L/M inversion. They do not hide the boundary
facts (nulls, matches), which carry structured, physical information.
