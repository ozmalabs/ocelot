"""collapse_engine — the DOMAIN-AGNOSTIC manifold-collapse loop, MY factoring.

The mandate asked me to design this abstraction MYSELF from my own prior runs
(scripts/manifold_collapse.py + scripts/ambiguous_prefix.py), NOT to accept a
prescribed interface. A prescribed core (scripts/collapse_core.py) exists with a
`trials/truth/fractions/evidence/manifold/forward/localise` contract; the mandate
says that prescription was wrong and was stopped. So this is a NEW file with the
interface I derived from what the loop ACTUALLY needs — I leave the prescribed
file untouched.

================================================================================
WHAT I DID: read my two runs back as my own work and asked the design questions.
================================================================================

In both prior scripts the loop and the domain were TANGLED in one file:
load_sentences, the n-gram LearnedStructure, the counted graph scorers, the
manifold, the five measurements, and the shuffle control all lived together, all
assuming "a sequence of words". Reading them back, the loop's domain-INVARIANT
essence is:

  Given a held-out POOL of candidate symbol-sequences and TARGET sequences,
  reveal each target symbol-by-symbol. At every revealed fraction:
    - HARD ADMISSIBILITY (Γ-prune): a candidate agrees with the revealed prefix
      up to its first mismatch. Pure symbol-EQUALITY — the core needs no domain
      knowledge: symbols are opaque, `==` is all it uses.
    - SOFT WEIGHT (learned structure): among agreeing candidates, weight by the
      DOMAIN's learned sequence-plausibility. The core does NOT know how that is
      computed — it asks the domain. This is the donkey-relevant driver.
    - CONFIDENCE = normalised weight; truth-confidence + admissible-set size read
      out at every fraction.

THE BOUNDARY I DREW.

The core OWNS, identically for every domain:
  1. the reveal iteration over fractions;
  2. manifold construction (hard agree term BETA*agree + soft seq_logprob, softmax);
  3. the five MEASUREMENTS — collapse curve (entropy + effective support),
     calibration (reliability + ECE), cohort/uniqueness (recognition-point
     distribution), garden-path / re-open count, and the next-symbol predictive
     manifold (the shuffle-sensitive signal);
  4. the SHUFFLE-CONTROL bookkeeping — re-run every measurement on a twin whose
     order was destroyed; the divergence proves real sequential structure;
  5. the LEARNING HOOK (collapse-failure -> localise -> construct): when the
     manifold fails to admit the truth's next symbol at a LEARNED context (the
     structure is present but lacks THIS transition), the core localises the gap
     (context, missing symbol) and hands it to the domain to construct from. I
     made this a first-class core output, not a buried hook — a collapse FAILURE
     is the loop's structure-discovery signal, which is the whole point.

The core DELEGATES (and ONLY these five things):
  - the corpus, already split by the domain into pool / train / targets (opaque
    symbol-sequences). The core never splits — it does not know what a good split
    is for a domain;
  - seq_logprob(seq): learned whole-sequence plausibility (counts only);
  - next_dist(context_prefix): learned next-symbol distribution ({} if unlearned);
  - shuffled: a twin plug with order destroyed and scorers re-learned (only the
    domain knows what "order" means for it);
  - donkey_audit(): the domain's own counts-only proof, printed verbatim.

WHAT I LEFT OUT, deliberately, as INCIDENTAL (NOT in the contract):
  - BETA (evidence strength) is a CORE constant: it is the loop's hard/soft
    trade-off, a property of collapse, not of any domain;
  - tokenisation, alphabet size, sequence lengths, "what a symbol means" — opaque;
  - the back-off scheme / n-gram order / graph materialisation — all inside the
    domain's two scorers; the core never sees an n-gram or a graph;
  - any notion of "word" / "letter" / "pass" — the core has none. (Grep this file
    for those words: zero hits.)
  - a `forward()` / analysis-by-synthesis method (the prescribed contract had one):
    my two runs never used synthesis to drive the collapse — the collapse is
    driven by counted next-symbol structure. Adding forward() would be padding the
    contract with something the loop doesn't need. Left OUT.
  - a generic `manifold(trial, evidence)` plug method (prescribed): that would let
    each domain reimplement the manifold, i.e. reimplement the CORE. The manifold
    IS the core's job; the domain only supplies the two scalar scorers it builds
    the manifold FROM. This is the key factoring difference: the prescribed
    interface delegated the manifold to the domain; I keep it in the core and
    delegate only the learned structure. That is what makes "one loop" real.

If the factoring is right, the SAME `evaluate()` below runs every domain with only
the plug swapped — which collapse_run.py demonstrates.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Hashable, Optional


# ==========================================================================
# THE DOMAIN-PLUG INTERFACE — the minimal contract, padded with nothing.
# ==========================================================================

@dataclass
class DomainPlug:
    """A domain provides EXACTLY these. Everything else the core does itself.

    name        : str (reporting only).
    pool        : list[tuple]  held-out candidate sequences (the manifold space).
    train       : list[tuple]  sequences the structure was counted from.
    targets     : list[tuple]  sequences to reveal symbol-by-symbol.
    seq_logprob : tuple -> float   learned whole-sequence log-plausibility (counts).
    next_dist   : tuple(ctx) -> dict[symbol,float]  learned next-symbol dist;
                  {} when the context is UNLEARNED (a coverage gap the core uses).
    shuffled    : Optional[DomainPlug]  order-destroyed twin (control).
    donkey_audit: Optional[() -> (str, bool)]  counts-only proof (printed verbatim).
    on_gap      : Optional[(ctx, symbol) -> None]  learning hook; the core calls it
                  on each localised collapse failure. None => core just COUNTS gaps.
    """
    name: str
    pool: list
    train: list
    targets: list
    seq_logprob: Callable
    next_dist: Callable
    shuffled: Optional["DomainPlug"] = None
    donkey_audit: Optional[Callable] = None
    on_gap: Optional[Callable] = None
    agree: Optional[Callable] = None  # SOFT-AGREE kernel agree(cand_sym, prefix_sym)
                                      # -> float in [0,1]: how well partial evidence
                                      # at this position agrees with the hypothesis.
                                      # None => the HARD symbol-equality special case
                                      # (the 3 discrete domains use None unchanged).
    truth_of: Optional[Callable] = None  # target -> the POOL member that is its
                                      # ground truth. None => IDENTITY (the target
                                      # IS its own pool member — the discrete case,
                                      # unchanged). A continuous domain reveals a
                                      # held-out PROBE but the truth is the matching
                                      # hypothesis in the pool (a reference code),
                                      # so probe != truth and this maps it.


# ==========================================================================
# CORE CONSTANTS — properties of the LOOP, not of any domain.
# ==========================================================================

BETA = 6.0                # evidence per matched revealed symbol (counted-scale, fixed)
FRACS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
REC_THRESH = 0.5          # truth recognised = top-1 AND >50% of manifold mass


# ==========================================================================
# CORE PRIMITIVES — identical for every domain.
# ==========================================================================

def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def k_at_fraction(L, f):
    return int(round(f * L))


def _hard_agree(a, b):
    """The DEFAULT agree kernel: opaque symbol EQUALITY. Returns 1.0 on a match,
    0.0 on a mismatch. This is the HARD special case of soft-agree — a 0.0 here
    signals a prefix break (the discrete left-to-right Γ-prune). The 3 discrete
    domains use exactly this; the core needs no domain knowledge for it."""
    return 1.0 if a == b else 0.0


def manifold(plug, prefix, seq_lp_cache):
    """The manifold over the whole pool given the revealed `prefix`:
    progressive AGREEMENT of the partial evidence (the SOFT-AGREE kernel, summed
    over revealed positions) + SOFT learned seq-plausibility, softmaxed.

    SOFT-AGREE: `agree(cand[i], prefix[i]) -> float in [0,1]` measures how well the
    partial continuous evidence at position i agrees with each hypothesis. The HARD
    discrete case is `agree(a,b) = 1.0 if a==b else 0.0` (plug.agree is None), and a
    0.0 there BREAKS the prefix (the discrete left-to-right Γ-prune) — so symbol
    equality is the exact special case of the metric kernel. A continuous kernel
    (e.g. a Gaussian on cue distance) is never exactly 0, so it never breaks: it
    accumulates soft evidence across every revealed cue. ONE code path, agree
    swapped. The only domain inputs are seq_lp_cache and the optional agree kernel."""
    k = len(prefix)
    agree_fn = plug.agree if plug.agree is not None else _hard_agree
    lws = []
    for c in plug.pool:
        agree = 0.0
        for i in range(min(k, len(c))):
            s = agree_fn(c[i], prefix[i])
            if s <= 0.0:        # mismatch: a hard break (discrete) / no-evidence (soft)
                break
            agree += s
        lws.append(BETA * agree + seq_lp_cache[c])
    mx = max(lws)
    ws = [math.exp(lw - mx) for lw in lws]
    z = sum(ws)
    return sorted(((c, w / z) for c, w in zip(plug.pool, ws)), key=lambda x: -x[1])


def manifold_entropy(man):
    return -sum(p * math.log2(p) for _c, p in man if p > 0)


def dist_entropy(d):
    return -sum(p * math.log2(p) for p in d.values() if p > 0)


def effective_support(man, mass=0.99):
    acc, n = 0.0, 0
    for _c, p in man:
        acc += p
        n += 1
        if acc >= mass:
            break
    return n


def calibration_curve(calib, nbins=10):
    bins = [[] for _ in range(nbins)]
    for p, hit in calib:
        bins[min(int(p * nbins), nbins - 1)].append((p, 1.0 if hit else 0.0))
    rows, ece = [], 0.0
    N = max(len(calib), 1)
    for b in range(nbins):
        if not bins[b]:
            continue
        mp = _mean([x[0] for x in bins[b]])
        acc = _mean([x[1] for x in bins[b]])
        n = len(bins[b])
        rows.append((b / nbins, (b + 1) / nbins, mp, acc, n))
        ece += (n / N) * abs(mp - acc)
    return rows, ece


# ==========================================================================
# THE COLLAPSE LOOP — identical for every domain.
# ==========================================================================

@dataclass
class CollapseResult:
    size: dict = field(default_factory=dict)
    ent: dict = field(default_factory=dict)
    truth_conf: dict = field(default_factory=dict)
    truth_in_set: dict = field(default_factory=dict)
    nw_ent: dict = field(default_factory=dict)
    nw_top1: dict = field(default_factory=dict)
    nw_top5: dict = field(default_factory=dict)
    calib: list = field(default_factory=list)
    rec_points: list = field(default_factory=list)
    garden_paths: int = 0
    garden_examples: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    n_next_points: int = 0


def run_collapse(plug, seq_lp_cache, max_targets=None):
    """THE LOOP. Reveal each target symbol-by-symbol; at each fraction build the
    manifold and measure. Nothing here names a domain: it calls plug.seq_logprob
    (via the cache) and plug.next_dist; everything else is opaque-symbol math."""
    R = CollapseResult()
    pf_size = {f: [] for f in FRACS}
    pf_ent = {f: [] for f in FRACS}
    pf_tc = {f: [] for f in FRACS}
    pf_tr = {f: [] for f in FRACS}
    pf_nwe = {f: [] for f in FRACS}
    pf_nw1 = {f: [] for f in FRACS}
    pf_nw5 = {f: [] for f in FRACS}

    targets = plug.targets if max_targets is None else plug.targets[:max_targets]
    truth_of = plug.truth_of if plug.truth_of is not None else (lambda t: t)
    for tgt in targets:
        L = len(tgt)
        if L < 2:
            continue
        truth = truth_of(tgt)        # the pool member that is ground truth (== tgt
                                     # for discrete domains; the matching reference
                                     # hypothesis for a continuous probe)
        committed_top = None
        rec_point = None
        for f in FRACS:
            k = k_at_fraction(L, f)
            prefix = tgt[:k]
            man = manifold(plug, prefix, seq_lp_cache)
            pf_size[f].append(effective_support(man))
            pf_ent[f].append(manifold_entropy(man))
            truth_conf, truth_rank = 0.0, -1
            for rank, (c, p) in enumerate(man):
                if c == truth:
                    truth_conf, truth_rank = p, rank
                    break
            pf_tc[f].append(truth_conf)
            pf_tr[f].append(truth_rank)
            if man:
                top_c, top_p = man[0]
                R.calib.append((top_p, top_c == truth))
                if committed_top is not None and top_c != committed_top \
                        and committed_top != truth:
                    R.garden_paths += 1
                    if len(R.garden_examples) < 8:
                        R.garden_examples.append(
                            (" ".join(map(str, prefix)),
                             " ".join(map(str, committed_top[:k + 2])),
                             " ".join(map(str, top_c[:k + 2]))))
                    committed_top = None
                if top_p > 0.8:
                    committed_top = top_c
            if rec_point is None and man and man[0][0] == truth \
                    and man[0][1] >= REC_THRESH:
                rec_point = f

            # ---- next-symbol predictive manifold + LEARNING-HOOK localisation ----
            # The anticipation target is the GROUND-TRUTH's next symbol (== tgt[k]
            # for discrete domains where truth is tgt; the truth hypothesis's next
            # cue for a continuous probe). next_dist predicts over pool-hypothesis
            # next symbols, so the hit means "the right hypothesis's next move was
            # anticipated from the revealed prefix" — the shuffle-sensitive signal.
            if 1 <= k < L:
                ctx = tgt[:k]
                true_next = truth[k]
                nd = plug.next_dist(ctx)
                if nd:
                    R.n_next_points += 1
                    pf_nwe[f].append(dist_entropy(nd))
                    ranked = sorted(nd.items(), key=lambda kv: -kv[1])
                    top1 = ranked[0][0]
                    top5 = set(w for w, _ in ranked[:5])
                    pf_nw1[f].append(1.0 if top1 == true_next else 0.0)
                    pf_nw5[f].append(1.0 if true_next in top5 else 0.0)
                    if nd.get(true_next, 0.0) <= 0.0:
                        R.gaps.append((ctx, true_next))
                        if plug.on_gap is not None:
                            plug.on_gap(ctx, true_next)
        R.rec_points.append(rec_point if rec_point is not None else 1.0)

    R.size = {f: _mean(pf_size[f]) for f in FRACS}
    R.ent = {f: _mean(pf_ent[f]) for f in FRACS}
    R.truth_conf = {f: _mean(pf_tc[f]) for f in FRACS}
    R.truth_in_set = {f: _mean([1.0 if r >= 0 else 0.0 for r in pf_tr[f]])
                      for f in FRACS}
    R.nw_ent = {f: _mean(pf_nwe[f]) for f in FRACS}
    R.nw_top1 = {f: _mean(pf_nw1[f]) for f in FRACS}
    R.nw_top5 = {f: _mean(pf_nw5[f]) for f in FRACS}
    return R


# ==========================================================================
# THE FULL EVALUATION — real + shuffle + verdict, identical for every domain.
# ==========================================================================

@dataclass
class Eval:
    name: str
    real: CollapseResult
    shuf: Optional[CollapseResult]
    nw_t1_real: float = 0.0
    nw_t1_shuf: float = 0.0
    nw_t5_real: float = 0.0
    nw_t5_shuf: float = 0.0
    nw_ent_real: float = 0.0
    nw_ent_shuf: float = 0.0
    ece: float = 0.0
    ece_shuf: float = 0.0
    collapses: bool = False
    honest: bool = False
    cohort: bool = False
    seq_driven: bool = False
    success: bool = False
    donkey_line: str = ""
    donkey_ok: bool = True


def evaluate(plug, max_targets=None):
    """Run the loop on the domain and its shuffled twin, apply the five gates.
    The SAME function for every domain — it NEVER branches on plug.name. That is
    the proof of domain-agnosticism."""
    if plug.donkey_audit is not None:
        d_line, d_ok = plug.donkey_audit()
    else:
        d_line, d_ok = "(no audit provided)", True

    seq_lp = {c: plug.seq_logprob(c) for c in plug.pool}
    real = run_collapse(plug, seq_lp, max_targets)

    shuf = None
    nw_t1_s = nw_t5_s = nw_ent_s = ece_s = 0.0
    if plug.shuffled is not None:
        sp = plug.shuffled
        seq_lp_s = {c: sp.seq_logprob(c) for c in sp.pool}
        shuf = run_collapse(sp, seq_lp_s, max_targets)
        nw_t1_s = _mean([shuf.nw_top1[f] for f in FRACS])
        nw_t5_s = _mean([shuf.nw_top5[f] for f in FRACS])
        nw_ent_s = _mean([shuf.nw_ent[f] for f in FRACS])
        _, ece_s = calibration_curve(shuf.calib)

    nw_t1_r = _mean([real.nw_top1[f] for f in FRACS])
    nw_t5_r = _mean([real.nw_top5[f] for f in FRACS])
    nw_ent_r = _mean([real.nw_ent[f] for f in FRACS])
    _, ece = calibration_curve(real.calib)

    collapses = real.ent[0.9] < real.ent[0.1] - 1e-6
    honest = ece < 0.15
    cohort = _mean(real.rec_points) < 1.0
    seq_driven = (shuf is not None
                  and nw_t1_r > nw_t1_s * 1.3 and nw_t5_r > nw_t5_s * 1.3)
    success = collapses and honest and cohort and seq_driven

    return Eval(plug.name, real, shuf, nw_t1_r, nw_t1_s, nw_t5_r, nw_t5_s,
                nw_ent_r, nw_ent_s, ece, ece_s,
                collapses, honest, cohort, seq_driven, success, d_line, d_ok)


# ==========================================================================
# REPORTING — domain-agnostic pretty-printer.
# ==========================================================================

def report(ev):
    R = ev.real
    print("=" * 72)
    print(f"DOMAIN: {ev.name}")
    print("=" * 72)
    print(f"  collapse over revealed fraction (SAME core code):")
    print(f"  {'frac':>4} | {'adm_size':>8} | {'H_bits':>7} | {'truth_conf':>10} | "
          f"{'truth_in_set':>12}")
    for f in FRACS:
        print(f"  {f:>4.1f} | {R.size[f]:>8.1f} | {R.ent[f]:>7.3f} | "
              f"{R.truth_conf[f]:>10.3f} | {R.truth_in_set[f]:>12.3f}")

    rows, _ = calibration_curve(R.calib)
    print(f"\n  CALIBRATION (top-1 conf vs hit-rate)  ECE={ev.ece:.4f}:")
    for lo, hi, mp, acc, n in rows:
        print(f"    [{lo:.1f},{hi:.1f})  mean_conf={mp:.3f}  hit={acc:.3f}  n={n}")

    rp = sorted(R.rec_points)

    def pct(xs, q):
        return xs[min(int(q * len(xs)), len(xs) - 1)] if xs else float("nan")
    print(f"\n  COHORT/UNIQUENESS recognition-fraction: median={pct(rp,0.5):.2f}  "
          f"mean={_mean(rp):.3f}  "
          f"never-unique={sum(1 for x in rp if x>=1.0)}/{len(rp)}")
    print(f"  GARDEN-PATH (committed-then-overturned): {R.garden_paths}")

    print(f"\n  NEXT-SYMBOL predictive manifold (shuffle-sensitive signal):")
    print(f"    measured at {R.n_next_points} learned-context points")
    print(f"    top-1 anticipation  REAL={ev.nw_t1_real:.3f}  "
          f"SHUF={ev.nw_t1_shuf:.3f}  "
          f"ratio={ev.nw_t1_real/max(ev.nw_t1_shuf,1e-9):.2f}x")
    print(f"    top-5 anticipation  REAL={ev.nw_t5_real:.3f}  "
          f"SHUF={ev.nw_t5_shuf:.3f}  "
          f"ratio={ev.nw_t5_real/max(ev.nw_t5_shuf,1e-9):.2f}x")
    print(f"    next-sym entropy    REAL={ev.nw_ent_real:.3f}  "
          f"SHUF={ev.nw_ent_shuf:.3f}  delta={ev.nw_ent_shuf-ev.nw_ent_real:+.3f}")

    print(f"\n  LEARNING HOOK — collapse-failure localisation: "
          f"{len(R.gaps)} zero-mass-at-truth gaps localised")
    for ctx, miss in R.gaps[:4]:
        c = " ".join(map(str, ctx[-3:]))
        print(f"    gap: ...{c}  -> MISSING next symbol '{miss}'")

    print(f"\n  DONKEY AUDIT: {ev.donkey_line}  ok={ev.donkey_ok}")

    print(f"\n  VERDICT GATES:")
    print(f"    (i)   collapses (H falls)        : "
          f"{'YES' if ev.collapses else 'NO'}  "
          f"(H {R.ent[0.1]:.2f} -> {R.ent[0.9]:.2f} bits)")
    print(f"    (ii)  honest/calibrated ECE<0.15 : "
          f"{'YES' if ev.honest else 'NO'}  (ECE={ev.ece:.3f})")
    print(f"    (iii) cohort structure           : "
          f"{'YES' if ev.cohort else 'NO'}  (mean rec-frac {_mean(rp):.2f})")
    print(f"    (iv)  driven by real order (shuf): "
          f"{'YES' if ev.seq_driven else 'NO'}  "
          f"(next-sym top-1 {ev.nw_t1_real/max(ev.nw_t1_shuf,1e-9):.2f}x shuffle)")
    print(f"    >>> {'SUCCESS' if ev.success else 'PARTIAL'}")
