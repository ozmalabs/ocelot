"""CONVOLUTION IS GRAPH-NATIVE AND SENSE-AGNOSTIC — one seed + one DSL Term, any modality.

The convolution lives in the GRAPH, not Python: kernels are seed data (Kernel nodes in
seeds/sensory_convolution.json), and a convolution RESPONSE is the Rust DSL Term
MaxOver(field's patches, Dot(kernel.weights, patch.vals)). The only Python is the I/O
boundary (domains/sensory_field.lay_field) that lays a 2-D field as Patch nodes and reads
the Term's value — there is NO convolution math in Python.

This runs the SAME graph-native faculty over two unrelated senses and shows its responses
discriminate each one's labels:
  · VISION  — synthetic 2-D shape grids (horizontal / vertical / diagonal / cross).
  · HEARING — cochleagram windows of piper-spoken words.

Same seed, same Term, different sense — the kernels that respond most differ by sense, chosen
by effect. If the convolution is graph-native AND runs on vision AND hearing, it is a general
perceptual primitive of the agent, in Rust + graph data, not Python.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_authors_convolution
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from substrate.seed_loader import manifest_for
import domains.sensory_field as SF

SEP = "=" * 80


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s._inner.load_seed_manifest(manifest_for("sensory_convolution"), ag)
    return s


def _grid(kind, shift):
    g = np.zeros((9, 9), dtype=np.float64); c = (4 + shift) % 9
    if kind == "horizontal": g[c, :] = 1.0
    elif kind == "vertical": g[:, c] = 1.0
    elif kind == "diagonal":
        for i in range(9): g[i, (i + shift) % 9] = 1.0
    elif kind == "cross": g[c, :] = 1.0; g[:, c] = 1.0
    return g


def vision_fields():
    return {k: [_grid(k, 0), _grid(k, 1)] for k in ("horizontal", "vertical", "diagonal", "cross")}


def ear_fields():
    from domains.speech_world import SpeechWorld
    sw = SpeechWorld(srs.Substrate())
    out = {}
    for (w, _p), (x, fs) in sw._ear_audio().items():
        out.setdefault(w, []).append(sw._ear_field(x, fs))
    return out


def run_sense(name, fields_by_label):
    s = boot()
    # the WHOLE thing is graph-native: the keep-Rule selects the kernels, and the seed's
    # discrimination_term scores the separation — the world only lays the labelled fields.
    d, sense = SF.sense_discrimination(s, fields_by_label)
    kept = sorted(s.node(k)["attrs"].get("name") for k in s.neighbours(sense, "kept_kernel"))
    print(f"  {name:<8}: graph Rule kept {kept}; graph-native discrimination={d:.4f}")
    return d > 0.0 and len(kept) >= 1


def main():
    print(SEP)
    print("CONVOLUTION IS GRAPH-NATIVE — seed kernels + the Rust DSL Term MaxOver(Dot), no Python math.")
    print(SEP)
    print("  Same seed + Term over two senses (responses computed by the graph, not Python):\n")
    ok_v = run_sense("VISION", vision_fields())
    ok_e = run_sense("HEARING", ear_fields())
    print(f"\n{SEP}")
    ok = ok_v and ok_e
    print(f"  VISION discriminated: {ok_v}    HEARING discriminated: {ok_e}")
    print(f"  {'PASS' if ok else 'FAIL'} — convolution is a GRAPH-NATIVE perceptual primitive (JSON seed "
          f"+ Rust DSL Term), sense-agnostic; the only Python is laying the field (I/O ingest).")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
