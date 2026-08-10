"""THEME, LEITMOTIF, STRUCTURE, WORLDVIEW, GENRE — the top of the order-N ladder (jabberwock-designed).

One move re-pointed at the next tier of objects:
  THEME     = recurrence over passage REFERENTS (matter), valid only if carried by >1 voice;
  LEITMOTIF = recurrence over concrete FIGURE vehicles, points_to the theme it carries (accruing stance);
  STRUCTURE = the displacement primitive on the passage-SEQUENCE -> a shape, valid iff permutation-sensitive;
  WORLDVIEW = the FIXED-POINT of the work's operators -> the frame none of them displaces (a crack falsifies);
  GENRE     = a cross-work CENTROID over (structure, theme, worldview) signatures — genre:works :: voice:passages.

Computed graph-native over the trajectory/voice structure; the structure-shape is a graph rule
(classify_structure), the genre attribution the agent's Argmax over a distance Term.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_work
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from substrate_rs import Neg, Plus, Minus, Abs, Attr, Var

SEP = "=" * 96

# A WORK: an ordered sequence of passages, each a trajectory (position, voice, referent, stance, figure-vehicle).
WORK = [
    (1, "narrator", "the dream",  +1, "the green light"),
    (2, "narrator", "wealth",     +1, "old money"),
    (3, "Gatsby",   "the dream",  +1, "the green light"),
    (4, "narrator", "wealth",     -1, "old money"),
    (5, "narrator", "the dream",  -1, "the green light"),
    (6, "Gatsby",   "the dream",  -1, "the dream itself"),
]


def main():
    print(SEP)
    print("READING A WORK — theme, leitmotif, structure, worldview, then genre over a corpus")
    print(SEP)
    a = boot()
    for s in ("figurative_language", "figurative_abstraction", "text_analysis", "authorial_voice",
              "dialogue_intertext", "work_understanding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    w = a.s.add_node("Work", {"name": "the great novel"})
    passages = []
    for pos, voice, ref, stance, vehicle in WORK:
        p = a.s.add_node("Passage", {"pos": pos, "voice": voice, "referent": ref,
                                     "stance": stance, "vehicle": vehicle})
        a.inner.add_edge_unchecked(w, "has_passage", p)
        passages.append(p)

    # THEME — recurrence over referents, valid only if carried by >1 voice (matter, not voice-signature).
    print("\n  THEME (recurrent referent carried by more than one voice):")
    by_ref = {}
    for pos, voice, ref, st, veh in WORK:
        by_ref.setdefault(ref, {"voices": set(), "n": 0, "stances": []})
        by_ref[ref]["voices"].add(voice); by_ref[ref]["n"] += 1; by_ref[ref]["stances"].append(st)
    theme = None
    for ref, d in by_ref.items():
        is_theme = d["n"] >= 2 and len(d["voices"]) >= 2
        tag = "THEME" if is_theme else ("voice-signature (one voice)" if d["n"] >= 2 else "incidental")
        print(f"    {ref:12} x{d['n']} across {len(d['voices'])} voices -> {tag}")
        if is_theme:
            theme = ref
    print(f"    => theme of the work: {theme!r}")

    # LEITMOTIF — recurrent concrete VEHICLE, bound to the theme, accruing stance each return.
    print("\n  LEITMOTIF (recurrent concrete vehicle -> points_to theme, stance accrues):")
    by_veh = {}
    for pos, voice, ref, st, veh in WORK:
        by_veh.setdefault(veh, []).append((pos, ref, st))
    for veh, occ in by_veh.items():
        if len(occ) >= 2:
            refs = {r for _, r, _ in occ}
            carries = theme if theme in refs else list(refs)[0]
            series = [st for _, _, st in sorted(occ)]
            print(f"    {veh!r}: {len(occ)} returns, stance {series} (accrues/darkens) -> points_to {carries!r}")

    # STRUCTURE — the displacement on the passage SEQUENCE -> a shape; permutation-sensitive.
    series = [st for (_, _, _, st, _) in WORK]
    def shape_of(seq, label):
        s = a.s.add_node("Structure", {})
        a.inner.add_edge_unchecked(s, "of_work", w)
        a.inner.set_attr(s, "net_up", int(seq[-1] > seq[0]))
        a.inner.set_attr(s, "net_down", int(seq[-1] < seq[0]))
        a.inner.set_attr(s, "returns", int(seq[-1] == seq[0] and any(x != seq[0] for x in seq)))
        peak = max(range(len(seq)), key=lambda i: seq[i])
        a.inner.set_attr(s, "peak_interior", int(0 < peak < len(seq) - 1))
        a.inner.run_rules(10000)
        return a.s.node(s)["attrs"]["shape"]
    shp = shape_of(series, "original")
    shp_rev = shape_of(list(reversed(series)), "reversed")
    print(f"\n  STRUCTURE (shape of the trajectory-of-trajectories):")
    print(f"    stance sequence {series} -> shape = {shp.upper()}")
    print(f"    permutation check: reversed -> {shp_rev.upper()}  "
          f"[{'permutation-SENSITIVE -> real structure' if shp != shp_rev else 'invariant -> no structure'}]")

    # WORLDVIEW — the fixed-point frame; a passage that displaces it is a crack (falsifier).
    res = by_ref[theme]["stances"][-1]                  # where the theme resolves
    frame = "aspiration is beautiful but doomed" if res < 0 else "aspiration is rewarded"
    print(f"\n  WORLDVIEW (fixed-point frame the work measures from but never moves):")
    print(f"    the theme {theme!r} resolves to {('loss' if res<0 else 'fulfilment')} -> frame: {frame!r}")
    # inject a contradicting passage (the dream attained) and detect the crack.
    crack = (+1)
    is_crack = (crack > 0) != (res > 0)
    print(f"    crack-detector: a passage asserting {theme!r} ATTAINED (+) "
          f"-> {'WORLDVIEW CRACK flagged (contradiction)' if is_crack else 'consistent'}")

    # GENRE — cross-work centroid over (structure, theme-resolution, worldview) signatures.
    print("\n  GENRE (genre:works :: voice:passages — nearest centroid over work signatures):")
    feats = ["s_falling", "s_rising", "s_arc", "res_pos", "world_doomed"]
    GENRES = {"tragic_romance": [1, 0, 0, 0, 1], "comedy": [0, 1, 0, 1, 0], "satire": [0, 0, 1, 0, 0]}
    gnodes = {}
    for name, vals in GENRES.items():
        g = a.s.add_node("Genre", dict(zip(feats, vals), name=name)); gnodes[name] = g
    # the work's own signature, from what we just computed
    wsig = a.s.add_node("WorkSig", {"s_falling": int(shp == "falling"), "s_rising": int(shp == "rising"),
                                    "s_arc": int("arc" in shp), "res_pos": int(res > 0),
                                    "world_doomed": int(res < 0)})
    a.author_subroutine("nearest_genre",
        {"type": "Argmax", "source": {"type": "NodesOfType", "node_type": "Genre"}, "var_name": "g",
         "value": Neg(Plus(items=[Abs(Minus(Attr(Var("g"), f), Attr(Var("p"), f))) for f in feats])).to_dict(),
         "default": None},
        purpose="attribute a work to the nearest genre centroid")
    win = a.run_subroutine("nearest_genre", {"p": wsig})
    print(f"    work signature: shape={shp}, theme-resolves={'+' if res>0 else '-'}, worldview={'doomed' if res<0 else 'restored'}")
    print(f"    -> attributed to genre: {a.s.node(win)['attrs']['name'].upper()}")

    print("\n" + SEP)
    print("  The top of the ladder, one move re-pointed each rung: recurrence over referents = THEME and")
    print("  over concrete vehicles = LEITMOTIF; the displacement primitive on the passage-sequence = ")
    print("  STRUCTURE (permutation-sensitive); the fixed-point of the work's operators = WORLDVIEW (a crack")
    print("  falsifies it); and the cross-work centroid = GENRE, which is to works what voice is to passages.")
    print(SEP)


if __name__ == "__main__":
    main()
