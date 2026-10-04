# Mary’s Room: red–green identification and quale compression — RESULTS

Preregistration v1 and runner were committed at `96ca4dbd`. Before its run, an
amendment was committed at `619fa8db`: the first plan had one retinal column per
color and repeated the two readouts in the compression adapter. That v1 result is
preserved at `results/marys_room_red_green_v1.json`. The amended v2 uses 12
independently computed red retinal columns and 12 green retinal columns in one
photon-eye exposure. Runner: `scripts/marys_room_red_green.py`.

## v2 result

- **Research-only identification:** 2/2 correct. The CIE 2006 standard-observer
  LMS values predict positive `L-M` for 610 nm red and negative `L-M` for 530 nm
  green.
- **Eye identification after release:** 24/24 retinal columns correct: 12/12
  red outputs have positive red–green signal, and 12/12 green outputs have
  negative signal.
- **Research-to-eye direction match:** mean **99.90/100** across red and green;
  angular mismatch is **2.86°** for red and **4.19°** for green.
- **Qualia-space category readout:** from each 24-observation field, the graph
  mints two `ColourCategory` prototypes with 12 members each. Their signatures
  expose the opponent coordinates as `attr:crg` and `attr:cby`.
- **Declared MDL code cost:** both fields reduce from 48 raw two-axis coordinate
  units (`N*d = 24*2`) to 28 category-plus-label units (`k*d+N = 2*2+24`):
  **1.714× compression**, or 41.7% fewer units under this code.

Engine provenance: `b6a41e3bbba6` in the isolated worktree. Raw v2 output:
`results/marys_room_red_green.json`.

## Interpretation

For this defined pair, Mary’s research-based physical model identifies red and
green without visual exposure, and the eye’s post-release signals support the
same labels. The retinal opponent vectors closely follow the research standard.
The substrate also compresses repeated two-axis signals into two prototypes
plus membership assignments. These findings support a specific computational
account: sensory color signals are physically predictable, remain useful for
discrimination, and can be represented compactly.

This does not show that Mary experiences a human red quale, because the CIE
standard-observer model is not subjective testimony and the substrate is not a
human participant. The compression number is the experiment’s declared
coordinate-code proxy, not a measured neural or thermodynamic saving. The test
supports the model-level claim; it does not prove that phenomenal experience in
general is only compression.
