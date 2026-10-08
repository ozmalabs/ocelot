# Synthetic structural census pilot

**Status:** exploratory structural-measurement pilot; not evidence that natural task graphs have cheap cuts or that partitioned execution preserves behavior.

## Question and method

Do independently measured treewidth and hierarchical separator statistics distinguish known sparse/decomposable graph families from dense or shuffled controls? The pilot measured six graph families (path, banded DAG, complete DAG, star, modular chain, and seeded sparse random) at n=8, 16, 32, and 64: 24 graph inputs. It computed exact treewidth on the undirected simple projection at n=8 and deterministic min-fill upper bounds at all sizes. For each input it recursively bisected node groups into leaf frames of at most eight nodes, once in ID-contiguous order and five times after fixed-seed shuffles. It recorded cross-frame edges, cut-boundary vertices, leaf apertures, hierarchy depth, and partition construction time.

Definitions and every per-cut/per-frame row are in the [raw census](../../../evaluation/reports/substrate_structural_census_pilot_20260924.json). The generator uses the existing [`graph_treewidth.py`](../../../domains/graph_treewidth.py) exact and min-fill routines; rerun from the repository root with `PYTHONPATH=. python3 scripts/substrate_structural_census_pilot.py`.

## Results at n=64

For each family, “contiguous” is the ID-ordered hierarchy. “Shuffled median” is the median of five fixed-seed permutations. “Max cut boundary” is the largest number of distinct endpoints at any binary hierarchy cut; leaf aperture is the largest number of within-frame vertices touching another leaf frame.

| Family | Edges | Treewidth upper bound | Contiguous cross-frame edges | Shuffled median cross-frame edges | Contiguous max cut boundary | Shuffled median max cut boundary | Contiguous leaf aperture max |
|---|---:|---:|---:|---:|---:|---:|---:|
| Path | 63 | 1 | 7 | 54 | 2 | 53 | 2 |
| Banded DAG | 125 | 2 | 21 | 111 | 4 | 62 | 4 |
| Complete DAG | 2,016 | 63 | 1,792 | 1,792 | 64 | 64 | 8 |
| Star | 63 | 1 | 56 | 56 | 33 | 33 | 8 |
| Modular chain | 126 | 3 | 14 | 111 | 3 | 61 | 3 |
| Sparse random | 99 | 9 | 87 | 87 | 51 | 47 | 8 |

The ID-contiguous partition makes the designed locality of paths, banded graphs, and modular chains visible: their maximum cut boundaries remain 2, 4, and 3 at n=64, while shuffled median maxima are 53, 62, and 61. The complete graph remains high-boundary under every partition. The sparse random family is not well described by edge density alone: it has only 99 edges but a min-fill width upper bound of 9 and large cut boundaries under both partition arms.

The star is a useful counterexample to treating treewidth and a balanced disjoint-frame cut as interchangeable. It has treewidth 1, but a balanced top-level split leaves about half the leaves on one side of the central vertex, so the combined cut boundary is 33 vertices at n=64. A separator decomposition that permits a shared articulation separator may represent it better; that is a different frame definition and must be specified before claiming a small aperture. Leaf aperture is capped in part by the chosen frame size 8, so it cannot be read as a scale-free property.

At n=8, the leaf-size rule yields one frame and therefore no inter-frame boundary; those records only inform exact treewidth and decomposition overhead. At n>10, reported treewidth is a valid min-fill upper bound, not the exact minimum. The ID-contiguous partition is deliberately favorable for ordered synthetic families, while shuffling is a baseline, not an optimizer.

## Limits and next gate

This census measures the undirected graph projection of synthetic graphs. It does not include rule-body hyperedges, read/write dependencies, learned frames, natural task snapshots, dynamic updates, or the cost of validating a cut semantically. The shuffled baseline is not an optimal partition; the measured gap establishes that node organization matters on these generated families, not that the engine discovers the useful order. Reported partition-construction timings are diagnostic micro-measures and need repetitions before comparison.

Next structural gate: freeze representative graph snapshots from at least two real substrate workload families, extract dependency graphs from actual active execution paths, compare authored/learned cuts against min-fill and a balanced baseline, and perturb cuts while checking partitioned results against monolithic execution. Include articulation-aware separator decomposition and a leaf-size sensitivity sweep. If the engine cannot produce or validate the candidate frames, treat this as a structural census only, not evidence for frame-local inference or rule closure.
