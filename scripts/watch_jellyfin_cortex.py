"""WATCH JELLYFIN WITH PROPER CORTEX MANAGEMENT — audio + video as SEPARATE
cortexes, on SEPARATE THREADS, with SEPARATE INDEPENDENT TICKS that AGREE ON
TIMING via a shared master clock.

The old scripts/watch_jellyfin.py and scripts/autonomous_watch.py ingest audio
THEN video SEQUENTIALLY on ONE thread — bypassing the substrate's cortex
machinery. This rebuilds the watcher to USE that machinery:

  MASTER CLOCK   — the stream position (seconds into the title). The substrate's
                   CortexScheduler holds the absolute clock; both cortexes
                   timestamp every output on it, so they AGREE ON TIMING
                   without sharing a tick.

  AUDIO CORTEX   — its OWN threading.Thread (concurrency.py posture: a module
                   on its own OS thread, real CPU parallelism via the Rust GIL
                   release). Ticks at its OWN rhythm (~tick_period_ms ≈ 80 ms);
                   each tick pulls its audio chunk (ffmpeg→opus over HTTP, no
                   download), runs the auditory front-end (cochlea/A1 via
                   ingest_speech) → AcousticSign / Utterance, timestamped on the
                   master clock. THIS is auditory_cortex.py's pipeline, run live.

  VIDEO CORTEX   — its OWN threading.Thread. Ticks at its OWN, DIFFERENT rhythm
                   (~tick_period_ms ≈ 160 ms / per-frame). Each tick pulls its
                   frame window (PyAV demux over HTTP) → Frame + MotionVector
                   temporal STRUCTURE, timestamped on the master clock.
                   (HONEST: this reads codec temporal structure, not the Eye's
                   decoded pixels — the library is HEVC and the agent's own
                   decoder is H.264-only; vision.py's GraphEye would need a
                   decode step. The cortex still runs on its own thread/tick.)

  EFFORT DIAL    — substrate_rs.EffortDial, per cortex, in REAL-TIME mode. The
                   watcher must keep up with the stream, so each cortex's
                   per-tick processing DEPTH (order-N passes + salience
                   threshold) is set by the dial against its tick DEADLINE: fall
                   behind → dial down; spend more on salient ticks.

  MEMORY FACULTY — substrate.memory_bound + memory_forget_over_budget (streaming,
                   in-tick) + memory_observe_and_bound (end-of-title persist).
                   Keeps node_count + bytes bounded over the whole run (no OOM).

  TIMING AGREEMENT — a thin master-thread sync pass links each Utterance to the
                   co-temporal Frames via synchronous_with on the shared master
                   clock (the teach_video_concept.py binding), proving the two
                   independent-tick cortexes agree on WHEN.

Both cortexes write into ONE shared substrate (the shared graph). Concurrent
add_node/add_edge from two threads is serialised safely at the PyO3 layer
(verified). The DECISIONS (effort, keep/forget, what to process) are the
substrate's; this file is the world-adapter loop that drives them.

Run:  python -m scripts.watch_jellyfin_cortex [seconds] [budget_nodes] [budget_mb]
"""
from __future__ import annotations

import os
import resource
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

RUN_SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 600
BUDGET_NODES = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
BUDGET_BYTES = (int(sys.argv[3]) if len(sys.argv) > 3 else 96) * 1024 * 1024
# 4th arg: "ff" / "fast" enables FAST-FORWARD — the clock is unpinned from wall
# time so the agent consumes media as fast as the pipeline allows (e.g. an entire
# series), instead of watching at 1x. Both cortexes still share ONE master clock
# (so they stay frame-aligned), but it advances at the rate they sustain.
_FLAGS = {a.lower() for a in sys.argv[4:]}
FAST_FORWARD = bool(_FLAGS & {"ff", "fast", "fastforward", "fast-forward"})
# VISION: actually decode PIXELS — but keep the codec's change-cheat: decode only
# KEYFRAMES (the codec's own "the picture changed enough to resend" markers, and
# self-contained so no reference chain), giving the agent full-frame vision of
# every scene change, cross-modally bound to what it hears.
VISION = bool(_FLAGS & {"vision", "pixels", "see", "eyes"})
MEM_CAP_GB = 8
VISION_SIZE = 64                       # downscaled percept grid (the retina's foveal grab)

# Tick periods — DELIBERATELY DIFFERENT so the two cortexes tick on their own
# rhythms (like brain regions at different frequencies). Each tick must process
# the chunk of stream it represents FASTER than real time, or it falls behind;
# the dial's real-time deadline is that chunk duration.
AUDIO_CHUNK_S = 1.0     # seconds of audio pulled + represented per audio tick
AUDIO_TICK_MS = 1000    # advance ~1s of stream per audio tick (real-time pace)
VIDEO_TICK_MS = 500     # video tick rhythm (a DIFFERENT clock from audio)
VIDEO_FRAMES_PER_TICK = 8
VIDEO_CHUNK_S = 0.5     # the stream span a video tick represents (deadline)

# FAST-FORWARD spans — BIGGER chunks so the per-chunk I/O (the remote stream
# re-open / ffmpeg spawn that caps network throughput) is amortised over more
# media; frames-per-window scale with the span so sampling density is preserved.
FF_AUDIO_CHUNK_S = 5.0
FF_VIDEO_CHUNK_S = 2.0
FF_VIDEO_FRAMES_PER_TICK = 32          # ~16 fps sampling over the 2s span
FF_MAX_LOOKAHEAD_S = 4.0               # how far one cortex may run ahead of the other
STAMP_INTERVAL_S = 0.5                 # max cross-modal timing-anchor density (binding tol)

# safety net only — the memory faculty is the real bound.
try:
    cap = MEM_CAP_GB * 1024 ** 3
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
except Exception as e:
    print(f"  (could not set RLIMIT_AS: {e})")

import substrate_rs as srs                                            # noqa: E402
from substrate_rs import audio as A, speech as SP, video as V         # noqa: E402
from substrate_rs import vision as VIS                                # noqa: E402
from substrate_rs import EffortDial, Production, NodePattern          # noqa: E402
import numpy as np                                                    # noqa: E402
from domains.cortex_scheduler import CortexScheduler                  # noqa: E402
from domains.auditory_cortex import install_auditory_cortex          # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                      # noqa: E402


# ----------------------------------------------------------------------------
# A SensoryCortex: its own thread, its own tick clock, its own effort dial.
# Satisfies the CortexScheduler cortex interface (tick_period_ms / tick / wake /
# _installed) so the scheduler can register it and model the independent clock —
# but the REAL per-tick processing runs in this cortex's own loop thread (the
# concurrency.py "module on its own OS thread" posture), keeping the master
# thread free. The scheduler's master clock is the timing-agreement substrate.
# ----------------------------------------------------------------------------
class SensoryCortex:
    def __init__(self, name, substrate, tick_period_ms, master_clock,
                 effort_max_passes, commit_lock, realtime_budget_ms,
                 chunk_span_s):
        self.lexicon_name = name
        self.name = name
        self.s = substrate
        # the media span (seconds) one tick/window represents — used by
        # process_chunk for the seek extent + by fast-forward to advance.
        self.chunk_span = chunk_span_s
        # REAL-TIME deadline: a tick must finish within the wall time the chunk
        # of stream it processes actually lasts, or the cortex falls behind the
        # stream. This is the dial's deadline (NOT the inter-tick period).
        self.realtime_budget_ms = realtime_budget_ms
        # SERIAL COMMIT: the graph is the shared global workspace. I/O + decode
        # (the expensive part) run fully parallel across the two cortex threads;
        # only the graph-MUTATION section is serialised under this lock so one
        # cortex's multi-step pipeline can't race the other's (or the memory
        # faculty's forget) and hit a freed slot. concurrency.py posture:
        # "parallel modules / serial commit".
        self.commit = commit_lock
        self.tick_period_ms = tick_period_ms
        self.master = master_clock          # shared MasterClock (stream pos)
        self._installed = True              # CortexScheduler precondition
        # Per-cortex EFFORT DIAL — real-time: keep within the tick deadline.
        self.dial = EffortDial(max_effort=10, min_passes=1,
                               max_passes=effort_max_passes,
                               hi_threshold=0.30, lo_threshold=0.02,
                               realtime_ceiling=6)
        # bookkeeping read by the report
        self.n_ticks = 0
        self.n_overruns = 0          # ticks whose processing blew the deadline
        self.tick_walls = []         # ms of real processing per tick
        self.effort_trace = []       # (effort, passes, surprise) per tick
        self.thread_id = None
        self.outputs = 0             # graph outputs this cortex minted
        self._per_pass_us = 4000     # seed estimate; refined from real walls
        # fast-forward sequential-read state
        self.ff_pos = 0.0            # seconds processed in the current title
        self.ff_done = False         # reached the title's end this epoch
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name=f"cortex:{name}")

    # ---- CortexScheduler interface (master-clock model) ----
    def tick(self, vote_counts=None):
        """Called by the scheduler on the master thread purely to MODEL the
        independent clock + advance bookkeeping. The heavy processing happens
        in this cortex's own thread (process_chunk). Returns an audit list."""
        return [(self.name, self.n_ticks)]

    def wake(self, vote_counts=None):
        return []

    def has_pending_work(self, vote_counts=None):
        return False

    # ---- own thread ----
    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        self.thread_id = threading.get_ident()
        if self.master.fast_forward:
            self._run_fast_forward()
        else:
            self._run_realtime()

    def _run_fast_forward(self):
        """Unpinned clock: process the title SEQUENTIALLY, window after window,
        with NO wall-time pacing — as fast as the pipeline allows. Both cortexes
        share the master clock (= the lagging edge), so a cortex that races ahead
        self-throttles to stay within max_lookahead of the other; they remain
        frame-aligned while the clock runs many x faster than real time."""
        seen_epoch = -1
        while not self._stop.is_set():
            epoch = self.master.epoch()
            if epoch != seen_epoch:               # new title — reset sequential read
                seen_epoch = epoch
                self.ff_pos = 0.0
                self.ff_done = False
                try:
                    self._ff_open(self.url_box[0])   # open the stream ONCE per title
                except Exception:
                    pass
            target = self.master.duration()
            if self.master.position() is None or self.ff_done \
                    or (target is not None and self.ff_pos >= target):
                if target is not None and self.ff_pos >= target:
                    self.ff_done = True
                if self.ff_done and target is not None:
                    self.master.report_progress(self.name, target)
                self._stop.wait(0.02)
                continue
            # bounded lookahead: don't run too far ahead of the other cortex.
            if self.master.lookahead(self.name) > self.master.max_lookahead_s:
                self._stop.wait(0.003)
                continue
            t0 = time.perf_counter()
            try:
                produced, surprise, advanced, eof = self._ff_step(self.ff_pos)
            except Exception:
                produced, surprise, advanced, eof = 0, 0.0, 0.0, False
            wall_ms = (time.perf_counter() - t0) * 1000.0
            if eof:                                # stream exhausted — title done
                if os.environ.get("DEBUG_FF"):
                    print(f"[ff-eof] {self.name} pos={self.ff_pos:.1f} target={target} "
                          f"ticks={self.n_ticks}", flush=True)
                self.ff_done = True
                if target is not None:
                    self.master.report_progress(self.name, target)
                continue
            if advanced <= 0.0:                    # reader not ready yet — retry
                self._stop.wait(0.003)
                continue
            # OFFLINE effort: no deadline — let the dial spend up on what's salient.
            self._per_pass_us = int(0.7 * self._per_pass_us
                                    + 0.3 * max(wall_ms * 1000.0, 1.0))
            self.dial.set_context("offline", deadline_us=10_000_000_000,
                                  per_pass_us=self._per_pass_us, surprise=surprise,
                                  cpu_load=0.0)
            self.effort_trace.append((self.dial.turn_dial(), self.dial.passes(),
                                      surprise))
            self.n_ticks += 1
            self.outputs += produced
            self.tick_walls.append(wall_ms)
            self.ff_pos += advanced
            rep = min(self.ff_pos, target) if target is not None else self.ff_pos
            self.master.report_progress(self.name, rep)
        self._ff_close()

    # ---- sequential-read hooks (overridden by each cortex; default = re-seek) ----
    def _ff_open(self, url):
        """Open the title's stream ONCE (sequential reader). Default: nothing."""
        pass

    def _ff_close(self):
        """Tear down the sequential reader. Default: nothing."""
        pass

    def _ff_step(self, stream_pos):
        """Read + process the NEXT block sequentially. Returns
        (produced, surprise, advanced_s, eof). Default fallback = the per-chunk
        re-seek path (advances by chunk_span)."""
        produced, surprise = self.process_chunk(stream_pos)
        return produced, surprise, self.chunk_span, False

    def _run_realtime(self):
        period = self.tick_period_ms / 1000.0
        next_fire = time.monotonic()
        while not self._stop.is_set():
            now = time.monotonic()
            if now < next_fire:
                # sleep until our OWN next pulse — sovereign timing.
                self._stop.wait(min(next_fire - now, 0.02))
                continue
            # The stream position at this tick = the master clock NOW.
            stream_pos = self.master.position()
            if stream_pos is None:
                next_fire = now + period
                continue
            t0 = time.perf_counter()
            try:
                produced, surprise = self.process_chunk(stream_pos)
            except Exception:
                produced, surprise = 0, 0.0
            wall_ms = (time.perf_counter() - t0) * 1000.0

            # --- EFFORT DIAL, REAL-TIME: fit depth to the real-time deadline ---
            # deadline = the wall time the processed chunk lasts; per-pass cost
            # refined from the measured wall so the dial learns its true cost.
            self._per_pass_us = int(0.7 * self._per_pass_us
                                    + 0.3 * max(wall_ms * 1000.0, 1.0))
            self.dial.set_context(
                "realtime",
                deadline_us=int(self.realtime_budget_ms * 1000),
                per_pass_us=self._per_pass_us,
                surprise=surprise,
                cpu_load=min(wall_ms / self.realtime_budget_ms, 1.0),
            )
            effort = self.dial.turn_dial()
            passes = self.dial.passes()
            self.effort_trace.append((effort, passes, surprise))

            self.n_ticks += 1
            self.outputs += produced
            self.tick_walls.append(wall_ms)
            if wall_ms > self.realtime_budget_ms:
                self.n_overruns += 1
            next_fire += period
            # if we fell badly behind, skip ahead (don't spiral) — the dial
            # will have dialed effort down in response.
            if time.monotonic() > next_fire + period:
                next_fire = time.monotonic() + period

    def avg_wall(self):
        return sum(self.tick_walls) / len(self.tick_walls) if self.tick_walls else 0.0

    def avg_effort(self):
        return (sum(e for e, _, _ in self.effort_trace) / len(self.effort_trace)
                if self.effort_trace else 0.0)


# ----------------------------------------------------------------------------
# MasterClock — the stream position, advanced by the watcher in real time.
# Both cortexes read it; that is the shared clock they agree timing on.
# ----------------------------------------------------------------------------
class MasterClock:
    def __init__(self, fast_forward=False, max_lookahead_s=FF_MAX_LOOKAHEAD_S):
        self._lock = threading.Lock()
        self._base_wall = None     # wall time when the title started
        self._base_pos = 0.0       # stream pos at that wall time
        self._title_start = 0.0    # ffmpeg -ss offset of the current title
        # --- fast-forward: the clock is DRIVEN by the cortexes' progress, not
        # wall time. position() = the LAGGING edge (min over cortexes) so both
        # modalities stay frame-aligned; a cortex that runs too far ahead of the
        # other self-throttles via lookahead(). epoch bumps each title so the
        # cortexes reset their sequential read position.
        self.fast_forward = fast_forward
        self.max_lookahead_s = max_lookahead_s
        self._progress = {}        # cortex name -> seconds processed this title
        self._epoch = 0            # title counter
        self._duration = None      # current title duration (EOF guard)

    def start_title(self, start_offset_s=0.0, duration_s=None):
        with self._lock:
            self._base_wall = time.monotonic()
            self._base_pos = start_offset_s
            self._title_start = start_offset_s
            self._progress = {}
            self._duration = duration_s
            self._epoch += 1

    def end_title(self):
        with self._lock:
            self._base_wall = None

    def report_progress(self, name, local_pos):
        with self._lock:
            self._progress[name] = local_pos

    def position(self):
        with self._lock:
            if self._base_wall is None:
                return None
            if self.fast_forward:
                if not self._progress:
                    return self._base_pos
                return self._base_pos + min(self._progress.values())
            return self._base_pos + (time.monotonic() - self._base_wall)

    def lookahead(self, name):
        """How far this cortex is ahead of the slowest (0 if it is the slowest)."""
        with self._lock:
            if not self._progress:
                return 0.0
            return self._progress.get(name, 0.0) - min(self._progress.values())

    def epoch(self):
        with self._lock:
            return self._epoch

    def duration(self):
        with self._lock:
            return self._duration


# ----------------------------------------------------------------------------
# AUDIO CORTEX — pulls a short opus chunk for THIS tick's window, runs the
# auditory front-end, timestamps Utterances on the master clock.
# ----------------------------------------------------------------------------
class AudioCortex(SensoryCortex):
    def __init__(self, substrate, master, lexicon, url_box, commit_lock):
        span = FF_AUDIO_CHUNK_S if master.fast_forward else AUDIO_CHUNK_S
        super().__init__("audio", substrate, AUDIO_TICK_MS, master,
                         effort_max_passes=6, commit_lock=commit_lock,
                         realtime_budget_ms=int(span * 1000),
                         chunk_span_s=span)
        self.lex = lexicon
        self.url_box = url_box       # mutable [url] so the title can change
        self.cochlea = None
        # optional TRANSCRIPT capture: the ordered sequence of heard sign ids,
        # one list per chunk (a "sentence" in the agent's own units) — for
        # learning sequential speech structure. None = off.
        self.heard_chunks = None
        self.heard_ts = None         # optional [(sign_id, master_t)] for grounding
        # optional feature transform (e.g. relational-invariance rank) applied to
        # each utterance's cochlear features before acquire_sign -> cleaner,
        # speaker-invariant units. None = raw cochlear features.
        self.feature_transform = None
        # optional FRAMEWISE capture: instead of one sign per utterance, capture
        # a per-FRAME cochleagram (fixed hop) so the unit stream is phone/syllable
        # scale, not phrase scale. Set frame_chunks=[] + frame_hop_s to enable.
        self.frame_chunks = None
        self.frame_hop_s = 0.05
        self.frame_ts = None         # optional [(frame_vec, master_t)] for grounding
        # fast-forward sequential reader: ONE ffmpeg per title decodes the source
        # SEQUENTIALLY and writes opus segments (no per-chunk -ss network seek,
        # which the breakdown showed is 68% of the per-chunk time).
        self._seg_dir = None
        self._seg_proc = None
        self._seg_idx = 0

    def _ingest_opus_file(self, path, stream_pos):
        """Run the audio front-end on a LOCAL opus file. Shared by the realtime
        per-chunk path and the fast-forward sequential-segment path."""
        produced = 0
        traj = []
        with self.commit:
            acn = A.open_container(self.s, path)
            asid = A.add_stream(self.s, acn)
            A.parse_stream(self.s, acn, asid)
            # detection needs only the cheap per-frame opus_mode hint, not the
            # disposable-tier OpusPacketInfo nodes.
            A.annotate_opus_modes(self.s, acn, asid)
            # cochlear filterbank built ONCE + reused (rebuild only if the bound
            # freed a filter node, to avoid a stale ref).
            if self.cochlea is None or not all(
                    self.s.has_node(f) for f in self.cochlea):
                self.cochlea = A.cochlea(self.s, n_bands=16, fs=48000)
            # FRAMEWISE: per-utterance per-FRAME cochleagram (fixed hop) -> a
            # dense phone/syllable-scale unit stream (captured for offline study).
            if self.frame_chunks is not None:
                frames = []
                for u in SP.detect_utterances(self.s, asid):
                    a = self.s.node(u)["attrs"]
                    ust = float(a.get("start_time_s", 0.0))
                    dur = float(a.get("end_time_s", 0.0)) - ust
                    if dur <= 0:
                        continue
                    nt = max(2, int(round(dur / self.frame_hop_s)))
                    try:
                        f = SP.extract_features(self.s, u, n_bands=16,
                                                n_time_windows=nt, fs=48000,
                                                cochlea_bank=self.cochlea)
                        mat = np.asarray(f, np.float32).reshape(16, nt)
                        for w in range(nt):
                            fv = mat[:, w].copy()
                            frames.append(fv)
                            if self.frame_ts is not None:   # (frame, master_t)
                                self.frame_ts.append(
                                    (fv, stream_pos + ust + w * self.frame_hop_s))
                    except Exception:
                        pass
                A.close_container(acn)
                if frames:
                    self.frame_chunks.append(frames)
                self.s.memory_roll_disposable()
                self.s.memory_forget_over_budget()
                return len(frames), 0.0
            res = SP.ingest_speech(self.s, asid, self.lex, n_bands=16,
                                   n_time_windows=4, fs=48000,
                                   threshold=0.80, cochlea_bank=self.cochlea,
                                   feature_transform=self.feature_transform)
            A.close_container(acn)
            chunk_seq = []
            for utt, sign, is_new in res:
                at = self.s.node(utt)["attrs"]
                local = float(at.get("start_time_s", 0.0))
                self.s.add_node("CortexStamp", {
                    "cortex": "audio", "kind": "utterance",
                    "master_t": stream_pos + local,
                    "ref": utt.value if hasattr(utt, "value") else int(utt),
                })
                if sign is not None:
                    sv = sign.value if hasattr(sign, "value") else int(sign)
                    chunk_seq.append(sv)
                    if self.heard_ts is not None:     # (sign, master_t) for grounding
                        self.heard_ts.append((sv, stream_pos + local))
                produced += 1
                traj.append(float(at.get("end_time_s", 0.0))
                            - float(at.get("start_time_s", 0.0)))
            if self.heard_chunks is not None and chunk_seq:
                self.heard_chunks.append(chunk_seq)   # transcript in heard order
            # roll the sensory register (echoic ring) + bound the kept tiers.
            self.s.memory_roll_disposable()
            self.s.memory_forget_over_budget()
        surprise = self.dial.surprise_of(traj) if traj else 0.0
        return produced, surprise

    def process_chunk(self, stream_pos):
        """REAL-TIME path: ffmpeg -ss extracts one chunk, then ingest."""
        url = self.url_box[0]
        if url is None:
            return 0, 0.0
        tmp = tempfile.mktemp(suffix=".ogg")
        try:
            r = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-ss", f"{stream_pos:.3f}", "-t", f"{self.chunk_span}",
                 "-i", url, "-vn", "-ar", "48000", "-ac", "1",
                 "-c:a", "libopus", tmp],
                capture_output=True, timeout=20)
            if r.returncode != 0 or not os.path.exists(tmp) \
                    or os.path.getsize(tmp) < 256:
                return 0, 0.0
            return self._ingest_opus_file(tmp, stream_pos)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    # ---- fast-forward sequential reader ----
    def _seg_path(self, i):
        return os.path.join(self._seg_dir, f"seg_{i:05d}.opus")

    def _ff_open(self, url):
        self._ff_close()
        if url is None:
            return
        self._seg_dir = tempfile.mkdtemp(prefix="ffaud_")
        self._seg_idx = 0
        # ONE sequential decode pass of the whole title -> opus segments; this
        # ffmpeg races AHEAD of consumption (it decodes many x real-time), so the
        # cortex's per-chunk cost drops to just the ingest compute.
        self._seg_proc = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", url, "-vn",
             "-ar", "48000", "-ac", "1", "-c:a", "libopus",
             "-f", "segment", "-segment_time", str(self.chunk_span),
             "-reset_timestamps", "1", self._seg_path(0).replace("00000", "%05d")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _ff_close(self):
        if self._seg_proc is not None:
            try:
                self._seg_proc.kill()
            except Exception:
                pass
            self._seg_proc = None
        if self._seg_dir is not None:
            shutil.rmtree(self._seg_dir, ignore_errors=True)
            self._seg_dir = None

    def _ff_step(self, stream_pos):
        if self._seg_dir is None:
            return 0, 0.0, 0.0, True
        cur = self._seg_path(self._seg_idx)
        nxt = self._seg_path(self._seg_idx + 1)
        done = self._seg_proc is None or self._seg_proc.poll() is not None
        if not os.path.exists(cur):
            return (0, 0.0, 0.0, True) if done else (0, 0.0, 0.0, False)
        # a segment is COMPLETE once the next one has started, or ffmpeg finished.
        if not os.path.exists(nxt) and not done:
            return 0, 0.0, 0.0, False
        if os.path.getsize(cur) < 256:
            try:
                os.unlink(cur)
            except OSError:
                pass
            self._seg_idx += 1
            return 0, 0.0, self.chunk_span, False
        produced, surprise = self._ingest_opus_file(cur, stream_pos)
        try:
            os.unlink(cur)
        except OSError:
            pass
        self._seg_idx += 1
        return produced, surprise, self.chunk_span, False


# ----------------------------------------------------------------------------
# VIDEO CORTEX — pulls a small frame window for THIS tick, reads temporal
# STRUCTURE (Frame + MotionVector), timestamps Frames on the master clock.
# ----------------------------------------------------------------------------
class VideoCortex(SensoryCortex):
    def __init__(self, substrate, master, url_box, commit_lock):
        span = FF_VIDEO_CHUNK_S if master.fast_forward else VIDEO_CHUNK_S
        super().__init__("video", substrate, VIDEO_TICK_MS, master,
                         effort_max_passes=4, commit_lock=commit_lock,
                         realtime_budget_ms=int(span * 1000),
                         chunk_span_s=span)
        self.frames_per_tick = (FF_VIDEO_FRAMES_PER_TICK if master.fast_forward
                                else VIDEO_FRAMES_PER_TICK)
        self.url_box = url_box
        self._vstream_idx = None
        # fast-forward sequential reader: ONE PyAV container per title, decoded
        # straight through (no per-window av.open/seek over the network).
        self._vcontainer = None
        self._vgen = None
        # VISION: FULL-VIDEO pixels — every frame, via an ffmpeg decode+scale
        # pipe (one per title; lossless speed, no frames dropped). V1 bank built
        # once + reused; a vision stamp every STAMP_INTERVAL_S binds to audio.
        self.vision = VISION
        if VISION:
            self.frames_per_tick = 8     # short lock bursts so audio stays responsive
        self._v1bank = None
        self._scene_idx = 0
        self._vpipe = None               # ffmpeg decode+scale pipe
        self._vfps = 24.0
        self._vframe_idx = 0
        self._prev_small = None          # previous percept -> real pixel-diff motion
        self._last_vstamp = -1e9
        # optional VISUAL LEXICON: acquire a visual sign on each visual EVENT
        # (scene change = motion spike) via the SAME acquire_sign the ear uses —
        # recurring scenes/shots condense into signs that saturate. Set by the
        # caller; None = off.
        self.vision_lex = None
        self._vis_thresh = 6.0           # mean-abs pixel-diff that counts as a "shot"
        self._vis_new = 0                # signs minted (new recurring patterns)
        self._vis_events = 0             # visual events presented
        self.vis_feat_size = 16          # cue feature grid — bump for SPECIFIC cues
        self.vis_match_threshold = 0.92  # cue merge: HIGHER = stricter = more distinct cues
        self.vis_crop = 1.0              # center-crop fraction (focus the cue on the object)
        self.vis_object_isolate = False  # subtract running background -> cue = the foreground OBJECT
        self.vis_relational = False      # cue = shape_signature(foreground): gain/scale-invariant
                                         # OBJECT-SIGN (the agent's OWN invariance op, the one that
                                         # gave audio speaker-invariant units, composed onto vision)
        self._vis_bg = None              # EMA background (the persistent presenter/set)
        self.seen_cues = None            # optional [(cue_id, master_t)] for grounding

    def _packet_record(self, packet, tb):
        """Codec STRUCTURE from the packet header (no decode): keyframe flag,
        coded_size (motion proxy), pts. The demux-only structure path."""
        kf = int(bool(packet.is_keyframe))
        ft = float(packet.pts) * tb if packet.pts is not None else 0.0
        return ("I" if kf else "P", kf, ft, int(packet.size))

    def _see_frame(self, small, master_t, motion):
        """The eye + V1 on ONE frame's downscaled percept: mint the percept,
        extract V1 edge structure, keep a compact VisualScene gist (edge
        energies + real pixel-diff motion), and — throttled to STAMP_INTERVAL_S —
        a vision CortexStamp that BINDS to what was heard. Percept + V1 maps +
        per-frame gist are disposable sensory scratch (rolled). Must run under
        the commit lock (graph mutation)."""
        try:
            # OBJECT ISOLATION: track an EMA background (the persistent presenter /
            # set) every frame; the foreground = |frame - background| is the new
            # NAMED object, with the constant background subtracted away.
            if self.vis_object_isolate:
                if self._vis_bg is None or self._vis_bg.shape != small.shape:
                    self._vis_bg = small.astype(np.float32).copy()
                else:
                    # GRAPH-NATIVE: the running background model is the held Rust
                    # op Substrate.ema_blend, not numpy.
                    self._vis_bg = np.asarray(
                        srs.Substrate.ema_blend(self._vis_bg.ravel(),
                                                small.ravel(), 0.05),
                        dtype=np.float32).reshape(small.shape)
            img = VIS.image_from_array(self.s, small, origin="frame")
            energies = []
            try:                                  # V1: the visual cortex seeing edges
                if self._v1bank is None:
                    self._v1bank = VIS.v1_bank(self.s, n_orientations=4, sigma=1.5)
                for rnid in VIS.v1_responses(self.s, img, self._v1bank):
                    energies.append(float(np.abs(VIS.image_to_array(self.s, rnid)).mean()))
            except Exception:
                energies = []
            sc = self.s.add_node("VisualScene", {
                "master_t": master_t, "frame": self._scene_idx, "motion": float(motion),
                "edge_e0": energies[0] if len(energies) > 0 else 0.0,
                "edge_e1": energies[1] if len(energies) > 1 else 0.0,
                "edge_e2": energies[2] if len(energies) > 2 else 0.0,
                "edge_e3": energies[3] if len(energies) > 3 else 0.0,
            })
            if master_t - self._last_vstamp >= STAMP_INTERVAL_S:
                self._last_vstamp = master_t
                self.s.add_node("CortexStamp", {
                    "cortex": "video", "kind": "vision", "master_t": master_t,
                    "ref": sc.value if hasattr(sc, "value") else int(sc),
                })
            # VISUAL LEXICON: on a visual EVENT (scene change), acquire a visual
            # sign from a coarse percept feature via the ear's own acquire_sign —
            # recurring shots become recurring signs (the visual lexicon saturates
            # just as the acoustic one does).
            if self.vision_lex is not None and (motion > self._vis_thresh
                                                or self._scene_idx == 0):
                try:
                    # cue = the foreground OBJECT (background-subtracted) if isolating,
                    # else the raw frame. GRAPH-NATIVE: foreground = the held Rust op
                    # Substrate.foreground (|frame - background|), not numpy.
                    if self.vis_object_isolate and self._vis_bg is not None:
                        base = np.asarray(
                            srs.Substrate.foreground(small.ravel(), self._vis_bg.ravel()),
                            dtype=np.float32).reshape(small.shape)
                    else:
                        base = small
                    region = base
                    if self.vis_crop < 1.0:        # focus on the (usually centered) object
                        h, w = base.shape
                        ch, cw = int(h * self.vis_crop), int(w * self.vis_crop)
                        region = base[(h - ch) // 2:(h - ch) // 2 + ch,
                                      (w - cw) // 2:(w - cw) // 2 + cw]
                    step = max(1, region.shape[0] // self.vis_feat_size)
                    feat = region[::step, ::step].flatten().astype(np.float32)
                    if self.vis_crop < 1.0:
                        feat = feat - feat.mean()   # de-brightness when cropping to the object
                    if self.vis_relational:
                        # OBJECT-SIGN: relational rank of the foreground = the agent's
                        # OWN invariance op (shape_signature), the one that gave audio
                        # speaker-invariant units, now composed onto the vision cue ->
                        # gain/scale-invariant object identity (recomposing held ops).
                        feat = np.asarray(srs.Substrate.shape_signature(feat),
                                          dtype=np.float32)
                    sg, is_new = SP.acquire_sign(self.s, self.vision_lex, feat,
                                                 threshold=self.vis_match_threshold)
                    self._vis_events += 1
                    if is_new:
                        self._vis_new += 1
                    if self.seen_cues is not None and sg is not None:
                        # keep the cue IMAGE with the event so groundings can be rendered even
                        # after the memory faculty retires the sign node at end of title.
                        self.seen_cues.append(
                            (sg.value if hasattr(sg, "value") else int(sg), master_t,
                             feat.astype(np.float32).copy()))
                except Exception:
                    pass
            self._scene_idx += 1
            return True
        except Exception:
            return False

    def _downscale(self, g):
        h, w = g.shape
        yi = np.linspace(0, h - 1, VISION_SIZE).astype(int)
        xi = np.linspace(0, w - 1, VISION_SIZE).astype(int)
        return g[np.ix_(yi, xi)].astype(np.float32)

    def _ingest_frames(self, frames, master_t0, dt):
        """Mint percept+V1 for a batch of downscaled frames (full vision), with
        real pixel-diff motion. One commit-lock burst."""
        produced = 0
        motions = []
        with self.commit:
            for i, arr in enumerate(frames):
                motion = (float(np.abs(arr - self._prev_small).mean())
                          if self._prev_small is not None else 0.0)
                self._prev_small = arr
                self._see_frame(arr, master_t0 + i * dt, motion)
                motions.append(motion)
                produced += 1
            self.s.memory_roll_disposable()
            self.s.memory_forget_over_budget()
        surprise = self.dial.surprise_of(motions) if motions else 0.0
        return produced, surprise

    def _commit_frames(self, decoded, base_master_t):
        """Mint Frame + follows + throttled CortexStamp anchors for a batch.
        base_master_t = the master-clock time of the FIRST frame; per-frame time
        is that plus the within-batch offset (handles absolute or relative pts)."""
        produced = 0
        motions = []
        base_ft = decoded[0][2] if decoded else 0.0
        with self.commit:
            prev = None
            last_stamp = -1e9
            for pict_type, key_frame, ft, coded in decoded:
                offset = min(max(0.0, ft - base_ft), self.chunk_span)
                master_t = base_master_t + offset
                fnid = self.s.add_node("Frame", {
                    "pict_type": pict_type, "key_frame": key_frame,
                    "time_s": ft, "coded_size": coded,
                })
                # CortexStamp is a cross-modal TIMING ANCHOR (~1 per
                # STAMP_INTERVAL_S + keyframes), not a per-frame record; the
                # Frame + follows chain carries the per-frame structure.
                if master_t - last_stamp >= STAMP_INTERVAL_S or key_frame:
                    last_stamp = master_t
                    self.s.add_node("CortexStamp", {
                        "cortex": "video", "kind": "frame",
                        "master_t": master_t,
                        "ref": fnid.value if hasattr(fnid, "value") else int(fnid),
                    })
                if prev is not None:
                    self.s.add_edge(fnid, "follows", prev)
                prev = fnid
                motions.append(float(coded))
                produced += 1
            self.s.memory_roll_disposable()
            self.s.memory_forget_over_budget()
        surprise = self.dial.surprise_of(motions) if motions else 0.0
        return produced, surprise

    def process_chunk(self, stream_pos):
        """REAL-TIME path: open the container seeked to stream_pos, read a window."""
        url = self.url_box[0]
        if url is None:
            return 0, 0.0
        import av
        try:
            container = av.open(url, options={"ss": f"{stream_pos:.3f}"})
        except Exception:
            return 0, 0.0
        try:
            vstream = container.streams.video[0]
            tb = (vstream.time_base.numerator / vstream.time_base.denominator
                  if vstream.time_base else 0.0)
            if self.vision:
                frames = []
                for packet in container.demux(vstream):
                    if packet.size == 0:
                        continue
                    for fr in packet.decode():       # FULL vision: every frame's pixels
                        frames.append(self._downscale(fr.to_ndarray(format="gray")))
                        if len(frames) >= self.frames_per_tick:
                            break
                    if len(frames) >= self.frames_per_tick:
                        break
                fps = (vstream.average_rate or 24) if vstream else 24
                container.close()
                if not frames:
                    return 0, 0.0
                return self._ingest_frames(frames, stream_pos, 1.0 / float(fps or 24))
            decoded = []
            for packet in container.demux(vstream):
                if packet.size == 0:
                    continue
                decoded.append(self._packet_record(packet, tb))
                if len(decoded) >= self.frames_per_tick:
                    break
        finally:
            if not self.vision:
                container.close()
        if not decoded:
            return 0, 0.0
        return self._commit_frames(decoded, stream_pos)

    # ---- fast-forward sequential reader ----
    def _frame_gen(self, container, vstream, tb):
        # DEMUX-ONLY: read codec STRUCTURE from packet headers (keyframe flag,
        # coded size = motion/complexity proxy, pts) WITHOUT decoding to pixels.
        # Measured ~5x faster than decode (181x vs 38x real-time) and the cortex
        # never uses pixels — exact P-vs-B pict_type is the only thing lost, and
        # coded_size already encodes it. GPU decode does NOT help here: it still
        # produces pixels we discard (VAAPI measured no faster than CPU). If the
        # visual cortex later wants pixels, decode SALIENT keyframes on demand.
        for packet in container.demux(vstream):
            if packet.size == 0:
                continue
            yield self._packet_record(packet, tb)

    def _ff_open(self, url):
        self._ff_close()
        if url is None:
            return
        if self.vision:
            # FULL VIDEO: ONE ffmpeg decodes + downscales EVERY frame straight through to a gray
            # rawvideo pipe (the lossless speed cheat — decode + scale in C, ~37x real time, no
            # frames dropped). -map 0:v:0 EXPLICITLY selects the video stream: without it,
            # ffmpeg's auto-selection hit a data stream on these matroska files and EOF'd after
            # one frame (fast forward saw ~0 frames). The C pipe stays — PyAV per-frame decode
            # would tank the bulk consumption rate.
            self._vfps = _probe_fps(url)
            self._vframe_idx = 0
            self._prev_small = None
            self._last_vstamp = -1e9
            self._vpipe = subprocess.Popen(
                ["ffmpeg", "-loglevel", "error", "-i", url, "-map", "0:v:0", "-an", "-vf",
                 f"scale={VISION_SIZE}:{VISION_SIZE},format=gray", "-f", "rawvideo", "pipe:1"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            return
        import av
        self._vcontainer = av.open(url)            # demux-only: opened ONCE
        vstream = self._vcontainer.streams.video[0]
        tb = (vstream.time_base.numerator / vstream.time_base.denominator
              if vstream.time_base else 0.0)
        self._vgen = self._frame_gen(self._vcontainer, vstream, tb)

    def _ff_close(self):
        self._vgen = None
        if self._vcontainer is not None:
            try:
                self._vcontainer.close()
            except Exception:
                pass
            self._vcontainer = None
        if self._vpipe is not None:
            try:
                self._vpipe.kill()
            except Exception:
                pass
            self._vpipe = None

    def _ff_step(self, stream_pos):
        if self.vision:
            return self._ff_step_vision()
        if self._vgen is None:
            return 0, 0.0, 0.0, True
        decoded = []
        for _ in range(self.frames_per_tick):
            try:
                decoded.append(next(self._vgen))
            except StopIteration:
                self._vgen = None
                break
        if not decoded:
            return 0, 0.0, 0.0, True
        base_ft = min(d[2] for d in decoded)       # demux pts can reorder (B-frames)
        produced, surprise = self._commit_frames(decoded, base_ft)
        advanced = max(max(d[2] for d in decoded) - self.ff_pos, 1e-3)
        return produced, surprise, advanced, False

    def _ff_step_vision(self):
        if self._vpipe is None:
            return 0, 0.0, 0.0, True
        nbytes = VISION_SIZE * VISION_SIZE
        frames = []                                # read OUTSIDE the commit lock
        for _ in range(self.frames_per_tick):
            # read EXACTLY one frame — a pipe read() can return PARTIAL data (< nbytes) when a
            # frame spans buffer boundaries; that is NOT EOF. Loop until the full frame or a
            # truly-empty read (real stream end).
            chunks, got = [], 0
            while got < nbytes:
                b = self._vpipe.stdout.read(nbytes - got)
                if not b:                          # genuine EOF
                    break
                chunks.append(b); got += len(b)
            if got < nbytes:
                self._vpipe = None
                break
            frames.append(np.frombuffer(b"".join(chunks), np.uint8)
                          .reshape(VISION_SIZE, VISION_SIZE).astype(np.float32))
        if not frames:
            return 0, 0.0, 0.0, True
        dt = 1.0 / max(self._vfps, 1.0)
        t0 = self._vframe_idx * dt
        self._vframe_idx += len(frames)
        produced, surprise = self._ingest_frames(frames, t0, dt)
        return produced, surprise, len(frames) * dt, False


# ----------------------------------------------------------------------------
# Timing-agreement: link each audio stamp to co-temporal video stamps via
# synchronous_with on the shared master clock (the teach_video_concept binding).
# ----------------------------------------------------------------------------
def _probe_fps(url, default=24.0):
    """Average frame rate of the video stream (ffprobe), for sequential
    rawvideo timing (the pipe carries no pts)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", url],
            capture_output=True, text=True, timeout=30).stdout.strip()
        if "/" in out:
            num, den = out.split("/")
            return float(num) / float(den) if float(den) else default
        return float(out) if out else default
    except Exception:
        return default


def bind_synchronous(s, tol_s=0.5):
    a_stamps, v_stamps = [], []
    for nid in s.nodes("CortexStamp"):
        at = s.node(nid)["attrs"]
        rec = (float(at.get("master_t", 0.0)), nid)
        if at.get("cortex") == "audio":
            a_stamps.append(rec)
        elif at.get("cortex") == "video":
            v_stamps.append(rec)
    v_stamps.sort(key=lambda r: r[0])   # by master_t only (NodeIDs aren't orderable)
    import bisect
    v_t = [t for t, _ in v_stamps]
    bound = 0
    for at, anid in a_stamps:
        lo = bisect.bisect_left(v_t, at - tol_s)
        hi = bisect.bisect_right(v_t, at + tol_s)
        for _, vnid in v_stamps[lo:hi]:
            try:
                s.add_edge(anid, "synchronous_with", vnid)
                bound += 1
            except Exception:
                pass
    return bound


def main():
    print("=" * 80)
    print("WATCH JELLYFIN — CORTEX MANAGEMENT (separate threads, separate ticks,")
    print("                 shared master clock, effort dial, memory faculty)")
    print("=" * 80)

    s = srs.Substrate()
    A.seed_audio_grammar(s)
    A.seed_native_codec_grammar(s)
    SP.seed_speech_grammar(s)
    V.seed_video_grammar(s)
    if VISION:
        VIS.seed_vision_grammar(s)    # Image / Kernel + convolve provenance edges
    install_auditory_cortex(s)
    # cross-modal timing-agreement vocabulary (CortexStamp + synchronous_with)
    for src, et, tgt, prov in [
        ("CortexStamp", "synchronous_with", "CortexStamp", "cx:stamp_sync"),
        ("Frame", "follows", "Frame", "cx:frame_follows"),
    ]:
        try:
            s.add_production(Production(
                src=NodePattern(type=src, var="a"), edge_type=et,
                tgt=NodePattern(type=tgt, var="b"), where=None, weight=None,
                provenance=prov).to_dict())
        except Exception:
            pass
    lex = SP.open_lexicon(s)

    # MEMORY FACULTY — bound the shared graph (nodes + bytes), streaming forget.
    s.memory_bound(BUDGET_NODES, BUDGET_BYTES, 3)
    # Sensory register (disposable circular buffer): ~the last few seconds of
    # raw scratch — deep for tiny frames, only the freshest large decode buffers.
    s.memory_disposable_capacity(8 * 1024 * 1024, 1024)

    jf = JellyfinWorld().connect()
    jf.ingest_catalog(s)

    master = MasterClock(fast_forward=FAST_FORWARD)
    url_box = [None]
    commit = threading.Lock()        # serial-commit door into the shared graph

    # The two SOVEREIGN cortexes, each on its OWN thread + tick + dial.
    audio_cx = AudioCortex(s, master, lex, url_box, commit)
    video_cx = VideoCortex(s, master, url_box, commit)
    # SEE REAL THINGS: give the eye a visual lexicon so recurring real objects condense into
    # visual signs (the same acquire_sign the ear uses), isolating the FOREGROUND object so the
    # cue is the real thing, not the whole frame. The inexperienced agent gains experience.
    if VISION:
        video_cx.vision_lex = SP.open_lexicon(s, name="vision")
        video_cx.vis_object_isolate = True
        # COARSER visual signs: 0.92 minted 10k+ near-unique signs in 3 episodes (every shot
        # distinct -> nothing recurs -> no grounding). A looser merge lets the SAME real thing
        # become ONE recurring sign across occurrences, so a sound can bind to it stably.
        video_cx.vis_match_threshold = 0.82
        video_cx.seen_cues = []            # [(visual_sign, t)] — to match sights to sounds
        audio_cx.heard_ts = []             # [(acoustic_sign, t)] — to match sounds to sights

    # Register with the substrate's CortexScheduler — the independent-clock
    # model + the shared master clock for timing agreement.
    sched = CortexScheduler()
    sched.register(audio_cx)
    sched.register(video_cx)

    audio_cx.start()
    video_cx.start()

    mode = ("FAST-FORWARD (clock unpinned — consume as fast as the pipeline allows)"
            if FAST_FORWARD else "REAL-TIME (clock pinned to wall time)")
    print(f"\n  MODE: {mode}")
    print(f"  VIDEO: {'CHANGE-DRIVEN VISION (keyframe pixels + V1)' if VISION else 'demux-only structure'}")
    print(f"  audio cortex thread started: chunk_span={audio_cx.chunk_span:.1f}s")
    print(f"  video cortex thread started: chunk_span={video_cx.chunk_span:.1f}s "
          f"({video_cx.frames_per_tick} frames/window)")
    print(f"  memory faculty bound: {BUDGET_NODES} nodes / "
          f"{BUDGET_BYTES//1024//1024} MB; sensory ring 8MB")

    watched = []
    peak_nodes = 0
    peak_bytes = 0
    media_consumed = 0.0             # total media-seconds the agent has watched
    total_sync_bound = 0             # cross-modal bindings made (consolidated per title)
    t0 = time.time()
    master_advances = 0

    # FORCE a specific series (WATCH_SERIES env) — e.g. a research-built learning corpus like
    # Sesame Street — instead of the autonomous novelty choice. Watch its episodes in order.
    forced = os.environ.get("WATCH_SERIES")
    forced_eps = []
    if forced:
        sid = next((it["id"] for it in jf.catalog(("Series",)) if it["name"] == forced), None)
        forced_eps = jf.episodes(sid, limit=30) if sid else []
        print(f"  FORCED SERIES: {forced} ({len(forced_eps)} episodes)")
    ep_cursor = 0

    print(f"\n  {'wall':>4} {'media':>6} {'x':>5} {'title':<26} {'a_tk':>5} {'v_tk':>5} "
          f"{'nodes':>6} {'MB':>5}")

    while time.time() - t0 < RUN_SECONDS:
        if forced:
            if ep_cursor >= len(forced_eps):
                break
            ep = forced_eps[ep_cursor]; ep_cursor += 1
            title = {"id": ep["id"], "name": f"{forced[:12]}-{ep.get('name', '')}"[:40]}
            eps = [ep]
        else:
            # AUTONOMOUS CHOICE — curiosity over unseen series (HTTP catalogue +
            # watched-set novelty; does not read the live graph, so no lock needed).
            picks = jf.choose(s, n=1, watched_series=watched)
            if not picks:
                break
            title = picks[0]
            eps = jf.episodes(title["id"], limit=1)
            if not eps:
                watched.append(title["name"])
                continue
        url_box[0] = jf.stream_url(eps[0]["id"])
        video_cx._vstream_idx = None
        duration = float(eps[0].get("runtime_s") or 0.0) or None
        # FAST-FORWARD needs a title length to know when to stop the sequential
        # read; fall back to a wall cap if metadata is missing.
        # Clear the PREVIOUS title's done-flags in THIS thread before bumping the epoch — else
        # the completion check below fires on the stale ff_done=True before the cortex workers
        # have reset them, so every new title "completes" instantly (only the 1st was watched).
        audio_cx.ff_done = video_cx.ff_done = False
        audio_cx.ff_pos = video_cx.ff_pos = 0.0
        master.start_title(0.0, duration_s=duration)

        # REAL-TIME: watch a wall slice. FAST-FORWARD: race the cortexes through
        # the whole title (clock = lagging edge), stop when BOTH reach the end.
        title_budget = (RUN_SECONDS - (time.time() - t0)) if FAST_FORWARD \
            else min(90, RUN_SECONDS - (time.time() - t0))
        tt0 = time.time()
        last_print = 0.0
        title_t0 = time.time()
        while time.time() - t0 < RUN_SECONDS:
            if FAST_FORWARD:
                # require the title to have actually run a moment before honouring done-flags
                # (closes the start-of-title race with the worker's epoch reset).
                if (duration is not None and audio_cx.ff_done and video_cx.ff_done
                        and time.time() - title_t0 > 0.3):
                    break
                if duration is None and time.time() - tt0 >= title_budget:
                    break
            else:
                if time.time() - tt0 >= title_budget:
                    break
            sched.advance(int((time.time() - t0) * 1000))
            master_advances += 1
            with commit:
                n = s.node_count()
                b = s.memory_total_bytes()
            peak_nodes = max(peak_nodes, n)
            peak_bytes = max(peak_bytes, b)
            pos = master.position() or 0.0
            now = time.time() - tt0
            if now - last_print >= (3 if FAST_FORWARD else 10):
                last_print = now
                wall = time.time() - t0
                x = (media_consumed + pos) / wall if wall else 0.0
                print(f"  {int(wall):>4} {int(media_consumed+pos):>6} {x:>5.1f} "
                      f"{title['name'][:25]:<26} "
                      f"{audio_cx.n_ticks:>5} {video_cx.n_ticks:>5} "
                      f"{n:>6} {b/1024/1024:>5.1f}", flush=True)
            time.sleep(0.05)
        # media-seconds consumed this title = the lagging-edge position reached.
        media_consumed += master.position() or 0.0
        master.end_title()
        # CONSOLIDATE the title: bind co-temporal audio/video, record the
        # alignment as a kept gist, then RETIRE the spent per-frame timing
        # anchors so node-count stays bounded across an entire SERIES (you keep
        # the gist + the lexicon after an episode, not every frame's timestamp).
        with commit:
            n_bound = bind_synchronous(s)
            total_sync_bound += n_bound
            n_a = sum(1 for nid in s.nodes("CortexStamp")
                      if s.node(nid)["attrs"].get("cortex") == "audio")
            n_v = sum(1 for nid in s.nodes("CortexStamp")
                      if s.node(nid)["attrs"].get("cortex") == "video")
            s.add_node("MemorySummary", {
                "kind": "title_alignment", "title": title["name"][:60],
                "audio_units": n_a, "video_units": n_v, "bindings": n_bound,
            })
            s.memory_forget_type("CortexStamp")   # anchors consolidated -> retire
            if VISION:
                s.memory_forget_type("Image")     # raw percepts + V1 maps = scratch
            tr = s.memory_observe_and_bound()
        watched.append(title["name"])
        url_box[0] = None

    audio_cx.stop()
    video_cx.stop()
    time.sleep(0.3)

    # TIMING AGREEMENT — bound per title (consolidated into per-title gists), plus
    # any residual stamps from a title cut short by the run budget.
    n_sync = total_sync_bound + bind_synchronous(s)

    # EXPERIENCE GAINED — what the inexperienced agent took away from SEEING REAL THINGS:
    # the lexicons (recurring patterns it acquired) + cross-modal groundings (saw + heard).
    ac_signs = SP.lexicon_signs(s, lex)
    ac_recur = sum(1 for sid in ac_signs if s.node(sid)["attrs"].get("hearings", 1) >= 2)
    exp = {"acoustic_signs": len(ac_signs), "acoustic_recurring": ac_recur,
           "groundings": n_sync, "visual_signs": 0, "visual_recurring": 0}
    if VISION and video_cx.vision_lex is not None:
        vs = SP.lexicon_signs(s, video_cx.vision_lex)
        exp["visual_signs"] = len(vs)
        exp["visual_recurring"] = sum(1 for sid in vs
                                      if s.node(sid)["attrs"].get("hearings", 1) >= 2)

    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print("RUN COMPLETE — NUMBERS")
    print("=" * 80)
    print("  EXPERIENCE GAINED (recurring patterns acquired by watching real content):")
    print(f"    acoustic signs (names heard)  : {exp['acoustic_signs']:>4}  "
          f"recurring(>=2): {exp['acoustic_recurring']}")
    print(f"    visual signs (real things seen): {exp['visual_signs']:>4}  "
          f"recurring(>=2): {exp['visual_recurring']}")
    print(f"    cross-modal groundings (saw+heard together): {exp['groundings']}")

    # WHAT IT GROUNDED — match each heard acoustic sign to the co-temporal SEEN visual sign(s);
    # the (sound, sight) pairs that co-occur MOST are the agent's strongest learned associations:
    # a recurring SOUND bound to a recurring REAL THING it saw. No English — pre-linguistic
    # concepts. The visual sign's prototype IS a little image of the thing (foreground object),
    # so we render it as ASCII to SHOW what was grounded.
    if VISION and getattr(audio_cx, "heard_ts", None) and getattr(video_cx, "seen_cues", None):
        import bisect
        from collections import Counter
        seen = sorted(video_cx.seen_cues, key=lambda r: r[1])
        st = [r[1] for r in seen]
        feat_by_sign = {}
        for r in seen:                              # a representative cue image per visual sign
            feat_by_sign.setdefault(int(r[0]), r[2])
        pairs = Counter()
        for asid, ta in audio_cx.heard_ts:
            lo = bisect.bisect_left(st, ta - 0.4)
            hi = bisect.bisect_right(st, ta + 0.4)
            for r in seen[lo:hi]:
                pairs[(int(asid), int(r[0]))] += 1

        def _hearings(nid):
            try:
                return int(s.node(nid)["attrs"].get("hearings", 1))
            except Exception:
                return "?"

        def _render(vsid, every=2):
            feat = feat_by_sign.get(int(vsid))
            if feat is None:
                return None
            feat = np.asarray(feat, dtype=np.float32)
            n = int(round(len(feat) ** 0.5))
            if n * n != len(feat) or n < 6:
                return None
            g = feat[:n * n].reshape(n, n)
            g = (g - g.min()) / (g.max() - g.min() + 1e-9)
            chars = " .:-=+*#%@"
            return ["".join(chars[min(int(v * 9), 9)] for v in row) for row in g[::every]]

        if audio_cx.heard_ts and seen:
            ta_lo, ta_hi = min(t for _, t in audio_cx.heard_ts), max(t for _, t in audio_cx.heard_ts)
            tv_lo, tv_hi = st[0], st[-1]
            mx = max(pairs.values()) if pairs else 0
            print(f"\n  [grounding stats: {len(audio_cx.heard_ts)} sounds (t {ta_lo:.0f}..{ta_hi:.0f}), "
                  f"{len(seen)} sights (t {tv_lo:.0f}..{tv_hi:.0f}), {len(pairs)} distinct pairs, "
                  f"max co-occur {mx}]")
        print("\n  WHAT IT GROUNDED — the strongest sound<->sight associations the agent formed:")
        print("  a recurring SOUND it heard bound to a recurring REAL THING it saw (the foreground")
        print("  object, rendered as ASCII). Pre-linguistic concepts — no English, just 'this")
        print("  sound goes with this thing', learned purely from co-occurrence while watching.")
        shown = 0
        seen_things = set()
        for (asid, vsid), cnt in pairs.most_common(200):
            if cnt < 2 or shown >= 6:
                break
            if vsid in seen_things:            # one entry per distinct THING
                continue
            img = _render(vsid)
            if img is None:
                continue
            seen_things.add(vsid)
            n_sounds = sum(1 for (a, v) in pairs if v == vsid and pairs[(a, v)] >= 2)
            print(f"\n    thing #{shown + 1}: seen + heard together {cnt}x "
                  f"(bound to {n_sounds} distinct sound(s)):")
            for row in img:
                print("      |" + row + "|")
            shown += 1
        if shown == 0:
            print("    (no strong groundings yet — watch more)")
    print(f"  mode                        : "
          f"{'FAST-FORWARD' if FAST_FORWARD else 'REAL-TIME'}")
    print(f"  wall time                   : {elapsed:.0f}s "
          f"({len(watched)} titles)")
    print(f"  MEDIA CONSUMED              : {media_consumed:.0f}s "
          f"({media_consumed/60:.1f} min of programming)")
    print(f"  -> throughput               : {media_consumed/elapsed:.1f}x real-time"
          f"  ({'consumed faster than watchable' if media_consumed > elapsed else 'real-time'})")
    if VISION:
        print(f"  FRAMES SEEN (full video)    : {video_cx._scene_idx}  "
              f"(EVERY frame decoded to pixels + V1 edge-extracted, pixel-diff motion)")
    print(f"  titles                      : "
          f"{', '.join(w[:24] for w in watched)}")
    print()
    print("  SEPARATE THREADS + SEPARATE INDEPENDENT TICKS:")
    print(f"    audio cortex  thread_id={audio_cx.thread_id}  "
          f"ticks={audio_cx.n_ticks}  "
          f"period={AUDIO_TICK_MS}ms  "
          f"eff_rate={audio_cx.n_ticks/elapsed:.2f} Hz  "
          f"avg_proc={audio_cx.avg_wall():.0f}ms")
    print(f"    video cortex  thread_id={video_cx.thread_id}  "
          f"ticks={video_cx.n_ticks}  "
          f"period={VIDEO_TICK_MS}ms  "
          f"eff_rate={video_cx.n_ticks/elapsed:.2f} Hz  "
          f"avg_proc={video_cx.avg_wall():.0f}ms")
    print(f"    -> DISTINCT thread ids: "
          f"{audio_cx.thread_id != video_cx.thread_id}; "
          f"DISTINCT tick counts/rates (ran concurrently on their own clocks)")
    print(f"    master clock advances (scheduler): {master_advances}")
    print()
    print("  TIMING AGREEMENT (shared master clock):")
    # stamps are consolidated per title into title_alignment gists; sum the gists.
    aligns = [s.node(nid)["attrs"] for nid in s.nodes("MemorySummary")
              if s.node(nid)["attrs"].get("kind") == "title_alignment"]
    n_astamp = sum(int(a.get("audio_units", 0)) for a in aligns)
    n_vstamp = sum(int(a.get("video_units", 0)) for a in aligns)
    print(f"    audio anchors={n_astamp}  video anchors={n_vstamp}  "
          f"synchronous_with bindings={n_sync} (consolidated into "
          f"{len(aligns)} per-title alignment gists)")
    print()
    print("  EFFORT DIAL (real-time, per cortex):")
    a_ov = audio_cx.n_overruns
    v_ov = video_cx.n_overruns
    print(f"    audio: avg_effort={audio_cx.avg_effort():.2f}/10  "
          f"deadline_overruns={a_ov}/{audio_cx.n_ticks}")
    print(f"    video: avg_effort={video_cx.avg_effort():.2f}/10  "
          f"deadline_overruns={v_ov}/{video_cx.n_ticks}")
    # show salient-vs-routine effort spread (dial spends more on salient)
    for cx in (audio_cx, video_cx):
        sal = [e for e, _, surp in cx.effort_trace if surp >= 0.3]
        rout = [e for e, _, surp in cx.effort_trace if surp < 0.3]
        if sal and rout:
            print(f"    {cx.name}: salient-tick avg effort "
                  f"{sum(sal)/len(sal):.2f} vs routine "
                  f"{sum(rout)/len(rout):.2f} "
                  f"(spends more on salient: "
                  f"{sum(sal)/len(sal) > sum(rout)/len(rout)})")
    print()
    print("  MEMORY BOUNDED:")
    print(f"    budget={BUDGET_NODES} nodes / {BUDGET_BYTES//1024//1024}MB")
    print(f"    peak nodes={peak_nodes}  peak={peak_bytes/1024/1024:.1f}MB")
    print(f"    final nodes={s.node_count()}  "
          f"final={s.memory_total_bytes()/1024/1024:.1f}MB")
    print(f"    bounded over {elapsed:.0f}s: "
          f"{peak_nodes <= BUDGET_NODES * 1.5}")
    print("=" * 80)


if __name__ == "__main__":
    main()
