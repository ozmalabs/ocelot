"""The agent autonomously assesses its FULL feature menu on its own confusions — in
the loop, no teacher, no orchestration.

The peer's role has shrunk to nothing here: the menu of cues IS the agent's feature
vocabulary, and the assessing is its own. For every pair it confuses, it composes
every cue, measures each one's separation on the confused words' OWN signs, and
grounds the single best as a feature it keeps — but only if that cue beats its current
whole-word separation. It is its own do-contrast over its own vocabulary; it grounds
what works and ignores the rest (including leaving a pair alone when nothing beats its
plain average). Wired into the developmental cycle, this is how it cracks its
confusions by itself, every cycle. See [[ozma_meta_abilities_are_leverage]] /
[[ozma_ideas_outside_the_seed]] (free generation; the SELECTOR is everything) /
[[ozma_agent_builds_pairwise]].
"""
from __future__ import annotations

import numpy as np

from domains.hint_grounding import compose_from_spec, CUE_MENU
from domains.acoustic_resolution import (enrich_sign_bands, enrich_sign_windows,
                                          enrich_sign_fft)


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _fisher(a, b) -> float:
    a = np.array([x for x in a if x == x])
    b = np.array([x for x in b if x == x])
    if len(a) < 2 or len(b) < 2:
        return 0.0
    return abs(a.mean() - b.mean()) / (a.std() + b.std() + 1e-6)


def agent_assess_cues(substrate, pipe, test_set, res: int,
                      fisher_floor: float = 0.8) -> list:
    """The agent assesses its full feature menu on each confusion and grounds the best
    separating cue (kept only if it beats the whole-word average). Returns the cues it
    grounded: [(X, Y, cue, fisher, baseline)]."""
    import scripts.fsdd_learner_world as fl
    terms = {c: compose_from_spec(res, c) for c in CUE_MENU}
    byword: dict = {}                       # word -> {cue: [vals], '_whole': [vals]}
    for path, digit, sp, idx in test_set:
        s, fs = fl.load_wav(path)
        pipe.ingest(substrate, s)
        substrate.tick(50000)
        st = None
        for n in substrate.nodes("AudioStream"):
            st = n
        sg = fl._collect_signs_from_stream(substrate, st) if st else []
        enrich_sign_bands(substrate, resolution=res, signs=sg)
        enrich_sign_windows(substrate, resolution=res, signs=sg)
        # the frequency-sharp second ear: linear-FFT bands the formant cues read
        enrich_sign_fft(substrate, signs=sg)
        d = byword.setdefault(fl._DIGITS[digit], {c: [] for c in CUE_MENU})
        d.setdefault("_whole", [])
        for g in sg:
            for c, t in terms.items():
                try:
                    d[c].append(float(substrate.evaluate(_P(t), {"s": g})))
                except Exception:
                    pass
            v = [substrate.node(g)["attrs"].get(f"band{res}_{i}") for i in range(res)]
            if all(x is not None for x in v):
                d["_whole"].append(float(np.mean(v)))

    have = {substrate.node(c)["attrs"].get("name") for c in substrate.nodes("Concept")
            if substrate.node(c)["attrs"].get("feature_kind") == "assessed_cue"}
    grounded = []
    for c in substrate.nodes("Confusion"):
        a = substrate.node(c)["attrs"]
        X, Y = a.get("true_word"), a.get("pred_word")
        if X not in byword or Y not in byword:
            continue
        base = _fisher(byword[X]["_whole"], byword[Y]["_whole"])
        best_f, best_c = base, None
        for cue in CUE_MENU:
            f = _fisher(byword[X][cue], byword[Y][cue])
            if f > best_f:
                best_f, best_c = f, cue
        name = f"cue_{best_c}_{X}_v_{Y}"
        if best_c and best_f > fisher_floor and name not in have:
            substrate.add_node("Concept", {
                "name": name, "feature_kind": "assessed_cue", "cue": best_c,
                "pair": f"{X}/{Y}", "predicate": compose_from_spec(res, best_c),
                "fisher": float(best_f), "baseline": float(base),
                "origin": "phonology", "composed_by": "agent", "assessed": 1})
            grounded.append((X, Y, best_c, best_f, base))
    return grounded


__all__ = ["agent_assess_cues"]
