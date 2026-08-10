"""Substrate STT on LibriSpeech dev-clean.

2703 FLAC files, 16 kHz mono, mean ~8 s each. Multiple speakers,
real continuous English. Filename format:
  <speaker>-<chapter>-<utterance>.flac

Reports: signs minted, speaker-invariant signs, top-sign coverage
per speaker, throughput.
"""
import sys
sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

import os
import re
import time
from collections import Counter, defaultdict

import av
import numpy as np

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams


DATA_DIR = '/tmp/LibriSpeech/dev-clean'
_FN_RE = re.compile(r'(\d+)-(\d+)-(\d+)\.flac')


def list_files(limit=None):
    files = []
    for root, _, names in os.walk(DATA_DIR):
        for fn in names:
            m = _FN_RE.match(fn)
            if not m:
                continue
            sp, ch, ut = m.groups()
            files.append((os.path.join(root, fn), sp, ch, int(ut)))
    files.sort()
    return files[:limit] if limit else files


def load_flac(path):
    c = av.open(path)
    s = c.streams.audio[0]
    arr = np.concatenate([
        f.to_ndarray().flatten().astype(np.float32)
        for f in c.decode(s)
    ])
    rate = s.rate
    c.close()
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr / peak * 0.7).astype(np.float32), rate


def _sv_threshold(sub):
    for op in sub.nodes("Operation"):
        a = sub.node(op)["attrs"]
        if a.get("kind") == "sonority_valley":
            return a.get("depth_threshold"), a.get("last_tune_direction")
    return None, None


def _lex_state(sub):
    """Snapshot lex + Reconsider state. Returns the 'stt' lex's
    attrs along with the chunking Capability's mode, and the
    SubstrateRoot's last_tick_ms."""
    out = {
        "lex": None, "n_signs": 0, "n_bigrams": 0,
        "promotion_threshold": 8,
        "cap": None, "mode": "active", "tick_budget_ms": 0.0,
        "root": None, "last_tick_ms": 0.0,
    }
    for lex in sub.nodes("AcousticLexicon"):
        a = sub.node(lex)["attrs"]
        if a.get("name") == "stt":
            out["lex"] = lex
            out["n_signs"] = int(a.get("n_signs", 0))
            out["n_bigrams"] = sum(1 for _ in sub.nodes("BigramObservation"))
            out["promotion_threshold"] = int(a.get("promotion_threshold", 8))
            for cap in sub.neighbours(lex, "regulated_by"):
                ca = sub.node(cap)["attrs"]
                if ca.get("name") == "chunking":
                    out["cap"] = cap
                    out["mode"] = ca.get("mode", "active")
                    out["tick_budget_ms"] = float(ca.get("tick_budget_ms", 0.0))
                    break
            break
    for root in sub.nodes("SubstrateRoot"):
        out["root"] = root
        out["last_tick_ms"] = float(sub.node(root)["attrs"].get("last_tick_ms", 0.0))
        break
    return out


def ingest_all(pipe, sub, files):
    results = []  # (speaker, chapter, utt, signs, n_phon, dt, n_utts)
    tune_log = []
    seen_assessments = set()
    start = time.time()
    prev_thr = None
    prev_prom_thr = None
    prev_mode = None
    for i, (path, sp, ch, ut) in enumerate(files):
        samples, fs = load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs))
            pipe.attach(sub)
        t0 = time.time()
        try:
            signs = pipe.ingest(sub, samples)
        except Exception as e:
            print(f"  FAIL {path}: {e}")
            results.append((sp, ch, ut, None, None, None, 0))
            continue

        # Time the tick — the agent's Reconsider Rule reads
        # SubstrateRoot.last_tick_ms to decide whether the chunking
        # Capability should throttle. Wall-clock here, not CPU
        # time, since the agent cares about latency.
        # Fire-cap is high enough that the GC Rule can drain a
        # multi-thousand-edge follows pile in one or two ticks
        # once the agent's Assessment authorises it.
        s = _lex_state(sub)
        tick_start = time.perf_counter()
        sub.tick(50000)
        tick_ms = (time.perf_counter() - tick_start) * 1000.0
        if s["root"] is not None:
            sub.set_attr(s["root"], "last_tick_ms", float(tick_ms))
            sub.set_attr(s["root"], "tick_count",
                          int(sub.node(s["root"])["attrs"].get("tick_count", 0)) + 1)
            # Re-tick so the Reconsider Rule sees the fresh cost
            # and can flip mode in the same ingest.
            sub.tick(50000)

        thr, direction = _sv_threshold(sub)
        s2 = _lex_state(sub)

        # Report any new Assessments the agent has authored.
        if s2["cap"] is not None:
            for a in sub.neighbours(s2["cap"], "has_assessment"):
                aattrs = sub.node(a)["attrs"]
                key = ("assessment", repr(a))
                if key not in seen_assessments:
                    seen_assessments.add(key)
                    print(f"  [agent] file {i+1}: Assessment minted — "
                          f"kind={aattrs.get('kind')!r} "
                          f"cause={aattrs.get('cause')!r} "
                          f"action={aattrs.get('recommended_action')!r} "
                          f"(tick_ms={aattrs.get('tick_ms_at_diagnosis')}, "
                          f"signs={aattrs.get('signs_at_diagnosis')})",
                          flush=True)

        if prev_thr is None:
            prev_thr = thr
            prev_prom_thr = s2["promotion_threshold"]
            prev_mode = s2["mode"]
            tune_log.append((i + 1, "depth_threshold", thr, "init"))
            tune_log.append((i + 1, "promotion_threshold", prev_prom_thr, "init"))
            tune_log.append((i + 1, "chunking.mode", prev_mode, "init"))
        else:
            if thr is not None and abs(thr - (prev_thr or 0)) > 1e-6:
                tune_log.append((i + 1, "depth_threshold", thr, direction))
                print(f"  [agent] file {i+1}: depth_threshold "
                      f"{prev_thr:.3f} -> {thr:.3f} ({direction})", flush=True)
                prev_thr = thr
            if s2["promotion_threshold"] != prev_prom_thr:
                tune_log.append((i + 1, "promotion_threshold", s2["promotion_threshold"], "agent"))
                print(f"  [agent] file {i+1}: promotion_threshold "
                      f"{prev_prom_thr} -> {s2['promotion_threshold']}", flush=True)
                prev_prom_thr = s2["promotion_threshold"]
            if s2["mode"] != prev_mode:
                tune_log.append((i + 1, "chunking.mode", s2["mode"], "reconsider"))
                print(f"  [agent] file {i+1}: chunking.mode "
                      f"{prev_mode} -> {s2['mode']} "
                      f"(last_tick_ms={s2['last_tick_ms']:.1f}, "
                      f"budget={s2['tick_budget_ms']:.1f})", flush=True)
                prev_mode = s2["mode"]

        dt = time.time() - t0
        n_phon = sum(1 for _ in sub.nodes("Phoneme"))
        results.append((sp, ch, ut, signs, n_phon, dt, len(signs)))
        if (i + 1) % 50 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            total_utts = sum(r[6] for r in results if r[3] is not None)
            print(f"  {i+1}/{len(files)}  phonemes={n_phon}  "
                  f"signs={s2['n_signs']}  bigrams={s2['n_bigrams']}  "
                  f"mode={s2['mode']}  tick_ms={s2['last_tick_ms']:.1f}/"
                  f"{s2['tick_budget_ms']:.0f}  "
                  f"thr={thr}  prom_thr={s2['promotion_threshold']}  "
                  f"{rate:.2f} files/sec  elapsed {elapsed:.1f}s",
                  flush=True)
    return results, pipe, tune_log


def report(sub, results):
    print()
    print("=" * 72)
    print("LibriSpeech dev-clean substrate-STT benchmark report")
    print("=" * 72)

    successes = [r for r in results if r[3] is not None]
    failures = len(results) - len(successes)
    print(f"\nProcessed: {len(successes)}/{len(results)}  "
          f"failures: {failures}")

    n_phon = sum(1 for _ in sub.nodes("Phoneme"))
    n_sign = sum(1 for _ in sub.nodes("AcousticSign"))
    n_utt = sum(1 for _ in sub.nodes("Utterance"))
    total_signs_from_files = sum(r[6] for r in successes)
    print(f"Substrate state: {n_phon} Phonemes, "
          f"{n_sign} AcousticSigns, {n_utt} Utterances")
    print(f"Mean Utterances per file: "
          f"{total_signs_from_files / max(len(successes), 1):.1f}")

    # Per-speaker stats.
    speaker_signs = defaultdict(Counter)
    for sp, ch, ut, signs, _, _, _ in successes:
        for s in signs:
            speaker_signs[sp][s] += 1
    speakers = sorted(speaker_signs)
    print(f"\nSpeakers in dataset: {len(speakers)}")

    # Cross-speaker: signs fired by >1 speaker.
    speakers_per_sign = defaultdict(set)
    for sp, _, _, signs, _, _, _ in successes:
        for s in signs:
            speakers_per_sign[s].add(sp)
    n_cross = sum(1 for v in speakers_per_sign.values() if len(v) > 1)
    print(f"\nSpeaker invariance:")
    print(f"  signs fired by >1 speaker: {n_cross} "
          f"({100*n_cross/max(len(speakers_per_sign),1):.1f}%)")
    print(f"  signs fired by 1 speaker:  "
          f"{len(speakers_per_sign) - n_cross}")

    # Sign usage histogram — how repeatedly is the top sign used?
    sign_total_uses: Counter = Counter()
    for sp, _, _, signs, _, _, _ in successes:
        for s in signs:
            sign_total_uses[s] += 1
    top = sign_total_uses.most_common(10)
    print(f"\nTop 10 most-used signs:")
    for sig, n in top:
        sp_set = speakers_per_sign[sig]
        print(f"  sign {sig}: used {n} times across "
              f"{len(sp_set)} speakers")

    # Lexicon-growth saturation: count how many distinct signs each
    # speaker contributed; ratio of speaker-specific signs over time.
    print(f"\nPer-speaker lexicon (signs only that speaker fired):")
    print(f"  {'speaker':<12}{'total_signs':<14}{'unique_to_speaker':<20}{'shared_with_others':<20}")
    for sp in speakers:
        sigs = set(speaker_signs[sp].keys())
        unique = sum(1 for s in sigs if len(speakers_per_sign[s]) == 1)
        shared = len(sigs) - unique
        print(f"  {sp:<12}{len(sigs):<14}{unique:<20}{shared:<20}")

    # Timing.
    times = [r[5] for r in successes if r[5] is not None]
    if times:
        print(f"\nTiming:")
        print(f"  total processing: {sum(times):.1f}s")
        print(f"  per file: avg={np.mean(times)*1000:.0f}ms "
              f"median={np.median(times)*1000:.0f}ms "
              f"max={max(times)*1000:.0f}ms")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None,
                        help='process only the first N files')
    args = parser.parse_args()

    files = list_files(limit=args.limit)
    print(f"Found {len(files)} files in {DATA_DIR}")
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=16000))
    pipe.attach(sub)
    results, pipe, tune_log = ingest_all(pipe, sub, files)
    report(sub, results)
    print(f"\nAgent tuning history ({len(tune_log)} entries):")
    for idx, attr, val, dirn in tune_log:
        print(f"  file {idx}: {attr}={val} ({dirn})")


if __name__ == "__main__":
    main()
