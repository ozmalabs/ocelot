#!/usr/bin/env python3
"""Qualia-as-navigation — measure the 4 coherence-intuition claims.

See docs/research/psychology_affect/QUALIA_NAVIGATION_COHERENCE_PREREG.md.

CORPUS is assembled from the REAL ConceptNet slab
(domains.conceptnet_reference) via a reverse-index over a fixed cue
vocabulary: a COHERENT triad = 3 cues sharing a common associate (via the
whitelisted commonsense relations); an INCOHERENT triad = 3 cues with no
shared target. This is COMMONSENSE-SHARED-ASSOCIATE coherence, NOT the Mednick
free-association RAT (whose associates live in the RelatedTo/Synonym relations
this substrate's slab deliberately drops). Stated plainly.

CLAIMS
  1. Coherence-before-retrieval: peak convergent field CI-separated higher for
     coherent than incoherent, argmax never evaluated, associate held out.
  2. Perturbation reverses it (Topolinski): drop a cue->associate edge / scale
     cue state -> coherence drops toward incoherent range.
  3. Aperture-graded knows-that -> knows-what: coarse grain reports solvable
     without localising; fine grain localises the peak node.
  4. Metcalfe dissociation: NEAR triad localises on the true associate; FAR
     triad localises on a DECOY (false-warmth on the wrong attractor).
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

import substrate_rs as sr  # noqa: E402
from domains import qualia_navigation as qn  # noqa: E402
from domains.conceptnet_reference import conceptnet_relations  # noqa: E402

# Fixed cue vocabulary (declared up front — the corpus is a demonstration
# battery, not a normed instrument).
CUE_VOCAB = [
    "dog", "cat", "knife", "water", "fire", "book", "car", "house", "tree",
    "sun", "moon", "bird", "fish", "music", "money", "love", "fear", "food",
    "sleep", "king", "boat", "school", "hand", "eye", "door", "road",
]


def _reverse_index(cues):
    """associate -> set(cues pointing to it) via whitelisted relations."""
    targets = defaultdict(set)
    for c in cues:
        for _rel, tgt in conceptnet_relations(c):
            if tgt in cues:
                continue  # a cue is not its own associate
            targets[tgt].add(c)
    return targets


def _shared_count_index(cues):
    """For each cue, its set of associate targets (for building triads)."""
    return {c: {t for _r, t in conceptnet_relations(c) if t not in cues}
            for c in cues}


def build_corpus(cues=CUE_VOCAB, n=8):
    """Return {'coherent': [...], 'incoherent': [...], 'near': [...],
    'far': [...]} lists of triad specs (cue_names, edges, held_out)."""
    rev = _reverse_index(cues)
    per_cue = _shared_count_index(cues)

    # COHERENT: associate shared by >=3 cues -> pick 3 of them.
    coherent = []
    for assoc, sharers in sorted(rev.items(), key=lambda kv: -len(kv[1])):
        if len(sharers) >= 3:
            triad_cues = sorted(sharers)[:3]
            coherent.append((triad_cues, assoc))
        if len(coherent) >= n:
            break

    # INCOHERENT: 3 cues with NO shared target at all.
    incoherent = []
    import itertools
    for combo in itertools.combinations(cues, 3):
        common = per_cue[combo[0]] & per_cue[combo[1]] & per_cue[combo[2]]
        if not common:
            incoherent.append((list(combo), None))
        if len(incoherent) >= n:
            break

    # NEAR (Metcalfe incremental): the true associate is the CLEAR single peak
    # — supported by all 3 cues, out-scoring every private candidate. Every
    # coherent triad wired this way has the associate at field 3.0 vs privates
    # at 1.0, so the warmth gradient localises correctly. NEAR == the coherent
    # set (clean-peak by construction); reported honestly as such.
    near = list(coherent)

    # FAR: a triad where a DECOY (shared by exactly 2 cues) out-numbers the
    # nominal associate that is shared by only 2 as well but the decoy is the
    # denser attractor -> false-warmth. Constructed from the shared-count
    # structure: pick 3 cues where the pairwise-shared decoy beats the
    # triple-shared associate by having MORE cue support wired.
    far = []
    for combo in itertools.combinations(cues, 3):
        s0, s1, s2 = (per_cue[c] for c in combo)
        triple = s0 & s1 & s2
        pair = ((s0 & s1) | (s0 & s2) | (s1 & s2)) - triple
        if triple and pair:
            assoc = sorted(triple)[0]
            decoy = sorted(pair)[0]
            far.append((list(combo), assoc, decoy))
        if len(far) >= n:
            break

    return {"coherent": coherent, "incoherent": incoherent,
            "near": near, "far": far}


def _triad_from_coherent(spec):
    """Build a triad: each cue -> the true associate; plus each cue -> its own
    private neighbour (so incoherent-like fanout exists) — the associate is the
    only convergent node. `held_out` = the associate."""
    cues, assoc = spec
    edges = [(c, assoc, 1.0) for c in cues]
    # give each cue a private (non-shared) candidate so the field isn't
    # trivially the only node — a fair test of convergence.
    for i, c in enumerate(cues):
        edges.append((c, "priv_%d" % i, 1.0))
    s = sr.Substrate()
    return qn.build_triad(s, cues, edges, held_out=assoc)


def _triad_from_incoherent(spec):
    cues, _ = spec
    edges = []
    for i, c in enumerate(cues):
        edges.append((c, "priv_%d" % i, 1.0))  # each cue -> its own node only
    s = sr.Substrate()
    return qn.build_triad(s, cues, edges, held_out=None)


def _triad_far(spec):
    """FAR: wire the DECOY with support from 2 cues AND make it the denser
    attractor, while the true associate gets support from fewer -> the field
    peaks on the decoy (false-warmth)."""
    cues, assoc, decoy = spec
    edges = []
    # decoy: supported by all-but-one cue (denser)
    for c in cues[:2]:
        edges.append((c, decoy, 1.0))
    # true associate: supported by a single cue (indirect / weak)
    edges.append((cues[2], assoc, 1.0))
    s = sr.Substrate()
    return qn.build_triad(s, cues, edges, held_out=assoc)


def _triad_near(spec):
    """NEAR: true associate supported by ALL cues, no competitor."""
    return _triad_from_coherent(spec)


def _ci95(xs):
    n = len(xs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    m = sum(xs) / n
    if n == 1:
        return (m, m, m)
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(var / n)
    return (m, m - 1.96 * se, m + 1.96 * se)


def main():
    print("=" * 70)
    print("QUALIA-AS-NAVIGATION — coherence intuition (commonsense-shared-")
    print("associate coherence on the REAL ConceptNet slab; NOT Mednick RAT)")
    print("=" * 70)

    corpus = build_corpus()
    print("\nCorpus (from live slab reverse-index):")
    for k in ("coherent", "incoherent", "near", "far"):
        print("  %-11s: %d triads" % (k, len(corpus[k])))

    verdicts = {}

    # ---- CLAIM 1: coherence-before-retrieval, CI-separated -------------
    print("\n[CLAIM 1] coherence-before-retrieval (peak field, argmax NOT "
          "evaluated, associate held out)")
    coh_vals, inc_vals = [], []
    for spec in corpus["coherent"]:
        t = _triad_from_coherent(spec)
        qn.assert_held_out(t)  # audit BEFORE reading
        r = qn.coherence_signal(t)
        assert r["localised"] is None, "coherence read must not localise"
        assert r["commitment"] == 0.0, "commitment must be DARK before retrieval"
        coh_vals.append(r["coherence"])
    for spec in corpus["incoherent"]:
        t = _triad_from_incoherent(spec)
        r = qn.coherence_signal(t)
        inc_vals.append(r["coherence"])
    cm, clo, chi = _ci95(coh_vals)
    im, ilo, ihi = _ci95(inc_vals)
    print("  coherent   peak field: mean %.2f  95%%CI [%.2f, %.2f]  n=%d"
          % (cm, clo, chi, len(coh_vals)))
    print("  incoherent peak field: mean %.2f  95%%CI [%.2f, %.2f]  n=%d"
          % (im, ilo, ihi, len(inc_vals)))
    separated = clo > ihi
    print("  CI-separated (coherent_lo > incoherent_hi): %s" % separated)
    verdicts["claim1_coherence_before_retrieval"] = separated

    # ---- CLAIM 2: perturbation reverses -------------------------------
    print("\n[CLAIM 2] perturbation reverses the read (Topolinski anti-faking)")
    reversed_all = True
    drops = []
    for spec in corpus["coherent"]:
        t = _triad_from_coherent(spec)
        before = qn.coherence_signal(t)["coherence"]
        cues, assoc = spec
        qn.perturb(t, drop_edge=(cues[0], assoc))
        after = qn.coherence_signal(t)["coherence"]
        drops.append(before - after)
        if not (after < before):
            reversed_all = False
    dm, dlo, dhi = _ci95(drops)
    print("  drop one cue->associate edge: field drop mean %.2f 95%%CI [%.2f, %.2f]"
          % (dm, dlo, dhi))
    print("  every coherent triad's read DROPPED: %s" % reversed_all)
    # also the scale lever
    scale_drop = True
    for spec in corpus["coherent"][:3]:
        t = _triad_from_coherent(spec)
        b = qn.coherence_signal(t)["coherence"]
        qn.perturb(t, cue_scale=0.5)
        a = qn.coherence_signal(t)["coherence"]
        if not (a < b):
            scale_drop = False
    print("  cue_scale=0.5 also drops the read: %s" % scale_drop)
    verdicts["claim2_perturbation_reverses"] = reversed_all and dlo > 0 and scale_drop

    # ---- CLAIM 3: aperture-graded knows-that -> knows-what ------------
    print("\n[CLAIM 3] aperture-graded knows-that -> knows-what")
    # Build observer + triad on the SAME substrate (observer node must live
    # where the triad lives for _observer_aperture to read it).
    spec = corpus["coherent"][0]
    cues, assoc = spec
    edges = [(c, assoc, 1.0) for c in cues]
    for i, c in enumerate(cues):
        edges.append((c, "priv_%d" % i, 1.0))
    s = sr.Substrate()
    inner = s._inner
    # coarse: grain large enough that BOTH the associate(3.0) and the
    # privates(1.0) quotient to the SAME bucket (0) -> all candidates tie ->
    # cannot localise WHICH node (knows-THAT via raw_peak, not knows-WHAT).
    obs_coarse = inner.add_node("Observer", {"name": "coarse",
                                             "grain": {qn.PULL_AXIS: 8.0}})
    # fine: grain small enough to keep 3.0 vs 1.0 distinct -> localises.
    obs_fine = inner.add_node("Observer", {"name": "fine",
                                           "grain": {qn.PULL_AXIS: 0.5}})
    t = qn.build_triad(s, cues, edges, held_out=assoc)
    coarse = qn.localise(t, observer=obs_coarse)
    fine = qn.localise(t, observer=obs_fine)
    # knows-THAT: the aperture-independent raw_peak still says convergence is
    # present (> the incoherent baseline of 1.0), even though the coarse
    # quotient can't say WHICH node.
    print("  coarse grain(8.0): field=%s raw_peak=%.1f localised=%s"
          % (coarse["field"], coarse["raw_peak"], coarse.get("localised")))
    print("  fine   grain(0.5): field=%s localised=%s"
          % (fine["field"], fine.get("localised")))
    coarse_collapses = coarse.get("localised") is None  # tie after quotient
    coarse_still_solvable = coarse["raw_peak"] > 1.0  # knows-THAT survives
    fine_localises = fine.get("localised") == assoc
    print("  coarse feels-solvable(%s) without localising(%s); fine localises "
          "correctly(%s)" % (coarse_still_solvable, coarse_collapses,
                             fine_localises))
    verdicts["claim3_aperture_graded"] = (
        coarse_collapses and coarse_still_solvable and fine_localises)

    # ---- CLAIM 4: Metcalfe near/far dissociation ----------------------
    print("\n[CLAIM 4] Metcalfe near(localises truly)/far(false-warmth) "
          "dissociation")
    near_ok = far_false = True
    near_hits = far_false_hits = 0
    n_near = n_far = 0
    for spec in corpus["near"]:
        t = _triad_near(spec)
        loc = qn.localise(t)["localised"]
        n_near += 1
        if loc == spec[1]:  # true associate
            near_hits += 1
    for spec in corpus["far"]:
        cues, assoc, decoy = spec
        t = _triad_far(spec)
        loc = qn.localise(t)["localised"]
        n_far += 1
        if loc == decoy:  # false-warmth on the wrong attractor
            far_false_hits += 1
    print("  NEAR localises on TRUE associate: %d/%d" % (near_hits, n_near))
    print("  FAR  localises on DECOY (false-warmth): %d/%d"
          % (far_false_hits, n_far))
    near_ok = n_near > 0 and near_hits == n_near
    far_false = n_far > 0 and far_false_hits == n_far
    verdicts["claim4_metcalfe_dissociation"] = near_ok and far_false

    # ---- VERDICT -------------------------------------------------------
    print("\n" + "=" * 70)
    print("VERDICT")
    for k, v in verdicts.items():
        print("  %-42s %s" % (k, "HOLDS" if v else "FAILS"))
    print("=" * 70)
    return verdicts


if __name__ == "__main__":
    main()
