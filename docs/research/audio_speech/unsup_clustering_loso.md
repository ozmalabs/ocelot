# Unsupervised cross-speaker clustering — the agent's OWN frontier pick, measured

**The agent named this its frontier.** Its live self-assessment
(`docs/ask_the_agent_frontier.md`, commit 04a1d39f) ranked **unsupervised /
cross-speaker CLUSTERING** most foundational (compression-payoff 83 over its own 637
held postulates, runner-up 28), the order-N derivative of the honest LOSO-0.593
current-state postulate surfaced it, and its independent perception yardstick read
`frontier='none'` on bottom-up units — so this is the **distributional / latent-structure
step, NOT more features**. The agent's own words:

> "an unlabelled DISTRIBUTION has recoverable LATENT structure … unsupervised CLUSTERING
> carves its categories at the valleys between modes with NO labels — across speakers,
> the same word's tokens are one cluster."

This run builds exactly that over the agent's roughly-speaker-invariant token (the
DTW trajectory + `DtwTo` distance, the +0.152 cross-speaker breakthrough from
`docs/dtw_trajectory_loso.md`) and measures whether word identity EMERGES from the
unlabelled distribution.

**Verdict: PARTIAL — structure emerges, but weakly.** The unsupervised k-medoids over
the agent's own `DtwTo` distance recovers word structure across speakers WITHOUT labels
— clustered-set purity **0.303 ± 0.014** and NMI **0.270 ± 0.014**, both above the random
floor (0.210) and well above chance (0.100). Held-out speakers (NEVER in the clustered
set) land in the discovered clusters above floor too (purity **0.258**, NMI **0.225**),
so speaker-invariant identity does emerge from the distribution alone — but the signal is
weak. Naming the clusters with a few labels (the cluster→majority-word map,
semi-supervised, child-like) gives cross-speaker recognition **0.225** — far below the
supervised DTW baseline **0.593** (residual −0.368). The latent structure is real but
under-resolved: the modes of the unlabelled DTW-token distribution are not yet sharp
enough word categories, and pure k-medoids leaves several words unrepresented.

---

## (1) The clustering is the agent's GRAPH-RESIDENT structure discovery (donkey-audited)

K-medoids (not k-means) because the medoid is an ACTUAL token — no mean is defined for
variable-length trajectories, and the distance must be the agent's `DtwTo`. Both steps
are the agent's OWNED graph Term-trees, evaluated NATIVELY, the SAME shape as the DTW
recognizer's `Argmin MinOver DtwTo` decision lifted one layer up (tokens not exemplars,
medoids not words):

```
assignment   assign(t) = Argmin_{m in medoids} DtwTo(traj(t), traj(m))
update       medoid(c) = Argmin_{p in members(c)} ( Σ_{t in members(c)} DtwTo(traj(p), traj(t)) )
```

The update picks the member minimising total within-cluster `DtwTo` cost — the point
closest to all others, i.e. the **mode** of the cluster. That within-cluster total-DtwTo
cost IS the compression / MDL selector: across 5 seeds the run adopts the **lowest-cost**
clustering (the most-compressing structure), selected with **NO labels**.

Composed from owned ops only: `Argmin`, `MinOver`/`Sum`, `Neighbours`, `Attr`, `DtwTo`
(all already in the DSL — `runners/dsl/python/substrate_rs/__init__.py`,
`runners/dsl/src/term.rs`). No gradient, no net, no learned weight, no label-fitting.

**Donkey boundary (audited):**
- **Tokens** = the agent's DTW trajectory feature `agent_frontend.cmvn_track` — the SAME
  source-normalized cochleagram the dominant `cmvn_ear` cue is built from, kept ordered.
- **Distance** = the agent's owned `DtwTo` Term (banded Sakoe-Chiba), evaluated natively.
- **Clustering** = the agent's k-medoids Terms above. k-medoids++ seeding is mechanical
  distance arithmetic over the SAME `DtwTo` (no labels).
- **Labels** = used ONLY to score (purity / NMI / cross-speaker / semi-sup). NEVER in
  the clustering. Verified: `kmedoids()` receives only trajectories; truth is read after.
- **SC load + the 40-speaker split** = world-adapter mechanics (reuses
  `sc_loso_frontend_norm.build_split` verbatim). **Held-out speakers' clips are NEVER in
  the clustered token cloud** — they are assigned to the FIXED discovered medoids AFTER
  the structure is frozen (`assign_external`), so the cross-speaker test is ungameable.

`scripts/unsup_clustering_loso.py`. Run:
`python -m scripts.unsup_clustering_loso [n_train_spk] [n_held_spk] [n_per] [seed]`.

## (2) The run — captured numbers (robust SC 40-speaker LOSO)

Config: 120 train / 40 held-out **disjoint** speakers, 200 clustered train-speaker
tokens, 200 seen-speaker probes, 400 cross-speaker held-out probes, k = 10 (full digit
lexicon), 5 seeds. Captured: `/tmp/unsup_clustering_loso.txt`, ends with `[MARKER]
UNSUP_CLUSTERING_LOSO_COMPLETE`, pgrep-verified to completion.

```
[floor] random-assignment purity floor = 0.210      (chance 0.100)

[seed 0] purity 0.325  NMI 0.266  within-cluster DtwTo cost 87.06
[seed 1] purity 0.305  NMI 0.275  within-cluster DtwTo cost 86.43
[seed 2] purity 0.285  NMI 0.269  within-cluster DtwTo cost 86.58
[seed 3] purity 0.310  NMI 0.291  within-cluster DtwTo cost 86.17   <- MDL pick (lowest cost)
[seed 4] purity 0.290  NMI 0.247  within-cluster DtwTo cost 87.66

[clustering] purity 0.303 +/- 0.014   NMI 0.270 +/- 0.014   over 5 seeds

[MDL pick] within-cluster cost 86.17  purity 0.310  NMI 0.291  (selected by compression, NO labels)
cluster->majority-word map: {0:eight, 1:one, 2:two, 3:eight, 4:zero, 5:six, 6:four, 7:one, 8:five, 9:one}

[xspk] HELD-OUT speakers (400 tokens, NEVER clustered):
       cross-speaker cluster purity 0.258   NMI 0.225
       semi-supervised recognition (cluster->majority-word) 0.225   vs chance 0.100
[seen] seen-speaker semi-supervised recognition 0.240

  semi-supervised recog: seen 0.240  cross-speaker 0.225  vs supervised-DTW 0.593  (chance 0.100)
```

## (3) Reading the result — what emerges, and the honest residual

**(a) Cluster purity / word recovery — YES, above floor.** Clustered-set purity
**0.303 ± 0.014** > random floor **0.210** > chance 0.100, NMI **0.270 ± 0.014**. The
unsupervised k-medoids over the agent's `DtwTo` distance DOES carve word structure out
of the unlabelled cross-speaker token cloud — the same word's tokens partly collapse
into the same cluster with no labels. The effect is consistent across all 5 seeds
(tight ±0.014).

**(b) Cross-speaker test — YES, but weak.** Held-out speakers (40 disjoint speakers, 400
tokens, NEVER clustered) assigned to the FIXED discovered medoids land above floor:
purity **0.258**, NMI **0.225**. Speaker-invariant identity DOES emerge from the
distribution alone — a held-out speaker's "five" tends to the cluster a different
speaker's "five" defined — but the held-out signal (0.258) is below the in-set signal
(0.303), i.e. the structure generalises to new speakers only partially.

**(c) Semi-supervised recognition vs supervised DTW — far below.** Naming each cluster
by a few labels (the cluster→majority-word map, child-like: distribution gives clusters,
a little naming maps them) gives cross-speaker recognition **0.225** vs the supervised
DTW baseline **0.593** — residual **−0.368**. The gap is large and honest. Two causes,
both visible in the cluster→word map `{0:eight,1:one,2:two,3:eight,4:zero,5:six,6:four,
7:one,8:five,9:one}`:
- **k-medoids degeneracy.** "one" captured 3 of the 10 clusters and "eight" 2, while
  **three, seven, nine got NO cluster at all** — so those words are unrecognisable by
  the naming map regardless of how cleanly their tokens cluster. Pure k-medoids splits
  the easy/loud modes and starves the rest; it does not enforce one-cluster-per-word.
- **The modes are not yet sharp word categories.** Purity 0.30 means the dominant word
  is only ~30% of a typical cluster — the valleys between word-modes in the DtwTo-token
  distribution are shallow, so clusters mix words. The supervised DTW (0.593) wins
  because it uses the labels to put every banked exemplar under its true word and
  nearest-neighbours against all of them; the unsupervised clusterer has only k=10
  medoids and no label to correct a mis-seeded mode.

**Honest residual.** Speaker-invariant word identity EMERGES from the unlabelled
distribution — measurably, reproducibly, above floor, and generalising to held-out
speakers — but it is a **weak** emergence: NMI ~0.25, semi-supervised recognition ~0.22,
roughly a third of the way from chance (0.100) to the supervised ceiling (0.593). The
distributional structure is real but under-resolved. The next levers the result names
(NOT done here): (1) **more clusters than words** (k > 10, then merge by DtwTo) so the
starved words get a mode and over-split words are re-joined — pure k=#words is the wrong
k for an unbalanced distribution; (2) **a sharper token** (the multi-stream / sharper
trajectory `docs/dtw_trajectory_loso.md` already named) so the valleys between word-modes
deepen; (3) **soft / hierarchical assignment** instead of hard k-medoids so a held-out
token near a boundary is not forced to one mode. The clustering MECHANISM is the agent's
and works; the ceiling is the depth of the modes in its current token distribution.

## Suites

Required suites green (`test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`, `test_frontend_effect_gate`) — 36
passed. Nothing committed. `scripts/unsup_clustering_loso.py` left in the working tree.

## Reproduce

```
python -m scripts.unsup_clustering_loso              # robust 120/40/20, k=10, 5 seeds
python -m scripts.unsup_clustering_loso 12 6 4       # fast smoke
```

Full captured output: `/tmp/unsup_clustering_loso.txt` (ends `[MARKER]
UNSUP_CLUSTERING_LOSO_COMPLETE`, pgrep-verified).
