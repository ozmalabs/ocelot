"""Motor signature — reverse-engineering HOW a stroke was made, above cheap recognition.

Recognising a glyph is the apparatus-invariant reflex (why anyone reads a 'd'); recovering
the generating apparatus (friction, care) is the separable deep layer. These gates validate
that (1) the signature recovers a known (friction, care) regime from synthetic ground truth,
and (2) the two layers are separable: the same glyph under two apparatuses reads as the same
shape while its motor signature differs.
"""
from __future__ import annotations

import numpy as np

from domains.motor_signature import (
    render_stroke, motor_signature, infer_environment, establish_deformation,
    canonicalize, _smooth,
)


def _rot(p, a):
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return p @ R.T


def _ideal_d():
    th = np.linspace(0, 2 * np.pi, 120)
    loop = np.c_[np.cos(th), np.sin(th)] * 0.5
    stem = np.c_[np.full(40, 0.5), np.linspace(1.2, -0.5, 40)]
    return np.vstack([loop, stem])


def _mean_sig(friction, care, key, *, k=8):
    ideal = _ideal_d()
    vals = []
    for seed in range(k):
        rng = np.random.default_rng(seed)
        vals.append(motor_signature(*render_stroke(ideal, friction=friction, care=care, rng=rng))[key])
    return float(np.mean(vals))


def test_signature_recovers_friction():
    """A draggy, high-friction stroke reads as higher friction than a clean glide — the
    stick-slip corner-slowdown and squaring recover the regime."""
    low = _mean_sig(0.05, 0.9, "friction")
    high = _mean_sig(0.7, 0.9, "friction")
    assert high > low + 0.2, f"friction recovered: glide {low:.2f} -> drag {high:.2f}"


def test_signature_recovers_care():
    """A shaky hand / grubby setup leaves a higher jitter floor, read as lower care —
    monotone across the range."""
    care_est = [_mean_sig(0.4, c, "care") for c in (0.2, 0.5, 0.8, 1.0)]
    assert care_est[0] < care_est[1] < care_est[2] < care_est[3], f"care recovered: {care_est}"
    assert care_est[-1] - care_est[0] > 0.4


def test_recognition_is_apparatus_invariant_but_motor_is_recoverable():
    """The two layers separate: the SAME glyph under a clean glide vs a draggy+shaky
    apparatus reads as the same shape (recognition is apparatus-invariant — why the 'd' is
    trivial), while the motor signature recovers the different HOW (the deep layer)."""
    ideal = _ideal_d()
    rng = np.random.default_rng(3)
    xA, tA = render_stroke(ideal, friction=0.05, care=1.0, rng=rng)   # clean glide
    xB, tB = render_stroke(ideal, friction=0.9, care=0.3, rng=rng)    # draggy + shaky
    sA, sB = motor_signature(xA, tA), motor_signature(xB, tB)

    def resample(p, m=120):
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        u = np.linspace(0, d[-1], m)
        return np.c_[np.interp(u, d, p[:, 0]), np.interp(u, d, p[:, 1])]

    shape_gap = float(np.linalg.norm(resample(_smooth(xA, 6)) - resample(_smooth(xB, 6)), axis=1).mean())
    assert shape_gap < 0.3, f"recognition survives the apparatus (same 'd'): shape gap {shape_gap:.2f}"
    assert abs(sA["friction"] - sB["friction"]) > 0.25, \
        f"motor signature recovers the different HOW: {sA['friction']:.2f} vs {sB['friction']:.2f}"
    assert sA["care"] > sB["care"] + 0.3, "and the different care (steady vs shaky)"


def test_pauses_recover_the_workspace_limit():
    """The hand rests on a surface with a bounded reach; a stroke that exceeds it forces
    RE-ANCHORING — a pause. A smaller workspace produces more pauses, recovered from the
    stationary-dwell events in the timing (the observable of the 'limits')."""
    ideal = _ideal_d()

    def mean_pauses(reach):
        return np.mean([motor_signature(*render_stroke(ideal, friction=0.3, care=0.9,
                        reach=reach, rng=np.random.default_rng(s)))["pauses"] for s in range(6)])

    assert mean_pauses(None) < 0.5, "unbounded reach -> no re-anchoring"
    assert mean_pauses(0.3) > 1.5, "a small workspace forces several re-anchor pauses"
    assert mean_pauses(0.3) > mean_pauses(0.55), "smaller workspace -> more pauses"


def test_distortion_is_confounded_in_a_single_glyph():
    """Distortion is confounded in a SINGLE glyph by that glyph's own shape: on a controlled
    isotropic ideal it is recovered, but on an intrinsically anisotropic glyph (a 'd' with its
    long stem) it reads high even with no deformation. (The fix is not per-glyph AbS — see
    the session test below.)"""
    th = np.linspace(0, 2 * np.pi, 160)
    circle = np.c_[np.cos(th), np.sin(th)]

    def anis(ideal, a):
        return np.mean([motor_signature(*render_stroke(ideal, friction=0.2, care=0.95,
                        anisotropy=a, rng=np.random.default_rng(s)))["anisotropy"] for s in range(6)])

    assert anis(circle, 0.0) < 0.2 < anis(circle, 0.4), "recovered on a controlled isotropic shape"
    assert anis(_ideal_d(), 0.0) > 0.4, "confounded on an intrinsically anisotropic glyph"


def test_shared_deformation_is_identifiable_across_a_session():
    """You do NOT need per-glyph AbS. The apparatus deformation is a SHARED session latent:
    confounded in any single glyph, but identifiable across a batch of different glyphs written
    in the same circumstances — their intended shapes average toward isotropic, so the common
    bias that remains is the deformation. Established once, every other glyph snaps to it."""
    base = _ideal_d()

    def batch(A, K=16):
        return [render_stroke(_rot(base, np.pi * k / K), friction=0.2, care=0.95,
                anisotropy=A, rng=np.random.default_rng(k))[0] for k in range(K)]

    none = establish_deformation(batch(0.0))["anisotropy"]
    real = establish_deformation(batch(0.4))["anisotropy"]
    assert none < 0.2 < real, f"the session recovers the shared deformation: {none:.2f} vs {real:.2f}"
    # meanwhile a single glyph cannot tell A=0 from A=0.4 (both confounded high).
    pg = np.mean([motor_signature(xy)["anisotropy"] for xy in batch(0.0)])
    assert pg > 0.4, "a single glyph reads deformation where the session shows there is none"


def test_single_glyph_infers_the_environment():
    """The payoff: from ONE glyph the motor signature places a posterior over the generating
    environment. A high-friction, careless render abduces a cheap/casual context; a clean,
    careful one abduces a good setup. One artifact, defeasible assumptions about the situation."""
    ideal = _ideal_d()
    rng = np.random.default_rng(7)
    draggy = infer_environment(motor_signature(*render_stroke(ideal, friction=0.85, care=0.3, rng=rng)))
    clean = infer_environment(motor_signature(*render_stroke(ideal, friction=0.05, care=0.98, rng=rng)))
    assert "cheap" in draggy["context"] or "casual" in draggy["context"], draggy
    assert "high-friction" in draggy["surface"] and "hurried" in draggy["engagement"]
    assert "good setup" in clean["context"] and "careful" in clean["engagement"]
    assert draggy["context"] != clean["context"], "one glyph separates the two environments"


def _alphabet(K=12):
    def make(seed):
        g = np.random.default_rng(seed)
        t = np.linspace(0, 1, 80)
        x, y = t.copy(), np.zeros_like(t)
        for _ in range(3):
            y += g.uniform(-0.4, 0.4) * np.sin(2 * np.pi * g.uniform(1, 4) * t + g.uniform(0, 2 * np.pi))
            x += g.uniform(-0.3, 0.3) * np.sin(2 * np.pi * g.uniform(1, 4) * t + g.uniform(0, 2 * np.pi))
        return np.c_[x, y]
    return [make(s) for s in range(K)]


def _norm(p, N=64):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    u = np.linspace(0, d[-1], N)
    q = np.c_[np.interp(u, d, p[:, 0]), np.interp(u, d, p[:, 1])]
    q = q - q.mean(0)
    return q / (np.sqrt((q ** 2).sum(1).mean()) + 1e-9)


def test_factoring_out_shared_deformation_raises_accuracy():
    """The prediction: establishing the shared session deformation once and canonicalising every
    glyph raises recognition accuracy — decisively under the strong deformation where raw
    template-matching collapses. The shared latent is a per-session nuisance transform, removed
    for the whole batch at once."""
    canon = _alphabet()
    templates = [_norm(c) for c in canon]

    def classify(q):
        return int(np.argmin([np.linalg.norm(q - tm) for tm in templates]))

    raw_ok = canon_ok = tot = 0
    for sess in range(10):
        g = np.random.default_rng(200 + sess)
        A = g.uniform(0.55, 0.75)                              # strong per-session deformation
        obs = []
        for c in canon:
            ctr = c.mean(0)
            obs.append(ctr + (c - ctr) * np.array([1 + A, 1 - A]) + g.normal(0, 0.01, c.shape))
        defm = establish_deformation(obs)
        for k, o in enumerate(obs):
            tot += 1
            raw_ok += classify(_norm(o)) == k
            canon_ok += classify(_norm(canonicalize(o, defm))) == k

    raw, canon_acc = raw_ok / tot, canon_ok / tot
    assert canon_acc > raw + 0.1, f"canonicalising lifts accuracy: raw {raw:.0%} -> canon {canon_acc:.0%}"
    assert canon_acc > 0.9, "and reaches high accuracy once the shared deformation is removed"
