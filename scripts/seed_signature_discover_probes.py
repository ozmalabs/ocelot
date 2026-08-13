#!/usr/bin/env python3
"""scripts/seed_signature_discover_probes.py — DISCOVERY, not measurement.

Boots a full agent, mints `SeedSummary.where_signature_json` via the new
`domains.seed_signature.ensure_seed_signature`, and mechanically searches the
real, skippable `SeedSummary` population for genuine Class A ("where-native":
a word present in some seed's structural signature but absent from that
seed's own `keywords_text`) and Class B ("name-native": a word present in a
seed's `keywords_text` — trivially most seed ids/rule names) probe
candidates, WITHOUT inventing any. This is the seed-grain analogue of
`scratch_investigate/discover_probes2.py`, the tool
`RULE_SIGNATURE_SLICE_PREREG.md` §AR1 cites as its own precedent for
"probes are discovered by scanning real data, never hand-guessed."

Read-only. No production file (`domains/reflective_faculty.py`) touched or
imported for writing. Output feeds
`docs/research/engine_substrate/SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md`'s
oracle registration.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
from domains import seed_signature as ssig  # noqa: E402


class _Agent:
    """Minimal duck-typed wrapper -- identical shape to
    scripts/rule_signature_measure.py's own `_Agent` (harness glue only)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


_WORD_RE = re.compile(r"[a-z][a-z_]{3,}")


def _words(text: str) -> set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


def main():
    t0 = time.time()
    print("Booting full agent (load_all_seeds) ...", flush=True)
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    print(f"  loaded {rep['loaded']}/{rep['total']} in {time.time()-t0:.1f}s", flush=True)

    t1 = time.time()
    n_touched = ssig.ensure_seed_signature(s)
    print(f"ensure_seed_signature: minted {n_touched} new attrs in {time.time()-t1:.1f}s", flush=True)

    n_total, n_skippable = 0, 0
    class_a = []   # (seed_id, word) -- in signature, NOT in keywords_text
    class_b = []   # (seed_id, word) -- in keywords_text (trivial, most seeds)
    per_seed = {}
    for n in s.nodes("SeedSummary"):
        at = s.node(n)["attrs"]
        n_total += 1
        if at.get("skippable") != 1.0:
            continue
        n_skippable += 1
        sid = at.get("seed_id")
        kw_text = (at.get("keywords_text") or "").lower()
        sig_json = at.get("where_signature_json") or ""
        if not sig_json:
            continue
        sig_words = _words(sig_json)
        kw_words = _words(kw_text)
        # Class A candidates: a word that appears as a SUBSTRING somewhere in
        # the structural JSON blob but is not a substring of keywords_text at
        # all (mirrors the StringIndexOf semantics the production Argmax
        # itself uses -- substring, not exact word membership).
        for w in sig_words:
            if len(w) < 5:
                continue
            if w in kw_text:
                continue
            if w in sig_json:
                class_a.append((sid, w))
        for w in kw_words:
            if len(w) < 5:
                continue
            if w in kw_text:
                class_b.append((sid, w))
        per_seed[sid] = {"kw_len": len(kw_text), "sig_len": len(sig_json),
                          "n_sig_words": len(sig_words)}

    print(f"\nSeedSummary population: {n_total} total, {n_skippable} skippable", flush=True)
    print(f"Class A candidates (word in signature, NOT in keywords_text): {len(class_a)}", flush=True)
    print(f"Class B candidates (word in keywords_text): {len(class_b)}", flush=True)

    out = {
        "n_total": n_total, "n_skippable": n_skippable,
        "class_a_sample": class_a[:40],
        "class_a_count": len(class_a),
        "class_b_sample": class_b[:20],
        "class_b_count": len(class_b),
        "per_seed_sample": dict(list(per_seed.items())[:10]),
    }
    out_path = os.path.join(ROOT, "scripts", "seed_signature_discover_probes_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWritten to {out_path}")
    print(f"Total wall time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
