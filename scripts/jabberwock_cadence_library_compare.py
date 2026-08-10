"""READ-trained vs AMI-trained cadence library — is the universal cadence DOMAIN-specific or truly universal?

The held library read held-out READ speakers (+30%) and even SPONTANEOUS speakers cross-domain (+26%). But the
library was banked from READ speech. This banks a SECOND library from SPONTANEOUS (AMI) speakers and runs the full
2x2: {READ-lib, AMI-lib} x {READ-test, SPONTANEOUS-test}, with AR (no library, the stream's own dynamics) as the
domain-free baseline. The questions:
  - IN-DOMAIN vs CROSS-DOMAIN: does AMI-lib read AMI-test better than READ-lib does (does domain-matched banking
    help)? Does READ-lib read READ-test better than AMI-lib does?
  - UNIVERSALITY: if cross-domain barely costs anything, the cadence arcs are genuinely universal, not a register
    artifact -- a library banked from one speaking style reads another.
Test speakers are DISJOINT from every library's training speakers (READ: held-out LibriSpeech; AMI-test = the TS
meeting group, AMI-lib trained only on the ES + IS groups -- no same-meeting leakage). Both libraries capped to the
same arc count for a fair k-NN comparison. Second-half evaluation, same metric as the library experiment.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cadence_library_compare
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains.cadence_library import CadenceLibrary, W
from scripts.jabberwock_cadence_predictor import ar_fit, P
from scripts.jabberwock_cadence_library import (LIB_PATH, all_speakers, speaker_streams, shuffled_persist,
                                                N_TRAIN, N_TEST, KNN)
from scripts.jabberwock_cadence_spontaneous import spontaneous_contours

AMI_LIB_PATH = "/home/matt/data/cadence_library_ami.npz"
AMI_TEST_GROUP = "TS3003a"     # held-out AMI meeting group (AMI-lib trains on the others -> no same-meeting leak)


def ami_library_and_test(cap=None, rebuild=False):
    """Bank an AMI (spontaneous) library from the ES+IS groups; return (library, held-out TS test contours).

    The library is the in-domain spontaneous bank; the TS group is disjoint (no same-meeting leak). Cached.
    """
    ami_all = spontaneous_contours()
    ami_train = [(l, c) for l, c in ami_all if not l.startswith(AMI_TEST_GROUP)]
    ami_test = [(l, c) for l, c in ami_all if l.startswith(AMI_TEST_GROUP)]
    if os.path.exists(AMI_LIB_PATH) and not rebuild and cap is None:
        return CadenceLibrary.load(AMI_LIB_PATH), ami_test
    lib = CadenceLibrary()
    lib.bank([c for _l, c in ami_train])
    if cap:
        lib.subsample(cap)
    lib.save(AMI_LIB_PATH)
    return lib, ami_test


def lib_skill(c, lib, sh):
    """Held-library k-NN prediction skill over chance on the second half of c."""
    n = len(c); start = max(W + 1, n // 2)
    errs = [np.abs(lib.predict_follower(c[k - W + 1:k + 1].reshape(-1), k=KNN) - c[k + 1]).mean()
            for k in range(start, n - 1)]
    return max(0.0, (sh - float(np.mean(errs))) / max(sh, 1e-9) * 100)


def ar_skill(c, sh):
    n = len(c); start = max(W + 1, n // 2)
    ars = [ar_fit(c[:start, d], P) for d in range(3)]
    errs = [np.abs(np.array([np.dot(ars[d], c[k - P + 1:k + 1, d][::-1]) for d in range(3)]) - c[k + 1]).mean()
            for k in range(start, n - 1)]
    return max(0.0, (sh - float(np.mean(errs))) / max(sh, 1e-9) * 100)


def mean_skill(test, read_lib, ami_lib):
    rl, al, ar = [], [], []
    for _label, c in test:
        sh = shuffled_persist(c)
        rl.append(lib_skill(c, read_lib, sh))
        al.append(lib_skill(c, ami_lib, sh))
        ar.append(ar_skill(c, sh))
    return float(np.mean(rl)), float(np.mean(al)), float(np.mean(ar))


def main():
    print("=" * 100)
    print("READ-trained vs AMI-trained cadence library — is the universal cadence domain-specific?")
    print("=" * 100)

    read_lib = CadenceLibrary.load(LIB_PATH)

    # Build the AMI-trained library from the ES + IS meeting groups; hold out the TS group for testing.
    ami_lib, ami_test = ami_library_and_test(rebuild=True)
    cap = min(len(read_lib), len(ami_lib))
    read_lib.subsample(cap); ami_lib.subsample(cap)            # equal arc count -> fair k-NN
    ami_lib.save(AMI_LIB_PATH)
    print(f"  READ-lib {len(read_lib)} arcs (LibriSpeech) | AMI-lib {len(ami_lib)} arcs (AMI ES+IS), "
          f"both capped to {cap}")

    read_test = speaker_streams(all_speakers()[N_TRAIN:N_TRAIN + N_TEST])
    print(f"  READ-test {len(read_test)} held-out LibriSpeech | SPONTANEOUS-test {len(ami_test)} held-out AMI "
          f"({AMI_TEST_GROUP})\n")

    r_rl, r_al, r_ar = mean_skill(read_test, read_lib, ami_lib)
    s_rl, s_al, s_ar = mean_skill(ami_test, read_lib, ami_lib)

    print("  held-library prediction skill over chance (cadence-beats-shuffle %), by train-domain x test-domain:")
    print(f"    {'':16}{'READ-test':>14}{'SPONTANEOUS-test':>20}")
    print(f"    {'READ-lib':16}{r_rl:>13.0f}%{s_rl:>19.0f}%")
    print(f"    {'AMI-lib':16}{r_al:>13.0f}%{s_al:>19.0f}%")
    print(f"    {'AR (no lib)':16}{r_ar:>13.0f}%{s_ar:>19.0f}%   <- domain-free baseline")

    print("\n" + "=" * 100)
    in_read, cross_read = r_rl, r_al        # READ-test: in-domain (read-lib) vs cross (ami-lib)
    in_spon, cross_spon = s_al, s_rl        # SPON-test: in-domain (ami-lib) vs cross (read-lib)
    in_gain = ((in_read - cross_read) + (in_spon - cross_spon)) / 2
    if in_gain > 4:
        print(f"  DOMAIN-MATCHED BANKING HELPS: the in-domain library leads by ~{in_gain:.0f}% on average (READ-test")
        print(f"  read-lib {in_read:.0f}% vs ami-lib {cross_read:.0f}%; SPON-test ami-lib {in_spon:.0f}% vs read-lib {cross_spon:.0f}%).")
        print("  Cadence arcs carry a register signature -- a library banked in the test's own style reads it best.")
    elif abs(in_gain) <= 4 and min(r_rl, r_al, s_rl, s_al) > 8:
        print(f"  THE CADENCE IS GENUINELY UNIVERSAL: cross-domain costs ~{abs(in_gain):.0f}% -- a library banked from ONE")
        print(f"  speaking style reads the OTHER nearly as well as its own (READ-test read-lib {r_rl:.0f}% vs ami-lib")
        print(f"  {r_al:.0f}%; SPON-test ami-lib {s_al:.0f}% vs read-lib {s_rl:.0f}%). The arcs are a register-independent")
        print("  prosodic shape, not a corpus artifact -- one held library transfers across speaking styles.")
    else:
        print(f"  MIXED: in-domain edge ~{in_gain:.0f}%; read both lower than spontaneous or vice-versa. See the table.")
    print("=" * 100)


if __name__ == "__main__":
    main()
