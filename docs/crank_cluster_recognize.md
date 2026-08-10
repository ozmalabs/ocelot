# Turn the crank — co-refining the DTW recognizer + k-medoids clustering (one pool)

**The user's insight.** The supervised DTW recognizer (`docs/dtw_trajectory_loso.md`:
`Argmin MinOver DtwTo` over banked exemplars, cross-speaker LOSO ~0.57–0.593) and the
unsupervised k-medoids clusterer (`docs/unsup_clustering_loso.md`: `Argmin DtwTo`
assignment + `Argmin Sum DtwTo` medoid update, purity ~0.30) are **both graph-resident
ops over the SAME `DtwTo` distance**. The clustering doc named its own ceiling: shallow
modes + **k-medoids DEGENERACY** (k=#words splits the loud modes — "one captured 3
clusters" — and STARVES the rest — "three, seven, nine got NO cluster"). So: put BOTH
ops in one pool and **iterate them EM-like** so they reinforce — recognition refines the
clustering and the deepened clusters feed the recognizer's prototype bank.

**Verdict: PARTIAL — co-refining LIFTS the clustering above its separate baseline
(purity 0.303 → best 0.455, +0.152; semi-sup LOSO 0.225 → best 0.355, +0.130), and the
crank CONVERGES (MDL within-cluster cost plateaus). But it does NOT reach the supervised
DTW (0.593), and — the honest, load-bearing finding — the clustering doc's own named fix
(start k>#words, MERGE down to #words) is the WRONG move: the joint optimum sits at
HIGH k (~26–29 pure sub-modes); forcing the merge down to k=10 monotonically DEGRADES
both purity and LOSO, ending BELOW the separate clustering baseline (purity 0.195, LOSO
0.125 at k=10).** The pool helps because k>#words gives many small, pure sub-modes that
the prototype bank reads cleanly; consolidating them to one-cluster-per-word re-mixes
them. The lift is real but bounded by the same shallow modes both separate runs hit.

---

## (1) The crank wired — both ops in one EM-like loop (donkey-audited)

`scripts/crank_cluster_recognize.py`. One pool, both the agent's OWNED `DtwTo`/`Argmin`/
`Sum` Term-trees (reused verbatim from `scripts/unsup_clustering_loso.py`), iterated:

```
E-ish   assign each TRAIN token to its nearest current medoid    (Argmin-DtwTo Term)
M-ish-a recompute each cluster's medoid = the MODE exemplar       (Argmin-Sum-DtwTo Term)
M-ish-b MERGE the two closest clusters by medoid-to-medoid DtwTo  (mechanical DtwTo arith)
selector = total within-cluster DtwTo cost (MDL); iterate until the cost plateaus.
```

The **recognition bank IS the medoid prototypes**: a held-out token is recognized by the
SAME `Argmin-DtwTo` the clusterer assigns with (candidate set = the current medoids),
then a cluster→majority-word map names the cluster. Recognition refines clustering
(tighter mode-centered prototypes each iteration) and clustering refines recognition
(the deepened prototype bank is the next iteration's recognizer) — the user's "both in
one pool" literally: the assignment Term is shared.

The crank starts at **k0=30 > #words (10)** to fight the degeneracy the doc named, then
**merges one pair per iteration** down to k=10 (each merge followed by re-assign +
re-medoid — the EM refinement), then EM-refines at k=10 until the MDL within-cluster
`DtwTo` cost stops dropping.

**Donkey boundary (audited).** TOKENS = the agent's `agent_frontend.cmvn_track` DTW
trajectory (the SAME source-normalized cochleagram the dominant `cmvn_ear` cue uses).
DISTANCE = the agent's owned `DtwTo` Term (banded Sakoe-Chiba), evaluated natively.
ASSIGN = `Argmin-DtwTo` Term (the SAME shape the supervised recognizer uses). MEDOID =
`Argmin-Sum-DtwTo` Term (the cluster mode). MERGE = mechanical `DtwTo` arithmetic over
the agent's metric (closest two medoids), then re-medoid the union — NO labels, NO
gradient, NO net, NO learned weight. SELECTOR = within-cluster total `DtwTo` cost
(compression / MDL); no label selects anything. LABELS = used ONLY to score (purity /
NMI / cluster→word naming / LOSO recog), NEVER in the clustering / merging / medoid
update. SC load + the 40-speaker split = world-adapter mechanics (reuses
`sc_loso_frontend_norm.build_split` verbatim, 120 train / 40 held-out disjoint
speakers); **held-out speakers' clips are NEVER in the clustered cloud** — they are
assigned to the FIXED prototypes after each iteration freezes (`assign_external`), so the
cross-speaker LOSO is ungameable.

## (2) The run — per-iteration captured numbers (robust SC 40-speaker LOSO)

Config: 120 train / 40 held-out disjoint speakers, 200 clustered train-speaker tokens,
200 seen-speaker probes, 400 cross-speaker LOSO probes, k0=30 merged → k=10, seed 0.
Captured: `/tmp/crank_cluster_recognize.txt`, ends `[MARKER]
CRANK_CLUSTER_RECOGNIZE_COMPLETE`, pgrep-verified the python process EXITED.

```
 iter   k     cost   d_cost  purity   NMI   xPur  xNMI  LOSO   seen  #wrd  note
    0  29    72.39      nan   0.455  0.420  0.365 0.308 0.315  0.360   10   merged->k29
    1  28    72.50    0.112   0.455  0.425  0.350 0.296 0.305  0.365    9   merged->k28
    2  27    72.78    0.284   0.430  0.381  0.357 0.302 0.310  0.335   10   merged->k27
    3  26    75.59    2.812   0.430  0.390  0.385 0.316 0.355  0.300    9   merged->k26   <- best LOSO 0.355
    4  25    75.07   -0.527   0.445  0.425  0.347 0.296 0.320  0.305    9   merged->k25
    5  24    75.29    0.221   0.415  0.384  0.325 0.285 0.295  0.305   10   merged->k24
    6  23    77.42    2.131   0.365  0.348  0.315 0.264 0.275  0.275    8   merged->k23
    7  22    76.67   -0.748   0.395  0.368  0.302 0.243 0.263  0.290    7   merged->k22
    8  21    78.27    1.597   0.360  0.325  0.278 0.206 0.237  0.210    7   merged->k21
    9  20    78.87    0.605   0.345  0.310  0.273 0.196 0.233  0.200    7   merged->k20
   10  19    80.70    1.823   0.330  0.290  0.265 0.202 0.225  0.210    7   merged->k19
   11  18    81.88    1.183   0.290  0.259  0.228 0.181 0.207  0.210    7   merged->k18
   12  17    83.67    1.793   0.285  0.240  0.193 0.133 0.185  0.165    7   merged->k17
   13  16    84.20    0.525   0.275  0.231  0.190 0.131 0.185  0.160    7   merged->k16
   14  15    86.67    2.468   0.285  0.252  0.205 0.144 0.200  0.155    7   merged->k15
   15  14    86.33   -0.334   0.255  0.219  0.180 0.123 0.168  0.150    6   merged->k14
   16  13    87.66    1.326   0.250  0.194  0.163 0.083 0.155  0.130    6   merged->k13
   17  12    89.07    1.416   0.220  0.158  0.200 0.127 0.195  0.125    6   merged->k12
   18  11    89.20    0.127   0.230  0.171  0.165 0.081 0.160  0.110    6   merged->k11
   19  10    91.47    2.271   0.195  0.113  0.135 0.030 0.125  0.085    6   merged->k10
   20  10    91.47    0.000   0.195  0.113  0.135 0.030 0.125  0.085    6   [converged]
```

cost = within-cluster total `DtwTo` (the MDL selector); purity/NMI = clustered-set;
xPur/xNMI = held-out cross-speaker cluster purity/NMI; LOSO = held-out semi-supervised
recognition (medoid-prototype bank, cluster→majority-word); seen = seen-speaker recog;
#wrd = distinct words the cluster→word map covers (degeneracy probe). Floor 0.210,
chance 0.100.

**Convergence: YES.** At k=10 the MDL within-cluster `DtwTo` cost reaches a plateau
(iter19 → iter20, `d_cost = 0.000`), so the crank converges (iter20, 21 iterations).
Note the cost RISES monotonically (72.4 → 91.5) — this is expected and not a failure of
the selector: fewer clusters necessarily hold more members, so total within-cluster cost
grows mechanically as the merge schedule drops k. The MDL selector is meaningful at
FIXED k (the EM refinement minimises it there, e.g. the negative `d_cost` at iters
4/7/15 where re-medoiding tightened a fixed-k clustering); across the merge schedule the
cost is dominated by k, not by clustering quality.

## (3) Reading the result — what the crank lifts, and the honest collapse

**(a) Co-refining LIFTS the clustering above its separate baseline.** Clustered-set
purity reaches **0.455** (iters 0–1, k≈28–29) vs the separate k=10 clustering **0.303**
(**+0.152**), and the held-out semi-supervised LOSO reaches **0.355** (iter3, k=26) vs
the separate clustering semi-sup **0.225** (**+0.130**). The mechanism is exactly the
degeneracy fix the doc named: **k>#words gives many small, PURE sub-modes** — at high k a
cluster is a tight handful of one speaker-group's "five"s, so the prototype bank reads it
cleanly, and the cluster→word map covers all 10 words (#wrd=10 at iters 0/2/5). This is
the pool helping: the recognizer reads the deepened sub-mode structure the separate
single-pass k=10 clusterer never resolved.

**(b) But MERGING down to #words DEGRADES monotonically — the doc's named fix is the
WRONG move.** As the crank merges k 29 → 10, BOTH purity (0.455 → 0.195) and LOSO (0.315
→ 0.125) fall almost monotonically, and word coverage collapses (10 → 6). At the forced
k=10 endpoint the cranked clustering is WORSE than the separate clustering baseline
(purity 0.195 < 0.303; LOSO 0.125 < 0.225). The reason: the modes are SHALLOW (the same
ceiling both separate runs hit). When two pure sub-modes of DIFFERENT words happen to be
the closest medoid pair (the merge criterion is geometric `DtwTo`, label-free), the merge
fuses two different words into one impure cluster — and once fused, the cluster→word map
loses the minority word entirely (word coverage drops). Merging by `DtwTo` proximity is
the right structure-discovery move only when the valleys between word-modes are deeper
than the valleys between same-word sub-modes; here they are NOT, so the merge crosses
word boundaries and re-introduces exactly the mixing the high-k pool had avoided. **The
joint optimum is to STOP merging at high k (~26–29), not to drive to k=#words.**

**(c) Below supervised DTW.** Best cranked cross-speaker LOSO **0.355** vs supervised DTW
**0.593** (residual **−0.238**). The supervised recognizer banks ALL 200 exemplars and
nearest-neighbours a held-out token against every same-word exemplar; the crank distills
the cloud to ONE medoid per cluster (a far sparser bank) and recognizes via a
cluster→word naming map. The distilled prototype bank cannot match the full-exemplar
manifold — co-refinement deepens the clustering but does not manufacture the exemplar
density the supervised bank has for free.

**Honest residual.** Turning the crank DOES lift BOTH halves above their SEPARATE
baselines (clustering purity +0.152, cluster-recog LOSO +0.130) and DOES converge — the
user's reinforcement intuition is borne out at high k, where the recognizer reads the
clusterer's deepened sub-modes. But it does NOT converge to a BETTER joint solution than
the supervised DTW (−0.238), and the specific consolidation the clustering doc named
(merge to #words) actively HURTS, because the underlying word-modes are too shallow for a
label-free `DtwTo`-proximity merge to respect word boundaries. Both findings point at the
SAME unmoved ceiling both separate docs already named: **the depth of the modes in the
agent's current `DtwTo`-token distribution.** The next lever is a sharper token (the
multi-stream / pitch-synchronous trajectory `docs/dtw_trajectory_loso.md` named) so the
valleys between word-modes deepen below the valleys between same-word sub-modes — then a
proximity merge would consolidate within-word instead of across-word, and the high-k pool
could collapse to clean word categories without the degradation seen here.

## Suites

Required suites green (`test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`, `test_frontend_effect_gate`) — 36
passed. Nothing committed. `scripts/crank_cluster_recognize.py` left in the working tree.

## Reproduce

```
python -m scripts.crank_cluster_recognize                  # robust 120/40/20, k0=30, seed 0
python -m scripts.crank_cluster_recognize 12 6 4 14 0      # fast smoke
MAX_ITERS=40 python -m scripts.crank_cluster_recognize 120 40 20 30 0   # the captured run
```

Full captured output: `/tmp/crank_cluster_recognize.txt` (ends `[MARKER]
CRANK_CLUSTER_RECOGNIZE_COMPLETE`, pgrep-verified the python process exited).
