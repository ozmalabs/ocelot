#!/usr/bin/env python3
"""fetch_lingua_libre — OFFLINE WORLD-PREP tool (NOT agent code).

Fetch a small, multilingual subset of Lingua Libre (the Wikimedia project of
recorded isolated-word pronunciations — free, CC, many languages, many speakers,
NO access gate) into the 8 kHz isolated-word cache the pedagogical loader reads.

This is the gateless, multilingual REAL teaching voice for the self-directed
speech world (docs/research_pedagogical_corpora.md): the clear citation-form
pronunciation register the PARENT can utter instead of synthetic espeak.

ACCESS PATH (verified live, 2026-06):
  · SPARQL endpoint https://lingualibre.org/sparql (Blazegraph, 78M triples).
  · Data model: each Record item has
        prop:P4 -> language  (entity:Q22=en, Q21=fr, Q24=de, Q386=es)
        prop:P7 -> transcription (the spoken word, a literal string)
        prop:P5 -> speaker   (an entity; the speaker who voiced it)
        prop:P3 -> audio file (a Commons Special:FilePath URL, a 16-bit PCM .wav)
  · The audio is real WAV on Wikimedia Commons (PCM s16, mono, 44.1 kHz),
    fetched by HTTP from Special:FilePath; resampled here to 8 kHz mono.

This is a WORLD ADAPTER prep step: pure I/O, no agent decisions. It writes
{word}_{speaker}_{idx}.wav into ~/.cache/ozma/lingualibre/<lang>/ so the loader's
ll_speakers()/ll_index_for() are pure filename filters — IDENTICAL LOSO mechanic
to FSDD. Held-out speakers are a filename filter, never banked.

Usage:
  python3 scripts/fetch_lingua_libre.py            # fetch en/fr/de/es digits
  python3 scripts/fetch_lingua_libre.py --report   # query coverage only, no download
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

ENDPOINT = "https://lingualibre.org/sparql"
UA = "ozma-research/1.0 (gamma-substrate; hrdwrbob@gmail.com)"
CACHE = Path.home() / ".cache" / "ozma" / "lingualibre"
TARGET_FS = 8000

# Lingua Libre language entity Q-codes (verified by probing transcriptions).
LANG_Q = {"en": "Q22", "fr": "Q21", "de": "Q24", "es": "Q386"}

# The digit words per language, matching _DIGIT_WORDS in self_directed_speech_world.
# Loader filenames use the ASCII forms below; the LL transcription may carry
# diacritics (e.g. German "fünf"), mapped via _XLIT so the cache key is ASCII-safe.
DIGITS = {
    "en": ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"],
    "fr": ["zero", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
           "huit", "neuf"],
    "de": ["null", "eins", "zwei", "drei", "vier", "funf", "sechs", "sieben",
           "acht", "neun"],
    "es": ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
           "ocho", "nueve"],
}
# ASCII loader-word -> the LL transcription strings to accept for it.
_TRANSCRIPTIONS = {"funf": ["funf", "fünf"]}


def _accept_strings(word):
    return _TRANSCRIPTIONS.get(word, [word])


def _which(name):
    from shutil import which
    return which(name)


def sparql(query, timeout=60):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        url, headers={"Accept": "application/sparql-results+json",
                      "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["results"]["bindings"]


def query_records(lang):
    """Return [(word, speaker_id, file_url), ...] for one language's digit words.
    word is the ASCII loader key; speaker_id is the LL entity local name (Q-id);
    file_url is the Commons Special:FilePath .wav URL."""
    Q = LANG_Q[lang]
    accept = {}                     # transcription-string -> loader word
    for w in DIGITS[lang]:
        for s in _accept_strings(w):
            accept[s] = w
    vals = " ".join('"%s"' % s.replace('"', '') for s in accept)
    query = f'''
PREFIX entity: <https://lingualibre.org/entity/>
PREFIX prop: <https://lingualibre.org/prop/direct/>
SELECT ?t ?spk ?file WHERE {{
  VALUES ?t {{ {vals} }}
  ?r prop:P4 entity:{Q} ;
     prop:P7 ?t ;
     prop:P5 ?spk ;
     prop:P3 ?file .
}}'''
    rows = []
    for b in sparql(query):
        t = b["t"]["value"]
        word = accept.get(t)
        if word is None:
            continue
        spk = b["spk"]["value"].rstrip("/").split("/")[-1]    # entity Q-id
        rows.append((word, spk, b["file"]["value"]))
    return rows


def _safe_speaker(spk):
    """Filename-safe, lowercase speaker token (the LOSO filter key). LL speaker
    ids are like 'Q19778' -> 'q19778'."""
    return re.sub(r"[^a-z0-9]", "", spk.lower())


def download_resample(url, out_path):
    """Fetch the Commons WAV and resample to 8 kHz mono 16-bit PCM at out_path.
    Pure boundary I/O (HTTP fetch + ffmpeg resample). Returns True on success."""
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "raw")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
        except Exception as e:
            print(f"    FETCH FAIL {url}: {e}", file=sys.stderr)
            return False
        with open(raw, "wb") as f:
            f.write(data)
        if _which("ffmpeg"):
            try:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                                "-ar", str(TARGET_FS), "-ac", "1",
                                "-sample_fmt", "s16", out_path],
                               check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError as e:
                print(f"    FFMPEG FAIL {url}: {e.stderr[:200]!r}", file=sys.stderr)
                return False
        # No ffmpeg: only usable if already a readable wav; rare in this env.
        try:
            with wave.open(raw, "rb"):
                pass
            os.replace(raw, out_path)
            return True
        except Exception:
            return False


def fetch_lang(lang, limit_per_word=None):
    rows = query_records(lang)
    out_dir = CACHE / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    # idx counter per word so filenames are {word}_{speaker}_{idx}.wav.
    counts = {}
    written = 0
    by_word = {}
    for word, spk, url in rows:
        by_word.setdefault(word, []).append((spk, url))
    for word, items in by_word.items():
        if limit_per_word:
            items = items[:limit_per_word]
        for spk, url in items:
            safe = _safe_speaker(spk)
            idx = counts.get((word, safe), 0)
            counts[(word, safe)] = idx + 1
            fn = f"{word}_{safe}_{idx}.wav"
            out_path = str(out_dir / fn)
            if os.path.exists(out_path):
                written += 1
                continue
            if download_resample(url, out_path):
                written += 1
            time.sleep(0.05)            # be polite to Commons
    return written, len(rows)


def report():
    print("Lingua Libre digit coverage (speakers x recordings per word):\n")
    for lang in LANG_Q:
        rows = query_records(lang)
        per = {}
        spk = {}
        for word, s, _ in rows:
            per[word] = per.get(word, 0) + 1
            spk.setdefault(word, set()).add(s)
        print(f"=== {lang} ({LANG_Q[lang]}) ===")
        tot = 0
        for w in DIGITS[lang]:
            n = per.get(w, 0)
            ns = len(spk.get(w, ()))
            tot += n
            print(f"  {w:8s} speakers={ns:>3} recordings={n:>3}")
        print(f"  TOTAL recordings={tot}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true",
                    help="query coverage only, no download")
    ap.add_argument("--langs", default="en,fr,de,es")
    ap.add_argument("--limit-per-word", type=int, default=None,
                    help="cap clips per word per language (smaller subset)")
    args = ap.parse_args()
    if args.report:
        report()
        return
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    grand = 0
    for lang in langs:
        print(f"Fetching {lang} ...", flush=True)
        w, n = fetch_lang(lang, limit_per_word=args.limit_per_word)
        print(f"  {lang}: wrote {w}/{n} clips -> {CACHE / lang}", flush=True)
        grand += w
    print(f"\nDONE: {grand} clips in {CACHE}")


if __name__ == "__main__":
    main()
