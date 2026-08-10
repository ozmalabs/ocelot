"""AUTONOMOUS WATCH — the jabberwock roams the real library on its own, bounded.

Composes the whole arc into one self-running, self-bounding loop:
  choose (curiosity, jellyfin_world) -> watch a window (audio->shared lexicon, video
  temporal structure) -> SELF-BOUND (memory_self_management: the agent's compression
  selector forgets the per-input firehose, keeps the saturating lexicon, persists to
  disk) -> re-choose (unseen series) -> repeat.

So it can run indefinitely without OOM: a hard process memory cap is the safety net,
and the agent's own faculty is the real bound (node_count returns to baseline after
each video). State persists to disk each round -> resumable across sessions.

Run:  python -m scripts.autonomous_watch [rounds] [window_s] [budget_nodes]
"""
from __future__ import annotations

import os
import resource
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
WINDOW = int(sys.argv[2]) if len(sys.argv) > 2 else 60
BUDGET = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
TIME_LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else 0   # seconds; 0 = use ROUNDS
V_FRAMES = 120
MEM_CAP_GB = 8
BUDGET_BYTES = int(sys.argv[5]) if len(sys.argv) > 5 else 64 * 1024 * 1024  # byte bound
STATE = "/tmp/jabberwock_state/autonomous.json"

# --- safety net: hard process memory cap (the faculty is the real bound) ---
try:
    cap = MEM_CAP_GB * 1024 ** 3
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
except Exception as e:
    print(f"  (could not set RLIMIT_AS: {e})")

import substrate_rs as srs                                           # noqa: E402
from substrate_rs import audio as a, speech as sp, video as V        # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                     # noqa: E402
from domains import memory_self_management as msm                    # noqa: E402
from domains import long_term_memory as ltmod                        # noqa: E402
from domains import self_persistence as selfp                        # noqa: E402

LTM_DIR = "/tmp/jabberwock_state/longterm"
HOT_WINDOW = 3       # how many shows' records stay resident in working memory


def _vstream(url):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=index", "-of", "csv=p=0", url],
                         capture_output=True, text=True, timeout=60).stdout.strip()
    return int(out) if out else 0


def watch_one(s, jf, lex, series_item, fac=None):
    eps = jf.episodes(series_item["id"], limit=1)
    if not eps:
        return None
    url = jf.stream_url(eps[0]["id"])
    tmp = tempfile.mktemp(suffix=".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0", "-t", str(WINDOW),
                    "-i", url, "-vn", "-ar", "48000", "-ac", "1", "-c:a", "libopus",
                    tmp], check=True, timeout=240)
    acn = a.open_container(s, tmp); asid = a.add_stream(s, acn)
    a.parse_stream(s, acn, asid); a.parse_native(s, acn, asid)
    res = sp.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                           fs=48000, threshold=0.80)
    a.close_container(acn); os.unlink(tmp)
    # STREAMING bound: shed the firehose AS it arrives (audio done) so a pathological
    # episode cannot spike the store before the video firehose lands on top.
    if fac is not None:
        fac.forget_over_budget(s)
    new = sum(1 for *_, i in res if i)
    vcn = V.open_container(s, url)
    vsid = V.add_stream(s, vcn, _vstream(url), export_motion_vectors=True)
    V.parse_stream(s, vcn, vsid, frame_limit=V_FRAMES)
    V.close_container(vcn)
    if fac is not None:
        fac.forget_over_budget(s)            # shed the video firehose too, in-stream
    return {"series": series_item["name"], "utts": len(res), "new": new}


def main():
    jf = JellyfinWorld().connect()
    print("=" * 80)
    print(f"AUTONOMOUS WATCH — {ROUNDS} rounds, {WINDOW}s each, budget {BUDGET} nodes, "
          f"cap {MEM_CAP_GB}GB")
    print("=" * 80)
    s = srs.Substrate()
    a.seed_audio_grammar(s); a.seed_native_codec_grammar(s); sp.seed_speech_grammar(s)
    V.seed_video_grammar(s)
    lex = sp.open_lexicon(s)
    jf.ingest_catalog(s)
    if selfp.state_exists(STATE):
        selfp.load_state(s, STATE)
        print(f"  resumed from disk: {STATE}")
    fac = msm.MemorySelfManagement(budget_nodes=BUDGET,
                                   budget_bytes=BUDGET_BYTES)
    ltm = ltmod.LongTermMemory(LTM_DIR, hot_window=HOT_WINDOW)   # the disk shuffle tier

    all_series = jf.catalog(("Series",))
    seen_signs, watched = set(), []
    t0 = time.time()
    print(f"\n  mode: {'time ' + str(TIME_LIMIT) + 's' if TIME_LIMIT else str(ROUNDS)+' rounds'}")
    print(f"  {'rnd':>3} {'t':>4} {'chose':<24} {'new':>4} {'lex':>5} {'peak':>6} "
          f"{'RAM':>6} {'MB':>6} {'clstr':>5} {'recall':>10}")
    r = 0
    while True:
        r += 1
        elapsed = time.time() - t0
        if TIME_LIMIT and elapsed >= TIME_LIMIT:
            break
        if not TIME_LIMIT and r > ROUNDS:
            break
        picks = jf.choose(s, n=1, watched_series=watched)
        if not picks:
            # curiosity exhausted -> REVISIT (round-robin), which triggers recall
            if not all_series:
                print("  (no titles)"); break
            p = all_series[r % len(all_series)]
        else:
            p = picks[0]
        # if seen before, RECALL by ORDER-N SHAPE DESCENT (storage = retrieval key):
        # build the query's shape from what we know of the show, descend the order-N
        # shape index to its cluster, page the whole drawer hot.
        recalled = "-"
        if ltm.findable(p["name"]):
            qa = {"new_signs": len(s.nodes("AcousticSign")), "utts": 0, "round": r}
            d = ltm.recall_by_shape(s, qa, r)
            if d is not None:
                recalled = f"shape->{d['cluster_id'][4:][:8]}"
        try:
            rec = watch_one(s, jf, lex, p, fac=fac)
        except Exception as e:
            print(f"  {r:>3} {int(elapsed):>4} {p['name'][:23]:<24}  "
                  f"WATCH-SKIP ({type(e).__name__})")
            watched.append(p["name"]); continue
        if not rec:
            watched.append(p["name"]); continue
        peak = s.node_count()
        tr = fac.observe_and_bound(s, persist_path=STATE)   # SENSORY forget + persist
        # CONSOLIDATE this show's distinctive learning to long-term disk, then SHUFFLE
        mr = s.add_node("MemoryRecord", {"show": rec["series"], "round": r,
                                         "new_signs": rec["new"], "utts": rec["utts"]})
        ltm.consolidate(s, rec["series"], mr, r, meta={"new_signs": rec["new"]})
        ltm.shuffle(s, r)                                   # evict cold records -> disk
        watched.append(rec["series"])
        signs_now = len(s.nodes("AcousticSign"))
        seen_signs.add(signs_now)
        st = ltm.stats()
        mb = tr["bytes_after"] / (1024 * 1024)
        print(f"  {r:>3} {int(elapsed):>4} {rec['series'][:23]:<24} {rec['new']:>4} "
              f"{signs_now:>5} {peak:>6} {tr['total_after']:>6} {mb:>6.1f} "
              f"{st['index_clusters']:>5} {recalled:>10}", flush=True)

    final = s.node_count()
    final_bytes = s.memory_total_bytes()    # the Rust faculty's byte estimate
    st = ltm.stats()
    state_mb = (os.path.getsize(STATE) / (1024 * 1024)) if os.path.exists(STATE) else 0
    print(f"\n  AUTONOMOUS SESSION DONE — {len(watched)} titles watched. 3 memory tiers:")
    print(f"    SENSORY  : firehose FORGOTTEN in-stream (keep_value=salience+order_n, "
          f"byte-bound) -> bounded, no spike. final {final} nodes (budget {BUDGET}), "
          f"{final_bytes/1024/1024:.1f}MB (budget {BUDGET_BYTES/1024/1024:.0f}MB).")
    print(f"    WORKING  : lexicon hot in RAM, accumulated "
          f"{len(s.nodes('AcousticSign'))} signs (hot window {HOT_WINDOW}).")
    print(f"    LONG-TERM: {st['on_disk']} per-show records on DISK; "
          f"index = ORDER-N SHAPE RULE over {st['index_clusters']} CLUSTERS "
          f"(bounded, NOT per-item); recall by shape descent (Rust faculty).")
    print(f"    state file: {state_mb:.1f}MB (was 461MB when broken); "
          f"persisted (resumable): {os.path.exists(STATE)}; store: {LTM_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
