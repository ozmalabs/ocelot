"""REFERENTIAL COMMUNICATION — THE CAPSTONE: the full communicative loop closes over MEANING.

This ties the whole architecture into ONE loop where a referent (an intent / a meaning) is CONVEYED,
RECOVERED, and GROUNDED — donkey=0, every decision a held Rust Term, every piece REUSED (not re-derived):

  SPEAKER has a REFERENT (intent)
     -> PRODUCES a word-form  (the two-model PRAGMATIC speaker: models the listener + shared context,
        picks the midpoint encoding J = recovery - lambda*cost   [pragmatic_speaker, 212f4316])
     -> LISTENER RECOVERS THE REFERENT  (referential comprehension = the held Bayes posterior over
        referents: P(referent | form, shared-context)            [context_prior_speaker, 697a72a2 +
        referential_word_learning recogniser, e505642b])
     -> GROUNDING / REPAIR on failure  (held Bayesian belief-update over the audience; common ground
        builds turn by turn                                       [grounding_repair, 067bce32])

THE WORD-FORM CHANNEL IS REAL (earn-not-borrow). The referents + word-forms come from
referential_word_learning (real LibriSpeech tokens -> earned referent-driven space; comprehension =
recover the referent). A PRODUCTION at explicitness e interpolates a real held-out token z of the
intended referent from the DECISION BOUNDARY with its nearest confusable competitor (e=0, terse,
ambiguous, cheap) to the token itself (e=1, explicit, clear, costly). The listener scores it against
the held referent centroids. So the loop genuinely transmits a MEANING over the audio word channel.

WHAT IS HELD / DONKEY=0. Speaker midpoint = PS.choose_encoding (held Argmax-of-Plus). Listener =
CP.posterior_recovery / posterior_predict (held Bayes posterior over referents). Repair = GR.belief_update
+ GR.outcome_loglik (held Bayesian update). The referent geometry / likelihoods are adapter math; every
DECISION is a Rust Term via substrate.evaluate. No LLM, no borrowed net, no gradient-net.

GATE (controls, honest):
  (a) ★ COMMUNICATIVE SUCCESS — the listener recovers the SPEAKER'S INTENDED REFERENT >> chance and >>
      a form-only baseline (cheap blind production + no shared context). Meaning in -> meaning out.
  (b) ★ PRAGMATIC / SHARED-CONTEXT ADVANTAGE — the speaker that MODELS THE LISTENER + uses the shared
      referent-context prior beats a listener-BLIND speaker on referent-transmission; and the referent
      prior DRIVES the encoding (terser when the shared referent-context is peaked).
  (c) ★ GROUNDING / REPAIR — when transmission FAILS the held belief-update improves it over rounds and
      common ground BUILDS (|assumed - true| shrinks); repair curve vs no-feedback (+ wrong-direction).
  (d) DISCRIMINATIVE — real referent-communication > SHUFFLED; each piece (pragmatic, shared-context,
      repair) contributes (ablation).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/referential_communication.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np

from substrate_rs import Substrate
import domains.many_settings_recognizer as MS
import domains.pragmatic_speaker as PS
import domains.context_prior_speaker as CP
import domains.grounding_repair as GR
from scripts.referential_word_learning import (
    load_tokens, pca_fit, lda_fit, centroids_of, _unit, cross_situational_em, build_scenes)

Pred = MS._Pred
LAMBDA = 0.3                         # speaker's production-vs-decoding trade (fixed; from grounding_repair_gate)
N_RUNGS = 7                          # explicitness spectrum (terse boundary -> explicit prototype)
TEMP = 0.20                          # likelihood softness: a terse form is genuinely ambiguous, so the
#                                      shared-context prior carries the discrimination (drives terseness)
SUCCESS_THR = 0.60                   # decode-success threshold on the held Bayes recovery
GRID = [0.0, 0.4, 0.7, 0.9, 0.98]    # belief grid over candidate audience peakednesses
TURN_BUDGET = 6


def _softmax(x, t):
    x = np.asarray(x, float) / t; x -= x.max()
    e = np.exp(x); return e / e.sum()


# --------------------------------------------------------------------------- #
#  GEOMETRY — reuse referential_word_learning: real tokens -> earned referent-driven space + centroids.
# --------------------------------------------------------------------------- #
def setup(quick):
    rng = np.random.default_rng(0)
    feats, vocab = load_tokens(10 if quick else 30, 16 if quick else 22, 16 if quick else 26)
    V = len(vocab); ref_of = {w: i for i, w in enumerate(vocab)}; all_refs = list(range(V))
    Xtr, ytr, Xte, yte = [], [], [], []
    for w in vocab:
        Z = feats[w]; idx = rng.permutation(len(Z)); cut = int(0.7 * len(Z))
        for i in idx[:cut]: Xtr.append(Z[i]); ytr.append(w)
        for i in idx[cut:]: Xte.append(Z[i]); yte.append(w)
    Xtr = np.stack(Xtr); Xte = np.stack(Xte)
    mu, Wp = pca_fit(Xtr, 40); Ptr = (Xtr - mu) @ Wp; Pte = (Xte - mu) @ Wp
    scenes = build_scenes(ytr, ref_of, all_refs, 4, rng)
    inferred = cross_situational_em(Ptr, scenes, all_refs, rng, iters=10)   # referents inferred, NO transcripts
    Wref = lda_fit(Ptr, inferred, 40); Ztr = _unit(Ptr @ Wref); Zte = _unit(Pte @ Wref)
    cen = centroids_of(Ztr, [ref_of[w] for w in ytr])                       # listener's referent centroids
    d = next(iter(cen.values())).shape[0]
    C = np.stack([cen.get(r, np.zeros(d)) for r in range(V)])
    sims = C @ C.T
    nbr_rank = [[int(j) for j in np.argsort(-sims[r]) if j != r] for r in range(V)]   # confusability ranking
    tokens = [(ref_of[w], _unit(z[None])[0]) for z, w in zip(Zte, yte)]     # held-out productions (real audio)
    return dict(V=V, vocab=vocab, C=C, nbr=nbr_rank, tokens=tokens, rng=rng)


def episode(ti, z, C, nbr, n_rungs=N_RUNGS, temp=TEMP):
    """Production spectrum for intent referent ti from a real token z: e=0 is maximally REDUCED toward the
    GLOBAL centroid (terse/cheap/ambiguous among ALL referents — the shared context must disambiguate);
    e=1 is the token itself (explicit/costly/clear, the form carries the meaning alone). Per rung: the
    held listener LIKELIHOOD over referents (softmax of dot to the referent centroids)."""
    anchor = _unit(C.mean(0)[None])[0]                                     # maximally ambiguous reduction
    es = np.linspace(0.0, 1.0, n_rungs)
    liks, ts, cn, forms = [], [], [], []
    for e in es:
        form = _unit(((1 - e) * anchor + e * z)[None])[0]
        forms.append(form); liks.append(_softmax(C @ form, temp).tolist())
        ts.append(float(1 - e)); cn.append(float(e))                       # terseness ; explicitness cost
    return dict(ti=ti, nbr=nbr[ti], ts=ts, cn=cn, liks=liks, es=es.tolist(), _forms=forms)


def speaker_choose(ep, peak, blind=False, fixed_e=None):
    """The held pragmatic speaker: pick the rung that maximises J = recovery(under shared context) -
    lambda*cost (PS.choose_encoding). A listener-BLIND speaker ignores recovery (fixed explicitness)."""
    if blind:
        return int(np.argmin(np.abs(np.array(ep["es"]) - (0.5 if fixed_e is None else fixed_e))))
    pri = CP.parametric_prior(len(ep["liks"][0]), ep["ti"], peak, neighbour_idx=ep["nbr"])
    recs = [CP.posterior_recovery(Substrate, Pred, lik, pri, ep["ti"]) for lik in ep["liks"]]
    _t, idx = PS.choose_encoding(Substrate, Pred, ep["ts"], recs, ep["cn"], LAMBDA)
    return idx


def listener_recover(ep, idx, peak, C=None):
    """The held Bayes listener: recover the referent = argmax P(referent | form, shared-context).
    C (optional) permutes the centroids for the SHUFFLED control (form no longer matches its referent)."""
    lik = ep["liks"][idx]
    if C is not None:                                                      # shuffled: re-score against permuted centroids
        form = ep["_forms"][idx]; lik = _softmax(C @ form, TEMP).tolist()
    pri = CP.parametric_prior(len(lik), ep["ti"], peak, neighbour_idx=ep["nbr"])
    return CP.posterior_predict(Substrate, Pred, lik, pri, ep["ti"])


# =========================================================================== #
def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 100)
    print("REFERENTIAL COMMUNICATION — the full loop closes over MEANING (speaker->form->listener->repair)")
    print("  every decision a held Rust Term (donkey=0); word-form channel = real audio (earn-not-borrow)")
    print("=" * 100, flush=True)
    g = setup(quick); V, C, nbr, tokens, rng = g["V"], g["C"], g["nbr"], g["tokens"], g["rng"]
    chance = 1.0 / V
    print(f"  {V} referents (chance {chance:.3f}); {len(tokens)} held-out productions  [{time.time()-t0:.0f}s]",
          flush=True)
    n_trials = min(len(tokens), 150 if quick else 400)
    sel = rng.permutation(len(tokens))[:n_trials]
    peaks_mix = [0.0, 0.4, 0.7, 0.9]                                        # mixed shared-context strength

    # ---- (a) COMMUNICATIVE SUCCESS: meaning in -> meaning out ----
    eps = [episode(*tokens[k], C, nbr) for k in sel]
    succ_full = succ_form = succ_blind = succ_flat = 0
    e_full = []
    for ep in eps:
        peak = float(rng.choice(peaks_mix))
        idx = speaker_choose(ep, peak); e_full.append(ep["es"][idx])
        succ_full += int(listener_recover(ep, idx, peak) == ep["ti"])      # FULL loop (pragmatic + context)
        # form-only: cheapest blind production (terse, e=0) decoded with NO shared context (flat prior)
        succ_form += int(listener_recover(ep, 0, 0.0) == ep["ti"])
        # ablations for (d): blind speaker (fixed mid e) WITH context ; full speaker WITHOUT context (flat)
        succ_blind += int(listener_recover(ep, speaker_choose(ep, peak, blind=True), peak) == ep["ti"])
        succ_flat += int(listener_recover(ep, speaker_choose(ep, 0.0), 0.0) == ep["ti"])
    n = len(eps)
    print("\n--- (a) ★ COMMUNICATIVE SUCCESS — listener recovers the speaker's INTENDED referent ---")
    print(f"  FULL loop (pragmatic + shared context) : {succ_full/n:.3f}")
    print(f"  form-only (cheap blind, no context)    : {succ_form/n:.3f}")
    print(f"  chance                                 : {chance:.3f}")
    print(f"  -> meaning in -> meaning out: {succ_full/n:.3f} vs form-only {succ_form/n:.3f} vs chance {chance:.3f}")

    # ---- (b) PRAGMATIC / SHARED-CONTEXT ADVANTAGE + referent-prior drives terseness ----
    print("\n--- (b) ★ PRAGMATIC vs listener-BLIND + does the referent-prior DRIVE terseness ---")
    print(f"  referent-transmission: pragmatic {succ_full/n:.3f}  vs  blind(fixed-e) {succ_blind/n:.3f}  "
          f"vs  no-context(flat) {succ_flat/n:.3f}")
    print(f"  {'peak':>5} {'mean chosen explicitness e*':>28}  (terser = LOWER e as shared context PEAKS)")
    e_by_peak = []
    sweep = [0.0, 0.4, 0.7, 0.9, 0.98]
    probe = eps[: min(len(eps), 120)]
    for peak in sweep:
        me = float(np.mean([ep["es"][speaker_choose(ep, peak)] for ep in probe]))
        e_by_peak.append(me); print(f"  {peak:5.2f} {me:28.3f}{'   (no context: hopeless -> no effort spent)' if peak==0 else ''}")
    # the wife-vs-wide effect lives in the INFORMATIVE range (peak>0): terser as shared context PEAKS.
    drives = e_by_peak[1] - e_by_peak[-1]
    print(f"  -> within informative context (peak 0.4->0.98) explicitness FALLS by {drives:+.3f} "
          f"({'referent-prior DRIVES terseness — terser when context peaks' if drives > 0.03 else 'weak/no drive'})")

    # ---- (c) GROUNDING / REPAIR over referents: common ground builds ----
    print("\n--- (c) ★ GROUNDING / REPAIR — held belief-update builds common ground over rounds ---")
    P_TRUE = 0.4                                                            # audience really has little shared context
    rep_refs = eps[: min(len(eps), 12 if quick else 40)]

    # OVER-CONFIDENT start: the speaker initially believes the audience shares MORE context than it does
    # (MAP on the highest peakedness) -> it starts too TERSE and must repair DOWN to explicit.
    init_lb = [-3.0 * (len(GRID) - 1 - i) for i in range(len(GRID))]
    init_lb = [v - max(init_lb) for v in init_lb]

    def run_dialogue(ep, mode):
        lb = list(init_lb); succ_curve = []; map_curve = []
        for _turn in range(TURN_BUDGET):
            if mode == "explicit":                                         # always-explicit control (flat assume)
                p_assume = GRID[0]
            else:
                p_assume, _ = GR.belief_map(Substrate, Pred, GRID, lb)
            idx = speaker_choose(ep, p_assume)
            rec = CP.posterior_recovery(Substrate, Pred, ep["liks"][idx],
                                        CP.parametric_prior(V, ep["ti"], P_TRUE, neighbour_idx=ep["nbr"]), ep["ti"])
            success = rec >= SUCCESS_THR
            succ_curve.append(int(success)); map_curve.append(p_assume)
            recs_grid = [CP.posterior_recovery(Substrate, Pred, ep["liks"][idx],
                         CP.parametric_prior(V, ep["ti"], pg, neighbour_idx=ep["nbr"]), ep["ti"]) for pg in GRID]
            if mode == "feedback":
                ll = GR.outcome_loglik(recs_grid, success, SUCCESS_THR)
            elif mode == "wrongdir":
                ll = GR.outcome_loglik_wrongdir(recs_grid, success, SUCCESS_THR)
            else:                                                          # nofeedback / explicit: belief frozen
                ll = [0.0] * len(GRID)
            lb, _pp, _mp, _mi = GR.belief_update(Substrate, Pred, GRID, lb, ll)
        return np.array(succ_curve, float), np.array(map_curve, float)

    curves = {m: np.mean([run_dialogue(ep, m)[0] for ep in rep_refs], 0)
              for m in ("feedback", "nofeedback", "wrongdir")}
    map_fb = np.mean([run_dialogue(ep, "feedback")[1] for ep in rep_refs], 0)
    print(f"  audience TRUE peakedness P_TRUE={P_TRUE}; success thr={SUCCESS_THR}; turns={TURN_BUDGET}")
    print(f"  {'turn':>5} {'feedback':>9} {'no-feedback':>12} {'wrong-dir':>10}   assumed-peak(feedback)")
    for ti in range(TURN_BUDGET):
        print(f"  {ti:5d} {curves['feedback'][ti]:9.3f} {curves['nofeedback'][ti]:12.3f} "
              f"{curves['wrongdir'][ti]:10.3f}        {map_fb[ti]:.3f}")
    cg0, cg1 = abs(map_fb[0] - P_TRUE), abs(map_fb[-1] - P_TRUE)
    print(f"  -> common ground BUILDS: |assumed-true| {cg0:.3f} -> {cg1:.3f}; "
          f"repair success {curves['feedback'][0]:.3f} -> {curves['feedback'][-1]:.3f} "
          f"(no-feedback flat at {curves['nofeedback'][-1]:.3f})")

    # ---- (d) DISCRIMINATIVE: real vs shuffled referent-communication ----
    perm = rng.permutation(V); Csh = C[perm]                               # break form<->referent grounding
    succ_shuf = 0
    for ep in eps:
        peak = float(rng.choice(peaks_mix))
        succ_shuf += int(listener_recover(ep, speaker_choose(ep, peak), peak, C=Csh) == ep["ti"])
    print("\n--- (d) DISCRIMINATIVE — real vs shuffled; ablation ---")
    print(f"  real referent-communication : {succ_full/n:.3f}")
    print(f"  SHUFFLED referents          : {succ_shuf/n:.3f}  (form no longer matches its referent)")
    print(f"  ablation: full {succ_full/n:.3f} | -pragmatic(blind) {succ_blind/n:.3f} | "
          f"-context(flat) {succ_flat/n:.3f} | -repair (turn0 {curves['feedback'][0]:.3f} vs final "
          f"{curves['feedback'][-1]:.3f})")

    print("\n--- donkey=0 / earn-not-borrow ---")
    print("  speaker midpoint = PS.choose_encoding (held Argmax-of-Plus); listener = CP.posterior_recovery/")
    print("  predict (held Bayes posterior over referents); repair = GR.belief_update (held Bayes). Word-form")
    print("  channel = real audio -> earned referent space. No LLM, no borrowed net, no gradient-net.")
    print(f"\n[done {time.time()-t0:.0f}s]", flush=True)

    a_pass = succ_full / n > max(3 * chance, succ_form / n + 0.05)
    b_pass = succ_full / n > succ_blind / n + 0.02 and drives > 0.03
    c_pass = curves['feedback'][-1] > curves['feedback'][0] + 0.1 and cg1 < cg0 - 0.05 and \
        curves['feedback'][-1] > curves['nofeedback'][-1] + 0.05
    d_pass = succ_full / n > succ_shuf / n + 0.1
    print("=" * 100)
    print(f"VERDICT  (a)COMMUNICATIVE-SUCCESS {'PASS' if a_pass else 'PARTIAL'}   "
          f"(b)PRAGMATIC+CONTEXT {'PASS' if b_pass else 'PARTIAL'}   "
          f"(c)REPAIR/COMMON-GROUND {'PASS' if c_pass else 'PARTIAL'}   "
          f"(d)DISCRIMINATIVE {'PASS' if d_pass else 'FAIL'}")
    print("=" * 100)


if __name__ == "__main__":
    main()
