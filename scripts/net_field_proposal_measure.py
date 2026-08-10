"""NET AS THE PER-CELL FIELD PROPOSAL, UNDER A REFUSABLE VERDICT — block 133000.

Pre-registration: VISION_NET_FIELD_PROPOSAL_PREREG.md (committed BEFORE this ran).

The TARGET is the RetinaCell STATE field's per-cell update (the "wave relaxation",
51% of the tick per 132000): predict S_{t+1} from S_t. The field is a radius-1
deterministic CA (wv_propagate/refract/recover) + exogenous random ignition. A small
conv net PROPOSES the update; the substrate REFUSES on the residual (the held CA
rule, applied as a cheap reconstruction); exact recompute runs where surprise is high.

THREE FACETS (all measured):
  1. PREDICTABILITY  — per-cell accuracy, residual concentration, net-vs-exact cost.
  2. COMPUTE-∝-SURPRISE — sound gate (byte-identical) vs conf gate (bounded); speedup.
  3. REFUSAL — substrate residual (comparison) vs net-confidence (selection), paired.

The net is a MEASURED host-side proposal mechanism (torch), admissible like 130000's
CNN baselines. The EXACT engine path is UNCHANGED and default (§9). NO agent logic.

USAGE
  PYTHONPATH=runners/dsl/python:. python scripts/net_field_proposal_measure.py \
      --out results/net_field_proposal.json
"""
from __future__ import annotations
import argparse, gc, json, os, statistics, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: pin THIS tree's engine before any substrate_rs import.
from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
import domains.seed_registry  # noqa: F401,E402
from domains.wave_world import WaveWorld  # noqa: E402

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

# ---- state codes ----
REST, ACT, REC, REF = 0, 1, 2, 3
NAME = {"rested": REST, "active": ACT, "recruited": REC, "refractory": REF}
REFRACTORY_STEPS = 4.0
IGNITE_EVERY = 5

# ---- fixed config (prereg §4/§5) ----
DATA_GRID = 32
WARMUP_STEPS = 40
STEPS_PER_WORLD = 240
TRAIN_WORLDS = [133000, 133001, 133002, 133003]
TEST_WORLDS = list(range(133100, 133110))     # 10 confirmatory, never trained/tuned
NET_SEED = 133500
BOOT_RNG = 133600
EPOCHS = 60
GRIDS_TIME = [16, 24, 32, 48, 64, 96, 128, 192, 256]
TRIALS_TIME = {16: 9, 24: 9, 32: 9, 48: 7, 64: 7, 96: 7, 128: 7, 192: 7, 256: 7}
TIME_TICKS = 30       # timed iterations per trial
TIME_WARM = 5
RT_BUDGET_MS = 1000.0 / 23.976


def _loadavg():
    try:
        return list(os.getloadavg())
    except OSError:
        return None


def _governor():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def _bootstrap_ci(xs, n=10000, alpha=0.05, seed=133000):
    xs = np.asarray(xs, float)
    if len(xs) < 2:
        return (float(xs[0]), float(xs[0])) if len(xs) else (0.0, 0.0)
    rng = np.random.default_rng(seed)
    bs = [float(np.median(rng.choice(xs, len(xs), replace=True))) for _ in range(n)]
    return float(np.percentile(bs, 100 * alpha / 2)), float(np.percentile(bs, 100 * (1 - alpha / 2)))


# ---------------------------------------------------------------------------
# ENGINE world + exact numpy CA (verified byte-identical, scratch control)
# ---------------------------------------------------------------------------
def boot(g, seed):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    w = WaveWorld(s, h=g, w=g, seed=seed, fovea_radius=0)
    return s, w


def read_fields(s, w):
    ids = w._cell_ids
    st = s.get_attr_many(ids, "state")
    aa = s.get_attr_many(ids, "activated_at")
    fa = s.get_attr_many(ids, "fired_at")
    S = np.zeros((w.h, w.w), np.int8)
    A = np.full((w.h, w.w), -999.0)
    F = np.full((w.h, w.w), -999.0)
    for (r, c), stt, a, f in zip(w._cell_rc, st, aa, fa):
        S[r, c] = NAME[stt]; A[r, c] = float(a); F[r, c] = float(f)
    return S, A, F


def ca_tick(S, A, F, step):
    """Exact ONE-tick wave relaxation on the pre-tick field. Verified byte-identical
    to s.tick() (scripts/_scratch_ca_verify.py: 9 configs x 60 steps)."""
    S2 = S.copy(); F2 = F.copy()
    fresh_active = (S == ACT) & (A == step)
    old_active = (S == ACT) & (A < step)
    recover = (S == REF) & ((step - F) >= REFRACTORY_STEPS)
    S2[old_active] = REF; F2[old_active] = step
    S2[recover] = REST
    rested_now = (S2 == REST)
    nf = np.zeros_like(fresh_active)
    nf[1:, :] |= fresh_active[:-1, :]; nf[:-1, :] |= fresh_active[1:, :]
    nf[:, 1:] |= fresh_active[:, :-1]; nf[:, :-1] |= fresh_active[:, 1:]
    S2[rested_now & nf] = REC
    return S2, A.copy(), F2


def commit_ignite(S, A, F, step, ignite_rc):
    """Adapter's exogenous part: recruited->active(step); ignited rested->active(step)."""
    S2 = S.copy(); A2 = A.copy()
    commit = (S2 == REC)
    S2[commit] = ACT; A2[commit] = step
    for (r, c) in ignite_rc:
        if S2[r, c] == REST:
            S2[r, c] = ACT; A2[r, c] = step
    return S2, A2, F.copy()


# ---------------------------------------------------------------------------
# data generation from the ENGINE (real substrate ground truth)
# ---------------------------------------------------------------------------
def record_world(g, seed, steps, warmup):
    """Run the engine committed wave schedule; capture per step the POST-tick field
    (S,A,F) and the ignition (r,c) list. Returns list of dicts with consecutive
    fields so target-B pairs (S_t -> S_{t+1}) and the deterministic reconstruction
    can both be formed. Ground truth is the ENGINE."""
    s, w = boot(g, seed)
    ign = {}
    o_ign = w.ignite
    idmap = {nid: rc for rc, nid in zip(w._cell_rc, w._cell_ids)}

    def wrapped(k, _o=o_ign, _st=ign, _w=w, _m=idmap):
        out = _o(k)
        step = int(float(_w.s.node(_w.retina)["attrs"]["step"]))
        _st[step] = [_m[n] for n in out]
        return out
    w.ignite = wrapped

    frames = None
    seq = []
    for i in range(warmup + steps):
        k = 1 if (i % IGNITE_EVERY == 0) else 0
        step_next = int(float(s.node(w.retina)["attrs"]["step"]) + 1)
        w.step(ignite_k=k, frame=frames)
        S, A, F = read_fields(s, w)
        if i >= warmup:
            seq.append({"step": step_next, "S": S, "A": A, "F": F,
                        "ignite": ign.get(step_next, [])})
    return seq


def encode(S, A, F, step):
    """6-channel input: state one-hot(4) + clipped(step-A)/8 + clipped(step-F)/8."""
    H, Wd = S.shape
    x = np.zeros((6, H, Wd), np.float32)
    for k in range(4):
        x[k] = (S == k)
    x[4] = np.clip(step - A, 0, 8) / 8.0
    x[5] = np.clip(step - F, 0, 8) / 8.0
    return x


def make_pairs(seq):
    """Target-B: predict S_{t+1} (post-tick) from encode(S_t). Also return the
    ignition mask that produced t+1 (the exogenous surprise) for split analysis."""
    X, Y, IGN = [], [], []
    for a, b in zip(seq[:-1], seq[1:]):
        X.append(encode(a["S"], a["A"], a["F"], a["step"]))
        Y.append(b["S"].astype(np.int64))
        m = np.zeros(a["S"].shape, bool)
        for (r, c) in b["ignite"]:
            m[r, c] = True
        # neighbour-ignition also perturbs (a rested cell recruited by an ignited
        # neighbour) — mark the 4-neighbourhood of ignition too as exogenous-touched
        nb = m.copy()
        nb[1:, :] |= m[:-1, :]; nb[:-1, :] |= m[1:, :]
        nb[:, 1:] |= m[:, :-1]; nb[:, :-1] |= m[:, 1:]
        IGN.append(nb)
    return X, Y, IGN


def deterministic_next(a):
    """The substrate's HELD RULE applied as a reconstruction: commit + tick with NO
    ignition — the lawful next-state the substrate can cheaply reconstruct. This is
    the COMPARISON mechanism (H3) and the sound-gate exact kernel."""
    Sp, Ap, Fp = commit_ignite(a["S"], a["A"], a["F"], a["step"] + 1, [])
    S2, A2, F2 = ca_tick(Sp, Ap, Fp, a["step"] + 1)
    return S2


# ---------------------------------------------------------------------------
# the SMALL net
# ---------------------------------------------------------------------------
class FieldNet(nn.Module):
    def __init__(self, ch=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(6, ch, 3, padding=1), nn.ReLU(),
            nn.Conv2d(ch, ch, 3, padding=1), nn.ReLU(),
            nn.Conv2d(ch, 4, 1))

    def forward(self, x):
        return self.net(x)


def n_params(m):
    return sum(p.numel() for p in m.parameters())


def train_net(train_pairs, epochs, seed):
    torch.manual_seed(seed)
    net = FieldNet()
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    lossf = nn.CrossEntropyLoss()
    X = torch.from_numpy(np.stack([p[0] for p in train_pairs]))
    Y = torch.from_numpy(np.stack([p[1] for p in train_pairs]))
    n = X.shape[0]
    t0 = time.perf_counter()
    net.train()
    bs = 32
    for ep in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            out = net(X[idx])
            loss = lossf(out, Y[idx])
            loss.backward()
            opt.step()
    train_s = time.perf_counter() - t0
    net.eval()
    return net, train_s, float(loss.item())


# ---------------------------------------------------------------------------
# FACET 1: predictability on held-out worlds
# ---------------------------------------------------------------------------
@torch.no_grad()
def eval_predictability(net, test_seqs):
    tot = det_tot = ign_tot = 0
    correct = det_correct = ign_correct = 0
    err_frac_per_step = []
    err_ign_frac = []          # of the errors, fraction that are ignition-touched
    changed_frac = []          # fraction of cells that actually change (the front)
    for seq in test_seqs:
        X, Y, IGN = make_pairs(seq)
        for x, y, ign, a in zip(X, Y, IGN, seq[:-1]):
            xt = torch.from_numpy(x).unsqueeze(0)
            pred = net(xt).argmax(1).squeeze(0).numpy()
            err = (pred != y)
            det = ~ign
            tot += y.size; correct += int((~err).sum())
            det_tot += int(det.sum()); det_correct += int((~err & det).sum())
            ign_tot += int(ign.sum()); ign_correct += int((~err & ign).sum())
            err_frac_per_step.append(err.mean())
            ne = int(err.sum())
            err_ign_frac.append(float((err & ign).sum()) / ne if ne else 0.0)
            changed_frac.append(float((y != a["S"]).mean()))
    return {
        "cell_accuracy": correct / tot,
        "det_accuracy": det_correct / max(det_tot, 1),
        "ignition_accuracy": ign_correct / max(ign_tot, 1),
        "err_frac_median": float(np.median(err_frac_per_step)),
        "err_frac_mean": float(np.mean(err_frac_per_step)),
        "err_frac_p95": float(np.percentile(err_frac_per_step, 95)),
        "changed_frac_median": float(np.median(changed_frac)),
        "of_errors_ignition_touched_median": float(np.median(err_ign_frac)),
        "n_cells_scored": tot, "det_cells": det_tot, "ignition_cells": ign_tot,
    }


# ---------------------------------------------------------------------------
# FACET 3: refusal — comparison (substrate residual) vs selection (net confidence)
# ---------------------------------------------------------------------------
def _auroc(score, label):
    """AUROC via Mann-Whitney; label bool (1=positive=net error)."""
    label = np.asarray(label, bool)
    score = np.asarray(score, float)
    npos = int(label.sum()); nneg = int((~label).sum())
    if npos == 0 or nneg == 0:
        return np.nan
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score), float)
    ranks[order] = np.arange(1, len(score) + 1)
    # average ties
    s_sorted = score[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    sum_pos = ranks[label].sum()
    return (sum_pos - npos * (npos + 1) / 2.0) / (npos * nneg)


@torch.no_grad()
def refusal_test(net, test_seqs, seed=133600, n_boot=2000):
    """Per cell: label = net error. Two signals:
      selection  = net-confidence surprise = 1 - softmax_max (SELECTION)
      comparison = |net_pred != deterministic_reconstruction| soft = KL-ish; we use
                   the substrate residual = 1 if net_argmax != S_det else graded by
                   net prob mass off the lawful class (a COMPARISON to the held rule).
    Reported for ALL / DETERMINISTIC-only / IGNITION-only error subsets."""
    conf_all, comp_all, lab_all, ign_all = [], [], [], []
    for seq in test_seqs:
        X, Y, IGN = make_pairs(seq)
        for x, y, ign, a in zip(X, Y, IGN, seq[:-1]):
            xt = torch.from_numpy(x).unsqueeze(0)
            logit = net(xt).squeeze(0)
            prob = torch.softmax(logit, 0).numpy()      # (4,H,W)
            pred = prob.argmax(0)
            conf_surprise = 1.0 - prob.max(0)           # SELECTION signal
            sdet = deterministic_next(a)                # substrate reconstruction
            # COMPARISON signal: substrate residual = net's probability NOT on the
            # lawful (reconstructed) class — high where the proposal diverges from
            # the held rule. Cheap (sdet is commit+tick, the substrate's own op).
            lawful_prob = np.take_along_axis(prob, sdet[None].astype(np.int64), 0)[0]
            comp_surprise = 1.0 - lawful_prob
            err = (pred != y)
            conf_all.append(conf_surprise.ravel())
            comp_all.append(comp_surprise.ravel())
            lab_all.append(err.ravel())
            ign_all.append(ign.ravel())
    conf = np.concatenate(conf_all); comp = np.concatenate(comp_all)
    lab = np.concatenate(lab_all); ign = np.concatenate(ign_all)

    NEG_CAP = 40000    # bootstrap subsample cap on NEGATIVES (keep ALL positives)

    def paired(mask):
        idx = np.where(mask if mask is not None else np.ones_like(lab, bool))[0]
        L = lab[idx]
        if L.sum() == 0 or (~L).sum() == 0:
            return {"auroc_comparison": np.nan, "auroc_confidence": np.nan,
                    "paired_diff": np.nan, "ci": [np.nan, np.nan],
                    "sep": "undef", "n_pos": int(L.sum()), "n": int(len(idx))}
        # POINT estimate on FULL data (one argsort each -- cheap and exact)
        a_comp = _auroc(comp[idx], L); a_conf = _auroc(conf[idx], L)
        # BOOTSTRAP on a stratified subsample: all positives + capped negatives, so
        # each resampled AUROC is O(NEG_CAP log NEG_CAP) not O(2.4M). Adds a little
        # conservatism (fewer negatives) -- reported honestly.
        pos_i = idx[L]; neg_i = idx[~L]
        rng = np.random.default_rng(seed)
        if len(neg_i) > NEG_CAP:
            neg_i = rng.choice(neg_i, NEG_CAP, replace=False)
        sub = np.concatenate([pos_i, neg_i])
        cs = comp[sub]; cf = conf[sub]; ls = lab[sub]
        m = len(sub)
        diffs = []
        for _ in range(n_boot):
            r = rng.integers(0, m, m)
            Lr = ls[r]
            if Lr.sum() == 0 or (~Lr).sum() == 0:
                continue
            diffs.append(_auroc(cs[r], Lr) - _auroc(cf[r], Lr))
        lo, hi = (float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))) if diffs else (np.nan, np.nan)
        return {"auroc_comparison": float(a_comp), "auroc_confidence": float(a_conf),
                "paired_diff": float(a_comp - a_conf), "ci": [lo, hi],
                "sep": "SEP+" if lo > 0 else ("SEP-" if hi < 0 else "ns"),
                "n_pos": int(L.sum()), "n": int(len(idx)),
                "n_boot_subsample": int(m)}
    # ignition-error detectability against the CORRECT background (exclude det errs):
    # can EITHER signal flag the exogenous ignition, or is it invisible to both?
    correct = ~lab
    ign_err = lab & ign
    det_err = lab & ~ign
    ign_vs_correct_mask = ign_err | correct
    lab_ivc = ign_err[ign_vs_correct_mask]
    def _sub_auroc(sig):
        return float(_auroc(sig[ign_vs_correct_mask], lab_ivc))
    return {"all_errors": paired(None),
            "deterministic_errors": paired(~ign),
            "ignition_errors_within": paired(ign),
            "ignition_vs_correct": {
                "auroc_comparison": _sub_auroc(comp),
                "auroc_confidence": _sub_auroc(conf),
                "n_ign_err": int(ign_err.sum()), "n_correct": int(correct.sum())},
            "counts": {"n_cells": int(len(lab)), "n_err": int(lab.sum()),
                       "n_det_err": int(det_err.sum()), "n_ign_err": int(ign_err.sum())}}


# ---------------------------------------------------------------------------
# FACET 2: compute-∝-surprise — gates
# ---------------------------------------------------------------------------
@torch.no_grad()
def gate_analysis(net, test_seqs):
    """SOUND gate: the change-possible band (cells that CAN change under the CA:
    active/recruited/refractory, or a rested cell with an active/recruited neighbour)
    — recompute exact there, trust net elsewhere. Report band fraction + whether it
    catches EVERY net error (soundness) on the deterministic part.
    CONF gate: recompute exact on the top-f% least-confident cells; report residual
    error + miss rate at f in {0,1,2,5,10}. Thresholds from TRAIN residual (§13)."""
    band_fracs, sound_missed_det, sound_catches, sound_full_resid = [], [], [], []
    conf_curves = {f: {"resid": [], "miss": []} for f in (0.0, 1.0, 2.0, 5.0, 10.0)}
    for seq in test_seqs:
        X, Y, IGN = make_pairs(seq)
        for x, y, ign_mask, a in zip(X, Y, IGN, seq[:-1]):
            xt = torch.from_numpy(x).unsqueeze(0)
            prob = torch.softmax(net(xt).squeeze(0), 0).numpy()
            pred = prob.argmax(0)
            S = a["S"]; step = a["step"]
            # EXACT deterministic-changer band under the CA (a cheap local scan of
            # S + timers): active(->refr), recruited(->active), refractory ABOUT to
            # recover, and rested adjacent to a RECRUITED cell (which commits to
            # fresh-active and recruits it). NOT rested-adjacent-to-active: an active
            # cell refracts next step, it does not propagate. Ignition (rested->active
            # at a random cell + its induced recruits) is EXOGENOUS -> outside this
            # field-derived band by construction -> the irreducible surprise.
            active = (S == ACT); rec = (S == REC)
            refr_recover = (S == REF) & ((step - a["F"]) >= REFRACTORY_STEPS - 1)
            nbr_rec = np.zeros_like(rec)
            nbr_rec[1:, :] |= rec[:-1, :]; nbr_rec[:-1, :] |= rec[1:, :]
            nbr_rec[:, 1:] |= rec[:, :-1]; nbr_rec[:, :-1] |= rec[:, 1:]
            band = active | rec | refr_recover | ((S == REST) & nbr_rec)
            band_fracs.append(float(band.mean()))
            # SOUND gate: exact-recompute on the band, trust net elsewhere. Ignition
            # (exogenous) lands OUTSIDE the band by construction -> NOT catchable by a
            # field-only gate; report soundness on the DETERMINISTIC part (~ign_mask).
            err = (pred != y)
            det_err = err & (~ign_mask)
            missed_det = det_err & (~band)
            sound_catches.append(float(missed_det.sum() == 0))
            sound_missed_det.append(float(missed_det.mean()))
            # final field of the sound gate: exact (substrate reconstruction) on band,
            # net elsewhere. Residual vs truth = the exogenous ignition the field-only
            # gate cannot see (its irreducible floor).
            final_sound = np.where(band, deterministic_next(a), pred)
            sound_full_resid.append(float((final_sound != y).mean()))
            # conf gate
            sdet = deterministic_next(a)     # substrate reconstruction (once/pair)
            conf_surprise = 1.0 - prob.max(0)
            flat = conf_surprise.ravel()
            for f in conf_curves:
                if f == 0.0:
                    flagged = np.zeros_like(flat, bool)
                else:
                    k = max(1, int(len(flat) * f / 100.0))
                    thr = np.partition(flat, -k)[-k]
                    flagged = flat >= thr
                flagged = flagged.reshape(S.shape)
                # exact recompute on flagged: use the substrate reconstruction sdet
                # (the lawful next), net elsewhere; compare to truth y
                final = np.where(flagged, sdet, pred)
                resid = (final != y)
                miss = (pred != y) & (~flagged)
                conf_curves[f]["resid"].append(float(resid.mean()))
                conf_curves[f]["miss"].append(float(miss.mean()))
    out = {
        "band_frac_median": float(np.median(band_fracs)),
        "sound_gate_catches_all_deterministic_frac": float(np.mean(sound_catches)),
        "sound_gate_missed_det_frac_median": float(np.median(sound_missed_det)),
        "sound_gate_full_residual_median": float(np.median(sound_full_resid)),
        "conf_gate": {str(f): {"resid_median": float(np.median(v["resid"])),
                               "miss_median": float(np.median(v["miss"]))}
                      for f, v in conf_curves.items()},
    }
    return out


# ---------------------------------------------------------------------------
# FACET 2: TIMING — engine tick vs numpy-exact vs net forward (machine ALONE)
# ---------------------------------------------------------------------------
def _median_ci(xs):
    med = float(statistics.median(xs))
    lo, hi = _bootstrap_ci(xs)
    return med, lo, hi


def time_engine(g, trials, ticks, warm):
    """ms per s.tick() (the wave relaxation) on a live committed-schedule world."""
    out = []
    for t in range(trials):
        gc.collect()
        s, w = boot(g, seed=BOOT_RNG + t)
        for i in range(warm):
            w.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0, frame=None)
        # time s.tick() in isolation, accumulate over `ticks` committed steps
        acc = 0.0; n = 0
        for i in range(ticks):
            st = float(s.node(w.retina)["attrs"]["step"]) + 1.0
            s.set_attr(w.retina, "step", st)
            states = s.get_attr_many(w._cell_ids, "state")
            recruited = [nid for nid, stt in zip(w._cell_ids, states) if stt == "recruited"]
            if recruited:
                s.set_attr_many(recruited, "state", "active")
                s.set_attr_many(recruited, "activated_at", st)
            if i % IGNITE_EVERY == 0:
                w.ignite(1)
            t0 = time.perf_counter()
            s.tick(200_000)
            acc += time.perf_counter() - t0; n += 1
        out.append(acc / n * 1000.0)
        del s, w
    return _median_ci(out)


def _repr_field(g):
    s, w = boot(g, seed=BOOT_RNG)
    for i in range(30):
        w.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0, frame=None)
    S, A, F = read_fields(s, w)
    del s, w
    return S, A, F


def time_numpy(g, trials, ticks, warm):
    """ms per numpy full-step (commit+ignite+ca_tick) — the byte-identical control."""
    S, A, F = _repr_field(g)
    rng = np.random.default_rng(BOOT_RNG)
    out = []
    for t in range(trials):
        Sx, Ax, Fx = S.copy(), A.copy(), F.copy()
        step = 100.0
        for _ in range(warm):
            ig = [(int(rng.integers(0, g)), int(rng.integers(0, g)))]
            Sp, Ap, Fp = commit_ignite(Sx, Ax, Fx, step, ig)
            Sx, Ax, Fx = ca_tick(Sp, Ap, Fp, step); step += 1
        acc = 0.0
        for _ in range(ticks):
            ig = [(int(rng.integers(0, g)), int(rng.integers(0, g)))]
            t0 = time.perf_counter()
            Sp, Ap, Fp = commit_ignite(Sx, Ax, Fx, step, ig)
            Sx, Ax, Fx = ca_tick(Sp, Ap, Fp, step)
            acc += time.perf_counter() - t0
            step += 1
        out.append(acc / ticks * 1000.0)
    return _median_ci(out)


def time_net(net, g, trials, ticks, warm):
    """ms per net proposal: encode(field) + conv forward + argmax->state. Encode is
    included because the net needs the field re-encoded each step (fair vs the
    exact arms' produce-next-field cost)."""
    S, A, F = _repr_field(g)
    out = []
    with torch.no_grad():
        for t in range(trials):
            xx = torch.from_numpy(encode(S, A, F, 100.0)).unsqueeze(0)
            for _ in range(warm):
                net(xx)
            acc = 0.0
            for _ in range(ticks):
                t0 = time.perf_counter()
                x = torch.from_numpy(encode(S, A, F, 100.0)).unsqueeze(0)
                _ = net(x).argmax(1).numpy().astype(np.int8)
                acc += time.perf_counter() - t0
            out.append(acc / ticks * 1000.0)
    return _median_ci(out)


def _fit_exponent(cells, ms):
    lc = np.log(np.asarray(cells, float)); lm = np.log(np.asarray(ms, float))
    A = np.vstack([lc, np.ones_like(lc)]).T
    coef, *_ = np.linalg.lstsq(A, lm, rcond=None)
    pred = A @ coef
    ss_res = ((lm - pred) ** 2).sum(); ss_tot = ((lm - lm.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {"exponent": float(coef[0]), "intercept": float(coef[1]), "r2": float(r2)}


def timing_sweep(net, grids):
    rows = []
    for g in grids:
        T = TRIALS_TIME[g]
        em, elo, ehi = time_engine(g, T, TIME_TICKS, TIME_WARM)
        nm, nlo, nhi = time_numpy(g, T, TIME_TICKS, TIME_WARM)
        tm, tlo, thi = time_net(net, g, T, TIME_TICKS, TIME_WARM)
        cells = g * g
        row = {"grid": g, "cells": cells,
               "engine_ms": em, "engine_ci": [elo, ehi], "engine_us_cell": em * 1000 / cells,
               "numpy_ms": nm, "numpy_ci": [nlo, nhi], "numpy_us_cell": nm * 1000 / cells,
               "net_ms": tm, "net_ci": [tlo, thi], "net_us_cell": tm * 1000 / cells,
               "speedup_net_vs_engine": em / tm, "speedup_numpy_vs_engine": em / nm,
               "net_vs_numpy": nm / tm,
               "engine_ci_frac": (ehi - elo) / 2 / em,
               "numpy_ci_frac": (nhi - nlo) / 2 / nm,
               "net_ci_frac": (thi - tlo) / 2 / tm}
        rows.append(row)
        print(f"  g={g:3d} cells={cells:6d} T={T} | engine {em:9.4f}ms ({100*(ehi-elo)/2/em:+.2f}%) "
              f"numpy {nm:8.5f}ms net {tm:8.5f}ms | net/engine x{em/tm:8.1f} "
              f"numpy/engine x{em/nm:8.1f} net/numpy x{nm/tm:.2f}", flush=True)
    return rows


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()

    torch.set_num_threads(a.threads)
    os.environ.setdefault("OMP_NUM_THREADS", str(a.threads))

    prov = provenance_line()
    load0 = _loadavg()
    print(prov, flush=True)
    print(f"loadavg start {load0} governor {_governor()} torch_threads {torch.get_num_threads()}", flush=True)

    grids = [16, 24, 32] if a.quick else GRIDS_TIME
    tw = TRAIN_WORLDS[:2] if a.quick else TRAIN_WORLDS
    testw = TEST_WORLDS[:2] if a.quick else TEST_WORLDS
    spw = 60 if a.quick else STEPS_PER_WORLD
    epochs = 8 if a.quick else EPOCHS

    res = {"provenance": prov, "provenance_stamp": provenance_stamp(),
           "loadavg_start": load0, "governor": _governor(),
           "torch_threads": torch.get_num_threads(),
           "config": {"data_grid": DATA_GRID, "train_worlds": tw, "test_worlds": testw,
                      "steps_per_world": spw, "epochs": epochs, "net_seed": NET_SEED,
                      "grids_time": grids, "ignite_every": IGNITE_EVERY},
           "block_seeds_drawn": {"train_worlds": tw, "test_worlds": testw,
                                 "net_seed": NET_SEED, "boot_rng": BOOT_RNG}}

    # ---- data ----
    print("== generating engine data (train + held-out) ==", flush=True)
    train_seqs = [record_world(DATA_GRID, s, spw, WARMUP_STEPS) for s in tw]
    test_seqs = [record_world(DATA_GRID, s, spw, WARMUP_STEPS) for s in testw]
    train_pairs = []
    for seq in train_seqs:
        X, Y, _ = make_pairs(seq)
        train_pairs += list(zip(X, Y))
    print(f"  train pairs {len(train_pairs)}  test worlds {len(test_seqs)}", flush=True)

    # ---- train ----
    print("== training small net ==", flush=True)
    net, train_s, final_loss = train_net(train_pairs, epochs, NET_SEED)
    res["net"] = {"params": n_params(net), "train_seconds": train_s,
                  "final_train_loss": final_loss, "architecture": "Conv6-16-16-4 (3x3,3x3,1x1), RF 5x5"}
    print(f"  params {n_params(net)}  train {train_s:.1f}s  loss {final_loss:.4f}", flush=True)

    # ---- FACET 1 ----
    print("== FACET 1: predictability ==", flush=True)
    res["predictability"] = eval_predictability(net, test_seqs)
    p = res["predictability"]
    print(f"  cell_acc {p['cell_accuracy']:.5f}  det_acc {p['det_accuracy']:.5f}  "
          f"ign_acc {p['ignition_accuracy']:.5f}  err_frac_med {p['err_frac_median']:.5f}  "
          f"changed_frac_med {p['changed_frac_median']:.5f}", flush=True)

    # ---- FACET 3 ----
    print("== FACET 3: refusal (comparison vs confidence) ==", flush=True)
    res["refusal"] = refusal_test(net, test_seqs)
    for k in ("all_errors", "deterministic_errors", "ignition_errors_within"):
        v = res["refusal"][k]
        print(f"  {k:24s} comp {v['auroc_comparison']} conf {v['auroc_confidence']} "
              f"diff {v['paired_diff']} {v.get('sep','')} n_pos {v['n_pos']}", flush=True)
    ivc = res["refusal"]["ignition_vs_correct"]
    print(f"  ignition_vs_correct       comp {ivc['auroc_comparison']:.4f} conf {ivc['auroc_confidence']:.4f} "
          f"(n_ign_err {ivc['n_ign_err']})", flush=True)

    # ---- FACET 2 gates ----
    print("== FACET 2: gates ==", flush=True)
    res["gates"] = gate_analysis(net, test_seqs)
    gg = res["gates"]
    print(f"  band_frac_med {gg['band_frac_median']:.4f}  sound_catches_all_det {gg['sound_gate_catches_all_deterministic_frac']:.3f}  "
          f"sound_missed_det_med {gg['sound_gate_missed_det_frac_median']:.5f}  sound_full_resid_med {gg['sound_gate_full_residual_median']:.5f}", flush=True)
    for f, v in gg["conf_gate"].items():
        print(f"    conf f={f:>5}%  resid_med {v['resid_median']:.5f}  miss_med {v['miss_median']:.5f}", flush=True)

    # ---- FACET 2 timing (ALONE) ----
    print("== FACET 2: timing sweep (machine ALONE) ==", flush=True)
    rows = timing_sweep(net, grids)
    res["timing"] = rows
    cells = [r["cells"] for r in rows]
    res["fit_engine"] = _fit_exponent(cells, [r["engine_ms"] for r in rows])
    res["fit_numpy"] = _fit_exponent(cells, [r["numpy_ms"] for r in rows])
    res["fit_net"] = _fit_exponent(cells, [r["net_ms"] for r in rows])

    res["loadavg_end"] = _loadavg()
    res["provenance_after"] = provenance_line()
    stamp2 = provenance_stamp()
    res["source_match_after"] = stamp2.get("source_match")
    assert stamp2.get("source_match") in ("own", "shared"), stamp2

    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2, default=str)
    print("wrote", a.out, flush=True)
    print(f"loadavg end {res['loadavg_end']}  source_match_after {res['source_match_after']}", flush=True)


if __name__ == "__main__":
    main()
