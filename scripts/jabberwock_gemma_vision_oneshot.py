"""WARM-START: does REUSING Gemma 4's vision encoder one-shot real Omniglot? (the agent's decided path)

The jabberwock decided (compute-bound EV) to take the pretrained WARM-START path: reuse already-learned vision
features instead of paying to learn them from zero. Gemma 4's vision tower is on disk (gemma4-text:
model.vision_tower.* -- a 16-layer, 768-d ViT). This OPENS it (weights from the safetensors; the borrowed net
run via torch is the admissible RULER/teacher midpoint per the two-rules clarification -- kept live + shed
toward the floor later) and measures the FROZEN-feature one-shot transfer on held-out Omniglot characters:
the warm-start ruler. If Gemma's vision features one-shot these glyphs well, the warm-start path is validated
and the next step is the agent's trainer adapting a small live student (nothing frozen) toward the floor.

20-way 1-shot, cosine 1-NN on mean-pooled vision-tower features. No training here -- pure feature reuse.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_gemma_vision_oneshot.py [n_chars]
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import torch
from PIL import Image
from safetensors import safe_open
from transformers import Gemma4VisionModel, Gemma4VisionConfig, Gemma4ImageProcessorPil
from domains import omniglot_world as ow

SEP = "=" * 100
HF = "/home/matt/.cache/huggingface/hub/models--google--gemma-4-E4B-it/snapshots/fee6332c1abaafb77f6f9624236c63aa2f1d0187"
VLLM = "/var/lib/vllm-models/gemma4-text"
GEOMETRIC_CEILING, HUMAN = 81.0, 95.0
CANVAS = 180


def load_vision():
    vc = Gemma4VisionConfig(**json.load(open(HF + "/config.json"))["vision_config"])
    model = Gemma4VisionModel(vc)
    sd = {}
    for s in sorted(glob.glob(VLLM + "/*.safetensors")):
        with safe_open(s, framework="pt") as f:
            for k in f.keys():
                if k.startswith("model.vision_tower."):
                    sd[k[len("model.vision_tower."):]] = f.get_tensor(k).float()
    model.load_state_dict(sd, strict=False)
    model.eval()
    torch.set_num_threads(8)
    return model


def render(path) -> Image.Image:
    """Render an Omniglot drawing as black strokes on a white canvas (a natural-ish image for the encoder)."""
    strokes = ow.load_strokes(path)
    allpts = np.concatenate([s for s in strokes if len(s)], 0) if strokes else np.zeros((0, 2))
    a = np.full((CANVAS, CANVAS, 3), 255, np.uint8)
    if len(allpts) == 0:
        return Image.fromarray(a)
    mn, mx = allpts.min(0), allpts.max(0); span = np.maximum(mx - mn, 1e-6)
    for s in strokes:
        if len(s) == 0:
            continue
        q = (s - mn) / span * (CANVAS - 24) + 12
        for i in range(len(q) - 1):
            for t in np.linspace(0, 1, 40):
                x, y = (q[i] * (1 - t) + q[i + 1] * t).astype(int)
                a[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4] = 0
    return Image.fromarray(a)


def main():
    n_chars = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    print(SEP)
    print("WARM-START — Gemma 4 vision encoder, FROZEN-feature one-shot on held-out Omniglot (the ruler).")
    print(SEP)
    if not ow.have_data("evaluation"):
        print("\n  data missing."); return 1

    print("\n  opening Gemma 4 vision tower (16-layer 768-d ViT) from disk...", flush=True)
    model = load_vision()
    ip = Gemma4ImageProcessorPil(max_soft_tokens=70)

    @torch.no_grad()
    def embed(pils):
        feats = []
        for i in range(0, len(pils), 16):
            chunk = pils[i:i + 16]
            procs = [ip(images=im, return_tensors="pt") for im in chunk]
            pv = torch.cat([p["pixel_values"] for p in procs], 0)
            pid = torch.cat([p["image_position_ids"] for p in procs], 0)
            out = model(pixel_values=pv, pixel_position_ids=pid)
            lh = out.last_hidden_state if hasattr(out, "last_hidden_state") else out[0]
            B = len(chunk)
            lh = lh.reshape(B, lh.shape[0] // B, lh.shape[-1])     # (B, tokens, 768)
            f = lh.mean(1).cpu().numpy()                            # mean-pool tokens
            feats.append(f)
            print(f"    embedded {min(i + 16, len(pils))}/{len(pils)}", end="\r", flush=True)
        F = np.concatenate(feats, 0)
        return F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)

    # index eval characters; take a subset; 2 drawings each (support + query).
    rng = np.random.default_rng(0)
    chars = []
    for al in ow.alphabets("evaluation"):
        for ch in ow.characters(al, "evaluation"):
            dr = ow.drawings(ch)
            if len(dr) >= 2:
                chars.append(dr)
    idx = rng.permutation(len(chars))[:n_chars]
    chars = [chars[i] for i in idx]
    print(f"  embedding {n_chars} held-out characters x 2 drawings ({2*n_chars} images)...", flush=True)

    pils, owner = [], []
    for ci, dr in enumerate(chars):
        pick = rng.permutation(len(dr))[:2]
        for j in pick:
            pils.append(render(dr[j])); owner.append(ci)
    F = embed(pils)
    print()

    # group features by character (each has 2: [0]=support, [1]=query)
    by_char = {}
    for f, ci in zip(F, owner):
        by_char.setdefault(ci, []).append(f)
    support = np.stack([by_char[ci][0] for ci in range(n_chars)])    # (n_chars, 768)
    query = np.stack([by_char[ci][1] for ci in range(n_chars)])

    # 20-way 1-shot, cosine 1-NN on Gemma vision features.
    correct = total = 0
    for _ in range(1000):
        cls = rng.choice(n_chars, 20, replace=False)
        qi = int(rng.integers(20))
        S = support[cls]                                            # (20, 768)
        q = query[cls[qi]]
        pred = int((S @ q).argmax())                               # cosine (normalized) NN
        correct += (pred == qi); total += 1
    acc = 100 * correct / total

    print("\n" + SEP)
    print(f"  20-way 1-shot on held-out Omniglot ({n_chars}-char pool), Gemma 4 vision features, cosine 1-NN:")
    print(f"    Gemma-vision FROZEN features : {acc:5.1f}%")
    print(f"    geometric ceiling (arc)      : ~{GEOMETRIC_CEILING:.0f}%")
    print(f"    human one-shot bar (rule 2)  : ~{HUMAN:.0f}%")
    verdict = ("CLEARS the human bar" if acc >= HUMAN else
               "beats the geometric ceiling" if acc > GEOMETRIC_CEILING else
               "does not beat the geometric ceiling")
    print(f"\n  RULER VERDICT: reusing Gemma 4's vision features {verdict} ({acc:.1f}%) -- with ZERO training,")
    print(f"  pure feature reuse. This is the warm-start the agent chose; if it clears, the next step is the")
    print(f"  agent's trainer adapting a small LIVE student from it (nothing frozen) and shedding toward the floor.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
