# Mary’s Room: research prediction versus experienced red (PREREGISTRATION)

## Question

How closely does a research-derived prediction of “red” match the chromatic
opponent signal emitted by the photon eye when it receives red light?

This compares a standard-observer prediction with the model eye’s output. The
CIE cone fundamentals are physiological reference data and the eye output is a
simulated retinal signal; neither is a measurement of a person’s private
phenomenal experience. The result is a chromatic representation match, not a
solution to the hard problem.

## Research reference

Use the CIE 2006 LMS cone fundamentals for a 2° standard observer, in energy
units, at 610 nm: `L=0.7057161`, `M=0.2052721`, `S=0.000008034895`. These values
are transcribed from CIE dataset CIE 170-1:2006, table 6.7
(https://cie.co.at/datatable/cie-2006-lms-cone-fundamentals-2-field-size-terms-energy).

Transform this research vector into the photon eye’s two reported opponent axes:

- `RG = L - M`
- `BY = S - 0.5*(L + M)`

The opponent formula is read from the `photon_retina` rule and is also stated in
the repository’s `seeds/vision_color.json`. Normalize the 2D vector to unit
length. This removes arbitrary overall scale while retaining hue/opponent
direction.

## Stimulus and arms

Use four independent, fresh `GraphEye(n_az=1)` instances. Send each a single
610 nm photon packet with count respectively 250, 500, 1000, and 2000. Wait for
exactly one processed exposure. No adaptation history is shared across arms.

The eye’s output for each arm is the first percept’s `(red_green, blue_yellow)`
vector. Normalize it to unit length and compare it with the CIE prediction by
cosine similarity. A zero-length output is a failed/dead arm and receives no
score.

## Primary statistic

For cosine similarity `c`, report angular mismatch `acos(c)` in degrees and a
signed-direction match score:

`score = 100 * (1 + c) / 2`

Thus identical opponent directions score 100, orthogonal directions score 50,
and opposite directions score 0. The primary summary is the mean score over all
four photon counts; report every arm and the worst-arm score. This metric is
fixed before measurement and has no fitted weights or thresholds.

## Decision/reporting

Report CIE vector, transformed research opponent vector, raw eye vectors, their
normalized forms, per-arm cosine/angle/score, mean score, worst score, and engine
provenance. This is descriptive; no pass/fail threshold is asserted because no
human matching distribution is being estimated.

## Interpretation boundary

A high score means the photon eye’s red/green and blue/yellow signal points in a
similar direction to the CIE standard-observer prediction for 610 nm. It does
not show that the two systems have the same complete color appearance, that the
eye has human cone fundamentals, or that they share phenomenal experience.

## Provenance and pilot note

The immediately preceding isolated probe at 610 nm and 1000 photons observed
`(red_green, blue_yellow)=(0.3436120168,-0.3456013062)`. This is pilot data and
is not part of the confirmatory summary. The fixed four-arm measurement begins
only after this preregistration and runner are committed.
