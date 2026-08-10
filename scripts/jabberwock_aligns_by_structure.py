"""jabberwock_aligns_by_structure — THE STYLE MANIFOLD ALIGNS BY ORDER-N
STRUCTURE, not just vocabulary.

The creator's point: 'the axes need to be ORDER N — the vocabulary isn't how
things align only.' The committed manifold (domains/cross_text_prior) located a
text by VOCABULARY (bag-of-content-words cosine) + flat register markers — so two
fables are 'near' because they share lion/fox, and a fable + a news article can
align on a few shared words. That is WRONG for STYLE.

This run adds STRUCTURAL axes at MULTIPLE nested levels — the levels the reader
already COMPREHENDS a text at (comprehension_reader.read_and_comprehend):

  * (order-2) CONSTRUCTION — the distribution of clause/argument patterns the
    clause parser produced (cop / intransitive / transitive / ditransitive).
  * (order-3) DISCOURSE   — the distribution of coherence relations the discourse
    layer decoded between spans (contrast / cause / sequence / elaboration / none).
  * (order-N) NARRATIVE   — the arc shape: the distribution of story-grammar roles
    (setup / problem / solution / action / consequence / resolution) + arc depth.

The location combines VOCABULARY (order-1, kept) + these structural axes into a
NESTED distance: two texts near iff they share structure at MULTIPLE levels, not
just words. Every gate runs behind the VOCABULARY null (struct_w=0).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_aligns_by_structure.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                               # noqa: E402
from domains import cross_text_prior as ctp                            # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  Two fables, SAME arc shape, DISJOINT vocabulary (no shared content word).
# --------------------------------------------------------------------------- #
FABLE_LION = ("A hungry lion saw a deer. The deer was fast. The lion set a trap. "
              "The deer fell. The lion feasted.")
FABLE_HAWK = ("A greedy hawk spotted a hare. The hare was quick. The hawk built a "
              "snare. The hare tumbled. The hawk gorged.")
# an encyclopedic text that SHARES the LION fable's vocabulary but has NO arc.
ENC_SHARED = ("The lion is a large cat. The deer is a herbivore. A trap is a "
              "device. The lion and the deer are animals. A cat is a predator.")
# a VOCABULARY DECOY: an encyclopedic list that SHARES the HAWK fable's content
# words (hawk / hare / snare) but is structurally a LIST (all copular, no arc) —
# vocabulary-cosine wrongly aligns the held-out hawk fable HERE; structure does not.
HAWK_LIST = ("A hawk is a bird. A hare is a mammal. A snare is a tool. The hawk "
             "and the hare are animals.")
# distractors (different vocab AND different structure).
NEWS_1 = ("The council approved a budget on Monday. Officials announced the plan. "
          "Residents will pay higher taxes next year.")
NEWS_2 = ("The mayor signed a contract yesterday. The company will build a bridge. "
          "Commuters expect delays during construction.")


def gate_a_same_arc_different_vocab(ag) -> dict:
    """(a) SAME-ARC-DIFFERENT-VOCABULARY ALIGN: two fables with DIFFERENT animals
    but the SAME arc shape locate NEAR on the narrative/structural axes, though
    vocabulary-cosine ALONE would NOT align them (no shared content words)."""
    sa = ctp.structural_signature(ag, FABLE_LION)
    sb = ctp.structural_signature(ag, FABLE_HAWK)
    lv = ctp.structural_level_distances(sa, sb)
    vocab_cos = ctp._cosine(ctp._content_freq(ag, FABLE_LION),
                            ctp._content_freq(ag, FABLE_HAWK))
    shared = set(ctp._content_freq(ag, FABLE_LION)) & set(ctp._content_freq(ag, FABLE_HAWK))
    struct_d = ctp._structural_distance(sa, sb)

    # the MANIFOLD test: prime the same-arc fable (DISJOINT vocab), a VOCABULARY
    # DECOY (shares the held-out fable's words but is a structureless list), and a
    # news distractor. Hold out the HAWK fable. Rank by (i) pure vocabulary cosine
    # and (ii) the ORDER-N structural distance, and show the nearest FLIPS from the
    # decoy (vocabulary's wrong pick) to the same-arc fable (structure's right one).
    prime = _fresh()
    ctp.accumulate_text(prime, FABLE_LION, label="fable-lion", structural=True)
    ctp.accumulate_text(prime, HAWK_LIST, label="hawk-list-DECOY", structural=True)
    ctp.accumulate_text(prime, NEWS_1, label="news-1", structural=True)

    held = ctp._content_freq(ag, FABLE_HAWK)
    held_sig = ctp.structural_signature(ag, FABLE_HAWK)
    rows = []
    for nn in ctp.points(prime):
        lbl = prime.s.node(nn)["attrs"].get("label")
        pwc = ctp._point_word_counts(prime.s, nn)
        vd = 1.0 - ctp._cosine(held, ctp._content_only(pwc))
        sd = ctp._structural_distance(held_sig, ctp._point_structural_sig(prime.s, nn))
        rows.append((lbl, vd, sd))
    vocab_rank = sorted(rows, key=lambda r: r[1])
    struct_rank = sorted(rows, key=lambda r: r[2])
    return {"vocab_cosine_fableA_fableB": vocab_cos,
            "shared_content_words_between_fables": sorted(shared),
            "structural_distance_fableA_fableB": struct_d, "level_distances": lv,
            "vocab_only_nearest": vocab_rank[0][0],
            "structure_nearest": struct_rank[0][0],
            "vocab_ranking": [(l, round(v, 4)) for l, v, _ in vocab_rank],
            "structure_ranking": [(l, round(s, 4)) for l, _, s in struct_rank]}


def gate_b_shared_vocab_different_structure(ag) -> dict:
    """(b) SHARED-VOCABULARY-DIFFERENT-STRUCTURE SEPARATE: two texts with
    overlapping words but different construction/discourse/arc locate APART on the
    structural axes (vocabulary-cosine alone would align them)."""
    sf = ctp.structural_signature(ag, FABLE_LION)
    se = ctp.structural_signature(ag, ENC_SHARED)
    lv = ctp.structural_level_distances(sf, se)
    vocab_cos = ctp._cosine(ctp._content_freq(ag, FABLE_LION),
                            ctp._content_freq(ag, ENC_SHARED))
    shared = set(ctp._content_freq(ag, FABLE_LION)) & set(ctp._content_freq(ag, ENC_SHARED))
    struct_d = ctp._structural_distance(sf, se)
    return {"vocab_cosine": vocab_cos, "shared_content_words": sorted(shared),
            "structural_distance": struct_d, "level_distances": lv}


def gate_c_load_bearing_per_level(ag) -> dict:
    """(c) LOAD-BEARING per-level: a text's nearest-neighbour structural distance
    decomposed by level (vocabulary vs construction vs discourse vs narrative) —
    which level actually carries the alignment."""
    # fable vs fable (same arc): expect narrative + construction ~0.
    ff = ctp.structural_level_distances(ctp.structural_signature(ag, FABLE_LION),
                                        ctp.structural_signature(ag, FABLE_HAWK))
    # fable vs encyclopedic (shared vocab): expect narrative + construction high.
    fe = ctp.structural_level_distances(ctp.structural_signature(ag, FABLE_LION),
                                        ctp.structural_signature(ag, ENC_SHARED))
    return {"fable_vs_fable_levels": ff, "fable_vs_encyclopedic_levels": fe}


def _load_genre(genre: str, cap: int) -> list:
    p = Path(ROOT) / "data" / "hf_corpus" / (genre + ".json")
    if not p.exists():
        return []
    rows = json.loads(p.read_text())
    out = []
    for r in rows:
        t = (r.get("text") or "").strip()
        if len(t) >= 120:                              # skip too-short units
            out.append(t)
        if len(out) >= cap:
            break
    return out


def gate_d_real_corpus_clustering(ag, *, genres=("stories", "news", "wikipedia"),
                                  cap: int = 4) -> dict:
    """(d) REAL CORPUS: does ORDER-N alignment cluster by GENRE better than
    vocabulary-alone? Measure within-genre vs cross-genre MEAN distance for the
    vocabulary-only metric vs the vocabulary+structure metric; the SEPARATION
    (cross - within) is the clustering signal. Structure improves it iff its
    separation is larger."""
    texts = {}                                         # genre -> [text, ...]
    sigs = {}                                          # (genre,i) -> struct sig
    vocs = {}                                          # (genre,i) -> content freq
    for g in genres:
        texts[g] = _load_genre(g, cap)
        for i, t in enumerate(texts[g]):
            sigs[(g, i)] = ctp.structural_signature(ag, t)
            vocs[(g, i)] = ctp._content_freq(ag, t)

    keys = [(g, i) for g in genres for i in range(len(texts[g]))]

    def voc_d(ka, kb):
        return 1.0 - ctp._cosine(vocs[ka], vocs[kb])

    def struct_d(ka, kb):
        return ctp._structural_distance(sigs[ka], sigs[kb])

    within_v, cross_v, within_s, cross_s = [], [], [], []
    within_b, cross_b = [], []                          # blended (vocab+structure)
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            ka, kb = keys[a], keys[b]
            vd, sd = voc_d(ka, kb), struct_d(ka, kb)
            bd = 0.6 * vd + 0.4 * sd                    # the blended metric
            same = ka[0] == kb[0]
            (within_v if same else cross_v).append(vd)
            (within_s if same else cross_s).append(sd)
            (within_b if same else cross_b).append(bd)

    def mean(x):
        return sum(x) / len(x) if x else 0.0

    sep_v = mean(cross_v) - mean(within_v)
    sep_s = mean(cross_s) - mean(within_s)
    sep_b = mean(cross_b) - mean(within_b)
    # SCALE-FREE separation ratio (cross/within): bag-of-words distances saturate
    # near 1.0 (sparse vectors ~orthogonal both within AND cross), so the ABSOLUTE
    # gap understates a metric whose distances live on a smaller scale. The ratio
    # is the honest cross-scale comparison — how many times farther cross-genre is.
    def ratio(cross, within):
        return (mean(cross) / mean(within)) if mean(within) else float("inf")
    rv, rs, rb = (ratio(cross_v, within_v), ratio(cross_s, within_s),
                  ratio(cross_b, within_b))
    return {"genres": list(genres), "n_per_genre": {g: len(texts[g]) for g in genres},
            "vocab_within": mean(within_v), "vocab_cross": mean(cross_v),
            "vocab_separation_abs": sep_v, "vocab_separation_ratio": rv,
            "struct_within": mean(within_s), "struct_cross": mean(cross_s),
            "struct_separation_abs": sep_s, "struct_separation_ratio": rs,
            "blended_within": mean(within_b), "blended_cross": mean(cross_b),
            "blended_separation_abs": sep_b, "blended_separation_ratio": rb,
            "structure_ratio_beats_vocab": rs > rv,
            "blend_ratio_beats_vocab": rb > rv}


def main():
    ag = _fresh()
    print("=" * 72)
    print("GATE (a) — SAME-ARC-DIFFERENT-VOCABULARY ALIGN")
    a = gate_a_same_arc_different_vocab(ag)
    print(json.dumps(a, indent=2, default=str))
    print("=" * 72)
    print("GATE (b) — SHARED-VOCABULARY-DIFFERENT-STRUCTURE SEPARATE")
    print(json.dumps(gate_b_shared_vocab_different_structure(ag), indent=2, default=str))
    print("=" * 72)
    print("GATE (c) — LOAD-BEARING per-level contribution")
    print(json.dumps(gate_c_load_bearing_per_level(ag), indent=2, default=str))
    print("=" * 72)
    print("GATE (d) — REAL-CORPUS genre clustering vs vocabulary baseline")
    print(json.dumps(gate_d_real_corpus_clustering(ag), indent=2, default=str))


if __name__ == "__main__":
    main()
