# Full-seed GenInfer and generator mint measurement

**Run date:** 2026-09-26  
**Engine:** `24073a9be843`  
**Evidence grade:** current-source full-seed experiment; all six registered gates pass  
**Status:** exact bounded 2-D integer-linear discovery path is demonstrated; general learning tractability remains open.

## Method

The runner boots the normal core and installs `seeds/shape_decode_loop.json` through the production reflective-faculty path. It uses one asymmetric four-cell L signature, an integer 2-D coordinate frame, and the existing seed's switch for generator induction. Each arm evaluates the full rule closure rather than calling `GenInfer` alone. Controls include held-out maps, a six-member orbit, fixed seeded value substitutions, a held rotation, a downstream new member, and a nonlinear warp. The runner measured 15.629 seconds for the complete experiment body, across all arms including 400 fresh-core noise controls. This excludes Python interpreter/module startup, and the script does not separately time individual cases or measure memory.

The measurement gate was run with:

```sh
GENMINT_OUTPUT=/absolute/path/evaluation/reports/substrate_genmint_measurement_YYYYMMDD.json \
PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_measure.py
python3 scripts/analyze_substrate_genmint_measurement_v1.py
```

The runner stores SHA-256 hashes for itself, the seed, relevant Python orchestration, Rust Term implementations, build manifest, and loaded native library. The independent analyzer checks these hashes and recomputes the registered outcome assertions from the raw JSON. The preserved capture is [`raw report`](../../../evaluation/reports/substrate_genmint_measurement_20260926.json); its [`independent analysis`](../../../evaluation/reports/substrate_genmint_measurement_analysis_20260926.json) passes all nine checks.

## Results

- **Held-out discovery:** three maps—`[1,0,1,1]`, `[1,1,0,1]`, and `[2,1,1,1]`—each produce the correct distinct `DimensionGenerator`, zero `CapabilityAxis` minting, and `recognized_transformed` status.
- **Orbit reuse:** six successive powers of one shear are recognized after one generator mint. With GenInfer disabled, the same sequence mints six quanta. The runner's declared description-length proxy falls from 24 to 12 tokens (2× compression).
- **Fixed null family:** across 400 deterministic color assignments (seeds 25,000–25,399), the full seed mints zero linear generators. This supports the finite control only; it does not establish incompressibility or general false-positive rates.
- **Occam control:** a held rotation is recognized with no newly induced linear generator and no quantum.
- **Downstream effect:** after a generator is learned, an unseen second orbit member is `recognized_transformed`; with induction disabled, that same member is `minted` as a quantum.
- **Class boundary:** a quadratic coordinate warp produces no linear generator and falls through to one quantum.

## Interpretation and limits

This is stronger than a primitive-level GenInfer probe: the full authored seed performs recognition, generator acquisition, graph storage, and later reuse. It establishes a successful capability in a deliberately constructed 2-D integer-linear family and a finite set of negative/held-out controls. The MDL proxy is the runner's chosen token accounting, not a learned or calibrated universal description-length measure.

The 400 nulls share one shape, coordinate frame, and color-substitution mechanism; they are not independent samples of natural tasks. The three positive generators and six-member orbit are authored to match the inducer's class. The result therefore does not estimate natural residual frequency, generalization outside the seed's model family, scaling with graph size or dimension, CPU time per inference, memory, or the expense of acquiring more expressive hypothesis classes. Automatic seed-driven minting is now covered; detailed trace attribution of the follow-on decode and robust runtime scaling remain open.

## Reproduction artifacts

- Runner: [`genmint_measure.py`](../../../scripts/genmint_measure.py)
- Independent analyzer: [`analyze_substrate_genmint_measurement_v1.py`](../../../scripts/analyze_substrate_genmint_measurement_v1.py)
- Raw capture: [`substrate_genmint_measurement_20260926.json`](../../../evaluation/reports/substrate_genmint_measurement_20260926.json)
- Analysis: [`substrate_genmint_measurement_analysis_20260926.json`](../../../evaluation/reports/substrate_genmint_measurement_analysis_20260926.json)
- Seeded rule system: [`shape_decode_loop.json`](../../../seeds/shape_decode_loop.json)
