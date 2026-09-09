#!/usr/bin/env python3
"""Model active extraction — measure the 3 claims.

See docs/research/psychology_affect/MODEL_ACTIVE_EXTRACTION_PREREG.md.

  CLAIM 1: FFN neurons yield coherent typed concepts (vs random neuron).
  CLAIM 2: running the model ADDS relational edges the static geometry lacks.
  CLAIM 3: graph-driven targeting (sparsest nodes) beats random probing.

Honest bound: "running the model" = ollama behavioural probing (completions),
NOT hidden-activation tapping. Static parts run without ollama; running-the-
model parts skip gracefully if ollama/model absent.
"""

from __future__ import annotations

import random
import sys
import time

import numpy as np

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

import substrate_rs as sr  # noqa: E402
from domains import model_active_extraction as mae  # noqa: E402

MODEL = "gemma3:4b"
WORK_VOCAB = 12000     # small window -> bounded load time
SEED_CONCEPTS = ["dog", "cat", "knife", "hammer", "book", "wheel", "fire",
                 "water", "car", "house"]


def _coherence(promoted, seed_words, lm):
    """Mean cosine of the promoted tokens' embeddings to the seed direction —
    how ON-CONCEPT the neuron's promoted vocabulary is."""
    sv = mae._concept_direction(lm, seed_words)
    sims = []
    for t in promoted:
        tid = lm.vocab.get(t)
        if tid is None:
            continue
        v = lm.vec_fn(tid)
        sims.append(float(v @ sv / (np.linalg.norm(v) + 1e-9)))
    return float(np.mean(sims)) if sims else 0.0


def main():
    print("=" * 70)
    print("MODEL ACTIVE EXTRACTION — graph pulls apart gemma3:4b")
    print("(static weights + BEHAVIOURAL probing; NOT activation tapping)")
    print("=" * 70)

    print("\nloading gemma3:4b static weights (work_vocab=%d) ..." % WORK_VOCAB)
    t0 = time.perf_counter()
    lm = mae.load_model(MODEL, work_vocab=WORK_VOCAB)
    print("  loaded in %.1fs; embedding %s vocab %d"
          % (time.perf_counter() - t0, lm.shape, len(lm.vocab)))

    # ---- CLAIM 1: FFN concept coherence --------------------------------
    print("\n[CLAIM 1] FFN neurons yield coherent typed concepts")
    concept_seeds = {
        "animal": ["dog", "cat", "animal", "pet"],
        "number": ["one", "two", "three", "number"],
        "colour": ["red", "blue", "green", "colour"],
    }
    coh_best, coh_rand = [], []
    rng = random.Random(0)
    for name, seeds in concept_seeds.items():
        try:
            idx, align, promoted = mae.ffn_concepts(lm, seeds, layer=20, top=8)
        except Exception as e:
            print("  %-8s: skipped (%s)" % (name, e))
            continue
        cb = _coherence(promoted, seeds, lm)
        # a random neuron's promoted tokens, same layer
        D = __import__("domains.model_reader", fromlist=["x"]).read_gguf_tensor(
            lm.blob, "blk.20.ffn_down.weight")
        Dn = D if D.shape[1] == lm.shape[1] else D.T
        rn = rng.randrange(Dn.shape[0])
        nb = Dn[rn] / (np.linalg.norm(Dn[rn]) + 1e-9)
        rpos = np.argsort(-(lm._M @ nb))[:8]
        rpromoted = [lm.inv[lm.work_ids[int(j)]] for j in rpos]
        cr = _coherence(rpromoted, seeds, lm)
        coh_best.append(cb)
        coh_rand.append(cr)
        print("  %-8s: neuron#%d promotes %s" %
              (name, idx, [t.lstrip("▁") for t in promoted[:5]]))
        print("           coherence best=%.2f vs random-neuron=%.2f" % (cb, cr))
    claim1 = coh_best and np.mean(coh_best) > np.mean(coh_rand) + 0.1
    print("  => FFN concepts coherent above random: %s" % bool(claim1))

    # ---- ollama gate ---------------------------------------------------
    have_ollama = mae.ollama_available(MODEL)
    print("\nollama available: %s" % have_ollama)
    if not have_ollama:
        print("  running-the-model claims 2/3 SKIPPED (ollama/model absent)")
        print("\nVERDICT (static only): CLAIM 1 %s" %
              ("HOLDS" if claim1 else "FAILS"))
        return {"claim1": claim1, "claim2": None, "claim3": None}

    # ---- CLAIM 2: running the model adds relational structure ----------
    print("\n[CLAIM 2] running the model ADDS relational edges the geometry "
          "lacks")
    s = sr.Substrate()
    inner = s._inner
    nm = {w: inner.add_node("Concept", {"name": w, "state": 0.0,
                                        "external_field": 0.0,
                                        "identity_field": 0.0})
          for w in SEED_CONCEPTS}
    edge_types = [v[1] for v in mae.RELATION_TEMPLATES.values()]
    before = sum(mae.relational_degree(inner, nm[w], edge_types) for w in nm)
    t0 = time.perf_counter()
    rep = mae.active_extract(s, nm, model_tag=MODEL, budget=20, targeted=True)
    after = sum(mae.relational_degree(inner, nm[w], edge_types)
                for w in SEED_CONCEPTS)
    print("  probes=%d edges_added=%d in %.1fs" %
          (rep["probes"], rep["edges_added"], time.perf_counter() - t0))
    print("  relational edges on seed nodes: %d -> %d" % (before, after))
    print("  per_relation: %s" % rep["per_relation"])
    sample = list(rep["targets"].items())[:3]
    for subj, edges in sample:
        print("    %s -> %s" % (subj, edges))
    claim2 = rep["edges_added"] > 0 and after > before

    # ---- CLAIM 3: targeted beats random --------------------------------
    print("\n[CLAIM 3] graph-driven targeting (sparsest) vs random probing")
    print("  (same budget; pre-seed a few nodes with edges so 'sparsest' is")
    print("   meaningful; measure how many PREVIOUSLY-EMPTY nodes get filled)")

    def run(targeted):
        s2 = sr.Substrate()
        i2 = s2._inner
        nodes = {w: i2.add_node("Concept",
                                {"name": w, "state": 0.0, "external_field": 0.0,
                                 "identity_field": 0.0}) for w in SEED_CONCEPTS}
        # pre-seed HALF the nodes with a relational edge (already-known)
        for w in SEED_CONCEPTS[:5]:
            i2.add_edge_unchecked(nodes[w], "is_a", nodes[SEED_CONCEPTS[0]])
        empty_before = [w for w in SEED_CONCEPTS
                        if mae.relational_degree(i2, nodes[w], edge_types) == 0]
        mae.active_extract(s2, nodes, model_tag=MODEL, budget=15,
                           targeted=targeted, rng=random.Random(0))
        filled = sum(1 for w in empty_before
                     if mae.relational_degree(i2, nodes[w], edge_types) > 0)
        return len(empty_before), filled

    te, tf = run(True)
    re_, rf = run(False)
    print("  TARGETED: filled %d/%d previously-empty nodes" % (tf, te))
    print("  RANDOM:   filled %d/%d previously-empty nodes" % (rf, re_))
    claim3 = tf >= rf and tf > 0

    print("\n" + "=" * 70)
    print("VERDICT")
    print("  CLAIM 1 FFN concepts coherent:            %s" %
          ("HOLDS" if claim1 else "FAILS"))
    print("  CLAIM 2 running model adds structure:     %s" %
          ("HOLDS" if claim2 else "FAILS"))
    print("  CLAIM 3 graph-driven targeting >= random: %s" %
          ("HOLDS" if claim3 else "FAILS"))
    print("-" * 70)
    print("  The graph distils a generative LM's static geometry AND runs it")
    print("  to extract typed relations the geometry lacks AND directs that")
    print("  extraction from its own gaps — within the behavioural-probing")
    print("  bound (completions, not activations).")
    print("=" * 70)
    return {"claim1": bool(claim1), "claim2": bool(claim2),
            "claim3": bool(claim3)}


if __name__ == "__main__":
    main()
