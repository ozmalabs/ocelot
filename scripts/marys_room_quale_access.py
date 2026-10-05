"""EXPLORATORY, POST-HOC (not preregistered): what can Mary learn about her own
eye when cognition has QUALE-LEVEL access only?

Correction to scripts/marys_room_model_vs_know.py, which let Mary read her eye's
(RG, BY) values as numbers. In the qualia-space account (papers/formal/01f,
def. qualia-space / aperture) cognition receives the aperture-quantised
signature, not the coordinates. Mary can therefore report only:

  SIGN    whether a light looks reddish / greenish, bluish / yellowish
          (probit on the opponent sign, internal noise SIGMA_INT);
  NULL    the setting of a PUBLIC knob (wavelength) at which a light looks
          neither reddish nor greenish, or neither bluish nor yellowish;
  MATCH   the PUBLIC knob settings (mixture ratio, intensity) at which two lights
          look the same (a Rayleigh-type and a Moreland-type colour match, and
          brightness matches between whites).

Knob settings are numbers on the apparatus, not on her eye: she reads the dial,
not her cones. This is how cone fundamentals were measured in humans.

Same prior, eye, and forward model as marys_room_model_vs_know.py. All task
designs and noise levels are declared below before running.

Run from repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_quale_access
"""
from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path

import numpy as np

from scripts import marys_room_model_vs_know as mk
from scripts.marys_room_aperture_link import nelder_mead

ROOT = mk.ROOT
OUT = ROOT / "results" / "marys_room_quale_access_exploratory.json"
TRUE = mk.TRUE_THETA

# ======================= DECLARATIONS (fixed before running) =================
SIGMA_INT = 0.005            # internal noise on the opponent signal behind a sign report
SIGMA_NULL_NM = 2.0          # within-observer SD of a hue-null setting (declared)
SIGMA_RATIO = 0.01           # SD of a mixture-ratio match setting
SIGMA_LOGQ = 0.01            # SD of an intensity match setting (log10 units)
NULL_Q = [100, 1000, 10000]  # intensities at which nulls are set
RAYLEIGH = {"test_nm": 589.0, "a_nm": 545.0, "b_nm": 670.0, "test_q": 1000.0}
MORELAND = {"test_nm": 480.0, "a_nm": 440.0, "b_nm": 520.0, "test_q": 1000.0}
BRIGHT_REF = ("E", 100.0)    # adjustable E white matched in brightness to D65 / A whites
BRIGHT_TESTS = [("D65", 100.0), ("A", 100.0), ("D65", 1000.0), ("A", 1000.0)]
FD = 1e-4
# ============================================================================


def act_lines(lams, counts, t):
    """L, M, S activations for a line spectrum (arrays of wavelengths and counts)."""
    lams, counts = np.asarray(lams, float), np.asarray(counts, float)
    h = 10.0 ** t[6]
    out = []
    for r in range(3):
        caught = float((counts * np.exp(-0.5 * ((lams - t[2 * r]) / t[2 * r + 1]) ** 2)).sum())
        out.append(caught / (caught + h))
    return np.array(out)


def opp(a):
    return np.array([a[0] - a[1], a[2] - 0.5 * (a[0] + a[1])])


def bisect(f, lo, hi, it=80):
    flo = f(lo)
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ------------------------------------------------------------- task outcomes
def null_rg(t, q):
    return bisect(lambda l: opp(act_lines([l], [q], t))[0], 480.0, 620.0)


def null_by(t, q):
    return bisect(lambda l: opp(act_lines([l], [q], t))[1], 430.0, 530.0)


def colour_match(t, spec, channels):
    """Settings (f, log10 Q_mix) at which the mixture f*b + (1-f)*a matches the test
    on the two given activation channels. Newton on the two primary amounts."""
    target = act_lines([spec["test_nm"]], [spec["test_q"]], t)
    goal = np.array([ch(target) for ch in channels])

    def resid(uv):
        a = act_lines([spec["a_nm"], spec["b_nm"]], [uv[0], uv[1]], t)
        return np.array([ch(a) for ch in channels]) - goal
    # initial guess: match L and M catches exactly (linear in the primaries)
    g = lambda lam, r: math.exp(-0.5 * ((lam - t[2 * r]) / t[2 * r + 1]) ** 2)
    A = np.array([[g(spec["a_nm"], 0), g(spec["b_nm"], 0)], [g(spec["a_nm"], 1), g(spec["b_nm"], 1)]])
    T = spec["test_q"] * np.array([g(spec["test_nm"], 0), g(spec["test_nm"], 1)])
    uv = np.linalg.solve(A, T)
    uv = np.where(uv > 1e-6, uv, spec["test_q"] * 0.5)
    for _ in range(60):
        r = resid(uv)
        if np.abs(r).max() < 1e-15:
            break
        Jm = np.empty((2, 2))
        for j in range(2):
            d = 1e-6 * max(uv[j], 1.0)
            up = uv.copy(); up[j] += d
            Jm[:, j] = (resid(up) - r) / d
        step = np.linalg.solve(Jm, -r)
        lam = 1.0
        while np.any(uv + lam * step <= 0) and lam > 1e-6:
            lam *= 0.5
        uv = uv + lam * step
    Q = uv.sum()
    return np.array([uv[1] / Q, math.log10(Q)]), float(np.abs(resid(uv)).max())


RG_LUM = [lambda a: a[0] - a[1], lambda a: a[0] + a[1]]
BY_LUM = [lambda a: a[2] - 0.5 * (a[0] + a[1]), lambda a: a[0] + a[1]]


_WHITE = {}


def white_quanta(ill):
    """Expected (unrounded) quanta per bin of a white at 1 td; brightness matches use
    the continuous expectation so the setting is a smooth function of the eye."""
    if ill not in _WHITE:
        spd = mk.th.spd_from_recipe({"kind": "scene", "illuminant": ill, "scene_td": 1.0,
                                     "reflectance": None, "filter": None, "step": 1})
        _WHITE[ill] = np.asarray(mk.sf.expected_quanta(spd), float)
    return _WHITE[ill]


def white_lum(t, ill, td):
    q = white_quanta(ill) * td
    h = 10.0 ** t[6]
    a = []
    for r in range(2):
        c = float(q @ np.exp(-0.5 * ((mk.GRID - t[2 * r]) / t[2 * r + 1]) ** 2))
        a.append(c / (c + h))
    return a[0] + a[1]


def bright_match(t, ill, td):
    """log10 td of the E white that matches the test white in L+M brightness."""
    goal = white_lum(t, ill, td)
    return bisect(lambda ltd: white_lum(t, BRIGHT_REF[0], 10.0 ** ltd) - goal, -1.0, 5.0, it=80)


# ------------------------------------------------------------- information
def settings_vector(t, tasks):
    v = []
    for name in tasks:
        if name == "null_rg":
            v += [null_rg(t, q) for q in NULL_Q]
        elif name == "null_by":
            v += [null_by(t, q) for q in NULL_Q]
        elif name == "rayleigh":
            v += list(colour_match(t, RAYLEIGH, RG_LUM)[0])
        elif name == "moreland":
            v += list(colour_match(t, MORELAND, BY_LUM)[0])
        elif name == "bright_white":
            v += [bright_match(t, ill, td) for ill, td in BRIGHT_TESTS]
    return np.array(v)


def setting_sd(tasks):
    s = []
    for name in tasks:
        if name in ("null_rg", "null_by"):
            s += [SIGMA_NULL_NM] * len(NULL_Q)
        elif name in ("rayleigh", "moreland"):
            s += [SIGMA_RATIO, SIGMA_LOGQ]
        elif name == "bright_white":
            s += [SIGMA_LOGQ] * len(BRIGHT_TESTS)
    return np.array(s)


def jac(fun, t):
    base = fun(t)
    J = np.empty((len(base), 7))
    for j in range(7):
        d = FD * max(abs(t[j]), 1.0)
        tp, tm = t.copy(), t.copy()
        tp[j] += d
        tm[j] -= d
        J[:, j] = (fun(tp) - fun(tm)) / (2 * d)
    return J


def _log_ncdf(z):
    """log Phi(z), accurate in both tails."""
    if z > -30:
        return math.log(max(0.5 * math.erfc(-z / math.sqrt(2)), 1e-320))
    return -0.5 * z * z - math.log(-z) - 0.5 * math.log(2 * math.pi)


def sign_fisher(C, t):
    """Fisher information of probit sign reports on RG and BY for stimuli C."""
    Y = mk.forward(C, t)[0].ravel()
    J = mk.jacobian(C, t)
    w = np.empty(len(Y))
    for i, y in enumerate(Y):
        z = y / SIGMA_INT
        log_phi = -0.5 * z * z - 0.5 * math.log(2 * math.pi)
        w[i] = math.exp(2 * log_phi - _log_ncdf(z) - _log_ncdf(-z)) / SIGMA_INT ** 2
    return (J * w[:, None]).T @ J


def summarise(F, mu, sd, label):
    P0 = np.diag(1.0 / sd ** 2)
    P = P0 + F
    bits = 0.5 * (np.linalg.slogdet(P)[1] - np.log(np.diag(P0)).sum()) / math.log(2)
    cov = np.linalg.inv(P)
    return {"access": label, "bits_gained": float(bits),
            "posterior_sd_over_prior_sd": dict(zip(mk.PARAM_NAMES, (np.sqrt(np.diag(cov)) / sd).tolist())),
            "rg_zero_posterior_sd_nm": mk.zero_sd_from_cov(TRUE, cov)}


def main():
    mu, sd = mk.build_prior("population")
    M = mk.manifest_stimuli()
    rooms = {}
    for rname, ills in (("room_E_eyelid", ["E"]), ("room_all_eyelid", ["E", "D65", "A"])):
        _, C = mk.room_stimuli(ills, True)
        rooms[rname] = C
    true_settings = {k: settings_vector(TRUE, [k]).tolist()
                     for k in ("null_rg", "null_by", "rayleigh", "moreland", "bright_white")}
    rows = []
    # room: sign reports on everything seen, plus brightness matches between whites
    for rname, C in rooms.items():
        F_sign = sign_fisher(C, TRUE)
        rows.append(summarise(F_sign, mu, sd, f"{rname}: sign reports"))
        if rname == "room_all_eyelid":
            Jb = jac(lambda t: settings_vector(t, ["bright_white"]), TRUE)
            sb = setting_sd(["bright_white"])
            F_b = (Jb / sb[:, None]).T @ (Jb / sb[:, None])
            rows.append(summarise(F_sign + F_b, mu, sd, f"{rname}: sign reports + white brightness matches"))
    # release: sign reports on the 93 monochromatic lights
    F_rel_sign = sign_fisher(M["C_train"], TRUE)
    rows.append(summarise(F_rel_sign, mu, sd, "release: sign reports on 93 mono lights"))
    # release: nulling and matching tasks (public knob settings)
    F_tasks = {}
    for task in ("null_rg", "null_by", "rayleigh", "moreland"):
        J = jac(lambda t, task=task: settings_vector(t, [task]), TRUE)
        s = setting_sd([task])
        F_tasks[task] = (J / s[:, None]).T @ (J / s[:, None])
        rows.append(summarise(F_tasks[task], mu, sd, f"release: {task}"))
    F_all = sum(F_tasks.values())
    rows.append(summarise(F_all, mu, sd, "release: null_rg + null_by + rayleigh + moreland"))
    F_room = sign_fisher(rooms["room_all_eyelid"], TRUE)
    rows.append(summarise(F_all + F_rel_sign + F_room, mu, sd, "room signs + release signs + all four tasks"))

    # MAP from the four release tasks: Mary fits her eye to her own knob settings.
    # ADDED AFTER THE FIRST RUN (labelled): repeats per setting and the broad prior.
    tasks = ["null_rg", "null_by", "rayleigh", "moreland"]
    obs, s = settings_vector(TRUE, tasks), setting_sd(tasks)
    J4 = sum(F_tasks.values())
    maps = {}
    for pname in ("population", "broad"):
        mu_p, sd_p = mk.build_prior(pname)
        for reps in (1, 10, 100):
            se = s / math.sqrt(reps)

            def nlp(t, se=se, mu_p=mu_p, sd_p=sd_p):
                if t[1] <= 1 or t[3] <= 1 or t[5] <= 1:
                    return 1e12
                try:
                    r = (settings_vector(t, tasks) - obs) / se
                except Exception:
                    return 1e12
                return 0.5 * float((r ** 2).sum() + (((t - mu_p) / sd_p) ** 2).sum())
            t_hat, _ = nelder_mead(nlp, mu_p, 2500)
            t_hat, _ = nelder_mead(nlp, t_hat, 2500)
            fisher = summarise(J4 * reps, mu_p, sd_p, f"four tasks x{reps}, {pname} prior")
            maps[f"{pname}|reps={reps}"] = {"fisher": fisher,
                                           "map": mk.predictive_report(t_hat, M, "MAP from quale tasks")}
    map_rep = maps

    out = {"status": "EXPLORATORY, POST-HOC; quale-level access only; eye not built; no frozen file changed",
           "provenance": mk.rd.provenance_line(),
           "utc_timestamp": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
           "script_sha256": mk.sha256_file(Path(__file__)),
           "declared": {"sigma_int": SIGMA_INT, "sigma_null_nm": SIGMA_NULL_NM, "sigma_ratio": SIGMA_RATIO,
                        "sigma_logq": SIGMA_LOGQ, "null_q": NULL_Q, "rayleigh": RAYLEIGH,
                        "moreland": MORELAND, "bright_tests": BRIGHT_TESTS},
           "true_eye_settings": true_settings,
           "prior_mean_settings": {k: settings_vector(mu, [k]).tolist()
                                   for k in ("null_rg", "null_by", "rayleigh", "moreland")},
           "fisher_rows": rows, "map_from_quale_tasks": map_rep,
           "numeric_readout_reference": "marys_room_model_vs_know_exploratory.json: room_all_eyelid 22.7 bits, + release 37.6 bits (sigma 0.005)"}
    OUT.write_text(json.dumps(mk.rd._jsonable(out), indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
