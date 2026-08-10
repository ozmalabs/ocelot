"""VIDEO ACCUMULATION — BRING-UP PILOT. Seeds 74900-74999, DECLARED BURNED.

Not a measurement. Checks that (a) the split is what the pre-registration says,
(b) an installed codebook behaves like a grown one, (c) the freeze holds K and
the floor fixed across a pass. No arm, no headline, tiny N.
"""
from __future__ import annotations

import importlib.util as iu
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains import video_accumulation_world as aw  # noqa: E402


def _vp():
    spec = iu.spec_from_file_location("vp", str(HERE / "video_probe_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


print(ep.provenance_line())

train, held = aw.block_split(150)
print(f"split: train={len(train)} held={len(held)} "
      f"overlap={len(set(train)&set(held))}")
print(f"  train head {train[:14]}")
print(f"  held  head {held[:14]}")

vp = _vp()
frames, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=aw.GRID,
                                  episode_index=0)
print(f"corpus C1 episode={meta.get('episode_id')} n={len(frames)}")
steps, thr, cuts = aw.cut_flags(frames)
print(f"otsu={thr:.4f} cuts_at={[t for t,c in enumerate(cuts) if c]}")

q = [aw.quantize(f) for f in frames]
qr = [aw.regions_of(x) for x in q]
gr = [aw.grey_regions_of(f) for f in frames]

# ---- (b) grow a tiny codebook -----------------------------------------
rng = np.random.RandomState(74900)
w = aw.AccumWorld("ncc")
w.calibrate(rng, 8)
w.run()
t0 = time.time()
mints = []
for t in train[:12]:
    for i in range(16):
        k0 = w.codebook_size()
        w.present(qr[t][i], gr[t][i], tag=f"{t}_{i}")
        w.run()
        if w.codebook_size() > k0:
            mints.append((t, i))
print(f"grow: K={w.codebook_size()} mints={len(mints)} "
      f"({time.time()-t0:.1f}s for {12*16} obs)")

# ---- (c) install the SAME entries into a fresh world -------------------
rng2 = np.random.RandomState(74901)
w2 = aw.AccumWorld("ncc")
w2.calibrate(rng2, 8)
w2.run()
w2.install_codebook([(f"{t}_{i}", qr[t][i], gr[t][i]) for t, i in mints])
print(f"install: K={w2.codebook_size()}")

# ---- freeze + eval pass -----------------------------------------------
nfroz = w2.freeze()
print(f"freeze: K={nfroz} floor={w2._frozen_floor}")
acc, scores = [], []
t0 = time.time()
for t in held[:10]:
    for i in range(16):
        w2.present(qr[t][i], gr[t][i], tag=f"ev_{t}_{i}")
        w2.run()
        r = w2.read_full()
        w2.refreeze()
        acc.append(0.0 if r["status"] == "is_novel" else 1.0)
        scores.append(float(r["is_max"]))
k, f = w2.assert_frozen()
print(f"eval: n={len(acc)} accept={np.mean(acc):.4f} "
      f"mean_is_max={np.mean(scores):.4f} ({time.time()-t0:.1f}s)")
print(f"FREEZE GATE OK: K={k} floor={f}")
