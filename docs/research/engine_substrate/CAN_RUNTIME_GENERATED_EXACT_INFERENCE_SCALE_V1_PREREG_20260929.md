# Runtime-generated exact-inference scale v1 preregistration (2026-09-29)

## Question

How do post-closure exact CAN inference time and Python allocation scale with runtime-extracted graph size for two low-width topologies and two discrete vocabularies?

## Design

Run fresh-process workers for N in {32,64,128,256}, topology in {path, banded2}, discrete mode in {2state,3state}, and three deterministic replicates per cell (48 workers). `path` contains edges (i,i+1); `banded2` also contains (i,i+2). Factors and fields are seeded and quantized identically across paired topologies. The worker builds the model in native graph storage, settles with the current native CAN rules to a fixed point, extracts the live CAN network, then runs min-fill and exact junction-tree MAP without committing state.

An independently implemented explicit factor-table variable-elimination routine, using natural live-node order rather than the solver's min-fill order, supplies the oracle energy. The model objective is independently rescored from the returned state. Record closure, extraction, ordering, JT, and oracle time; per-call Python `tracemalloc`; process high-water RSS; node/edge counts; width; and oracle operation count.

## Integrity gates

Require 48 fresh worker PIDs and complete cell coverage; exact expected graph sizes and pair counts; native rule closure under the fixed cap and a zero-work terminal probe; extracted factors equal the deterministic fixture; min-fill upper bound at most 2; JT and independently rescored energies match the oracle within 1e-7; valid state vocabulary; no graph/model mutation; and pre/post source/native lock equality. Performance has no pass threshold.

## Scope

These are authored synthetic path/banded graphs assembled in native graph storage, settled by the native rule engine, and then extracted at runtime. They isolate low-width inference scaling over N=32–256 and vocabulary size 2/3. They do not estimate natural task topology, learned frame discovery, general inference performance, or 10^7-node capability. Process RSS is a whole-worker high-water mark; `tracemalloc` covers Python allocations only.

## Reproduction

```sh
python3 evaluation/substrate_capability/can_runtime_generated_exact_inference_scale_v1.py --lock
python3 evaluation/substrate_capability/can_runtime_generated_exact_inference_scale_v1.py
```
