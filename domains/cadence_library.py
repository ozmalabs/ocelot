"""CadenceLibrary — bank cadence ARCS (contour windows + their follower) across TRAINING speakers.

The repetition-free move, second route. The same-stream RECALL predictor matches the contour-so-far against
EARLIER windows of the SAME stream -- repetition-hungry (song > read). This banks (window -> follower) arcs from a
set of OTHER speakers, so a test stream's cadence is predicted by recalling the nearest UNIVERSAL prosodic shape,
not its own repeats. Mechanical I/O only: it slices z-normalised contours into fixed-length arcs and stores them;
the DECISION (match a test window to the nearest held arc, predict the follower) is the same recall predictor
pointed at the held bank instead of the same stream. Cross-speaker, so repetition-free by construction.

Windows are euclidean-flattened (W*3 vector) for a vectorised nearest-arc query over the whole bank at once.
Contours are z-normalised per stream (the agent's contour_from_audio), so matching is on prosodic SHAPE -- a
speaker's absolute rate/pitch is normalised out, the arc that remains is what transfers across speakers.
"""
from __future__ import annotations

import numpy as np

W = 5


class CadenceLibrary:
    def __init__(self, w: int = W):
        self.w = int(w)
        self.windows = np.zeros((0, self.w * 3))   # (N, W*3) flattened arcs
        self.followers = np.zeros((0, 3))          # (N, 3) the element that FOLLOWED each arc

    def bank(self, contours):
        """Slice each z-normalised contour into (window[i-W+1..i] -> follower[i+1]) arcs; append to the bank."""
        ws, fs = [], []
        for c in contours:
            if c is None or len(c) < self.w + 2:
                continue
            c = np.asarray(c)
            for i in range(self.w - 1, len(c) - 1):
                ws.append(c[i - self.w + 1:i + 1].reshape(-1))
                fs.append(c[i + 1])
        if ws:
            self.windows = np.vstack([self.windows, np.array(ws)])
            self.followers = np.vstack([self.followers, np.array(fs)])
        return len(ws)

    def subsample(self, cap, seed=0):
        if len(self.windows) > cap:
            idx = np.random.RandomState(seed).permutation(len(self.windows))[:cap]
            self.windows, self.followers = self.windows[idx], self.followers[idx]
        return len(self.windows)

    def predict_follower(self, window_flat, k=1):
        """k nearest held arcs -> distance-weighted mean follower (universal-shape recall; k>1 denoises)."""
        d = ((self.windows - window_flat[None, :]) ** 2).sum(1)
        if k <= 1:
            return self.followers[int(np.argmin(d))]
        idx = np.argpartition(d, min(k, len(d) - 1))[:k]
        wts = 1.0 / (d[idx] + 1e-9)
        return (self.followers[idx] * wts[:, None]).sum(0) / wts.sum()

    def __len__(self):
        return len(self.windows)

    def save(self, path):
        np.savez(path, windows=self.windows, followers=self.followers, w=self.w)

    @classmethod
    def load(cls, path):
        z = np.load(path)
        lib = cls(int(z["w"]))
        lib.windows, lib.followers = z["windows"], z["followers"]
        return lib
