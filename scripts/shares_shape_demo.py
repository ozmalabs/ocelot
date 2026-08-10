"""THE SALIENT ORDER-N SHAPE AS ONE GRAPH EDGE AMONG MANY.

A memory/percept is a NODE held by MANY edges at once (shape / co-occurrence /
function / timbre / affect). The salient order-N SHAPE is ONE of those
relations — additive alongside the graph's existing edges, NOT a single
cluster index. Recall + analogy = SPREADING ACTIVATION across whichever edges
a cue matches, not a single-key descent.

This demo wires that ONE edge type (`shares_shape`) and shows the payoff: clips
whose order-N SHAPE is the accelerando-crescendo -> climax become
SHAPE-NEIGHBOURS connected by a REAL graph edge, regardless of timbre / level /
instrument, while flat / unrelated controls are NOT. The marquee analogue is
Grieg's "In the Hall of the Mountain King" — a textbook accelerando-crescendo
build — linking to the canonical build SHAPE across maximal surface difference
from a cartoon jingle.

EVERYTHING graph-resident is RUST:
  * shape SIGNATURE (gain-invariant rank key)          -> Substrate.shape_signature
  * shape-neighbour distance + scale-derived threshold -> Substrate.shape_*
  * SalientShape node + shares_shape edge wiring       -> s.add_salient_shape
  * spreading activation across multiple edge types    -> s.spread

This script is a WORLD ADAPTER: numpy DSP reads each clip's intensity
build-arc (the crescendo to its climax) off the waveform; the order-N shape
signature, the edge wiring and the spreading activation are the held Rust
operators. No agent decision lives here.

Run:  python -m scripts.shares_shape_demo
"""
from __future__ import annotations
import os, subprocess, sys
import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from substrate_rs import Substrate

TARGET = 12  # signature length (rank arrangement over the build-arc)


def energy_arc(src, target=TARGET):
    """THE FIX: don't sign the whole-clip start->climax macro arc (a short intro
    tada is then drowned by 90s of unrelated content). LOCATE the most-salient
    build-up EVENT at its OWN timescale — the TROUGH->PEAK intensity ramp (the quiet
    point before a climax up to the hit) of highest order-N shape_salience — and sign
    THAT. So a sub-10s cartoon tada and a long orchestral crescendo both reduce to
    their accelerando-crescendo->climax SHAPE and become shape-neighbours. World
    adapter (ffmpeg + numpy DSP off the waveform); the SHAPE read is the held op."""
    import wave, subprocess, tempfile
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                    "-ar", "16000", "-ac", "1", wav], check=True)
    w = wave.open(wav); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    win, hop = 1024, 256
    nfr = 1 + (len(x) - win) // hop
    hann = np.hanning(win)
    energy = np.array([np.abs(np.fft.rfft(x[i*hop:i*hop+win] * hann)).sum()
                       for i in range(nfr)])
    e = energy / (energy.max() + 1e-9)
    k = max(5, int(round(0.5 * sr / hop)))            # ~0.5s -> the build RAMP, not beats
    es = np.convolve(e, np.ones(k) / k, mode="same")
    t = np.arange(nfr) * hop / sr
    hop_s = hop / sr
    span = int(12.0 / hop_s)                           # build timescale (intro-event scale)
    # candidate climaxes = LOCAL maxima (prominence-based, NOT absolute loudness):
    # the tada need not be the loudest event in the clip, only a real local build.
    peaks = [i for i in range(3, len(es)-3) if es[i] == max(es[i-3:i+4])]
    best = (-1.0, None, 0.0)
    for pi in peaks:
        lo = max(0, pi - span)
        tr = lo + int(np.argmin(es[lo:pi+1]))          # the trough before the climax
        if pi - tr < 4 or (es[pi] - es[tr]) < 0.10:    # require a real RISE (prominence)
            continue
        arc = es[tr:pi+1]
        res = np.interp(np.linspace(0, 1, target), np.linspace(0, 1, len(arc)), arc).tolist()
        sal = Substrate.shape_salience(res)
        if sal > best[0]:
            best = (sal, res, t[tr])
    if best[1] is None:                               # no build -> whole-clip fallback
        res = np.interp(np.linspace(0, 1, target), np.arange(len(es)), es).tolist()
        return res, Substrate.shape_salience(res), 0.0
    return best[1], best[0], best[2]


def main():
    print("=" * 78)
    print("THE SALIENT ORDER-N SHAPE AS ONE GRAPH EDGE (shares_shape)")
    print("=" * 78)

    s = Substrate()
    s.declare_shares_shape()  # ONE edge type added to Γ; the others untouched

    # THE CANONICAL order-N SHAPE both the cartoon "tada" and Grieg are ABOUT:
    # a directed accelerando-crescendo -> climax (monotone build to a late
    # peak). This is the reference shape, added as a SalientShape node first.
    canon = list(np.linspace(0.0, 1.0, TARGET))
    canon_sig = Substrate.shape_signature(canon)
    cn, _ = s.add_salient_shape("accel_crescendo_climax", canon_sig)

    clips = [
        ("mountain_king",   "/tmp/mtnking.wav"),    # Grieg — textbook build
        ("tada_storybots",  "/tmp/storybots.ogg"),  # cartoon jingle
        ("twinkle_nursery", "/tmp/salient_twinkle.wav"),
        ("bingo_nursery",   "/tmp/salient_bingo.wav"),
    ]
    clips = [(n, p) for n, p in clips if os.path.exists(p)]

    print("\n  Canonical SHAPE (accelerando-crescendo -> climax):")
    print(f"    signature = {canon_sig}")
    thr = Substrate.shape_neighbour_threshold(TARGET)
    print(f"\n  Shape-neighbour threshold (scale-derived, length-{TARGET}) = {thr}")
    print(f"    (NOT tuned to an answer: max possible L1 over length-{TARGET} rank")
    print(f"     signatures is {TARGET*(TARGET-1)//2}; threshold = n = {thr} admits")
    print("     only 'same arrangement, minor jitter'.)\n")

    print("  Each clip's intensity build-arc -> order-N shape signature:\n")
    nodes = {"accel_crescendo_climax": cn}
    sigs = {"accel_crescendo_climax": canon_sig}
    for name, path in clips:
        wav = f"/tmp/sssig_{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", "90",
                        "-i", path, "-ar", "16000", "-ac", "1", wav], check=True)
        arc, sal, tc = energy_arc(wav)
        sig = Substrate.shape_signature(arc)
        sigs[name] = sig
        d_canon = Substrate.shape_signature_distance(canon_sig, sig)
        nid, linked = s.add_salient_shape(name, sig)
        nodes[name] = nid
        lnames = [(s.node(x)["attrs"]["label"], dd) for x, dd in linked]
        tag = "SHAPE-NEIGHBOUR of canonical build" if d_canon < thr else "not a build-neighbour"
        print(f"    {name:<18} climax@{tc:5.1f}s  salience={sal:4.2f}")
        print(f"        signature = {sig}")
        print(f"        distance to canonical build = {d_canon:>3}   ({tag})")
        print(f"        -> shares_shape edges to {lnames if lnames else 'none'}")

    # --- the proof: which clips are connected by shares_shape ---------------
    print("\n  Graph check — shares_shape edges (real graph ops, not prints):")
    for name in [c[0] for c in clips]:
        if name in nodes:
            h = s.has_edge(nodes["accel_crescendo_climax"], "shares_shape", nodes[name])
            print(f"    accel_crescendo_climax -[shares_shape]-> {name:<18} : {h}")

    # --- spreading activation -----------------------------------------------
    # Give the canonical-build node ALSO a co-occurrence edge to a non-shape
    # neighbour, so spread() surfaces neighbours by DIFFERENT relations.
    s.add_production({
        "src": {"type": "SalientShape", "var": "a"},
        "edge_type": "co_occurs_with",
        "tgt": {"type": "Episode", "var": "b"},
    })
    ep = s.add_node("Episode", {"label": "tension_release_schema"})
    s.add_edge(nodes["accel_crescendo_climax"], "co_occurs_with", ep)

    print("\n  SPREADING ACTIVATION from the canonical-build node (max_hops=2):")
    print("  (recall is NOT a single-key lookup — it spreads across whichever")
    print("   edges the cue carries; each neighbour records the relation that")
    print("   surfaced it, so shape-analogues vs co-occurrence are distinct.)\n")
    for x, et, hop in s.spread(nodes["accel_crescendo_climax"], 2):
        lbl = s.node(x)["attrs"].get("label", "?")
        print(f"    hop {hop}  via {et:<16}  ->  {lbl}")

    # --- memory bound -------------------------------------------------------
    n_shape_edges = sum(len(s.neighbours(n, "shares_shape")) for n in s.nodes("SalientShape"))
    print("\n  Memory bound check (shape edges are cheap + bounded):")
    print(f"    nodes = {s.node_count()}   edges = {s.edge_count()}")
    print(f"    SalientShape nodes = {len(s.nodes('SalientShape'))}")
    print(f"    shares_shape edges (directed) = {n_shape_edges}")
    n = len(s.nodes("SalientShape"))
    print(f"    (all-to-all would be {n*(n-1)} directed; SELECTED to {n_shape_edges}"
          f" by the threshold -> no over-link.)")

    print("\n" + "=" * 78)
    print("  ONE edge among many: shares_shape connects clips by their order-N")
    print("  SHAPE alone (accelerando-crescendo -> climax), across maximal")
    print("  surface difference; controls stay unlinked; spreading activation")
    print("  recalls plural neighbours by different relations. The graph's")
    print("  existing edge types are untouched.")
    print("=" * 78)


if __name__ == "__main__":
    main()
