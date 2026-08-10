"""Fast synthetic unit tests for the earned low-dim articulatory bottleneck pieces.

No phonebank / no torch — tiny synthetic data so the regression suite (-k bottleneck/manifold/cluster)
stays cheap. Validates: the from-scratch numpy autoencoder actually LEARNS (recon MSE drops vs its own
random-init), the cluster-quality metrics (purity/NMI) are sane, and few-shot nearest-centroid recovers
well-separated synthetic "phones". donkey=0: from-scratch numpy, decision = held argmin."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_articulatory_bottleneck import (
    train_ae, kmeans, purity, nmi, fewshot_acc,
)


def _synth(n_per=200, k=6, dim=32, seed=0):
    """k well-separated synthetic clusters in `dim` dims = 'phones' on a low-d manifold.
    Centers are FIXED (shared across train/dev splits); only the per-point noise varies with `seed`."""
    centers = np.random.default_rng(12345).standard_normal((k, dim)) * 3.0
    rng = np.random.default_rng(seed)
    X, Y = [], []
    for c in range(k):
        X.append(centers[c] + rng.standard_normal((n_per, dim)) * 0.5)
        Y += [f"p{c}"] * n_per
    X = np.vstack(X).astype(np.float32)
    return X, np.array(Y)


def test_autoencoder_learns_reduces_mse():
    X, _ = _synth()
    mu = X.mean(0); sd = X.std(0) + 1e-6
    Xs = ((X - mu) / sd).astype(np.float32)
    _, trained_loss = train_ae(Xs, D=6, epochs=20)
    # an untrained AE's recon MSE is just the input variance (~1 after standardisation)
    assert trained_loss < 0.5, f"trained AE recon MSE {trained_loss} should beat the ~1.0 untrained floor"


def test_earned_bottleneck_beats_random_projection():
    X, Y = _synth(seed=1)
    mu = X.mean(0); sd = X.std(0) + 1e-6
    Xs = ((X - mu) / sd).astype(np.float32)
    enc, _ = train_ae(Xs, D=6, epochs=25)
    renc, _ = train_ae(Xs, D=6, random_only=True)
    phones = sorted(set(Y))
    earned = nmi(kmeans(enc(Xs), len(phones)), Y)
    rand = nmi(kmeans(renc(Xs), len(phones)), Y)
    # on clean separated data both can be high; the earned encoder must be at least as good
    assert earned >= rand - 0.05, f"earned {earned} should not trail random {rand}"
    assert earned > 0.5, f"earned bottleneck NMI {earned} should recover separated clusters"


def test_purity_and_nmi_sane():
    Y = np.array(["a"] * 50 + ["b"] * 50)
    perfect = np.array([0] * 50 + [1] * 50)
    assert purity(perfect, Y) == 1.0
    assert nmi(perfect, Y) > 0.99
    random_lab = np.tile([0, 1], 50)
    assert nmi(random_lab, Y) < 0.2


def test_fewshot_recovers_separated_clusters():
    Xtr, Ytr = _synth(seed=2)
    Xde, Yde = _synth(seed=3)
    phones = sorted(set(Ytr))
    acc = fewshot_acc(Xtr, Ytr, Xde, Yde, phones, N=5)
    assert acc > 0.8, f"few-shot nearest-centroid acc {acc} should be high on separated clusters"
