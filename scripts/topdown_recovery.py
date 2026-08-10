"""topdown_recovery — DO-CONTRAST: does routing recognition through the TOP-DOWN
recovery COMPENSATE for the BLUNT cochlea, the way humans recognise robustly with
the same coarse ear?

THE JABBERWOCK'S OWN REFRAMED PRESCRIPTION (docs/jabberwock_human_bad_ears.md):
don't densify the cochlea — wire the TOP-DOWN SYNTHESIS in as the RECOVERY of what
the blunt cochlea under-resolves. The human cochlea is the SAME coarse front-end
the agent copies; humans recognise robustly anyway by routing recognition through
TOP-DOWN recovery: invert the forward model against a NARROW ADMISSIBLE SET (the
prior/context), so the coarse cue only PRUNES the manifold rather than RESOLVING
the answer.

THE HYPOTHESIS (the agent's, to TEST):
  The blunt cochlear estimate CAPS bottom-up recognition (the coarse cue must
  carry the whole decision). Route recognition through the TOP-DOWN recovery the
  agent ALREADY BUILT — native collapse core (T8) + owned forward model (T10) +
  surprise + a prior — with the coarse cue PRUNING the admissible set and the
  forward model + prior RESOLVING. Does it COMPENSATE for the blunt ear?

THE DO-CONTRAST (one blunt front end, two recognition ROUTES):

  BLUNT EAR  — the SAME deliberately-coarsened cochlea for BOTH routes. We coarsen
    the 32-band gammatone trajectory to N_BLUNT effective bands (the "human bad
    ears" copy: a low-resolution spectral snapshot). This is the blunt cue.

  (A) BOTTOM-UP (the blunt estimate RESOLVES) — classify by the coarse cue
      directly: argmin over words of the BLUNT-representation DTW distance to the
      forward model. The coarse cochlear snapshot must carry the whole decision.
      This is the cap the directive names.

  (B) TOP-DOWN RECOVERY (coarse cue PRUNES, forward model + prior RESOLVE) — the
      blunt cue only PRUNES the candidate manifold to the top-K admissible set
      (it CANNOT rule out the answer, only narrow it). Then the agent's OWN native
      collapse core RESOLVES among the pruned set by INVERTING the forward model:
      the manifold log-weight of each surviving candidate is
          lw(w) = -DtwTo(heard, forward_model[w])  +  log prior(w)
      collapsed natively (T_CONF / T_SURPRISE in Rust), surprise as the signal.
      The DtwTo MATCH runs on the FULL forward-model trajectory (the synthesis the
      agent can imagine at full resolution — the brain inverts an internal model,
      not the blurred input) — so the blunt ear PRUNES, the synthesis RESOLVES.
      This is analysis-by-synthesis (T6/T10) routed through the collapse core (T8)
      with the coarse cue as the admissibility PRUNE, exactly the prescription.

  The PRIOR is the agent's own learned context: a frequency/transition prior over
  the lexicon read off the data the forward model was built from (NOT a fit; a
  count). On continuous digit-strings it becomes a bigram-transition prior — the
  same top-down "restoration from context" the order-N loop uses. DONKEY-clean: a
  count, not a parameter.

ARCHITECTURE (CLAUDE.md): the cognition is NATIVE. The collapse decision,
confidence, surprise, and the DtwTo match all run as graph Term-trees evaluated by
substrate.evaluate in Rust (NC.T_MAX_LW / T_Z / T_CONF / T_SURPRISE,
RG.synth_error_term's DtwTo). The forward model is the owned per-word mean A1
trajectory (T10, LOSO). Python is the WORLD ADAPTER + measurement instrument ONLY:
audio I/O, the blunt-ear coarsening (a mechanical signal op — downsample the band
axis), and the do-contrast bookkeeping. The PRUNE and the PRIOR enter the manifold
as graph data (candidate set restriction + log-prior added to lw); the RESOLUTION
is the native collapse. NO net, NO .fit, NO gradient, NO sweep. solve_for_n.py and
CortexLoop are UNTOUCHED. No new Python cognition: the recognition DECISION is the
native argmax-of-collapse, not a Python conditional.

Run: PYTHONUNBUFFERED=1 python -m scripts.topdown_recovery [n_per_speaker_per_digit]
"""
from __future__ import annotations

import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams
from domains import recognition_graph as RG
import scripts.native_collapse as NC
from scripts.analysis_by_synthesis_accept import (
    utterance_trajectory, traj_to_matrix, as_tuple,
)
from scripts.fsdd_learner_world import load_wav, gather_files

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# WORLD ADAPTER (1) — THE BLUNT EAR. Coarsen an A1 trajectory matrix
# (frames x patches) to N_BLUNT effective bands by averaging adjacent patch
# groups. This is the deliberate "human bad ears" copy: a low-resolution spectral
# snapshot. A mechanical signal op (downsample the band axis), NO graph decision.
# BOTH recognition routes consume the blunt features — the front end is identical;
# only the ROUTE differs. The blunt trajectory keeps the SAME number of frames
# (time resolution unchanged) so DTW is comparable; only the spectral axis is
# blurred — the cochlear-resolution knob.
# ==========================================================================

def blunt_matrix(M, n_blunt):
    """frames x patches  ->  frames x n_blunt  by averaging contiguous patch
    groups (box-car spectral downsample = a blunter cochlea). If n_blunt >= the
    native patch count, returns M unchanged (the sharp ear)."""
    if M is None:
        return None
    P = M.shape[1]
    if n_blunt >= P:
        return M
    edges = np.linspace(0, P, n_blunt + 1).astype(int)
    cols = [M[:, edges[k]:edges[k + 1]].mean(axis=1) for k in range(n_blunt)
            if edges[k + 1] > edges[k]]
    return np.stack(cols, axis=1).astype(np.float32)


# ==========================================================================
# THE FORWARD MODEL (T10) — per-word mean A1 trajectory over TRAIN speakers
# (LOSO). The owned word->sound forward model, at FULL resolution (the synthesis
# the agent can imagine sharply, even though the EAR is blunt). We also hold its
# blunt projection (for the bottom-up route + the prune cue).
# ==========================================================================

def build_forward_model(loaded, utt_traj, held_speaker):
    """word -> full-resolution mean per-utterance A1 trajectory matrix over
    TRAIN-speaker exemplars (LOSO). The owned forward model."""
    fm = {}
    for w in _DIGITS:
        ts = [utt_traj[i] for i, (x, fs, d, s) in enumerate(loaded)
              if _DIGITS[d] == w and s != held_speaker and utt_traj[i] is not None]
        if not ts:
            fm[w] = None
            continue
        L = min(len(t) for t in ts)
        fm[w] = traj_to_matrix(np.mean([t[:L] for t in ts], axis=0))
    return fm


def build_prior(loaded, held_speaker):
    """The agent's own learned PRIOR over the lexicon = the unigram count of each
    word over the TRAIN data (LOSO). A COUNT, not a fitted parameter — the
    top-down 'learned-category prior' the directive names. Returns log P(w)
    (add-1 smoothed; a fixed floor, not a knob)."""
    cnt = {w: 1.0 for w in _DIGITS}          # add-1 floor (fixed)
    for x, fs, d, s in loaded:
        if s != held_speaker:
            cnt[_DIGITS[d]] += 1.0
    tot = sum(cnt.values())
    return {w: float(np.log(cnt[w] / tot)) for w in _DIGITS}


def build_bigram_prior(strings_words):
    """Bigram TRANSITION prior over digit-strings (the top-down context prior the
    order-N loop leans on). log P(w_t | w_{t-1}) from COUNTS over the held-out
    speaker's own strings is NOT available (that is the test set); instead we use
    the count over the TRAIN strings. Returns (log_uni, log_bi) where log_bi maps
    (prev, w) -> log prob (add-1 over the lexicon)."""
    uni = {w: 1.0 for w in _DIGITS}
    bi = {}
    for ws in strings_words:
        for i, w in enumerate(ws):
            uni[w] += 1.0
            if i > 0:
                key = ws[i - 1]
                bi.setdefault(key, {v: 1.0 for v in _DIGITS})
                bi[key][w] += 1.0
    tot = sum(uni.values())
    log_uni = {w: float(np.log(uni[w] / tot)) for w in _DIGITS}
    log_bi = {}
    for prev, d in bi.items():
        z = sum(d.values())
        log_bi[prev] = {w: float(np.log(d[w] / z)) for w in _DIGITS}
    return log_uni, log_bi


# ==========================================================================
# THE NATIVE COLLAPSE UNIT — wires the native collapse core (scripts/
# native_collapse) over the digit manifold. Per segment, the candidate
# log-weights are set to  lw(w) = -DtwTo(heard, fm[w]) + log_prior(w)  and the
# winner / confidence / surprise are read NATIVELY (graph Term-trees in Rust).
#
# Two knobs the DO-CONTRAST flips, BOTH entering as GRAPH DATA (not Python
# cognition):
#   - admissible:  the set of candidates whose Cand node participates (the coarse
#     cue's PRUNE — non-admissible candidates get lw = -inf, i.e. removed from the
#     manifold). The collapse RESOLVES among the admitted.
#   - use_prior:   whether log_prior(w) is added to lw (the top-down prior).
#   - match_res:   'full' (DtwTo on the full forward model = top-down synthesis
#     resolves) or 'blunt' (DtwTo on the blunt forward model = the bottom-up
#     coarse-cue-resolves cap).
# ==========================================================================

class CollapseUnit:
    def __init__(self, sub, fm_full, fm_blunt, n_blunt):
        self.sub = sub
        self.n_blunt = n_blunt
        RG.mark_words(sub, _DIGITS)
        self.word_c = {}
        for w in _DIGITS:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "topdown"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"topdown_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())
        self.cands = NC.build_cand_nodes(sub, _DIGITS)
        self.fm_full = fm_full
        self.fm_blunt = fm_blunt

    def _heard_full(self, M):
        return as_tuple(M)

    def _heard_blunt(self, M):
        return as_tuple(blunt_matrix(M, self.n_blunt))

    def errs(self, heardM, match_res):
        """Native DtwTo synth-error of the heard segment vs each word's forward
        model, in the chosen resolution. Returns {word: error}. match_res='full'
        -> the agent inverts its full-resolution internal forward model (top-down
        synthesis resolves); 'blunt' -> the blunt forward model (coarse cue
        resolves). Both evaluated by the native graph DtwTo Term."""
        if heardM is None or heardM.shape[0] < 2:
            return {}
        if match_res == 'full':
            heard = self._heard_full(heardM)
            fm = self.fm_full
        else:
            heard = self._heard_blunt(heardM)
            fm = self.fm_blunt
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, heard)
        out = {}
        for w, c in self.word_c.items():
            if fm.get(w) is None:
                continue
            self.sub.set_attr(c, RG.WORD_FEAT_ATTR, as_tuple(fm[w]))
            out[w] = float(self.sub.evaluate(self.err_term,
                                             {"s": self.sign, "w": c}))
        return out

    def collapse(self, errs, admissible, log_prior):
        """Native collapse over the manifold: write lw(w) = -err(w) + log_prior(w)
        for ADMISSIBLE w (others removed: lw = -1e30 so exp(.)~0 — pruned out of
        the manifold), then read the winner / native confidence / native surprise
        in Rust. The PRUNE (admissible) and PRIOR (log_prior) are GRAPH DATA; the
        RESOLUTION is the native collapse Term-tree. Returns (best, conf,
        surprise)."""
        if not errs:
            return None, 0.0, 30.0
        for w in _DIGITS:
            if w in errs and w in admissible:
                lw = -errs[w] + (log_prior.get(w, 0.0) if log_prior else 0.0)
            else:
                lw = -1e30                    # pruned: removed from the manifold
            self.sub.set_attr(self.cands[w], "lw", float(lw))
        root = self.cands["__root__"]
        mx = float(self.sub.evaluate(NC.T_MAX_LW, {"r": root}))
        Z = float(self.sub.evaluate(NC.T_Z, {"r": root, "mx": mx}))
        # winner = admissible candidate of max lw == max(-err+prior)
        adm = [w for w in errs if w in admissible]
        if not adm:
            adm = list(errs)
        best = max(adm, key=lambda w: -errs[w]
                   + (log_prior.get(w, 0.0) if log_prior else 0.0))
        conf = float(self.sub.evaluate(
            NC.T_CONF, {"c": self.cands[best], "mx": mx, "Z": Z}))
        surprise = NC.native_surprise(self.sub, conf)
        return best, conf, surprise


# ==========================================================================
# THE PRUNE — the coarse cochlear cue narrows the admissible set. The BLUNT
# distance ranks candidates; keep the top-K. The coarse cue CANNOT resolve (K>1)
# — it only removes the candidates it is confident enough to rule out. A
# mechanical ranking over the blunt errors (no graph decision; the resolution is
# the native collapse among survivors).
# ==========================================================================

def prune_admissible(blunt_errs, keep_k):
    """Keep the keep_k lowest-blunt-error candidates (the coarse cue's admissible
    set). keep_k >= len -> no prune (the blunt cue admits everything)."""
    if not blunt_errs:
        return set(_DIGITS)
    ranked = sorted(blunt_errs, key=blunt_errs.get)
    return set(ranked[:max(1, keep_k)])


# ==========================================================================
# RECOGNITION ROUTES (isolated digits) — both consume the SAME blunt ear.
# ==========================================================================

def recognise_bottom_up(cu, heardM, log_prior=None):
    """(A) BOTTOM-UP: the blunt estimate RESOLVES. argmin over ALL words of the
    BLUNT-representation DtwTo (the coarse snapshot carries the whole decision).
    Native collapse with match_res='blunt', no prune, optional prior. The cap."""
    be = cu.errs(heardM, 'blunt')
    best, conf, surp = cu.collapse(be, set(_DIGITS), log_prior or {})
    return best, conf, surp


def recognise_top_down(cu, heardM, keep_k, log_prior):
    """(B) TOP-DOWN RECOVERY: the coarse cue PRUNES, the forward model + prior
    RESOLVE. Step 1: the BLUNT cue ranks candidates -> admissible top-K (prune).
    Step 2: the agent inverts its FULL-resolution forward model (DtwTo on the full
    synthesis) among the admitted, collapsed natively WITH the prior. The blunt
    ear narrows; the synthesis + prior resolve."""
    be = cu.errs(heardM, 'blunt')
    admissible = prune_admissible(be, keep_k)
    fe = cu.errs(heardM, 'full')               # full-res synthesis match
    best, conf, surp = cu.collapse(fe, admissible, log_prior)
    return best, conf, surp


# ==========================================================================
# CONTINUOUS — concatenate digit-strings; the top-down route adds the BIGRAM
# transition prior (restoration from context). Boundaries given by the equal-split
# (the continuous venue's degraded bottom-up hypothesis, same as stage6); we score
# per-segment identity under each route. This tests whether the top-down recovery
# compensates for the blunt ear on CONTINUOUS speech too.
# ==========================================================================

def concat(audios, fs):
    parts, bounds = [], [0]
    for a in audios:
        parts.append(a.astype(np.float32))
        bounds.append(sum(len(p) for p in parts))
    return np.concatenate(parts), bounds


def equal_split(x, n):
    if n < 2:
        return []
    return [int(round(len(x) * k / n)) for k in range(1, n)]


def segment(x, bounds):
    edges = [0] + list(bounds) + [len(x)]
    return [x[edges[i]:edges[i + 1]] for i in range(len(edges) - 1)]


def span_matrix(x, fs):
    return traj_to_matrix(utterance_trajectory(x, fs))


def recognise_string_bottom_up(cu, spans, fs, log_uni):
    """Bottom-up per-segment on a continuous string (blunt resolves, unigram
    prior only — no context)."""
    out = []
    for sp in spans:
        M = span_matrix(sp, fs)
        w, _, _ = recognise_bottom_up(cu, M, log_uni)
        out.append(w)
    return out


def recognise_string_top_down(cu, spans, fs, keep_k, log_uni, log_bi):
    """Top-down per-segment with the BIGRAM CONTEXT prior (restoration from
    context). The prior on segment t is log P(w | prev) using the PREVIOUS
    segment's top-down decision — the order-N restoration-from-context the
    directive names, with the blunt cue pruning each step."""
    out = []
    prev = None
    for sp in spans:
        M = span_matrix(sp, fs)
        be = cu.errs(M, 'blunt')
        admissible = prune_admissible(be, keep_k)
        fe = cu.errs(M, 'full')
        prior = log_bi.get(prev, log_uni) if prev is not None else log_uni
        w, _, _ = cu.collapse(fe, admissible, prior)
        out.append(w)
        prev = w
    return out


# ==========================================================================
def acc(preds, truths):
    ok = sum(1 for p, t in zip(preds, truths) if p == t)
    return ok / max(len(truths), 1)


def main():
    t0 = time.time()
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    random.seed(1)
    np.random.seed(1)

    print("=" * 76)
    print("TOP-DOWN RECOVERY vs BOTTOM-UP BLUNT-ESTIMATE — does the synthesis")
    print("COMPENSATE for the BLUNT cochlea? (do-contrast, SAME blunt front end)")
    print("  BLUNT EAR coarsens the cochlea; (A) bottom-up = coarse cue RESOLVES;")
    print("  (B) top-down = coarse cue PRUNES, forward model + prior RESOLVE")
    print("  (native collapse core T8 + owned forward model T10 + surprise; LOSO).")
    print("=" * 76)

    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n_per])
    speakers = sorted(set(it[2] for it in items))
    print(f"\nFSDD: {len(items)} recordings, {len(speakers)} speakers, 10 digits")

    loaded = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        loaded.append((x, fs, digit, sp))
    fs = loaded[0][1]

    print("\n--- extracting per-utterance A1 trajectories (forward-model exemplars) ---")
    utt_traj = []
    for k, (x, _fs, _d, _s) in enumerate(loaded):
        utt_traj.append(utterance_trajectory(x, fs))
        if (k + 1) % 100 == 0:
            print(f"  {k+1}/{len(loaded)}  ({time.time()-t0:.0f}s)", flush=True)
    have = sum(1 for t in utt_traj if t is not None)
    print(f"  extracted {have}/{len(loaded)} clean trajectories")

    by_sp_digit = {}
    for i, (x, _fs, d, s) in enumerate(loaded):
        if utt_traj[i] is not None:
            by_sp_digit.setdefault(s, {}).setdefault(d, []).append(i)

    # one synth substrate (mints the A1Patch layout) shared by the collapse unit.
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    pipe.ingest(sub, loaded[0][0])
    sub.tick(50000)

    # The blunt-ear band counts to sweep across (the cochlear-resolution axis). The
    # native A1 patch count is the sharp ear; we coarsen to a few effective bands.
    native_P = None
    for t in utt_traj:
        if t is not None:
            native_P = traj_to_matrix(t).shape[1]
            break
    print(f"\nnative A1 patch (band) count = {native_P}  (the SHARP ear)")
    blunt_levels = [3, 4, 6]        # the "bad ears" copies (coarse band counts)
    keep_k = 3                       # the coarse cue prunes to top-K admissible

    # ==================================================================
    # ISOLATED DIGITS — LOSO, per blunt level: bottom-up vs top-down.
    # ==================================================================
    print("\n" + "=" * 76)
    print("(I) ISOLATED DIGITS — LOSO, the SAME blunt ear, two routes")
    print("=" * 76)

    iso_results = {}     # n_blunt -> dict of accuracies
    for n_blunt in blunt_levels:
        bu_ok = bu_tot = 0
        td_ok = td_tot = 0
        tdp_ok = 0       # top-down WITHOUT prior (isolate the prune+synth effect)
        for held in speakers:
            fm_full = build_forward_model(loaded, utt_traj, held)
            if any(fm_full[w] is None for w in _DIGITS):
                continue
            fm_blunt = {w: blunt_matrix(M, n_blunt) for w, M in fm_full.items()}
            log_prior = build_prior(loaded, held)
            cu = CollapseUnit(sub, fm_full, fm_blunt, n_blunt)
            te = [i for i, (x, _f, d, s) in enumerate(loaded)
                  if s == held and utt_traj[i] is not None]
            for i in te:
                M = traj_to_matrix(utt_traj[i])
                true_w = _DIGITS[loaded[i][2]]
                # (A) bottom-up: blunt resolves (+ unigram prior, for fairness)
                bw, _, _ = recognise_bottom_up(cu, M, log_prior)
                bu_ok += int(bw == true_w)
                bu_tot += 1
                # (B) top-down: prune + full-res synth + prior resolve
                tw, _, _ = recognise_top_down(cu, M, keep_k, log_prior)
                td_ok += int(tw == true_w)
                # (B') top-down WITHOUT prior — isolate prune+synthesis alone
                twp, _, _ = recognise_top_down(cu, M, keep_k, {})
                tdp_ok += int(twp == true_w)
                td_tot += 1
        bu_acc = bu_ok / max(bu_tot, 1)
        td_acc = td_ok / max(td_tot, 1)
        tdp_acc = tdp_ok / max(td_tot, 1)
        iso_results[n_blunt] = dict(bu=bu_acc, td=td_acc, tdp=tdp_acc,
                                    n=bu_tot)
        print(f"  blunt={n_blunt:>2} bands  (n={bu_tot:>3})  "
              f"BOTTOM-UP {bu_acc:.3f}  |  TOP-DOWN {td_acc:.3f} "
              f"(no-prior {tdp_acc:.3f})  delta {td_acc-bu_acc:+.3f}",
              flush=True)

    # Sharp-ear reference (full resolution, both routes collapse to AxS).
    print("\n  [reference] SHARP ear (full A1, top-down == bottom-up = AxS):")
    sharp_ok = sharp_tot = 0
    for held in speakers:
        fm_full = build_forward_model(loaded, utt_traj, held)
        if any(fm_full[w] is None for w in _DIGITS):
            continue
        cu = CollapseUnit(sub, fm_full, fm_full, native_P)
        log_prior = build_prior(loaded, held)
        te = [i for i, (x, _f, d, s) in enumerate(loaded)
              if s == held and utt_traj[i] is not None]
        for i in te:
            M = traj_to_matrix(utt_traj[i])
            tw, _, _ = recognise_bottom_up(cu, M, log_prior)
            sharp_ok += int(tw == _DIGITS[loaded[i][2]])
            sharp_tot += 1
    sharp_acc = sharp_ok / max(sharp_tot, 1)
    print(f"     sharp-ear AxS acc: {sharp_acc:.3f}  ({sharp_ok}/{sharp_tot})")

    # ==================================================================
    # CONTINUOUS — concatenated digit-strings (LOSO). The top-down route adds the
    # BIGRAM CONTEXT prior; does it compensate for the blunt ear on continuous
    # speech, where bottom-up has NO context to lean on?
    # ==================================================================
    print("\n" + "=" * 76)
    print("(II) CONTINUOUS digit-strings — LOSO, bigram-context top-down")
    print("=" * 76)
    n_blunt = 4
    rng = random.Random(7)

    # build the bigram prior from TRAIN strings (a count over random strings drawn
    # from the train speakers — the agent's learned context model).
    train_strings = []
    for s in speakers:
        digmap = by_sp_digit.get(s, {})
        usable = [d for d in range(10) if digmap.get(d)]
        if len(usable) < 2:
            continue
        for _ in range(20):
            n_dig = rng.randint(2, 5)
            train_strings.append([_DIGITS[rng.choice(usable)] for _ in range(n_dig)])
    log_uni, log_bi = build_bigram_prior(train_strings)

    cont_bu_ok = cont_bu_tot = 0
    cont_td_ok = cont_td_tot = 0
    cont_tdu_ok = 0      # top-down with prune+synth but UNIGRAM only (no context)
    n_strings_per = 4
    for held in speakers:
        fm_full = build_forward_model(loaded, utt_traj, held)
        if any(fm_full[w] is None for w in _DIGITS):
            continue
        fm_blunt = {w: blunt_matrix(M, n_blunt) for w, M in fm_full.items()}
        cu = CollapseUnit(sub, fm_full, fm_blunt, n_blunt)
        digmap = by_sp_digit.get(held, {})
        usable = [d for d in range(10) if digmap.get(d)]
        if len(usable) < 2:
            continue
        for _rep in range(n_strings_per):
            for n_dig in (2, 3, 4):
                seq = [rng.choice(usable) for _ in range(n_dig)]
                audios = [loaded[rng.choice(digmap[d])][0] for d in seq]
                truth = [_DIGITS[d] for d in seq]
                wav, _ = concat(audios, fs)
                spans = segment(wav, equal_split(wav, n_dig))
                if len(spans) != n_dig:
                    continue
                bu = recognise_string_bottom_up(cu, spans, fs, log_uni)
                td = recognise_string_top_down(cu, spans, fs, keep_k,
                                               log_uni, log_bi)
                # control: top-down prune+synth but NO bigram context (flat bigram
                # = unigram) — isolates how much of the gain is the CONTEXT prior
                # vs the prune+synthesis alone.
                tdu = recognise_string_top_down(cu, spans, fs, keep_k,
                                                log_uni, {})
                cont_bu_ok += sum(1 for p, t in zip(bu, truth) if p == t)
                cont_td_ok += sum(1 for p, t in zip(td, truth) if p == t)
                cont_tdu_ok += sum(1 for p, t in zip(tdu, truth) if p == t)
                cont_bu_tot += len(truth)
                cont_td_tot += len(truth)
        print(f"  speaker {held} done  ({time.time()-t0:.0f}s)", flush=True)

    cont_bu = cont_bu_ok / max(cont_bu_tot, 1)
    cont_td = cont_td_ok / max(cont_td_tot, 1)
    cont_tdu = cont_tdu_ok / max(cont_td_tot, 1)
    print(f"\n  continuous (blunt={n_blunt}, {cont_bu_tot} segments):")
    print(f"    BOTTOM-UP (blunt resolves, unigram)      : {cont_bu:.3f}")
    print(f"    TOP-DOWN (prune + synth, NO context)     : {cont_tdu:.3f}  "
          f"(delta {cont_tdu-cont_bu:+.3f})")
    print(f"    TOP-DOWN (prune + synth + bigram context): {cont_td:.3f}  "
          f"(delta {cont_td-cont_bu:+.3f})")

    # ==================================================================
    # VERDICT
    # ==================================================================
    print("\n" + "=" * 76)
    print("=== VERDICT — does TOP-DOWN recovery COMPENSATE for the BLUNT ear? ===")
    print("=" * 76)
    print(f"  isolated digits (LOSO), per blunt-ear level:")
    print(f"  {'blunt_bands':>11} {'bottom_up':>10} {'top_down':>9} "
          f"{'td_no_prior':>12} {'delta':>8}")
    iso_gain = []
    for nb in blunt_levels:
        r = iso_results[nb]
        d = r['td'] - r['bu']
        iso_gain.append(d)
        print(f"  {nb:>11} {r['bu']:>10.3f} {r['td']:>9.3f} "
              f"{r['tdp']:>12.3f} {d:>+8.3f}")
    mean_gain = float(np.mean(iso_gain))
    print(f"  mean isolated-digit gain (top-down - bottom-up): {mean_gain:+.3f}")
    print(f"  sharp-ear reference AxS acc                     : {sharp_acc:.3f}")
    print(f"  continuous-speech gain (top-down - bottom-up)   : "
          f"{cont_td-cont_bu:+.3f}")
    print(f"    of which prune+synth (no context)             : "
          f"{cont_tdu-cont_bu:+.3f}")
    print(f"    of which bigram CONTEXT prior adds            : "
          f"{cont_td-cont_tdu:+.3f}")

    compensates = mean_gain > 0.01 or (cont_td - cont_bu) > 0.01
    # does top-down on the BLUNT ear RECOVER toward the sharp-ear ceiling?
    best_blunt_td = max(iso_results[nb]['td'] for nb in blunt_levels)
    best_blunt_bu = max(iso_results[nb]['bu'] for nb in blunt_levels)
    recovered_frac = ((best_blunt_td - best_blunt_bu)
                      / max(sharp_acc - best_blunt_bu, 1e-9))
    print("  " + "-" * 60)
    print(f"  >>> TOP-DOWN COMPENSATES for the blunt ear            : {compensates}")
    print(f"      (best blunt bottom-up {best_blunt_bu:.3f} -> best blunt "
          f"top-down {best_blunt_td:.3f}; recovers "
          f"{100*recovered_frac:.0f}% of the gap to sharp {sharp_acc:.3f})")
    print("=" * 76)
    print(f"\nelapsed {time.time()-t0:.0f}s")
    print("===MARKER_TOPDOWN_RECOVERY_COMPLETE===")


if __name__ == "__main__":
    main()
