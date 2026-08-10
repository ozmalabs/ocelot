"""phasefield_pc -- Kovesi monogenic-signal PHASE CONGRUENCY, in numpy.

THE MECHANISM, NOT THE CONSTANTS (PROTOCOL s13).  Phase congruency (Kovesi
1999/2003) marks a feature where the Fourier components of the image, across
scales, are maximally IN PHASE -- constructive interference.  It is
CONTRAST-INVARIANT (the sum-of-amplitudes normaliser cancels contrast), unlike
gradient magnitude / local energy, which scales with contrast.  That is the
whole reason it is the WAVEFIELD reading of a frame and not the value reading.

This is the MONOGENIC formulation (`phasecongmono`): one log-Gabor radial
filter bank + the Riesz transform, no orientation loop.  Its noise threshold
is the canonical "falls out of the noise energy" quantity: the smallest-scale
amplitude in a featureless region is Rayleigh-distributed, and the noise
energy mean/sigma are the Rayleigh moments -- NOT a picked number.  The `k`
sigma-multiplier is the one dial, and every downstream measurement SWEEPS it
(and cross-checks against Otsu) so no single value is load-bearing.

The filter-bank constants (minWaveLength, mult, sigmaOnf, cutOff, g) are
Kovesi's PUBLISHED defaults; they DEFINE the multi-scale log-Gabor
representation (the imported mechanism), exactly as the motion-energy rung's
DFT grid is fixed by the field.  They are declared CONFIGURATION and their
robustness is measured (nscale in {3,4,5}).

Everything real-valued that is a spatial COORDINATE stays integer (the frame is
the integer lattice); everything continuous (phase, filter response, energy)
lives in the FFT -- the cross-frame map (CLAUDE.md frame/continuum invariant).
"""
from __future__ import annotations

import numpy as np

EPS = 1e-4

# Kovesi published defaults -- CONFIGURATION (the log-Gabor bank definition).
MINWAVELENGTH = 3.0     # smallest filter wavelength = 3 px (pixel resolution)
MULT = 2.1              # scaling between successive filters
SIGMAONF = 0.55         # log-Gabor bandwidth (~2 octaves)
CUTOFF = 0.5            # frequency-spread weighting knee
G = 10.0               # frequency-spread weighting sharpness
K_NOISE_DEFAULT = 2.0   # sigma multiplier on the Rayleigh noise floor


def _lowpass(shape):
    """Butterworth lowpass (cutoff 0.45, order 15) to suppress the corner
    aliasing of the log-Gabor filters.  Kovesi's `lowpassfilter`."""
    rows, cols = shape
    yr = (np.arange(rows) - (rows // 2)) / rows
    xr = (np.arange(cols) - (cols // 2)) / cols
    x, y = np.meshgrid(xr, yr)
    radius = np.sqrt(x * x + y * y)
    return np.fft.ifftshift(1.0 / (1.0 + (radius / 0.45) ** (2 * 15)))


def _grids(shape):
    rows, cols = shape
    # normalised frequency grid, DC at (0,0) after ifftshift
    if cols % 2:
        xr = np.arange(-(cols - 1) / 2, (cols - 1) / 2 + 1) / (cols - 1)
    else:
        xr = np.arange(-cols / 2, cols / 2) / cols
    if rows % 2:
        yr = np.arange(-(rows - 1) / 2, (rows - 1) / 2 + 1) / (rows - 1)
    else:
        yr = np.arange(-rows / 2, rows / 2) / rows
    x, y = np.meshgrid(xr, yr)
    x = np.fft.ifftshift(x)
    y = np.fft.ifftshift(y)
    radius = np.sqrt(x * x + y * y)
    radius[0, 0] = 1.0        # avoid log(0)/div0 at DC
    return x, y, radius


def phase_congruency(img, nscale=4, k_noise=K_NOISE_DEFAULT,
                     minwavelength=MINWAVELENGTH, mult=MULT,
                     sigmaonf=SIGMAONF, cutoff=CUTOFF, g=G):
    """Monogenic phase congruency map PC in [0,1], NOISE-COMPENSATED.

    Returns dict with `pc` (the noise-compensated congruency, in [0,1]),
    `ori`, `energy`, `T` (the Rayleigh noise threshold that fell out),
    `sumAn`.  PC == 0 exactly where the local energy does not exceed the
    estimated noise floor -- so `pc > 0` is a THRESHOLD-FREE boundary set
    (the only 'threshold' is the noise floor, which is derived, not picked).
    """
    img = np.asarray(img, float)
    rows, cols = img.shape
    IM = np.fft.fft2(img)

    x, y, radius = _grids(img.shape)
    lp = _lowpass(img.shape)

    # Riesz transform (odd, monogenic) filters in the frequency domain.
    H = (1j * x - y) / radius
    H[0, 0] = 0.0

    sumAn = np.zeros((rows, cols))
    sumf = np.zeros((rows, cols))
    sumh1 = np.zeros((rows, cols))
    sumh2 = np.zeros((rows, cols))
    maxAn = None
    tau = None

    for s in range(nscale):
        wavelength = minwavelength * (mult ** s)
        fo = 1.0 / wavelength
        logGabor = np.exp(-(np.log(radius / fo) ** 2) /
                          (2 * np.log(sigmaonf) ** 2))
        logGabor *= lp
        logGabor[0, 0] = 0.0

        IMF = IM * logGabor
        f = np.real(np.fft.ifft2(IMF))
        h = np.fft.ifft2(IMF * H)
        h1 = np.real(h)
        h2 = np.imag(h)
        An = np.sqrt(f * f + h1 * h1 + h2 * h2)

        sumAn += An
        sumf += f
        sumh1 += h1
        sumh2 += h2

        if s == 0:
            maxAn = An.copy()
            # Rayleigh noise: robust median of the smallest-scale amplitude.
            # median(An)/sqrt(log(4)) is the Rayleigh mode estimator.
            tau = np.median(sumAn.ravel()) / np.sqrt(np.log(4.0))
        else:
            maxAn = np.maximum(maxAn, An)

    # Overall energy and orientation from the summed monogenic vector.
    ori = np.arctan2(sumh2, sumh1)
    # local phase / feature type not needed for the congruency magnitude
    XEnergy = np.sqrt(sumf * sumf + sumh1 * sumh1 + sumh2 * sumh2) + EPS
    MeanE = sumf / XEnergy
    MeanO = np.sqrt(sumh1 * sumh1 + sumh2 * sumh2) / XEnergy  # not used directly

    # Energy = |monogenic vector| (phase-aligned magnitude).
    energy = np.sqrt(sumf * sumf + sumh1 * sumh1 + sumh2 * sumh2)

    # Noise threshold that FALLS OUT of the Rayleigh distribution.
    totalTau = tau * (1 - (1.0 / mult) ** nscale) / (1 - (1.0 / mult))
    noise_mean = totalTau * np.sqrt(np.pi / 2.0)
    noise_sigma = totalTau * np.sqrt((4.0 - np.pi) / 2.0)
    T = noise_mean + k_noise * noise_sigma

    energy_c = np.maximum(energy - T, 0.0)

    # Frequency-spread weighting: penalise responses concentrated in one scale.
    width = (sumAn / (maxAn + EPS) - 1.0) / (nscale - 1)
    weight = 1.0 / (1.0 + np.exp(g * (cutoff - width)))

    pc = weight * energy_c / (sumAn + EPS)
    pc = np.clip(pc, 0.0, 1.0)
    return {"pc": pc, "ori": ori, "energy": energy, "T": float(T),
            "sumAn": sumAn, "tau": float(tau)}


def local_energy_magnitude(img, nscale=4, minwavelength=MINWAVELENGTH,
                           mult=MULT, sigmaonf=SIGMAONF):
    """THE MAGNITUDE-ONLY NEGATIVE COMPARATOR (the pre-registered trap).

    Local energy WITHOUT the sum-of-amplitudes phase normalisation -- i.e.
    the SAME log-Gabor bank, but the boundary strength is the raw monogenic
    energy magnitude, contrast-DEPENDENT.  If segmenting on this moves the
    size median as much as PC does, then PHASE is not the lever and the PC
    result is the negative (magnitude discarded the arrangement).
    Returned normalised to [0,1] by its own max for thresholding parity.
    """
    img = np.asarray(img, float)
    rows, cols = img.shape
    IM = np.fft.fft2(img)
    x, y, radius = _grids(img.shape)
    lp = _lowpass(img.shape)
    H = (1j * x - y) / radius
    H[0, 0] = 0.0
    sumf = np.zeros((rows, cols))
    sumh1 = np.zeros((rows, cols))
    sumh2 = np.zeros((rows, cols))
    for s in range(nscale):
        fo = 1.0 / (minwavelength * (mult ** s))
        logGabor = np.exp(-(np.log(radius / fo) ** 2) /
                          (2 * np.log(sigmaonf) ** 2))
        logGabor *= lp
        logGabor[0, 0] = 0.0
        IMF = IM * logGabor
        f = np.real(np.fft.ifft2(IMF))
        h = np.fft.ifft2(IMF * H)
        sumf += f
        sumh1 += np.real(h)
        sumh2 += np.imag(h)
    energy = np.sqrt(sumf * sumf + sumh1 * sumh1 + sumh2 * sumh2)
    m = float(energy.max())
    return energy / m if m > 0 else energy
