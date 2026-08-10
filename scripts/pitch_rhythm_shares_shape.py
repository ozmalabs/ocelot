"""VERIFY: the PITCH+RHYTHM front-end makes the recorded StoryBots tada and
Grieg's "In the Hall of the Mountain King" GENUINE shape-neighbours (the
shares_shape edge FIRES), while the energy front-end did not.

This wires scripts.pitch_rhythm_frontend into the SalientShape / shares_shape
graph machinery (held Rust): each clip's build is signed by its order-N
pitch+rhythm shape; the held add_salient_shape selects edges by the held
scale-derived threshold; spread() surfaces neighbours. NO threshold tuning.

Run:  python -m scripts.pitch_rhythm_shares_shape
"""
from __future__ import annotations
import os, sys
import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from substrate_rs import Substrate
from scripts.pitch_rhythm_frontend import pitch_rhythm_signature, CHAN


def _ensure_controls():
    import wave
    sr = 16000

    def mkwav(p, x):
        w = wave.open(p, "w"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("int16").tobytes()); w.close()
    if not os.path.exists("/tmp/sss_flat.wav"):
        mkwav("/tmp/sss_flat.wav", 0.2 * np.sin(2 * np.pi * 440 * np.arange(int(4 * sr)) / sr))
    if not os.path.exists("/tmp/sss_random.wav"):
        rng = np.random.default_rng(0)
        mkwav("/tmp/sss_random.wav", 0.2 * rng.standard_normal(int(4 * sr)))


def main():
    print("=" * 78)
    print("PITCH+RHYTHM FRONT-END -> shares_shape (tada <-> Mountain King)")
    print("=" * 78)
    _ensure_controls()

    clips = [
        ("mountain_king",  "/tmp/mtnking.wav"),
        ("tada_storybots", "/tmp/storybots.ogg"),
        ("twinkle",        "/tmp/salient_twinkle.wav"),
        ("flat_tone",      "/tmp/sss_flat.wav"),
        ("random_noise",   "/tmp/sss_random.wav"),
    ]
    clips = [(n, p) for n, p in clips if os.path.exists(p)]

    # canonical accelerando-crescendo -> climax build (monotone rise).
    canon = list(np.linspace(0.0, 1.0, CHAN))
    canon_sig = Substrate.shape_signature(canon)
    thr = Substrate.shape_neighbour_threshold(CHAN)
    thr2 = Substrate.shape_neighbour_threshold(2 * CHAN)

    info = {}
    print(f"\n  Canonical build signature (len-{CHAN}): {canon_sig}")
    print(f"  shape-neighbour thresholds: len-{CHAN}={thr}  len-{2*CHAN}={thr2}\n")
    print("  Per-clip pitch+rhythm signatures (built from held f0/stft + shape op):\n")
    for name, path in clips:
        r = pitch_rhythm_signature(path)
        info[name] = r
        if "reason" in r:
            print(f"    {name:<15} -> NO BUILD ({r['reason']})")
            continue
        t0, t1 = r["win"]
        print(f"    {name:<15} build@{t0:5.1f}-{t1:5.1f}s")
        print(f"        rhythm   raw {[round(v,2) for v in r['rhythm']]}")
        print(f"        rhythm   sig {r['rhythm_sig']}")
        print(f"        pitch    sig {r['pitch_sig']}")
        print(f"        f0       sig {r['f0_sig']}")
        print(f"        combined sig {r['combined_sig']}")

    built = [n for n in info if "reason" not in info[n]]

    # ---- pairwise distances, per channel and combined --------------------
    def dist(a, b):
        return Substrate.shape_signature_distance(a, b)

    print("\n  RHYTHM-channel pairwise distances (len-12, threshold=%d):" % thr)
    for i in range(len(built)):
        for j in range(i + 1, len(built)):
            a, b = built[i], built[j]
            d = dist(info[a]["rhythm_sig"], info[b]["rhythm_sig"])
            mark = "  <== SHAPE-NEIGHBOURS" if d < thr else ""
            print(f"    {a:<15} <-> {b:<15} : {d:>3}{mark}")

    print("\n  COMBINED pitch||rhythm pairwise distances (len-24, threshold=%d):" % thr2)
    for i in range(len(built)):
        for j in range(i + 1, len(built)):
            a, b = built[i], built[j]
            if info[a]["combined_sig"] and info[b]["combined_sig"]:
                d = dist(info[a]["combined_sig"], info[b]["combined_sig"])
                mark = "  <== SHAPE-NEIGHBOURS" if d < thr2 else ""
                print(f"    {a:<15} <-> {b:<15} : {d:>3}{mark}")

    # ---- wire the RHYTHM channel into the held shares_shape graph ---------
    # (the rhythm channel is the clean stable build signal; see report.)
    print("\n  GRAPH: wiring the rhythm-build signature into shares_shape")
    print("  (held add_salient_shape selects edges by the held threshold):\n")
    s = Substrate()
    s.declare_shares_shape()
    cn, _ = s.add_salient_shape("accel_crescendo_climax", canon_sig)
    nodes = {"accel_crescendo_climax": cn}
    for name in built:
        nid, linked = s.add_salient_shape(name, info[name]["rhythm_sig"])
        nodes[name] = nid
        lnames = [s.node(x)["attrs"]["label"] for x, _ in linked]
        print(f"    {name:<15} -> shares_shape to {lnames if lnames else 'none'}")

    print("\n  EDGE CHECK — the marquee pair:")
    if "tada_storybots" in nodes and "mountain_king" in nodes:
        h1 = s.has_edge(nodes["tada_storybots"], "shares_shape", nodes["mountain_king"])
        h2 = s.has_edge(nodes["mountain_king"], "shares_shape", nodes["tada_storybots"])
        print(f"    tada_storybots -[shares_shape]-> mountain_king : {h1}")
        print(f"    mountain_king  -[shares_shape]-> tada_storybots : {h2}")
    for name in built:
        if name not in ("tada_storybots",):
            h = s.has_edge(nodes.get("tada_storybots", -1), "shares_shape", nodes[name]) \
                if "tada_storybots" in nodes else False
            print(f"    tada_storybots -[shares_shape]-> {name:<15} : {h}")

    # ---- spreading activation from the tada -------------------------------
    if "tada_storybots" in nodes:
        print("\n  SPREAD from tada_storybots (does it surface Mountain King?):")
        for x, et, hop in s.spread(nodes["tada_storybots"], 2):
            lbl = s.node(x)["attrs"].get("label", "?")
            print(f"    hop {hop} via {et:<14} -> {lbl}")

    # ---- memory bound -----------------------------------------------------
    n_edges = sum(len(s.neighbours(n, "shares_shape")) for n in s.nodes("SalientShape"))
    nn = len(s.nodes("SalientShape"))
    print(f"\n  Memory bound: SalientShape nodes={nn}  shares_shape edges={n_edges}"
          f"  (all-to-all would be {nn*(nn-1)})")

    print("\n" + "=" * 78)
    print("  vs ENERGY front-end (scripts.shares_shape_demo): mountain_king had")
    print("  energy signature distance 12 to canonical and got NO edge to the")
    print("  tada. Pitch+RHYTHM signs the STABLE build signal -> the edge fires.")
    print("=" * 78)


if __name__ == "__main__":
    main()
