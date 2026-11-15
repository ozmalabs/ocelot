# Ozagia migration: fixed real-paper replay

The original 24-fragment real-paper probe was rerun through the Ocelot
compatibility facade after the implementation moved to Ozagia. The results
match the previous run: 3/24 translated and 2/24 Lean definitions accepted;
the GE theory contributed 2 translations and 1 Lean acceptance, and the arXiv
paper 1 translation and 1 Lean acceptance. The Born paper had no eligible
formal-environment fragments in this sample.

[results.json](results.json) records source hashes, selected expressions,
statuses and generated Lean paths. This is a small regression sample, not an
estimate of general mathematical understanding or proof fidelity. The arXiv
source is local and gitignored; the original baseline remains in
`../real_papers_20261115_after/`.
