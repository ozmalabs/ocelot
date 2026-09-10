"""Block 335000 — MEASURE elicitation throughput: sequential vs batched.

The scaling estimate for "extract everything" is bounded by forward-pass cost.
Block 332 elicited 59 is-a edges one-forward-at-a-time. This script:

  1. CORRECTNESS: on a sample, confirm forward_logits_batch (left-padded, one
     forward for B rows) yields the SAME constrained-argmax objects as B calls
     of forward_logits — the batch is a pure throughput optimization, not a
     different read.
  2. TIMING: measure sequential edges/s vs batched edges/s over a real
     multi-hundred-subject taxonomy, at a few batch sizes, and report the
     speedup + projected wall-clock for larger harvests.

Model + venv are under /applications (never committed). Pure measurement — no
seed is written, no substrate touched.

Run (nohup standalone; NOT setsid+pkill — that races the logfile):
  HF_HOME=/applications/data/model_graph_work/hf_home \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_harvest_timing.py > var/harvest_timing.log 2>&1 &
"""
from __future__ import annotations

import time

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"


# A larger taxonomy than block 332 (that was 34 chains / ~50 subjects). We want
# a few hundred subjects for a stable edges/s. Build breadth by enumerating many
# instances under shared hypernyms — the elicitation is per-subject regardless.
_ANIMALS = [
    "poodle", "beagle", "bulldog", "terrier", "spaniel", "mastiff", "collie",
    "dachshund", "husky", "boxer", "tabby", "siamese", "persian", "lion",
    "tiger", "leopard", "cheetah", "jaguar", "cougar", "lynx", "salmon",
    "trout", "cod", "tuna", "herring", "carp", "bass", "sardine", "mackerel",
    "sparrow", "eagle", "robin", "finch", "hawk", "falcon", "owl", "crow",
    "raven", "pigeon", "cobra", "python", "viper", "boa", "adder", "mamba",
    "frog", "toad", "newt", "salamander", "bee", "ant", "wasp", "beetle",
    "moth", "butterfly", "cricket", "grasshopper", "dragonfly", "ladybug",
]
_PLANTS = [
    "oak", "pine", "birch", "maple", "willow", "cedar", "spruce", "elm",
    "ash", "beech", "rose", "tulip", "daisy", "lily", "orchid", "daffodil",
    "sunflower", "poppy", "iris", "violet",
]
_MATERIALS = [
    "copper", "iron", "gold", "silver", "tin", "lead", "zinc", "nickel",
    "aluminium", "titanium", "granite", "sandstone", "limestone", "marble",
    "slate", "basalt", "quartz", "shale",
]
_ARTIFACTS = [
    "hammer", "saw", "wrench", "screwdriver", "drill", "chisel", "pliers",
    "chair", "table", "desk", "stool", "bench", "sofa", "cabinet",
    "car", "truck", "bus", "van", "motorcycle", "bicycle", "tractor",
]
_FOOD = [
    "apple", "banana", "orange", "grape", "pear", "peach", "plum", "cherry",
    "carrot", "potato", "onion", "spinach", "broccoli", "lettuce", "cabbage",
]
_BODY = [
    "heart", "lung", "liver", "kidney", "stomach", "brain", "spleen",
    "hand", "foot", "arm", "leg", "finger", "toe",
]

# candidate hypernym vocabulary (the constrained object space)
_CANDS = sorted(set([
    "dog", "cat", "fish", "bird", "snake", "reptile", "amphibian", "insect",
    "mammal", "animal", "organism", "tree", "flower", "plant", "metal", "rock",
    "mineral", "material", "substance", "tool", "furniture", "vehicle",
    "artifact", "object", "fruit", "vegetable", "food", "organ", "limb",
    "body_part",
]))

SUBJECTS = (_ANIMALS + _PLANTS + _MATERIALS + _ARTIFACTS + _FOOD + _BODY)


def main() -> int:
    print("=" * 74)
    print("HARVEST TIMING — block 335000 (sequential vs batched elicitation)")
    print("=" * 74)
    print("subjects: %d | candidates: %d" % (len(SUBJECTS), len(_CANDS)))

    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs" % (time.time() - t0))
    print("has forward_logits_batch: %s" % hasattr(m, "forward_logits_batch"))

    tmpl = "A {} is a kind of"

    # ---- 1. CORRECTNESS on a 24-subject sample -------------------------
    sample = SUBJECTS[:24]
    seq_pairs = ks.elicit_isa(m, tok, sample, candidates=_CANDS, template=tmpl)
    bat_pairs = ks.elicit_isa_batch(m, tok, sample, candidates=_CANDS,
                                    template=tmpl, batch_size=8)
    agree = sum(1 for a, b in zip(seq_pairs, bat_pairs) if a == b)
    print("\n[correctness] batched vs sequential agree on %d/%d sample subjects"
          % (agree, len(sample)))
    if agree != len(sample):
        for a, b in zip(seq_pairs, bat_pairs):
            if a != b:
                print("   MISMATCH seq=%s batch=%s" % (a, b))
    assert agree == len(sample), "batched read diverges from sequential — bug"

    # ---- 2. TIMING: sequential over a 64-subject slice -----------------
    tslice = SUBJECTS[:64]
    t = time.time()
    _ = ks.elicit_isa(m, tok, tslice, candidates=_CANDS, template=tmpl)
    seq_dt = time.time() - t
    seq_rate = len(tslice) / seq_dt
    print("\n[sequential] %d subjects in %.1fs = %.3f edges/s (%.0f edges/hr)"
          % (len(tslice), seq_dt, seq_rate, seq_rate * 3600))

    # ---- 3. TIMING: batched over the FULL set at a few batch sizes -----
    for bs in (8, 16, 32):
        t = time.time()
        pairs = ks.elicit_isa_batch(m, tok, SUBJECTS, candidates=_CANDS,
                                    template=tmpl, batch_size=bs)
        dt = time.time() - t
        rate = len(SUBJECTS) / dt
        print("[batched bs=%2d] %d subjects in %.1fs = %.3f edges/s "
              "(%.0f edges/hr)  speedup=%.1fx"
              % (bs, len(SUBJECTS), dt, rate, rate * 3600, rate / seq_rate))

    # ---- 4. PROJECTIONS from the best batched rate ---------------------
    # (use bs=32 rate captured last)
    best_rate = len(SUBJECTS) / dt
    print("\n[projection] at %.0f edges/hr (batched bs=32, single relation):"
          % (best_rate * 3600))
    for n, lbl in ((60000, "60k edges (~10k subj x 6 rel)"),
                   (600000, "600k edges"),
                   (6000000, "6M edges (~1M subj x 6 rel)")):
        hrs = n / (best_rate * 3600)
        print("   %-32s ~ %.1f hr (%.1f days)" % (lbl, hrs, hrs / 24))

    print("\nDONE (measurement only; no seed written, no substrate touched).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
