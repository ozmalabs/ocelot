"""gemma_teacher_adapter — a THIN, read-only adapter exposing the BORROWED Gemma 4 vision tower as a
FeatureTeacher embed_fn (a top-K PROPOSAL only). For the "convert a borrowed net to self-learning"
headline.

ARCHITECTURE: Gemma is the borrowed SCAFFOLD (a recognition PROPOSAL). The earned structure (the held
AbS recognizer + the grown library) makes the DECISION and stands alone. This adapter ONLY produces a
mean-pooled vision-tower feature per Omniglot drawing — read-only weight load from disk; NO closed file
is reopened (the minimal load+embed logic is replicated here, not imported from any closed scaffold).

The load-bearing proof lives elsewhere (conversion_loop.teach/extend with NO Gemma call): if the earned
structure teaches+extends WITHOUT this adapter, the borrowed capability is CONVERTED into held
structure. This adapter is the teacher; it is NOT in the teach/extend path.

torch/numpy are used here ONLY to run the borrowed encoder (the teacher proposal); the earned structure
(AbS + library) uses neither torch nor Gemma. Flagged. No LLM.
"""
from __future__ import annotations
import glob
import json
import numpy as _np                 # ADAPTER: feature array math for the proposal
import domains.omniglot_world as _ow

HF = ("/home/matt/.cache/huggingface/hub/models--google--gemma-4-E4B-it/snapshots/"
      "fee6332c1abaafb77f6f9624236c63aa2f1d0187")
VLLM = "/var/lib/vllm-models/gemma4-text"
CANVAS = 180

_MODEL = None
_IP = None


def available() -> bool:
    """Is the borrowed Gemma vision tower loadable (weights on disk + transformers present)?"""
    try:
        import torch  # noqa
        from transformers import Gemma4VisionModel  # noqa
        return len(glob.glob(VLLM + "/*.safetensors")) > 0 and bool(json.load(open(HF + "/config.json")))
    except Exception:
        return False


def _load():
    """READ-ONLY load of the borrowed vision tower (replicated minimal logic; no closed file reopened)."""
    global _MODEL, _IP
    if _MODEL is not None:
        return _MODEL, _IP
    import torch
    from safetensors import safe_open
    from transformers import Gemma4VisionModel, Gemma4VisionConfig, Gemma4ImageProcessorPil
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
    _MODEL, _IP = model, Gemma4ImageProcessorPil(max_soft_tokens=70)
    return _MODEL, _IP


def _render(path):
    """Render an Omniglot drawing as black strokes on a white canvas (ADAPTER, numpy)."""
    from PIL import Image
    strokes = _ow.load_strokes(path)
    a = _np.full((CANVAS, CANVAS, 3), 255, _np.uint8)
    allpts = _np.concatenate([s for s in strokes if len(s)], 0) if strokes else _np.zeros((0, 2))
    if len(allpts) == 0:
        return Image.fromarray(a)
    mn, mx = allpts.min(0), allpts.max(0); span = _np.maximum(mx - mn, 1e-6)
    for s in strokes:
        if len(s) == 0:
            continue
        q = (s - mn) / span * (CANVAS - 24) + 12
        for i in range(len(q) - 1):
            for t in _np.linspace(0, 1, 40):
                x, y = (q[i] * (1 - t) + q[i + 1] * t).astype(int)
                a[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4] = 0
    return Image.fromarray(a)


_CACHE = {}


def embed(path):
    """The BORROWED Gemma vision-tower feature of one drawing (mean-pooled tokens, L2-normalized).
    The teacher's PROPOSAL signal. Cached per path. Returns a 768-d numpy vector or None."""
    if path in _CACHE:
        return _CACHE[path]
    import torch
    model, ip = _load()
    pil = _render(path)
    with torch.no_grad():
        proc = ip(images=pil, return_tensors="pt")
        out = model(pixel_values=proc["pixel_values"], pixel_position_ids=proc["image_position_ids"])
        lh = out.last_hidden_state if hasattr(out, "last_hidden_state") else out[0]
        # (tokens, 768) -> mean-pool -> normalize
        v = lh.reshape(-1, lh.shape[-1]).mean(0).cpu().numpy()
    v = v / (_np.linalg.norm(v) + 1e-9)
    _CACHE[path] = v
    return v


def make_teacher():
    """A FeatureTeacher backed by the borrowed Gemma vision tower (proposal only)."""
    import domains.conversion_loop as cl
    return cl.FeatureTeacher(embed, name="gemma-borrowed")
