"""Deploy the agent's AUTHORED recogniser — compile its draft and route
recognition through it.

The agent authored a `recognise_specialised` pass (its own commission, when the
meta-monitor flagged feature-spam spinning). This is the last leg of the loop:
compile that Rust draft to a cdylib and call it from recognition, with the agent's
LEARNED data marshalled in — the confused pairs + the per-pair discriminating
band/threshold it minted as discriminative hypotheses. The agent authored the
ALGORITHM; its babble-loop learned the DATA; deploy runs them together.

`compile_and_deploy(source)` rustc's the draft; `apply(sub, score, signs)` is
called inside predict_one after the global signature — it promotes, for any
confused top-2 pair, the side the pair's learned feature points to. No-op until a
draft is deployed, so the recognition path is unchanged otherwise.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import tempfile

_STATE: dict = {"fn": None, "lib": None, "error": None}


def compile_and_deploy(source: str) -> bool:
    """rustc the authored draft into a cdylib and bind `recognise_specialised`.
    Returns True on success; stashes the compiler error otherwise."""
    try:
        d = tempfile.mkdtemp(prefix="ozma_recog_")
        rs = os.path.join(d, "lib.rs")
        so = os.path.join(d, "librecog.so")
        with open(rs, "w") as f:
            f.write(source)
        r = subprocess.run(["rustc", "--crate-type", "cdylib", "-O", rs,
                            "-o", so], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            _STATE["error"] = r.stderr
            return False
        lib = ctypes.CDLL(so)
        fn = lib.recognise_specialised
        fn.restype = None
        fn.argtypes = [
            ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,        # scores, n
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),  # a,b
            ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),     # obs,thr
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,        # high_a, npairs
        ]
        _STATE.update(fn=fn, lib=lib, error=None)
        return True
    except Exception as e:                       # noqa: BLE001
        _STATE["error"] = str(e)
        return False


def is_deployed() -> bool:
    return _STATE.get("fn") is not None


def last_error():
    return _STATE.get("error")


def apply(substrate, score: dict, signs) -> None:
    """Route this recognition through the agent's deployed recogniser: marshal the
    word scores + the learned per-pair features, call the compiled pass, read the
    adjusted scores back into `score`. No-op if nothing is deployed."""
    fn = _STATE.get("fn")
    if fn is None or not signs:
        return
    import scripts.fsdd_learner_world as fl
    from domains.acoustic_resolution import enrich_sign_bands
    enrich_sign_bands(substrate, signs=signs)            # ensure band attrs present
    word_to_digit = {v: k for k, v in fl._DIGITS.items()}
    n = 10
    scores = [-1.0e9] * n
    for w, sc in score.items():
        i = word_to_digit.get(w)
        if i is not None:
            scores[i] = float(sc)

    pa, pb, pobs, pthr, phigh = [], [], [], [], []
    for h in substrate.nodes("MismatchHypothesis"):
        a = substrate.node(h)["attrs"]
        if a.get("kind") != "discriminative_feature_needed":
            continue
        ai, bi = word_to_digit.get(a.get("true_word")), word_to_digit.get(a.get("pred_word"))
        if ai is None or bi is None:
            continue
        band = a.get("discriminating_band")
        vals = [substrate.node(s)["attrs"].get(band)
                for s in signs if band in substrate.node(s)["attrs"]]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        pa.append(ai)
        pb.append(bi)
        pobs.append(sum(vals) / len(vals))
        pthr.append(float(a.get("threshold", 0.0)))
        phigh.append(1 if a.get("high_word") == a.get("true_word") else 0)
    if not pa:
        return

    npairs = len(pa)
    sc_arr = (ctypes.c_float * n)(*scores)
    fn((sc_arr), n,
       (ctypes.c_uint32 * npairs)(*pa), (ctypes.c_uint32 * npairs)(*pb),
       (ctypes.c_float * npairs)(*pobs), (ctypes.c_float * npairs)(*pthr),
       (ctypes.c_uint8 * npairs)(*phigh), npairs)
    for w, i in word_to_digit.items():
        if 0 <= i < n:
            score[w] = float(sc_arr[i])


__all__ = ["compile_and_deploy", "is_deployed", "last_error", "apply"]
