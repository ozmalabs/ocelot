"""SOURCE WORLD — one window onto ARBITRARY media sources for the agent to learn speech from.

A world adapter (mechanical external-I/O -> samples, per CLAUDE.md). It merges:
  · Jellyfin  — the curated children's library (Sesame Street + more), streamed over HTTP
  · local dirs — the YouTube dumps (/tmp/nursery/vids/*.mp4 + /tmp/nursery/*.{wav,mp3,ogg})
  · (optional) LibriSpeech and any extra directory you point it at
behind ONE interface, so the agent can pick any source and the autonomous loop never cares
where the audio came from. No decisions over graph state — pure enumeration + extraction.

    w = SourceWorld()
    for s in w.sources(): ...           # [{id, kind, name, origin, ...}]
    a8 = w.play(src, t0, t1)            # 8 kHz mono np.float64 (what the ear ingests)
    words = w.whisper(src, t0, t1)      # the help button: [(word, t0, t1)]
    frames = w.frames(src, t0, t1)      # grayscale frames, only if vision is attached
"""
from __future__ import annotations
import glob
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import soundfile as sf
from scipy.signal import resample_poly

from scripts.jellyfin_world import JellyfinWorld

_AUDIO_EXT = (".wav", ".mp3", ".ogg", ".m4a", ".flac")
_VIDEO_EXT = (".mp4", ".mkv", ".webm", ".mov", ".avi")
DEFAULT_LOCAL_DIRS = ("/tmp/nursery/vids", "/tmp/nursery")


class SourceWorld:
    def __init__(self, local_dirs=DEFAULT_LOCAL_DIRS, include_jellyfin=True,
                 jellyfin_kinds=("Series",), whisper_model="base.en"):
        self.local_dirs = [d for d in local_dirs if os.path.isdir(d)]
        self.include_jellyfin = include_jellyfin
        self.jellyfin_kinds = jellyfin_kinds
        self._jf = None
        self._ep_cache = {}                # series_id -> (stream_url, duration_s)
        self._dur_cache = {}
        self._wm = None
        self._whisper_model = whisper_model

    # ---- catalogue (mechanical enumeration) ----
    def _jf_conn(self):
        if self._jf is None and self.include_jellyfin:
            try:
                self._jf = JellyfinWorld().connect()
            except Exception:
                self._jf = False          # mark unavailable
        return self._jf or None

    def sources(self, kinds=("video", "audio")):
        out = []
        jf = self._jf_conn()
        if jf is not None:
            for it in jf.catalog(self.jellyfin_kinds):
                out.append({"id": f"jf:{it['id']}", "kind": "video", "name": it["name"],
                            "origin": "jellyfin", "series_id": it["id"],
                            "genres": it.get("genres", [])})
        seen = set()
        for d in self.local_dirs:
            for p in sorted(glob.glob(os.path.join(d, "*"))):
                ext = os.path.splitext(p)[1].lower()
                if p in seen or not os.path.isfile(p):
                    continue
                kind = "video" if ext in _VIDEO_EXT else "audio" if ext in _AUDIO_EXT else None
                if kind is None:
                    continue
                seen.add(p)
                out.append({"id": f"local:{p}", "kind": kind, "name": os.path.basename(p),
                            "origin": "local", "uri": p})
        return [s for s in out if s["kind"] in kinds]

    # ---- resolve a source to an ffmpeg-openable URI (path or HTTP) ----
    def _uri(self, source):
        if source["origin"] == "local":
            return source["uri"]
        jf = self._jf_conn()
        sid = source["series_id"]
        if sid not in self._ep_cache:
            eps = jf.episodes(sid, limit=1)
            if not eps:
                raise RuntimeError(f"no episodes for {source['name']}")
            self._ep_cache[sid] = (jf.stream_url(eps[0]["id"]),
                                   float(eps[0].get("runtime_s") or 0.0))
        return self._ep_cache[sid][0]

    def duration(self, source):
        sid = source["id"]
        if sid in self._dur_cache:
            return self._dur_cache[sid]
        if source["origin"] == "jellyfin":
            self._uri(source)
            d = self._ep_cache[source["series_id"]][1]
        else:
            d = _ffprobe_duration(source["uri"])
        self._dur_cache[sid] = d
        return d

    # ---- extraction (mechanical I/O) ----
    def _extract(self, source, t0, t1, sr):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t0:.2f}",
                        "-i", self._uri(source), "-map", "0:a:0?", "-t", f"{max(0.1, t1-t0):.2f}",
                        "-ar", str(sr), "-ac", "1", path], check=True)
        a, _ = sf.read(path); os.unlink(path)
        return a.astype(np.float64)

    def play(self, source, t0, t1):
        """HEAR a selection: 8 kHz mono (what the held cochlea ingests)."""
        a16 = self._extract(source, t0, t1, sr=16000)
        if a16.size == 0:
            return np.zeros(0)
        return resample_poly(a16, 8000, 16000)

    def whisper(self, source, t0, t1):
        """The HELP BUTTON: Whisper transcript with word timestamps (rel. to t0)."""
        import re
        if self._wm is None:
            from faster_whisper import WhisperModel
            self._wm = WhisperModel(self._whisper_model, device="cpu", compute_type="int8")
        a16 = self._extract(source, t0, t1, sr=16000)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        sf.write(path, a16, 16000)
        segs, _ = self._wm.transcribe(path, language="en", word_timestamps=True)
        words = []
        for sg in segs:
            for w in (sg.words or []):
                nw = re.sub(r"[^a-z']", "", w.word.lower())
                if nw:
                    words.append((nw, float(w.start), float(w.end)))
        os.unlink(path)
        return words

    def frames(self, source, t0, t1, size=64, fps=4):
        """Grayscale frames (only used when the agent attaches vision)."""
        out = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.2f}", "-i", self._uri(source),
             "-t", f"{max(0.1, t1-t0):.2f}", "-map", "0:v:0?", "-vf",
             f"fps={fps},scale={size}:{size},format=gray", "-f", "rawvideo", "pipe:1"],
            capture_output=True)
        buf = np.frombuffer(out.stdout, np.uint8)
        n = buf.size // (size * size)
        if n == 0:
            return np.zeros((0, size, size), np.float32)
        return buf[:n * size * size].reshape(n, size, size).astype(np.float32)


def _ffprobe_duration(uri):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "json", uri], capture_output=True, text=True, timeout=30)
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def main():
    w = SourceWorld()
    srcs = w.sources()
    print("=" * 76)
    print("SOURCE WORLD — unified media for autonomous speech learning")
    by = {}
    for s in srcs:
        by.setdefault(s["origin"], []).append(s)
    for origin, items in by.items():
        print(f"  {origin:>9}: {len(items)} sources  e.g. " +
              ", ".join(i["name"][:22] for i in items[:4]))
    print("=" * 76)
    local = next((s for s in srcs if s["origin"] == "local" and s["kind"] == "video"), None)
    jf = next((s for s in srcs if s["origin"] == "jellyfin"), None)
    for tag, s in (("local", local), ("jellyfin", jf)):
        if not s:
            print(f"  ({tag}: none available)"); continue
        dur = w.duration(s)
        a8 = w.play(s, 5.0, 9.0)
        print(f"  {tag}: {s['name'][:30]:<30} dur={dur:.0f}s  played {len(a8)} samples @8k")
    if local:
        words = w.whisper(local, 0.0, 12.0)
        print(f"  whisper({local['name'][:24]}, 0-12s): "
              f"{' '.join(wd for wd, *_ in words[:14])}")
    print("=" * 76)


if __name__ == "__main__":
    main()
