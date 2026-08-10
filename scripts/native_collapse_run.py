"""native_collapse_run — VERIFY the native collapse cognition == the Python
prototype, prove SURPRISE is a native Term, and prove the LEARNING MUTATION is a
native graph mutation that DROPS surprise and GENERALISES to held-out data.

This is the INSTRUMENT (the experimenter's harness), not cognition. It drives
scripts/native_collapse.py (the native cognition) and scripts/collapse_engine.py
(the untouched Python mirror) on the SAME data and reports real numbers:

  (a) NATIVE == PYTHON: native manifold confidence + entropy reproduce the
      Python loop's, per candidate, per fraction, within float tolerance.
  (b) SURPRISE NATIVE: the native -log(conf) Term matches the Python surprise
      per step.
  (c) LEARNING NATIVE + WORKS: the native graph mutation (both the direct and
      the tick()-fired Rule path) constructs the localised gap; surprise DROPS
      at the constructed points and DROPS on HELD-OUT data too (generalises).
  (d) DONKEY: counts-only structure addition, no gradient/fit.

Run:  python -m scripts.native_collapse_run
"""
from __future__ import annotations

import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import collapse_engine as core          # the untouched Python mirror
from scripts import collapse_domains as dom
from scripts import native_collapse as nat
from substrate_rs import Substrate


# ==========================================================================
# (a)+(b)  NATIVE == PYTHON on the manifold, confidence, entropy, surprise.
# ==========================================================================

def verify_native_vs_python(plug, max_targets=40):
    """Run the Python manifold and the NATIVE manifold on the same prefixes;
    compare confidence (per candidate), entropy, and surprise per step."""
    s = Substrate()
    seq_lp = {c: plug.seq_logprob(c) for c in plug.pool}
    cand_nodes = nat.build_cand_nodes(s, plug.pool)

    max_conf_err = 0.0
    max_ent_err = 0.0
    max_surp_err = 0.0
    n_steps = 0
    n_conf_cmp = 0

    targets = plug.targets[:max_targets]
    for tgt in targets:
        L = len(tgt)
        if L < 2:
            continue
        for f in core.FRACS:
            k = core.k_at_fraction(L, f)
            prefix = tgt[:k]

            # PYTHON manifold (the mirror)
            py_man = core.manifold(plug, prefix, seq_lp)
            py_conf = {c: p for c, p in py_man}
            py_ent = core.manifold_entropy(py_man)

            # NATIVE manifold (the cognition, evaluated in Rust)
            root, mx, Z, nat_conf = nat.native_manifold(
                s, plug.pool, prefix, seq_lp, cand_nodes)
            nat_ent = nat.native_entropy(s, root, mx, Z)

            for c in plug.pool:
                max_conf_err = max(max_conf_err,
                                   abs(py_conf.get(c, 0.0) - nat_conf[c]))
                n_conf_cmp += 1
            max_ent_err = max(max_ent_err, abs(py_ent - nat_ent))

            # surprise at the TRUTH's confidence (truth == tgt for these domains)
            truth = tgt
            py_truth_conf = py_conf.get(truth, 0.0)
            nat_truth_conf = nat_conf[truth]
            py_surp = -math.log(max(py_truth_conf, 1e-12))
            nat_surp = nat.native_surprise(s, nat_truth_conf)
            max_surp_err = max(max_surp_err, abs(py_surp - nat_surp))
            n_steps += 1

    return {
        "n_steps": n_steps, "n_conf_cmp": n_conf_cmp,
        "max_conf_err": max_conf_err, "max_ent_err": max_ent_err,
        "max_surp_err": max_surp_err,
    }


# ==========================================================================
# (c)  NATIVE LEARNING MUTATION drops surprise + generalises (held-out).
# ==========================================================================

def _mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def _surprise_at_gaps(struct, gaps, s, eps=1e-12):
    """Mean NATIVE surprise of the next-symbol predictive distribution at a list
    of (ctx, true_next) points. surprise = -log(P_native(true_next | ctx)); the
    P is read from the domain's COUNTED structure (next_dist), the -log is the
    native Term. {} (unlearned context) counts as max surprise (-log eps)."""
    surps = []
    for ctx, true_next in gaps:
        nd = struct.next_dist(ctx)
        p = nd.get(true_next, 0.0) if nd else 0.0
        surps.append(nat.native_surprise(s, p, eps))
    return _mean(surps)


def learning_native_test(plug_factory, name, n_construct=80, n_holdout=80):
    """Build a domain with TWO disjoint target sets: a CONSTRUCT set (we localise
    its gaps and construct them as native graph mutations) and a HELD-OUT set
    (never constructed). Measure native surprise before/after on BOTH. A drop on
    held-out = the construction added REAL structure (generalises), not memorised
    the construct set.

    We split by building the plug, finding gaps over a large target slice, then
    partitioning gaps by which target they came from."""
    plug, _ = plug_factory()
    struct = plug._cs  # the CountedStructure (attached below for the instrument)
    s = struct.s       # the SAME substrate the counted structure lives in

    # collect gaps per target: a gap = (ctx, true_next) where the learned context
    # had ZERO mass on the truth's next symbol — the collapse-failure the loop
    # localises (mirror of collapse_engine.run_collapse's gap localisation).
    def gaps_of(tgt):
        out = []
        L = len(tgt)
        truth = tgt
        for f in core.FRACS:
            k = core.k_at_fraction(L, f)
            if 1 <= k < L:
                ctx = tgt[:k]
                true_next = truth[k]
                nd = struct.next_dist(ctx)
                if nd and nd.get(true_next, 0.0) <= 0.0:
                    out.append((ctx, true_next))
        return out

    targets = plug.targets
    construct_targets = targets[:n_construct]
    holdout_targets = targets[n_construct:n_construct + n_holdout]

    construct_gaps = []
    for t in construct_targets:
        construct_gaps.extend(gaps_of(t))
    holdout_gaps = []
    for t in holdout_targets:
        holdout_gaps.extend(gaps_of(t))

    # held-out gaps that SHARE a (last-ctx-symbol, missing) transition with one
    # constructed from the disjoint construct set — the sharp generalisation set.
    constructed_trans = set()
    for ctx, miss in construct_gaps:
        b = ctx[-1] if ctx else None
        constructed_trans.add((b, miss))
    shared_gaps = [(ctx, miss) for ctx, miss in holdout_gaps
                   if (ctx[-1] if ctx else None, miss) in constructed_trans]

    # BEFORE: native surprise at the construct gaps and the held-out gaps.
    before_construct = _surprise_at_gaps(struct, construct_gaps, s)
    before_holdout = _surprise_at_gaps(struct, holdout_gaps, s)
    before_shared = _surprise_at_gaps(struct, shared_gaps, s)

    # LEARN: construct EVERY construct-gap as a NATIVE GRAPH MUTATION. Use the
    # tick()-fired Rule path for HALF and the direct native-mutation path for the
    # other half, to prove both native mutation paths work; they are equivalent.
    n_rule = 0
    n_direct = 0
    for i, (ctx, miss) in enumerate(construct_gaps):
        if i % 2 == 0:
            nat.construct_gap_via_rule(struct, ctx, miss)
            n_rule += 1
        else:
            nat.construct_gap_direct(struct, ctx, miss)
            n_direct += 1

    # AFTER: re-measure native surprise. At the constructed points surprise must
    # drop (the structure now exists). On HELD-OUT gaps, surprise drops iff the
    # constructed transitions GENERALISE (shared structure), not memorisation.
    after_construct = _surprise_at_gaps(struct, construct_gaps, s)

    # held-out gaps must be RE-DERIVED against the now-grown structure (a context
    # that was unlearned before may now be covered by a constructed transition).
    holdout_gaps_after = []
    for t in holdout_targets:
        holdout_gaps_after.extend(gaps_of(t))
    after_holdout = _surprise_at_gaps(struct, holdout_gaps, s)
    after_shared = _surprise_at_gaps(struct, shared_gaps, s)
    n_holdout_gaps_remaining = len(holdout_gaps_after)

    # SHARP generalisation signal: of the held-out gaps, which share a
    # (last-context-symbol, missing-symbol) transition with one constructed from
    # the DISJOINT construct set? On exactly those, native surprise must drop —
    # the constructed admissibility transfers where the structure genuinely
    # recurs (the binary-vs-fit signature: it transfers there, and nowhere else,
    # not a smeared fit). before/after measured separately below.

    return {
        "name": name,
        "n_construct_gaps": len(construct_gaps),
        "n_holdout_gaps": len(holdout_gaps),
        "n_rule": n_rule, "n_direct": n_direct,
        "before_construct": before_construct, "after_construct": after_construct,
        "before_holdout": before_holdout, "after_holdout": after_holdout,
        "holdout_gaps_before": len(holdout_gaps),
        "holdout_gaps_after": n_holdout_gaps_remaining,
        "n_shared": len(shared_gaps),
        "before_shared": before_shared, "after_shared": after_shared,
    }


# ==========================================================================
# instrument plumbing: attach the CountedStructure to the plug so the learning
# instrument can mutate it natively. (collapse_domains builds it internally; we
# re-expose it WITHOUT touching collapse_domains by re-wrapping _build_plug.)
# ==========================================================================

def _plug_with_struct(name, pool, train, targets):
    cs = dom.CountedStructure()
    cs.learn(train)
    plug = dom._build_plug(name, pool, train, targets)
    # _build_plug builds its OWN cs internally; to mutate the SAME structure the
    # plug scores from, rebuild the plug around our cs explicitly.
    from scripts.collapse_engine import DomainPlug
    plug = DomainPlug(name=name, pool=pool, train=train, targets=targets,
                      seq_logprob=cs.seq_logprob, next_dist=cs.next_dist)
    plug._cs = cs
    return plug, len(pool)


def letters_factory():
    import random
    random.seed(8)
    sents = dom._load_sentences(min_len=1, max_len=60)
    words = set()
    for s in sents:
        for w in s:
            w = w.replace("'", "")
            if 4 <= len(w) <= 14 and w.isalpha():
                words.add(w)
    seqs = [tuple(w.lower()) for w in sorted(words)]
    random.shuffle(seqs)
    n_pool = min(1500, len(seqs) - 400)
    pool = seqs[:n_pool]
    train = seqs[n_pool:]
    targets = pool[:400]
    return _plug_with_struct("letters", pool, train, targets)


def sentences_factory():
    import random
    random.seed(8)
    sents = dom._load_sentences()
    random.shuffle(sents)
    seen, uniq = set(), []
    for s in sents:
        if s not in seen:
            seen.add(s); uniq.append(s)
    sents = uniq
    n_pool = min(1200, len(sents) - 400)
    pool = sents[:n_pool]
    train = sents[n_pool:]
    targets = pool[:400]
    return _plug_with_struct("sentences", pool, train, targets)


# ==========================================================================
# MAIN
# ==========================================================================

def main():
    t0 = time.time()
    print("=" * 72)
    print("NATIVE COLLAPSE CORE — cognition migrated to the Rust/graph runtime")
    print("=" * 72)

    # ---- (a)+(b) native == python on at least one domain (use llvm: small,
    # deterministic, real engineering grammar). Then also letters for breadth.
    print("\n[A/B] NATIVE == PYTHON  (manifold confidence + entropy + surprise)")
    for builder, label in ((lambda: dom.llvm_plug(n_targets=60)[0], "llvm_passes"),
                           (lambda: dom.letters_plug(n_pool=800, n_targets=40)[0],
                            "letters")):
        plug = builder()
        r = verify_native_vs_python(plug, max_targets=40)
        print(f"  domain={label:>12}  steps={r['n_steps']:>4}  "
              f"conf_cmps={r['n_conf_cmp']:>6}")
        print(f"    max |conf_native - conf_python|     = {r['max_conf_err']:.3e}")
        print(f"    max |entropy_native - entropy_py|   = {r['max_ent_err']:.3e}")
        print(f"    max |surprise_native - surprise_py| = {r['max_surp_err']:.3e}")
        ok = (r['max_conf_err'] < 1e-9 and r['max_ent_err'] < 1e-9
              and r['max_surp_err'] < 1e-9)
        print(f"    NATIVE==PYTHON within 1e-9: {'YES' if ok else 'NO'}")

    # ---- (c) native learning mutation drops surprise + generalises ----
    print("\n[C] NATIVE LEARNING MUTATION — surprise drop + held-out generalisation")
    for factory, name in ((letters_factory, "letters"),
                          (sentences_factory, "sentences")):
        r = learning_native_test(factory, name)
        d_con = r["before_construct"] - r["after_construct"]
        d_hold = r["before_holdout"] - r["after_holdout"]
        print(f"\n  domain={name}")
        print(f"    construct gaps localised : {r['n_construct_gaps']} "
              f"(via tick()-Rule: {r['n_rule']}, via direct native mutation: "
              f"{r['n_direct']})")
        print(f"    held-out gaps (disjoint) : {r['n_holdout_gaps']}")
        print(f"    SURPRISE @ constructed   : "
              f"{r['before_construct']:.3f} -> {r['after_construct']:.3f}  "
              f"(drop {d_con:+.3f})")
        print(f"    SURPRISE @ HELD-OUT      : "
              f"{r['before_holdout']:.3f} -> {r['after_holdout']:.3f}  "
              f"(drop {d_hold:+.3f})")
        print(f"    held-out gaps remaining  : "
              f"{r['holdout_gaps_before']} -> {r['holdout_gaps_after']} "
              f"(closed {r['holdout_gaps_before']-r['holdout_gaps_after']} "
              f"held-out gaps by generalisation)")
        d_shared = r["before_shared"] - r["after_shared"]
        print(f"    SHARP held-out (the {r['n_shared']} held-out gaps whose "
              f"transition was constructed from the DISJOINT set):")
        print(f"      SURPRISE @ shared      : "
              f"{r['before_shared']:.3f} -> {r['after_shared']:.3f}  "
              f"(drop {d_shared:+.3f})")
        gen = d_hold > 1e-6
        print(f"    drops at constructed: {'YES' if d_con > 1e-6 else 'NO'}   "
              f"GENERALISES to held-out: {'YES' if gen else 'NO'}")

    # ---- (d) donkey audit ----
    print("\n[D] DONKEY AUDIT")
    print("    learning = native graph mutation adding a COUNTED MBi transition")
    print("    edge (add_node/add_edge_unchecked, or a tick()-fired add_edge")
    print("    Rule effect). No gradient-on-surprise, no loss, no .fit, no net.")
    print("    surprise/confidence/entropy are native Term-trees (Exp/Log/Neg/")
    print("    Sum/MaxOver/Div) evaluated by the Rust runtime — no python exp/log.")

    print(f"\n(elapsed {time.time()-t0:.0f}s)")
    print("NATIVE_COLLAPSE_RUN_COMPLETED")


if __name__ == "__main__":
    main()
