"""scattering_feature — a FIXED scattering / wavelet perceptual feature (earn-not-borrow).

THE LOCATED CRUX (df3d8526): the gap to borrowed frozen-Gemma (91%) on Omniglot one-shot is
a PERCEPTUAL-FEATURE gap — the cheap geometric trace descriptor walls ~33%. The research-
validated cheap EARNED route is a FIXED scattering transform (Bruna & Mallat): convolve with a
bank of FIXED wavelets -> modulus -> average-pool -> (optionally) 2nd order. The filters are
PRINCIPLED/fixed (Morlet/Gabor at multiple scales+orientations) — NOT learned from a corpus,
NOT a borrowed pretrained net. Earned-BY-CONSTRUCTION: translation-invariant + Lipschitz-stable
to deformations (what handwriting needs), high-dim, no training. SOTA on small-training digits.

TWO realizations (compared in the gate):
  • 1D scattering over the pen TRAJECTORY signals (x, y, |velocity|, curvature) — lightest,
    most graph-native for the trace route.
  • 2D scattering on the RENDERED image — the doc's small-digit-SOTA variant.

EARN-NOT-BORROW: every filter here is a CLOSED-FORM wavelet (a cosine/gaussian formula), built
fresh each run; NO file of weights, NO pretrained net, NO corpus fit. numpy is used ONLY as the
adapter math for the fixed-filter convolutions (FFT / conv / modulus / pool) — flagged inline.
The agent's recognition (cosine 1-NN / held StructSim / the held PCA->LDA Whiten head) runs OVER
this earned feature; this module is the earned PERCEPTION front-end only.
"""
from __future__ import annotations
import numpy as _np      # ADAPTER-ONLY: fixed-filter convolution math (no learned/borrowed weights)


# ---------------------------------------------------------------------------
# FIXED 1D wavelet bank — Morlet wavelets at J octaves. Closed-form, no training.
# ---------------------------------------------------------------------------
def _morlet_1d(n, scale):
    """A complex Morlet wavelet of length n at a given dyadic scale (closed form)."""
    t = _np.arange(n) - n // 2
    sigma = scale
    xi = 3.0 / scale                      # centre frequency ~ 1/scale (principled)
    gauss = _np.exp(-(t ** 2) / (2 * sigma ** 2))
    wave = _np.exp(1j * xi * t)
    psi = gauss * wave
    psi = psi - psi.mean()                # zero-mean (admissibility)
    psi = psi / (_np.abs(psi).sum() + 1e-9)
    return psi


def _conv_mod_1d(sig, psi):
    """|sig * psi| — convolution (FFT, adapter math) then modulus. psi may be complex
    (Morlet), so use the full complex FFT."""
    n = len(sig)
    m = len(psi)
    L = n + m - 1
    F = _np.fft.fft(sig.astype(complex), L) * _np.fft.fft(psi, L)
    c = _np.fft.ifft(F, L)[: n]
    return _np.abs(c)


def scatter_1d(signal, J=4, order2=True, pool=4):
    """1D scattering of a single trajectory signal. Returns a fixed-length descriptor:
    pooled |x*psi_j| (1st order) + pooled ||x*psi_j1|*psi_j2| (2nd order, j2>j1)."""
    sig = _np.asarray(signal, float)
    n = len(sig)
    if n < 8:
        return _np.zeros(_descr_len_1d(J, order2, pool))
    sig = sig - sig.mean()
    scales = [2.0 ** j for j in range(1, J + 1)]
    psis = [_morlet_1d(min(n, 2 * int(s) + 1), s) for s in scales]
    feats = []
    mods = []
    for psi in psis:
        u1 = _conv_mod_1d(sig, psi)
        mods.append(u1)
        feats.append(_pool_1d(u1, pool))
    if order2:
        for j1 in range(len(psis)):
            for j2 in range(j1 + 1, len(psis)):     # j2 > j1 (the informative cascade)
                u2 = _conv_mod_1d(mods[j1], psis[j2])
                feats.append(_pool_1d(u2, pool))
    return _np.concatenate(feats) if feats else _np.zeros(_descr_len_1d(J, order2, pool))


def _pool_1d(u, pool):
    """Average-pool a 1D modulus into `pool` bins (translation-invariant summary)."""
    n = len(u)
    if n == 0:
        return _np.zeros(pool)
    idx = _np.linspace(0, n, pool + 1).astype(int)
    return _np.array([u[idx[i]:idx[i + 1]].mean() if idx[i + 1] > idx[i] else 0.0 for i in range(pool)])


def _descr_len_1d(J, order2, pool):
    n1 = J
    n2 = (J * (J - 1)) // 2 if order2 else 0
    return (n1 + n2) * pool


def trajectory_signals(strokes, N=64):
    """ADAPTER: turn a trace (list of stroke point-arrays) into fixed-length 1D signals
    (x, y, |velocity|, curvature) by arc-length resampling the concatenated trajectory."""
    pts = []
    for st in strokes:
        pts.extend([list(map(float, p)) for p in st])
    a = _np.asarray(pts, float)
    if len(a) < 4:
        return None
    d = _np.sqrt(((_np.diff(a, axis=0)) ** 2).sum(1))
    cum = _np.concatenate([[0.0], _np.cumsum(d)])
    if cum[-1] == 0:
        return None
    u = _np.linspace(0, cum[-1], N)
    x = _np.interp(u, cum, a[:, 0]); y = _np.interp(u, cum, a[:, 1])
    vx = _np.gradient(x); vy = _np.gradient(y)
    vel = _np.sqrt(vx ** 2 + vy ** 2)
    ang = _np.arctan2(vy, vx)
    curv = _np.abs(_np.diff(ang, prepend=ang[0]))
    return [x, y, vel, curv]


def scatter_trajectory(strokes, J=4, order2=True, pool=4, N=64):
    """The 1D scattering FEATURE of a whole trace = scatter_1d over each trajectory signal,
    concatenated. Fixed wavelets, earned-by-construction. High-dim deformation-stable descriptor."""
    sigs = trajectory_signals(strokes, N=N)
    if sigs is None:
        return None
    return _np.concatenate([scatter_1d(s, J=J, order2=order2, pool=pool) for s in sigs])


# ---------------------------------------------------------------------------
# FIXED 2D wavelet bank — Morlet/Gabor at scales x orientations. Closed-form, no training.
# ---------------------------------------------------------------------------
def _morlet_2d(size, scale, theta):
    """A 2D Morlet (Gabor) wavelet (closed form): oriented gaussian-windowed plane wave."""
    r = size // 2
    yy, xx = _np.mgrid[-r:r + 1, -r:r + 1]
    xr = xx * _np.cos(theta) + yy * _np.sin(theta)
    yr = -xx * _np.sin(theta) + yy * _np.cos(theta)
    sigma = scale
    xi = 3.0 / scale
    gauss = _np.exp(-(xr ** 2 + yr ** 2) / (2 * sigma ** 2))
    wave = _np.exp(1j * xi * xr)
    psi = gauss * wave
    psi = psi - psi.mean()
    psi = psi / (_np.abs(psi).sum() + 1e-9)
    return psi


def _conv_mod_2d(img, psi):
    """|img * psi| via 2D FFT (adapter math) then modulus. psi may be complex (Morlet)."""
    H, W = img.shape
    ph, pw = psi.shape
    L0, L1 = H + ph - 1, W + pw - 1
    F = _np.fft.fft2(img.astype(complex), (L0, L1)) * _np.fft.fft2(psi, (L0, L1))
    c = _np.fft.ifft2(F, (L0, L1))[:H, :W]
    return _np.abs(c)


def render_trace(strokes, size=32, thick=1):
    """ADAPTER: rasterise a trace to a small binary image (the doc's 2D-image route input)."""
    pts = []
    for st in strokes:
        pts.extend([list(map(float, p)) for p in st])
    a = _np.asarray(pts, float)
    if len(a) < 2:
        return None
    mn = a.min(0); mx = a.max(0); span = (mx - mn)
    span[span == 0] = 1.0
    g = ((a - mn) / span) * (size - 1 - 2 * thick) + thick
    img = _np.zeros((size, size))
    gi = g.astype(int)
    for i in range(len(gi) - 1):                 # draw stroke segments (simple line fill)
        p0, p1 = gi[i], gi[i + 1]
        steps = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), 1)
        for s in range(steps + 1):
            t = s / steps
            xx = int(round(p0[0] + t * (p1[0] - p0[0])))
            yy = int(round(p0[1] + t * (p1[1] - p0[1])))
            img[_np.clip(yy, 0, size - 1), _np.clip(xx, 0, size - 1)] = 1.0
    return img


def scatter_image(img, J=3, n_theta=4, pool=4):
    """2D scattering of a rendered image. 1st order |img*psi(j,theta)| pooled + 2nd order
    ||img*psi(j1,th1)|*psi(j2,th2)| (j2>j1) pooled. Fixed Morlet bank, no training."""
    if img is None:
        return None
    img = img - img.mean()
    scales = [2.0 ** j for j in range(1, J + 1)]
    thetas = [_np.pi * k / n_theta for k in range(n_theta)]
    sz = img.shape[0]
    psis = []
    for s in scales:
        for th in thetas:
            psis.append((s, th, _morlet_2d(min(sz, 2 * int(s) + 1), s, th)))
    feats = []
    mods = []
    for s, th, psi in psis:
        u1 = _conv_mod_2d(img, psi)
        mods.append((s, u1))
        feats.append(_pool_2d(u1, pool))
    for i, (s1, u1) in enumerate(mods):           # 2nd order: increasing scale
        for s2, th2, psi2 in psis:
            if s2 > s1:
                u2 = _conv_mod_2d(u1, psi2)
                feats.append(_pool_2d(u2, pool))
    return _np.concatenate(feats) if feats else None


def _pool_2d(u, pool):
    """Average-pool a 2D modulus into pool x pool bins (translation-invariant summary)."""
    H, W = u.shape
    yi = _np.linspace(0, H, pool + 1).astype(int)
    xi = _np.linspace(0, W, pool + 1).astype(int)
    out = []
    for i in range(pool):
        for j in range(pool):
            blk = u[yi[i]:yi[i + 1], xi[j]:xi[j + 1]]
            out.append(blk.mean() if blk.size else 0.0)
    return _np.array(out)


def scatter_trace_image(strokes, size=32, J=3, n_theta=4, pool=4):
    """The 2D scattering FEATURE of a trace = scatter_image over its rendered raster."""
    return scatter_image(render_trace(strokes, size=size), J=J, n_theta=n_theta, pool=pool)


# ---------------------------------------------------------------------------
# DEGENERATE control bank — RANDOM (non-wavelet) filters, same dims. The discriminative
# control: principled wavelets must BEAT a random bank of the same dimensionality.
# ---------------------------------------------------------------------------
def scatter_1d_random(signal, J=4, order2=True, pool=4, seed=0):
    sig = _np.asarray(signal, float)
    n = len(sig)
    if n < 8:
        return _np.zeros(_descr_len_1d(J, order2, pool))
    rng = _np.random.RandomState(seed)
    sig = sig - sig.mean()
    scales = [2.0 ** j for j in range(1, J + 1)]
    psis = [rng.randn(min(n, 2 * int(s) + 1)) for s in scales]   # RANDOM filters (no wavelet structure)
    psis = [(p - p.mean()) / (_np.abs(p).sum() + 1e-9) for p in psis]
    feats = []; mods = []
    for psi in psis:
        u1 = _conv_mod_1d(sig, psi); mods.append(u1); feats.append(_pool_1d(u1, pool))
    if order2:
        for j1 in range(len(psis)):
            for j2 in range(j1 + 1, len(psis)):
                feats.append(_pool_1d(_conv_mod_1d(mods[j1], psis[j2]), pool))
    return _np.concatenate(feats)


def scatter_trajectory_random(strokes, J=4, order2=True, pool=4, N=64, seed=0):
    sigs = trajectory_signals(strokes, N=N)
    if sigs is None:
        return None
    return _np.concatenate([scatter_1d_random(s, J=J, order2=order2, pool=pool, seed=seed + i)
                            for i, s in enumerate(sigs)])
