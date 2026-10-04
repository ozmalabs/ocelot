# Mary’s Room: red–green identification and quale compression (PREREGISTRATION)

## Question

With CIE standard-observer research held before exposure, can Mary classify a
fixed red/green pair, and how closely do the photon eye’s experienced opponent
signals match those research predictions? Does the shared color-identity loop
compress each two-axis field into a small category codebook?

This is a system experiment. “Experienced” means the current photon eye’s
computed retinal opponent signal. It is not a direct measure of phenomenal
experience. Classification success tests whether sensory exposure is needed for
this narrow discrimination; category compression tests a property of the
implemented representation.

## Research facts and fixed stimuli

Use the CIE 2006 LMS cone fundamentals for a 2° standard observer in energy
units, from CIE 170-1:2006 table 6.7:

- red stimulus: 610 nm, `(L,M,S)=(0.7057161, 0.2052721, 0.000008034895)`;
- green stimulus: 530 nm, `(L,M,S)=(0.7706373, 0.9356857, 0.01260114)`.

Source: https://cie.co.at/datatable/cie-2006-lms-cone-fundamentals-2-field-size-terms-energy

For both research prediction and photon-eye output, use the eye’s opponent axes:

- `RG = L-M` (for eye output, read `red_green`);
- `BY = S-0.5*(L+M)` (for eye output, read `blue_yellow`).

The theory-only classifier predicts **red iff RG > 0**, **green iff RG < 0**.
This fixed sign rule follows the named red–green opponent axis; there is no fit
on the eye data. Both test stimuli have nonzero RG under the CIE reference.

## Confirmatory photon-eye arm

**Amendment v2:** the initial preregistered plan used `GraphEye(n_az=2)` and one
retinal column per color. Review showed this could classify the pair but would
not supply a populated experienced field for the compression measurement. The
v1 run is preserved in `results/marys_room_red_green_v1.json`; its quantizer
compression repeats the same two returned vectors in the adapter and is not
counted as compression of a populated sensory field.

The v2 confirmatory apparatus is one fresh `GraphEye(n_az=24)`. Submit one
simultaneous exposure: columns 0–11 each receive 1000 photons at 610 nm; columns
12–23 each receive 1000 photons at 530 nm. Wait for one completed exposure and
read all 24 `VisionPercept` outputs. No labels are inserted into the eye graph.
Keep the column-to-stimulus mapping in the external scoring record only.

## Representation and compression arms

Separately process the two research vectors and the 24 eye-produced vectors
through the committed `vision_colour_identity` graph rules. Each vector is
mechanically encoded as a cone triple whose opponent transform reproduces
`(RG,BY)` exactly; this is a reversible coordinate adapter, not a classifier.
For research, replicate each standard-observer prediction across its 12 fixed
retinal positions. For the eye arm, use the 24 actual column outputs from the
single exposure. Labels are not inserted into graph nodes.

For each source (research and eye), the graph should mint two categories and
assign all 24 observations. The code-length proxy is the existing two-axis MDL
accounting: raw cost `N*d`; categorized cost `k*d+N`, with `N=24`, `d=2`, and
`k` read from the minted codebook. Report both costs and their ratio. This measures
compression under this declared code, not thermodynamic or brain-energy savings.

## Primary outputs and criteria

Report, without threshold-based pass claims:

1. Mary’s research-only red/green predictions and accuracy (2 items).
2. Photon-eye opponent vectors, predicted labels, and accuracy (2 items).
3. Per-color cosine direction match and angular mismatch between CIE and eye
   opponent vectors.
4. Research and eye category prototypes/signatures, mint counts, and MDL costs.
5. Cross-source prototype alignment per color using the same cosine/angle metric.
6. Engine provenance and all raw values.

A dead eye arm or missing/duplicate category remains a measured failure and is
reported; do not change the stimulus, sign rule, or cost model after seeing it.
The v2 eye-arm category count and member counts must be derived from the actual
24-column outputs. No adapter-side duplication is permitted.

## Interpretation boundary

If research-only and eye classifications both succeed, Mary can identify this
red/green pair before release using the declared physical knowledge. If the eye
signals also align with the research vectors and graph categories compress both
fields, that supports the narrower computational claim that the model carries
research-predictable color structure in a compressed sensory representation.
It does not establish that the sensory representation is a human quale, nor that
all qualia are reducible to compression.

## Pilot and run discipline

A pilot before v1 used one eye with simultaneous 610 nm red and 530 nm green
packets at 1000 photons. It returned red `(0.3436120,-0.3456013)` and green
`(-0.0753723,-0.6214368)`, with the expected opposite RG signs. The v1 result is
preserved separately and is not substituted for v2. The v2 amendment and updated
runner must be committed before its confirmatory invocation. The runner must pass
engine provenance before measuring.
