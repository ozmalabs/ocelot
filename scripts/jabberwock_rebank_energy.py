"""RE-BANK the phonebank WITH the per-frame ENERGY channel (the free first step).

The phone-gap decomposition (commit 1afd6698) found the per-frame phone model FEATURE-BOUND and
surfaced that the banked shards /home/matt/data/phonebank/*.pkl predate the energy channel — they
are 3-tuples (word, frames, phones), has_energy=False. The FREE energy win (commit 343d8c81:
phonebank.feed writes a 4th element en; ctxd(M,e) appends a log-energy+delta channel; _load_ph
with_energy surfaces it) is therefore NOT in the bank. This re-banks WITH energy so the default
phone model actually CONSUMES it.

SCOPE: re-banking the FULL 113+13 shards re-runs torchaudio forced-alignment over all of
LibriSpeech (~hours). This re-banks a SUFFICIENT SUBSET into a FRESH dir (the legacy shape-only
bank is left untouched) — enough train shards for one data-scale point + one dev shard for the
held-out — and reports the bound honestly. The bank is regenerable data (NOT committed).

MEMORY-SAFE: phonebank.feed already STREAMS per-utterance and dumps a shard every 4000 words
(buffer freed). The aligner model loads once. Run under ulimit -v ~12G. meta.pkl (test speakers +
targets) is energy-independent and is COPIED from the legacy bank so _meta() does not re-align all
of dev just to recompute targets.

Commands:
  rebank <n_train_utts> <n_dev_utts>   force-align a subset, write 4-tuple (w,fr,ph,en) shards.
  verify                               confirm the re-banked shards are 4-tuples with energy != None.
  measure <scale>                      default shallow phone model WITH energy vs energy-ABLATED on
                                       the SAME re-banked data (isolates the energy channel) +
                                       relate to the decomposition's shape-only 0.151.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_rebank_energy.py rebank 1500 160
"""
from __future__ import annotations
import os, sys, time, glob, pickle, shutil, gc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np

ENERGY_DIR = "/home/matt/data/phonebank_energy"
LEGACY = "/home/matt/data/phonebank"
LS = "/home/matt/data/LibriSpeech"


def _point_phonebank_at_energy_dir():
    """Redirect the bank modules at the fresh energy dir (mechanical I/O config — no decision)."""
    import scripts.phonebank as pb
    import scripts.jabberwock_subword_recognizer as sr
    os.makedirs(ENERGY_DIR, exist_ok=True)
    pb.CACHE = ENERGY_DIR
    pb.META = os.path.join(ENERGY_DIR, "meta.pkl")
    sr.BANK = ENERGY_DIR
    return pb, sr


def rebank(n_train, n_dev):
    pb, _sr = _point_phonebank_at_energy_dir()
    # reuse the legacy meta (test speakers + target words are energy-independent)
    if os.path.exists(os.path.join(LEGACY, "meta.pkl")) and not os.path.exists(pb.META):
        shutil.copy(os.path.join(LEGACY, "meta.pkl"), pb.META)
        print(f"  copied legacy meta.pkl -> {pb.META} (targets/test-speakers reused, energy-independent)")
    t0 = time.time()
    print("=" * 90)
    print(f"RE-BANK WITH ENERGY into {ENERGY_DIR}  (train={n_train} utts, dev={n_dev} utts)")
    print("=" * 90, flush=True)
    pb.feed(os.path.join(LS, "train-clean-100"), int(n_train), 0)
    print(f"  [train done {time.time()-t0:.0f}s]", flush=True)
    pb.feed(os.path.join(LS, "dev-clean"), int(n_dev), 1)
    print(f"  [all done {time.time()-t0:.0f}s]", flush=True)
    verify()


def verify():
    pb, sr = _point_phonebank_at_energy_dir()
    print("=" * 90)
    print("VERIFY re-banked shards carry the energy channel")
    print("=" * 90)
    shards = sorted(glob.glob(os.path.join(ENERGY_DIR, "*_*.pkl")))
    print(f"  energy-dir shards: {len(shards)}")
    tr = [s for s in shards if "train-clean-100_" in s]
    dv = [s for s in shards if "dev-clean_" in s]
    print(f"    train shards: {len(tr)}   dev shards: {len(dv)}")
    if not shards:
        print("  NO shards — run `rebank` first.")
        return False
    s0 = pickle.load(open(shards[0], "rb"))
    e0 = s0[0]
    print(f"  shard0 words={len(s0)}  tuple_len={len(e0)}")
    # has_energy as the consumers see it (_load_ph with_energy=True)
    w = sr._load_ph("train-clean-100_*.pkl", 1, with_energy=True)
    has_energy = bool(w) and w[0][3] is not None
    print(f"  _load_ph(with_energy=True)[0]: word={w[0][0]!r} frames={w[0][1].shape} "
          f"phones={w[0][2]} energy_shape={None if w[0][3] is None else w[0][3].shape}")
    print(f"  has_energy=True : {has_energy}")
    # legacy bank for contrast
    import scripts.jabberwock_subword_recognizer as sr2
    sr2.BANK = LEGACY
    wl = sr2._load_ph("train-clean-100_*.pkl", 1, with_energy=True)
    print(f"  (legacy bank has_energy: {bool(wl) and wl[0][3] is not None})")
    sr2.BANK = ENERGY_DIR
    return has_energy


def measure(scale):
    """Default shallow phone model: energy-ON (ctxd(M,e)) vs energy-ABLATED (ctxd(M)) on the
    SAME re-banked data — the cleanest control isolating the banked energy channel. Reuses the
    decomposition's memory-bounded fit/align so the model is the project's actual default."""
    scale = int(scale)
    pb, sr = _point_phonebank_at_energy_dir()
    import scripts.jabberwock_decompose_phone_gap as D
    from collections import Counter
    print("=" * 90)
    print(f"MEASURE default shallow phone model  energy-ON vs energy-OFF  (scale={scale} words)")
    print("=" * 90, flush=True)

    # enough train shards for the scale (4000 words/shard; +1 margin)
    cap = max(1, scale // 4000 + 2)
    t0 = time.time()
    all_words = D._load_ph("train-clean-100_*.pkl", cap, with_energy=True)
    has_e = bool(all_words) and all_words[0][3] is not None
    print(f"  loaded {len(all_words)} banked words ({cap} shards)  energy-in-bank={has_e}  [{time.time()-t0:.0f}s]")
    if not has_e:
        print("  ABORT: energy not in bank — rebank first."); return False
    scale = min(scale, len(all_words))
    words = all_words[:scale]
    phones_set = sorted({p for _w, _f, ph, _e in all_words for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}
    nP = len(phones_set)

    # held-out dev (proportional-label per-frame acc proxy — exactly the decomposition's dev)
    dev = D._load_ph("dev-clean_*.pkl", 3, with_energy=True)

    def dev_block(use_energy):
        Xl, Yl = [], []
        for (_w, fr, ph, en) in dev[:1500]:
            cx = D._feat(fr, en, use_energy)
            n = len(cx); Pn = len(ph)
            for i in range(n):
                p = ph[int(i * Pn / n)]
                if p in pi:
                    Xl.append(cx[i]); Yl.append(pi[p])
        return np.asarray(Xl, np.float32), Yl

    # phone-class accuracy split: stops vs fricatives (the channel energy should help most)
    STOPS = {"P", "B", "T", "D", "K", "G"}
    FRIC = {"F", "V", "S", "Z", "SH", "ZH", "TH", "DH", "HH", "CH", "JH"}

    def run(use_energy):
        X, Yidx = D.bootstrap_align(words, phones_set, pi, use_energy)
        enc, cent, cph = D.fit_model_mem(X, Yidx, phones_set, pi)
        Xde, Yde = dev_block(use_energy)
        pred = cph[(enc(Xde) @ cent.T).argmax(1)]
        Yde = np.asarray(Yde)
        acc = float(np.mean(pred == Yde))
        inv = {i: p for p, i in pi.items()}
        def cls_acc(cset):
            m = np.array([inv[int(y)] in cset for y in Yde])
            return float(np.mean(pred[m] == Yde[m])) if m.any() else float("nan"), int(m.sum())
        st, stn = cls_acc(STOPS); fr_, frn = cls_acc(FRIC)
        dim = Xde.shape[1]
        del X, Yidx, enc, cent, cph, Xde; gc.collect()
        return acc, st, stn, fr_, frn, dim, len(Yde)

    chance_blkX, chance_blkY = dev_block(True)
    n_dev = len(chance_blkY)
    chance = max(Counter(chance_blkY).values()) / n_dev
    del chance_blkX, chance_blkY; gc.collect()
    print(f"  phones={nP}  dev frames={n_dev}  chance(majority)={chance:.3f}", flush=True)

    t1 = time.time()
    off = run(False)
    print(f"  energy-OFF (shape-only ctxd(M))   acc {off[0]:.3f}  stops {off[1]:.3f}(n={off[2]}) "
          f"fric {off[3]:.3f}(n={off[4]})  dim={off[5]}  [{time.time()-t1:.0f}s]", flush=True)
    t2 = time.time()
    on = run(True)
    print(f"  energy-ON  (ctxd(M,e))            acc {on[0]:.3f}  stops {on[1]:.3f}(n={on[2]}) "
          f"fric {on[3]:.3f}(n={on[4]})  dim={on[5]}  [{time.time()-t2:.0f}s]", flush=True)
    print("=" * 90)
    print(f"  ENERGY LIFT (same data, default model): acc {on[0]-off[0]:+.3f}  "
          f"stops {on[1]-off[1]:+.3f}  fric {on[3]-off[3]:+.3f}")
    print(f"  reference: decomposition shape-only banked point ~0.151 (16k words, commit 1afd6698)")
    print(f"  donkey=0: per-frame decision is argmax (graph-native Dot/topk); no LLM, no borrowed weights.")
    print("=" * 90)
    return True


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "rebank":
        rebank(sys.argv[2] if len(sys.argv) > 2 else 1500,
               sys.argv[3] if len(sys.argv) > 3 else 160)
    elif len(sys.argv) >= 2 and sys.argv[1] == "verify":
        verify()
    elif len(sys.argv) >= 2 and sys.argv[1] == "measure":
        measure(sys.argv[2] if len(sys.argv) > 2 else 16000)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
