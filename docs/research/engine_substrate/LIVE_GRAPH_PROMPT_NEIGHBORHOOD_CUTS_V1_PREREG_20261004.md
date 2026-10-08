# Live graph prompt-neighborhood cut measurement v1

Date: 2026-10-04

## Question

Do prompt-rooted local neighborhoods in the retained live-task graph sample
have smaller graph boundaries than degree-matched Message-rooted controls,
and how sensitive is that comparison to neighborhood radius and hub handling?

## Dataset and procedure

Use the source-locked, two-replicate harvest of five repository-authored
conversation prompts. Collapse exact duplicate graphs by the recorded
canonical graph digest, yielding one structural observation per unique graph.
Do not use the provisional ownership annotations or treat them as ground
truth.

For each inbound prompt Message, construct weakly connected graph balls at
radii 1, 2, and 3 under hub degree cutoffs 10, 100, 1000, and none. Hub
cutoffs block traversal into a node whose weak degree exceeds the cutoff, but
the crossing edge remains part of the measured cut. For each graph, select
up to 64 other Message nodes, ranked by absolute degree distance from the
prompt root, with SHA-256 tie-breaking for deterministic matching. Compute
the same neighborhood measures for prompt and controls: node count/fraction,
frontier nodes, crossing edges, distinct outside boundary nodes, crossing
edges per frame node, and the prompt's empirical percentile among controls.

The evaluator locks and hashes the source graph archive, prior path audit,
and this script before reading the data. It preserves cell-level prompt and
control measurements to permit reaggregation. No labels are adjudicated and
no engine execution or timing is part of this assay.

## Interpretation gates

Report every graph × radius × cutoff cell. Summarize medians and ranges across
the five unique graphs, but do not use the 10 worker records as independent
structural replicates because identical digests are collapsed. Treat a lower
prompt cut ratio than matched controls as evidence of local graph sparsity
around the request anchor only; require consistent direction across radii
and cutoff settings before describing the pattern as robust within this
sample. Do not infer automatic frame discovery, separator uniqueness,
treewidth, or task ownership from this comparison.

## Claim limits

The sample has five authored prompts, one structural graph per prompt, and
only degree-matched Message-root controls. Prompt-centered balls are not
learned task frames, and the measurement does not establish the cheap-cut
hypothesis for natural tasks generally. The archived graphs are large but
selected production-route samples, not a prevalence sample of the world.
