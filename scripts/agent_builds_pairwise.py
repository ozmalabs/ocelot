"""The agent builds the pairwise recognition it asked for, via its own self-build.

It develops (its own loop), then SPECIFIES the pairwise tie-breaks from its own state
(agent_specify_pairwise reads its Confusions + ConfusionBands), then the mechanical
generator's tie-break Term is evaluated natively on HELD-OUT test clips of each
confused pair. We measure on the agent's OWN metric: for the pairs it confuses, does
its chosen band — used PAIRWISE — tell them apart, where its global recognition could
not? No benchmark chased.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.ask_agent as aa
import scripts.fsdd_learner_world as fl
from domains.acoustic_resolution import enrich_sign_bands, get_resolution
from domains.pairwise_recognition import agent_specify_pairwise, tie_break_term
from substrate_rs import Substrate


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    sub, pipe, test_set, vc, rec = aa._develop(cycles=10)
    res = get_resolution(sub)
    spec = agent_specify_pairwise(sub, top_k=8)

    print("\n====  The agent specified its pairwise tie-breaks (from its own state):  ====\n")
    for e in spec:
        print(f"  '{e['A']}' vs '{e['B']}' (confused x{e['count']}): use {e['band']} "
              f"— means {e['a_mean']:.3f} / {e['b_mean']:.3f}, Fisher {e['fisher']:.2f}")

    # held-out test clips by word
    by_word = {}
    for path, digit, sp, idx in test_set:
        by_word.setdefault(fl._DIGITS[digit], []).append(path)

    def band_of(path, band):
        s, _ = fl.load_wav(path)
        pipe.ingest(sub, s)
        sub.tick(50000)
        st = None
        for n in sub.nodes("AudioStream"):
            st = n
        sgs = fl._collect_signs_from_stream(sub, st) if st else []
        enrich_sign_bands(sub, signs=sgs)
        vals = [sub.node(g)["attrs"].get(band) for g in sgs
                if sub.node(g)["attrs"].get(band) is not None]
        return sum(vals) / len(vals) if vals else None

    print("\n====  Tested PAIRWISE on held-out clips (the agent's band, used only for "
          "that pair):  ====\n")
    for e in spec:
        A, B, band = e["A"], e["B"], e["band"]
        if band is None:
            continue
        term = tie_break_term(e)        # closer to a_mean -> A
        ok = n = 0
        for true_w in (A, B):
            for p in by_word.get(true_w, [])[:8]:
                v = band_of(p, band)
                if v is None:
                    continue
                n += 1
                pick_A = bool(sub.evaluate(_Pred(term), {"s": _clip_sign(sub, band, v)}))
                if (pick_A and true_w == A) or (not pick_A and true_w == B):
                    ok += 1
        if n:
            print(f"  '{A}'/'{B}' via {band}: {ok}/{n} = {100*ok//n}% pairwise "
                  f"(chance 50%)")


def _clip_sign(sub, band, value):
    """A throwaway node carrying just the band value, so the agent's tie-break Term
    evaluates on it (the term reads Attr(s, band))."""
    n = sub.add_node("AcousticSign", {band: float(value), "origin": "probe"})
    return n


if __name__ == "__main__":
    main()
