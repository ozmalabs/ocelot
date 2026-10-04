# Mary’s Room: research prediction versus experienced red — RESULTS

Preregistration and runner were committed before measurement at `2d7d5886`.
Runner: `scripts/marys_room_red_match.py`.

## Result

The CIE 2006 2° standard-observer cone vector for 610 nm is
`(L,M,S)=(0.7057161, 0.2052721, 0.000008034895)`. Transforming it through the
photon eye’s opponent axes gives research prediction `(RG,BY)=(0.500444,
-0.4554861)`, normalized `(0.739545,-0.673107)`.

The photon eye received a 610 nm packet at four photon counts. All four arms
were live. Mean directional match was **99.79/100**; worst-arm match was
**99.33/100**. The corresponding angular mismatch ranged from **1.12° to
9.42°** (mean **4.18°**).

| photons | eye opponent `(RG,BY)` | angular mismatch | direction score |
|---:|---:|---:|---:|
| 250 | `(0.161417,-0.130670)` | 3.32° | 99.92 |
| 500 | `(0.253821,-0.222078)` | 1.12° | 99.99 |
| 1000 | `(0.343612,-0.345601)` | 2.86° | 99.94 |
| 2000 | `(0.385837,-0.489044)` | 9.42° | 99.33 |

The score is `100*(1+cosine)/2` after unit-normalizing the two opponent
vectors. It measures hue/opponent-direction agreement and deliberately removes
overall response magnitude.

## Interpretation and limits

This is the useful comparison: a research-derived standard-observer prediction
for a defined red stimulus versus the actual opponent vector produced by the
photon eye’s graph pipeline. On the red–green / blue–yellow plane, the directions
match very closely across the tested intensities.

It is **not** a 99.79% match of complete qualia or of human subjective
experience. CIE cone fundamentals are a standard-observer physiological model,
not a report of what red feels like. The graph eye uses its own approximate
Gaussian receptor sensitivities and adaptation, not the CIE fundamentals; the
run tests the opponent direction they produce. The complete qualia system has
more than this two-axis color signal, and this run does not claim to compare all
of those dimensions.

Engine provenance: `b6a41e3bbba6` in the isolated worktree. Raw measurements:
`results/marys_room_red_match.json`.
