"""collapse_core — the DOMAIN-AGNOSTIC manifold-collapse engine.

The architectural mandate: MAKE THE COLLAPSE LOOP THE CORE, EVERYTHING ELSE
PLUGGABLE SCAFFOLDING. This file IS that core. It knows NOTHING about speech,
text, voice, or any domain. It operates ONLY on:

  * MANIFOLDS  — a distribution over a domain's admissible hypotheses
                 (a dict hypothesis -> probability).
  * COLLAPSE   — iterate: as the plug reveals evidence, rebuild the manifold and
                 watch it sharpen (admissibility prunes the inadmissible).
  * MEASURE    — entropy-collapse curve, calibration/ECE, cohort/recognition
                 point, shuffle control, garden-path / re-open detection.
  * LOCALISE   — on collapse FAILURE (truth pruned / collapse-to-wrong / surprise
                 / re-open) expose WHICH admissibility link failed. The
                 construct-the-structure step is a HOOK the plug/agent fills.

The core is PURE: collapse + measure + localise. No LM, no net, no .fit, no
sweep. All admissibility comes from the plug's OWN counted/constructed structure.

----------------------------------------------------------------------------
THE PLUG (the domain interface / contract). A domain is any object providing:

  trials()                 -> iterable of opaque `trial` handles (one per signal
                              to collapse; e.g. a target sentence, a held-out
                              speaker utterance).

  truth(trial)             -> the true hypothesis for `trial` (for measurement +
                              the learning signal).

  fractions()              -> the ordered list of evidence fractions to probe
                              (e.g. [0.0, 0.1, ... 0.9]); the x-axis of collapse.

  evidence(trial, frac)    -> the PROGRESSIVE EVIDENCE revealed at this fraction
                              (the "chop": reveal evidence incrementally). An
                              opaque token the plug's own scorer understands
                              (a prefix tuple, a list of revealed cues, ...).

  manifold(trial, evidence)-> the ADMISSIBLE manifold given that evidence: a list
                              of (hypothesis, probability) pairs, sorted desc,
                              normalised. Built from the domain's OWN counted /
                              constructed structure (donkey-clean). This is the
                              one method that encodes the domain's admissibility.

  --- OPTIONAL ---
  forward(hypothesis)      -> expected evidence for a hypothesis (analysis-by-
                              synthesis); if present the core can report
                              synthesis-error collapse. May be absent.

  localise(trial, evidence, manifold, truth)
                           -> when the core detects a collapse failure it asks the
                              plug to name the missing structure (which
                              admissibility link failed). Returns a short string /
                              dict. The core supplies WHEN (the failure events);
                              the plug supplies WHAT (its own structure). May be
                              absent (core then reports the generic failure kind).

That is the whole contract. Swap the plug, the core is identical.
"""
from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# pure manifold operations (the core's vocabulary — distributions over hyps)
# ---------------------------------------------------------------------------

def entropy_bits(manifold):
    """Shannon entropy of a manifold (list of (hyp, p)) in bits."""
    h = 0.0
    for _hyp, p in manifold:
        if p > 0:
            h -= p * math.log2(p)
    return h


def effective_support(manifold, mass=0.99):
    """# of top hypotheses holding `mass` of the probability — the manifold's
    effective admissible-set size (a graded cohort size)."""
    acc = 0.0
    n = 0
    for _hyp, p in manifold:
        acc += p
        n += 1
        if acc >= mass:
            break
    return n


def truth_entry(manifold, truth):
    """(rank, prob) of `truth` in the manifold, or (-1, 0.0) if pruned out."""
    for rank, (hyp, p) in enumerate(manifold):
        if hyp == truth:
            return rank, p
    return -1, 0.0


# ---------------------------------------------------------------------------
# the COLLAPSE ITERATION + MEASUREMENT (domain-agnostic)
# ---------------------------------------------------------------------------

REC_THRESH = 0.5      # truth recognised = it is top-1 AND holds >50% of the mass
COMMIT_THRESH = 0.8   # manifold "committed" to a top when it exceeds this
ECE_BINS = 10


def collapse_trial(plug, trial):
    """Run ONE trial through the collapse loop: at each fraction, ask the plug for
    evidence + the manifold, and record the manifold's state. Returns a per-trial
    record (all domain-agnostic measurements). Also extracts the LEARNING SIGNAL on
    any collapse failure, localised via the plug's hook if present."""
    truth = plug.truth(trial)
    fracs = plug.fractions()
    rows = []                      # per-fraction (frac, size, ent, truth_conf, truth_rank, top)
    calib = []                     # (top1_conf, top1_is_truth)
    rec_point = None               # fraction at which truth becomes confident top
    committed_top = None           # a hypothesis the manifold grew confident in
    garden_events = []             # (frac, committed, reopened_to) re-open events
    failures = []                  # learning signal: localised collapse failures

    has_fwd = hasattr(plug, "forward")
    synth_err = []                 # (frac, error) if a forward model is present

    for f in fracs:
        ev = plug.evidence(trial, f)
        man = plug.manifold(trial, ev)
        size = effective_support(man)
        ent = entropy_bits(man)
        t_rank, t_conf = truth_entry(man, truth)
        top = man[0] if man else (None, 0.0)
        rows.append((f, size, ent, t_conf, t_rank, top[0]))

        if man:
            top_hyp, top_p = top
            calib.append((top_p, top_hyp == truth))

            # --- garden-path / re-open: committed (>0.8) to a WRONG top, then a
            #     later fraction forces a different top (the bounded-flex re-open).
            if committed_top is not None and top_hyp != committed_top \
                    and committed_top != truth:
                garden_events.append((f, committed_top, top_hyp))
                # LEARNING SIGNAL: a re-open is a localisable structure failure.
                failures.append(_localise(plug, trial, ev, man, truth,
                                          kind="reopen"))
                committed_top = None
            if top_p > COMMIT_THRESH:
                committed_top = top_hyp

            # --- collapse-to-WRONG: committed-confident on a non-truth.
            if top_p > COMMIT_THRESH and top_hyp != truth:
                failures.append(_localise(plug, trial, ev, man, truth,
                                          kind="collapse_to_wrong"))

        # --- truth PRUNED: the true hypothesis fell out of the admissible set.
        if t_rank < 0 and man:
            failures.append(_localise(plug, trial, ev, man, truth,
                                      kind="truth_pruned"))

        # recognition point: truth is the manifold's confident top
        if rec_point is None and man and man[0][0] == truth \
                and man[0][1] >= REC_THRESH:
            rec_point = f

        # optional analysis-by-synthesis: how far is the top hyp's predicted
        # evidence from the observed evidence?
        if has_fwd and man:
            err = plug.synthesis_error(trial, ev, man[0][0]) \
                if hasattr(plug, "synthesis_error") else None
            if err is not None:
                synth_err.append((f, err))

    # --- SURPRISE failure: at the LAST fraction the truth is still not the
    #     confident top — the collapse never reached truth (a localisable miss).
    if rec_point is None:
        last_f = fracs[-1]
        ev = plug.evidence(trial, last_f)
        man = plug.manifold(trial, ev)
        failures.append(_localise(plug, trial, ev, man, truth, kind="surprise"))

    return {
        "truth": truth,
        "rows": rows,
        "calib": calib,
        "rec_point": rec_point if rec_point is not None else 1.0,
        "garden_events": garden_events,
        "failures": failures,
        "synth_err": synth_err,
    }


def _localise(plug, trial, ev, man, truth, kind):
    """Ask the plug to localise the failure (which admissibility link failed). The
    core supplies the failure KIND (when); the plug supplies the WHAT. If the plug
    has no localise hook, return the generic kind — the hook the agent can fill."""
    detail = None
    if hasattr(plug, "localise"):
        try:
            detail = plug.localise(trial, ev, man, truth, kind)
        except Exception as e:                     # plug hook is best-effort
            detail = f"<localise error: {e}>"
    return {"kind": kind, "detail": detail}


# ---------------------------------------------------------------------------
# aggregation across trials (the MEASUREMENT SUITE — domain-agnostic)
# ---------------------------------------------------------------------------

def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def calibration_curve(calib, nbins=ECE_BINS):
    """Reliability: bin top-1 confidence, report (lo, hi, mean_conf, hit_rate, n)
    per bin and the Expected Calibration Error (ECE). Pure: works on any domain's
    (confidence, was-truth) pairs."""
    bins = [[] for _ in range(nbins)]
    for p, hit in calib:
        b = min(int(p * nbins), nbins - 1)
        bins[b].append((p, 1.0 if hit else 0.0))
    rows = []
    ece = 0.0
    N = max(len(calib), 1)
    for b in range(nbins):
        if not bins[b]:
            continue
        mp = _mean([x[0] for x in bins[b]])
        acc = _mean([x[1] for x in bins[b]])
        n = len(bins[b])
        rows.append((b / nbins, (b + 1) / nbins, mp, acc, n))
        ece += (n / N) * abs(mp - acc)
    return rows, ece


def aggregate(plug, records):
    """Aggregate per-trial records into the full measurement suite. Domain-agnostic:
    it only ever touches manifolds, fractions, truth-presence, confidences."""
    fracs = plug.fractions()
    by_f = {f: {"size": [], "ent": [], "tconf": [], "tin": []} for f in fracs}
    calib = []
    rec_points = []
    garden = 0
    garden_examples = []
    n_failures = {"truth_pruned": 0, "collapse_to_wrong": 0, "reopen": 0,
                  "surprise": 0}
    failure_details = []
    synth_curve = {f: [] for f in fracs}

    for rec in records:
        for (f, size, ent, tconf, trank, _top) in rec["rows"]:
            by_f[f]["size"].append(size)
            by_f[f]["ent"].append(ent)
            by_f[f]["tconf"].append(tconf)
            by_f[f]["tin"].append(1.0 if trank >= 0 else 0.0)
        calib.extend(rec["calib"])
        rec_points.append(rec["rec_point"])
        garden += len(rec["garden_events"])
        for ev in rec["garden_events"][:1]:
            if len(garden_examples) < 8:
                garden_examples.append(ev)
        for fl in rec["failures"]:
            n_failures[fl["kind"]] = n_failures.get(fl["kind"], 0) + 1
            if fl["detail"] is not None and len(failure_details) < 12:
                failure_details.append(fl)
        for (f, err) in rec["synth_err"]:
            synth_curve[f].append(err)

    rows, ece = calibration_curve(calib)
    return {
        "fracs": fracs,
        "size": {f: _mean(by_f[f]["size"]) for f in fracs},
        "ent": {f: _mean(by_f[f]["ent"]) for f in fracs},
        "truth_conf": {f: _mean(by_f[f]["tconf"]) for f in fracs},
        "truth_in_set": {f: _mean(by_f[f]["tin"]) for f in fracs},
        "calib_rows": rows,
        "ece": ece,
        "rec_points": rec_points,
        "garden": garden,
        "garden_examples": garden_examples,
        "failures": n_failures,
        "failure_details": failure_details,
        "synth_curve": {f: _mean(synth_curve[f]) for f in fracs if synth_curve[f]},
        "n_trials": len(records),
    }


def run_plug(plug):
    """THE CORE LOOP. Run every trial of a plug through the collapse iteration and
    return the aggregated measurement suite. This function is IDENTICAL across all
    domains — only `plug` differs. That identity IS the domain-agnosticism proof."""
    records = [collapse_trial(plug, t) for t in plug.trials()]
    return aggregate(plug, records)


# ---------------------------------------------------------------------------
# reporting (domain-agnostic: prints any plug's collapse suite the same way)
# ---------------------------------------------------------------------------

def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    return xs[min(int(q * len(xs)), len(xs) - 1)]


def report(name, agg, hyp_label="hypothesis"):
    """Print the measurement suite for one plug. Same code for every domain."""
    fr = agg["fracs"]
    print("\n" + "=" * 68)
    print(f"PLUG: {name}   ({agg['n_trials']} trials, {hyp_label} hypotheses)")
    print("=" * 68)

    print("\n(1) COLLAPSE CURVE — admissible-set size & manifold entropy")
    print(f"{'frac':>5} | {'adm_size':>9} | {'entropy_bits':>12} | "
          f"{'truth_conf':>10} | {'truth_in_set':>12}")
    for f in fr:
        print(f"{f:>5.2f} | {agg['size'][f]:>9.1f} | {agg['ent'][f]:>12.3f} | "
              f"{agg['truth_conf'][f]:>10.3f} | {agg['truth_in_set'][f]:>12.3f}")

    print("\n(2) CALIBRATION — is the collapse HONEST? (reliability + ECE)")
    print(f"{'conf_bin':>14} | {'mean_conf':>9} | {'hit_rate':>8} | {'n':>6}")
    for lo, hi, mp, acc, n in agg["calib_rows"]:
        print(f"  [{lo:.1f},{hi:.1f})    | {mp:>9.3f} | {acc:>8.3f} | {n:>6}")
    print(f"Expected Calibration Error : {agg['ece']:.4f}")

    print("\n(3) COHORT / RECOGNITION POINT")
    rp = agg["rec_points"]
    print(f"  median {pct(rp,0.5):.2f}  mean {_mean(rp):.3f}  "
          f"p25 {pct(rp,0.25):.2f}  p75 {pct(rp,0.75):.2f}  "
          f"never-unique(=1.0): {sum(1 for x in rp if x>=1.0)}/{len(rp)}")
    hist = {}
    for x in rp:
        hist[round(x, 2)] = hist.get(round(x, 2), 0) + 1
    print("  recognition-point histogram: "
          + "  ".join(f"{k:.2f}:{hist[k]}" for k in sorted(hist)))

    print("\n(4) GARDEN-PATH / RE-OPEN")
    print(f"  committed-then-overturned events: {agg['garden']}")
    for f, was, now in agg["garden_examples"]:
        print(f"    @f={f:.2f}  committed={_short(was)}  ->  reopened={_short(now)}")

    if agg["synth_curve"]:
        print("\n(4b) ANALYSIS-BY-SYNTHESIS — top-hyp synthesis error vs fraction")
        for f in fr:
            if f in agg["synth_curve"]:
                print(f"  f={f:.2f}  synth_err={agg['synth_curve'][f]:.4f}")

    print("\n(5) LEARNING SIGNAL — localised collapse failures (the hook)")
    print(f"  failure counts: {agg['failures']}")
    for fl in agg["failure_details"][:6]:
        print(f"    [{fl['kind']}] {fl['detail']}")


def _short(h):
    s = str(h)
    return s if len(s) <= 40 else s[:37] + "..."
