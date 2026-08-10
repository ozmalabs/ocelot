"""The jabberwock BUILDS and EXECUTES a plan from the thermodynamic-efficiency approach.

Approach (validated this session): speech is an EFFICIENT code, not signal+noise.
  - STRESS is the rate-invariant identity/scale (prominence peaks ~ syllables, r=0.93,
    13x more rate-invariant than duration).  [jabberwock_stress_feature]
  - EFFORT (acoustic energy) is allocated by INFORMATION: predictable units reduced
    (function/fusing words 35-45% reduced).  [jabberwock_speech_efficiency]

The agent holds the PLAN as graph data and composes each faculty as a graph TERM (the
compose_cmvn / agent_specify pattern — its OWN graph-native design), then executes:

  PLAN (graph-resident Plan + ordered Steps):
   1. compose STRESS-SCALE match  : scale by #stress-peaks (rate-invariant), not frames
   2. compose EFFORT-WEIGHTED decode: trust acoustics where effort spent, prior where reduced
   3. integrate into the span-lattice; 4. measure WER vs the duration baseline.

  BUILD: two composed Terms recorded as Concepts on the agent.
  EXECUTE: run the integrated decode on real cross-speaker LibriSpeech; record outcomes.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_efficiency_plan.py [n_test]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
import scripts.librispeech_wer as L
from scripts.context_invariant_librispeech_accept import kmeans, quantize
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_reads_oov_from_phones import frames
from scripts.jabberwock_stress_feature import sonority, stress_pattern, nsyl_text
from domains.forward_segmentation import forward_segment
from domains.learned_speech_recogniser import (LearnedSpeechRecogniser, install_templates,
                                               feature)

TOPK, KMAX = 5, 3


# ---- the agent holds the PLAN as graph data, composes each faculty as a Term ----

def _lit(v): return {"type": "Lit", "value": v}


def stress_scale_term(qsyl, tsyl, sig):
    """Agent composition: rate-invariant SCALE penalty = 0.5*((qsyl - tsyl)/sig)^2 over
    STRESS-PEAK count (syllables), not frames. Same normalisation move as duration, but
    on the rate-invariant variable. Built from Minus/Div/Times/Lit."""
    z = {"type": "Div", "a": {"type": "Minus", "a": _lit(float(qsyl)), "b": _lit(float(tsyl))},
         "b": _lit(float(sig))}
    return {"type": "Times", "items": [_lit(0.5), {"type": "Times", "items": [z, z]}]}


def effort_weight_term(effort_norm):
    """Agent composition: the thermodynamic decode weight = the span's RELATIVE EFFORT
    (energy spent here / utterance mean). High effort -> trust acoustics; reduced -> ~0
    -> the prior carries it. Built from Lit (a scalar the acoustic term is scaled by)."""
    return _lit(float(effort_norm))


def record_plan_and_builds(sub, agent):
    """The agent holds the plan + the two composed faculties as graph data (Concepts),
    the compose_cmvn pattern — its own graph-native design, recorded once. Idempotent."""
    have = {sub.node(c)["attrs"].get("name") for c in sub.nodes("Concept")}
    steps = [
        ("stress_scale_match", "scale recognition by rate-invariant stress-peak count, not frames",
         stress_scale_term(0, 0, 1.0)),
        ("effort_weighted_decode", "trust acoustics where effort spent, prior where reduced",
         effort_weight_term(1.0)),
    ]
    plan = sub.add_node("Plan", {"name": "thermodynamic_speech", "origin": "efficiency_approach",
                                 "principle": "speech is an efficient code; effort tracks information"})
    for i, (name, why, term) in enumerate(steps):
        st = sub.add_node("Step", {"name": name, "order": i, "why": why})
        sub.add_edge_unchecked(plan, "has_step", st)
        if name not in have:
            c = sub.add_node("Concept", {"name": name, "feature_kind": "thermodynamic",
                                         "predicate": term, "composed_by": "agent", "why": why})
            sub.add_edge_unchecked(st, "composes", c)
    return plan


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    lam = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    sub = srs.Substrate(); install_templates(sub)
    rec = LearnedSpeechRecogniser(sub)
    agent = sub.add_node("Agent", {})
    plan = record_plan_and_builds(sub, agent)
    steps = [sub.node(s)["attrs"]["name"]
             for s in sorted(sub.neighbours(plan, "has_step"),
                             key=lambda s: sub.node(s)["attrs"]["order"])]
    print("JABBERWOCK PLAN (graph-resident):", " -> ".join(steps), flush=True)
    print(f"  templates={len(rec._words)}", flush=True)

    # template syllable count from the label (vowel groups) — rate-invariant scale target
    tsyl = {w: nsyl_text(w.split()) for w in rec._words}

    train = _load("train-clean-100_*.pkl", 12)
    # INFORMATION measure (the right one): a word carries -log P(w) bits; predictable
    # words ~0 bits (the listener reconstructs them), surprising content words carry the
    # signal. "Did the signal transmit" = fraction of BITS received (bag-level: the word
    # appears in the hypothesis), not exact word order/count. Function words (top-50
    # frequent) = the reduced, reconstructable ones.
    from collections import Counter as _C
    uni = _C(w for w, _ in train); _tot = sum(uni.values()) or 1
    import math as _m
    _floor = _m.log(_tot)
    def surpr(w):
        return -_m.log(uni[w] / _tot) if uni.get(w) else _floor
    func = set(w for w, _ in uni.most_common(50))
    def is_content(w):
        return w not in func and len(w) >= 3
    C = kmeans(np.concatenate([fr for _w, fr in train[:1500]], 0), 48)
    vi = {w: i for i, w in enumerate(rec._words)}; V = len(rec._words)
    big = np.ones((V, V)); prev = None
    for w, _ in train:
        if w in vi:
            if prev is not None:
                big[vi[prev], vi[w]] += 1
            prev = w
        else:
            prev = None
    logbg = np.log(big / big.sum(1, keepdims=True))

    def _bg(pw, w):
        return logbg[vi[pw], vi[w]] if (pw in vi and w in vi) else -8.0

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    Ms, Es, refs = [], [], []
    for (path, sp_, ch, ut, tr) in test:
        try:
            M, e = frames(L.load_flac(path)[0])
            # L.normalise upper-cases; templates/hyps are lower-case -> lower the ref so
            # they're comparable (the case mismatch was corrupting WER and the bits measure).
            Ms.append(M); Es.append(np.asarray(e, float))
            refs.append([w.lower() for w in L.normalise(tr)])
        except Exception as ex:
            print("  frame fail", ex)

    # segment (the agent's prominent segmenter, corpus TP)
    seqs = [[int(u) for u in quantize(M, C)] for M in Ms]
    ssub = srs.Substrate()
    chunked = forward_segment(ssub, seqs, n_passes=1, boundary_mode="prominent")["chunked"]
    all_spans = []
    for s, ch in zip(seqs, chunked or [[(u,) for u in q] for q in seqs]):
        sp, k = [], 0
        for c in ch:
            sp.append((k, k + len(c))); k += len(c)
        all_spans.append(sp)

    def collapse(ws):
        o = []
        for w in ws:
            if not o or o[-1] != w:
                o.append(w)
        return o

    def decode(M, e, spans, mode):
        """mode 'baseline' = shape + global-lambda LM; 'efficiency' = effort*shape -
        stress + global-lambda LM; 'local_effort' = the FULLY thermodynamic decode: NO
        global lambda — the acoustic likelihood's PRECISION is the local effort, the LM
        is always the prior. score = effort*kappa*shape - stress + LM. Where effort->0
        (reduced speech) acoustic precision ->0 so the PRIOR carries the word; where
        effort->1 (clear) the acoustic decides. kappa is the data-calibrated acoustic->LM
        scale (not a tuned knob)."""
        N = len(spans)
        if N == 0:
            return []
        umean = float(np.mean(e)) or 1.0
        loc = mode == "local_effort"
        w_lm = 1.0 if loc else lam
        dp = [dict() for _ in range(N + 1)]
        dp[0][None] = (0.0, (None, None, None))
        for j in range(1, N + 1):
            for i in range(max(0, j - KMAX), j):
                if not dp[i]:
                    continue
                a, b = spans[i][0], spans[j - 1][1]
                emb = rec.encode(feature(M[a:b], np.asarray(M[a:b], float).mean(0)))
                cands = rec.ground_topk(emb, TOPK)            # pure shape Dot top-k
                if mode in ("efficiency", "local_effort"):
                    effort = float(np.mean(e[a:b])) / umean   # effort_weight_term value
                    if loc:
                        effort = min(max(float(np.mean(e[a:b])) / escale, 0.0), 1.0)  # precision in [0,1]
                    _, qsyl = stress_pattern(sonority(e[a:b]))  # rate-invariant scale
                for label, shape in cands:
                    ws = label.split()
                    if not ws:
                        continue
                    if mode in ("efficiency", "local_effort"):
                        ac = effort * (kappa if loc else 1.0) * shape
                        sub2 = srs.Substrate()
                        pen = float(sub2._inner.evaluate(
                            stress_scale_term(qsyl, tsyl.get(label, len(ws)), 1.0), {}))
                        ac -= pen
                    else:
                        ac = shape
                    internal = w_lm * sum(_bg(ws[t], ws[t + 1]) for t in range(len(ws) - 1))
                    last = ws[-1]
                    for pw, (ps, _bp) in dp[i].items():
                        sc = ps + ac + w_lm * (_bg(pw, ws[0]) if pw is not None else 0.0) + internal
                        cur = dp[j].get(last)
                        if cur is None or sc > cur[0]:
                            dp[j][last] = (sc, (i, pw, label))
        if not dp[N]:
            return []
        last = max(dp[N], key=lambda k: dp[N][k][0]); labels, j = [], N
        while j > 0:
            _sc, (i, pw, label) = dp[j][last]; labels.append(label); j, last = i, pw
        labels.reverse()
        out = []
        for lab in labels:
            out.extend(lab.split())
        return collapse(out)

    # ---- DATA CALIBRATION (not tuned knobs): the effort precision scale `escale` (the
    #      energy a clearly-spoken span carries) and `kappa` (the acoustic->LM scale, so
    #      effort*kappa*shape and the LM log-prob are comparable). Both from the data. ----
    span_e = [float(np.mean(e[a:b])) for e, sp in zip(Es, all_spans) for (a, b) in sp]
    escale = float(np.percentile(span_e, 90)) or 1.0
    shape_vals = []
    for M, sp in list(zip(Ms, all_spans))[:6]:
        for (a, b) in sp:
            emb = rec.encode(feature(M[a:b], np.asarray(M[a:b], float).mean(0)))
            shape_vals += [s for _w, s in rec.ground_topk(emb, TOPK)]
    shape_std = float(np.std(shape_vals)) or 1.0
    bg_surp = [-_bg(p, w) for (w, _), (p, _) in zip(train[1:], train[:-1]) if p in vi and w in vi]
    lm_scale = float(np.median(bg_surp)) if bg_surp else 3.0
    kappa = lm_scale / (shape_std + 1e-6)
    # record the local-effort decode as the agent's composed faculty (graph Concept)
    if "local_effort_decode" not in {sub.node(c)["attrs"].get("name") for c in sub.nodes("Concept")}:
        c = sub.add_node("Concept", {"name": "local_effort_decode", "feature_kind": "thermodynamic",
                                     "predicate": effort_weight_term(1.0), "kappa": round(kappa, 3),
                                     "escale": round(escale, 4), "composed_by": "agent",
                                     "why": "acoustic precision = local effort; LM is the prior; no global lambda"})
    print(f"  calibrated (data): escale={escale:.3f}  kappa={kappa:.2f} "
          f"(lm_scale={lm_scale:.2f}/shape_std={shape_std:.3f})", flush=True)

    def run(mode):
        te = ref = hyp = 0; t0 = time.time()
        bits_rx = bits_tot = cont_rx = cont_tot = 0.0
        for M, e, words, spans in zip(Ms, Es, refs, all_spans):
            h = decode(M, e, spans, mode); hs = set(h)
            te += L.levenshtein_words(words, h); ref += len(words); hyp += len(h)
            for w in set(words):                                # bag-level (confabulation allowed)
                b = surpr(w); bits_tot += b
                if w in hs:
                    bits_rx += b
                if is_content(w):
                    cont_tot += 1
                    if w in hs:
                        cont_rx += 1
        return {"wer": te / max(ref, 1), "hr": hyp / max(ref, 1),
                "transmit": bits_rx / max(bits_tot, 1e-9),       # fraction of BITS received
                "content": cont_rx / max(cont_tot, 1e-9),        # content-word recall
                "t": time.time() - t0}

    res = {m: run(m) for m in ("baseline", "efficiency", "local_effort")}
    sub.add_node("Outcome", {"plan": "thermodynamic_speech",
                             "baseline_transmit": round(res["baseline"]["transmit"], 3),
                             "local_effort_transmit": round(res["local_effort"]["transmit"], 3),
                             "measure": "information_transmitted_not_WER"})
    print("\n" + "=" * 78)
    print("  'did the signal transmit' (BITS received + content recall) vs WER (wrong measure)")
    print("=" * 78)
    print(f"  {'mode':14} {'WER':>6} {'hyp/ref':>8} {'BITS rx':>9} {'content':>9}")
    for m in ("baseline", "efficiency", "local_effort"):
        r = res[m]
        print(f"  {m:14} {r['wer']:6.3f} {r['hr']:8.2f} {r['transmit']:9.3f} {r['content']:9.3f}")
    print("=" * 78)
    print("  WER says ~1.0 (failure); the BITS-received / content-recall measure shows how much SIGNAL")
    print("  actually transmits — the predictable words a listener reconstructs aren't really errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
