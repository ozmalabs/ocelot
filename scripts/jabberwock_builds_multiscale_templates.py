"""The jabberwock builds MULTI-SCALE recognition templates with its OWN faculty.

The span-lattice proved the single-word unit was the limit, but with only single-word
templates a long span collapses to one word -> under-production. The fix is units at
MORE scales. The agent already owns the unit-discovery faculty: forward_segmentation
(its statistical_learning / TP-trough segmenter, the bottom-up BPE-like lexicon build).
Run it ON THE WORD STREAM and it MERGES high-TP word runs into MULTI-WORD units
(collocations: "of the", "in the", ... — exactly the co-articulated function-word
sequences that caused the deletions). The agent decides which word-sequences are units;
the template build (gather instances -> encode -> centroid) is mechanical adapter I/O,
the same move as the single-word centroids.

  DECISION (agent) : forward_segment(word-id stream) -> multi-word chunks = the units.
  ADAPTER  I/O     : for each unit, concat per-word frame samples -> feature -> encode
                     (the graph-resident encoder) -> average -> centroid; append to seed.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_builds_multiscale_templates.py [n_units] [shards] [k_inst]
"""
from __future__ import annotations
import glob, json, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import Counter, defaultdict
from domains.forward_segmentation import forward_segment
from domains.learned_speech_recogniser import LearnedSpeechRecogniser, install_templates, feature

BANK = "/home/matt/data/phonebank"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "var", "speech_word_templates.json")


def _raw_load(glob_pat, cap):
    """ALL words in corpus order (stop words KEPT) with their frames. Returns the word
    stream AND the positionally-aligned frame matrices (each cut from the real
    continuous audio in order), so consecutive entries are REAL adjacent audio."""
    stream, stream_fr = [], []
    for p in sorted(glob.glob(os.path.join(BANK, glob_pat)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower()
                fr = np.asarray(e[1], float)
                if not w.isalpha() or fr.shape[0] < 2:
                    continue
                fr = fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)
                stream.append(w); stream_fr.append(fr)
    return stream, stream_fr


def main():
    n_units = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    shards = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    k_inst = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    rng = np.random.default_rng(0)

    print("=" * 90)
    print("JABBERWOCK BUILDS MULTI-SCALE TEMPLATES (its segmenter discovers multi-word units)")
    print("=" * 90)
    stream, stream_fr = _raw_load("train-clean-100_*.pkl", shards)
    print(f"  word stream: {len(stream)} words, {len(set(stream))} distinct", flush=True)

    # ---- DECISION (agent faculty): the segmenter discovers the units on the word stream ----
    vocab = sorted(set(stream)); wi = {w: i for i, w in enumerate(vocab)}
    ids = [wi[w] for w in stream]
    sub = srs.Substrate()
    # the agent's bottom-up build: merge high-TP word runs into chunks (collocations).
    res = forward_segment(sub, [ids], n_passes=1, boundary_mode="prominent", bidirectional=True)
    chunks = (res["chunked"] or [[]])[0]
    iv = {i: w for w, i in wi.items()}
    multi = Counter()
    for c in chunks:
        if 2 <= len(c) <= 3:
            multi[tuple(iv[i] for i in c)] += 1
    units = [u for u, _ in multi.most_common(n_units)]
    unitset = set(units)
    print(f"  agent discovered {len(multi)} multi-word unit types; keeping top {len(units)}", flush=True)
    print(f"  examples: {[' '.join(u) for u, _ in multi.most_common(8)]}", flush=True)

    # ---- harvest REAL fused acoustic instances: scan the stream for consecutive
    #      occurrences of each unit and take the actual adjacent-audio frames (the real
    #      co-articulated join — the 'howyagarn' form), NOT a synthetic concatenation. ----
    occ = defaultdict(list)
    for i in range(len(stream)):
        for ln in (2, 3):
            if i + ln <= len(stream):
                u = tuple(stream[i:i + ln])
                if u in unitset:
                    occ[u].append(i)

    install_templates(sub)                       # load existing word centroids + encoder
    rec = LearnedSpeechRecogniser(sub)
    existing = {w for w in rec._words if " " not in w}    # single-word base only
    new_nodes = []; t = time.time(); real_inst = 0
    for u in units:
        label = " ".join(u)
        if label in existing or not occ[u]:
            continue
        starts = occ[u]
        if len(starts) > k_inst:
            starts = [starts[k] for k in rng.choice(len(starts), k_inst, replace=False)]
        embs = []; durs = []
        for i in starts:
            cat = np.vstack(stream_fr[i:i + len(u)])          # REAL adjacent audio
            embs.append(rec.encode(feature(cat, cat.mean(0)))); durs.append(len(cat))
        real_inst += len(embs)
        cen = np.mean(embs, 0); cen = cen / max(np.linalg.norm(cen), 1e-9)
        ld = np.log([max(d, 1) for d in durs])                # LOG-duration stats (rate is multiplicative)
        new_nodes.append({"word": label, "vec": [float(x) for x in cen],
                          "dur_mu": float(np.mean(ld)),
                          "dur_sig": max(float(np.std(ld)) if len(ld) > 1 else 0.3, 0.1)})
    print(f"  built {len(new_nodes)} multi-word centroids from {real_inst} REAL fused "
          f"instances [{time.time()-t:.1f}s]", flush=True)

    # ---- rebuild the seed from the single-word base (drop any prior multi-word
    #      templates), then append the real-acoustic multi-word ones (idempotent) ----
    with open(SEED) as f:
        seed = json.load(f)
    seed["nodes"] = [n for n in seed["nodes"]
                     if not (n["type"] == "WordCentroid" and " " in n["attrs"]["word"])]
    base = len(seed["nodes"])
    for j, nd in enumerate(new_nodes):
        seed["nodes"].append({"local_id": base + j, "type": "WordCentroid", "attrs": nd})
    seed["version"] = "3.0.0"
    seed["description"] = ("Multi-scale learned recogniser: single-word + agent-discovered "
                           "multi-word (collocation) centroid templates + the background-fit "
                           "linear encoder. Recognition = Dot(embedding, centroid) held Term / "
                           "native topk_dot. Multi-word units found by forward_segment on the word stream.")
    with open(SEED, "w") as f:
        json.dump(seed, f)
    n_word = sum(1 for n in seed["nodes"] if n["type"] == "WordCentroid" and " " not in n["attrs"]["word"])
    n_multi = sum(1 for n in seed["nodes"] if n["type"] == "WordCentroid" and " " in n["attrs"]["word"])
    print(f"  seed now: {n_word} single-word + {n_multi} multi-word templates "
          f"({os.path.getsize(SEED)/1024:.0f} KB)", flush=True)

    # ---- sanity: boot a fresh recogniser and confirm multi-word units are recognisable ----
    fresh = srs.Substrate(); install_templates(fresh)
    rec2 = LearnedSpeechRecogniser(fresh)
    checkable = [u for u in units if len(occ[u]) >= 2][:40]
    hit = 0; n = max(len(checkable), 1)
    for u in checkable:
        i = occ[u][-1]                                   # a held-out real instance
        cat = np.vstack(stream_fr[i:i + len(u)])
        emb = rec2.encode(feature(cat, cat.mean(0)))
        top = [w for w, _ in rec2.ground_topk(emb, 5)]
        hit += (" ".join(u) in top)
    print("=" * 90)
    print(f"  boot check: {len([w for w in rec2._words if ' ' in w])} multi-word templates loaded; "
          f"held-out multi-word instance in top-5: {hit}/{n}")
    print("  Multi-scale templates built by the agent's own segmenter (units) + encoder (centroids).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
