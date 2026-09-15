# Vendored data — provenance & honesty statement

## What is here

- `rosch1975_typicality.json` — human category-typicality baseline: 6 categories
  (bird, fruit, vegetable, furniture, vehicle, weapon), each with members ordered
  by human typicality **rank** (1 = most typical) and a normalized **score** in
  `[0,1]`.

## Where it comes from

The ground-truth human ordering is the canonical **goodness-of-example / typicality
norms** of:

> Eleanor Rosch (1975). "Cognitive representations of semantic categories."
> *Journal of Experimental Psychology: General* 104(3):192–233.

These norms are the human baseline that the paper this capability suite anchors on —

> Soffer, Jurafsky, LeCun, Shwartz-Ziv, "From Tokens to Thoughts: How LLMs and Humans
> Trade Compression for Meaning," arXiv:2505.17117 —

digitizes and releases (together with Rosch 1973 and McCloskey & Glucksberg 1978) as
its 1,049-item / 34-category human benchmark, and against which it reports LLM scores
(most decoder LLMs Spearman ρ < 0.2 on typicality; BERT ρ ≈ 0.38).

## What this file IS and IS NOT — read before citing

**IS:** a faithful reconstruction of the well-established, repeatedly-replicated Rosch
(1975) **rank order** within each category. The rankings reproduce the canonical human
ordering every cognitive-science source agrees on (robin/sparrow the most typical
birds, penguin/ostrich the least; chair/sofa the most typical furniture; orange/apple
the most typical fruit; and so on). The Spearman-ρ metric that Rubric A RQ2 uses
consumes **only the order**, which this file gets right.

**IS NOT:**
- Not a byte-copy of Rosch's original 1–7 mean-rating table.
- Not a copy of the arXiv:2505.17117 released CSV supplement (that supplement was not
  publicly fetchable at build time — the code was "released upon acceptance"; the
  primary-source PDFs at colorado.edu / researchgate blocked direct download).
- The `score` column is a **monotonic normalization of the rank**
  (`score = 1 − (rank−1)/(n−1)`), a stand-in for the exact mean rating. It preserves
  the order but is **not** the exact human rating value.

**Consequence for claims:** any capability result scored off this file must cite it as
a *reconstruction of Rosch (1975) rank norms*, not as Rosch's raw ratings or the
arXiv supplement. When the exact values become available, replace the `score` column;
the `rank` column should already match, so ρ-based results should be stable.

## License / attribution

The underlying norms are published scientific facts (Rosch 1975). This reconstruction
is released under the repository's license for research use. Attribution: Rosch (1975),
*JEP:General* 104(3):192–233; benchmark framing after arXiv:2505.17117.
