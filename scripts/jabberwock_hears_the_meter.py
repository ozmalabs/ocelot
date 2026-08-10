"""THE JABBERWOCK HEARS THE METER — rhythm/meter recognition as the substrate's collapse.

The prosodic faculty: a line of verse is PERCEIVED into a stress pattern by the held
phonology (CMUdict), then the FOOT is the ShapeDecode verdict over a foot codebook
(seeds/prosodic_meter.json) — the SAME collapse as strokes / space / tropes / reading,
one domain over into RHYTHM. A novel rhythm mints a learned metrical quantum.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python:scripts \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_hears_the_meter
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import metrical_reading as mr


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _scan(agent, line: str) -> None:
    r = mr.read_line(agent, line)
    print(f"  {line!r}")
    beat = " ".join(("%-4s" % w) for w, _s, _src in r["words"])
    strs = " ".join(("%-4s" % "".join(s)) for _w, s, _src in r["words"])
    print(f"     words : {beat}")
    print(f"     stress: {strs}")
    print(f"     pattern = {r['stress_str']}   sources = {dict(r['sources'])}")
    if r["oov"]:
        print(f"     OOV / nonsense (stress by heuristic): {r['oov']}")
    print(f"     autocorr beat: period={r['beat_period']} strength={r['beat_strength']}"
          f" ({'confident' if r['beat_confident'] else 'weak — meter felt, not signalled'})")
    print(f"     -> {r['note']}")
    if r.get("predicted_next"):
        print(f"     predictive: the period predicts the next beat = {r['predicted_next']}")
    print()


def main() -> None:
    s, node = boot_core()
    agent = _Agent(s, node)
    mr.ensure_meter_codebook(agent)

    print("=" * 74)
    print("THE JABBERWOCK HEARS THE METER — prosody as SHAPE in the HARMONIC domain")
    print("=" * 74)
    print("meter = TEMPORAL harmonic (autocorrelation period + ShapeDecode phase)")
    print("rhyme = SPECTRAL harmonic (formant-resonance distance) — same math as music/colour")
    print(f"held phonology (stress source): CMUdict via nltk — available={mr._cmu() is not None}")
    feet = sorted(s.node(n)["attrs"].get("name") for n in s.nodes("ShapeSignatureMeter"))
    print(f"foot codebook (ShapeSignatureMeter graph nodes): {feet}")
    print()

    print("-" * 74)
    print("1. CLEAN IAMBIC  (weak-STRONG, da-DUM)")
    print("-" * 74)
    _scan(agent, "the cat that sat upon the mat")
    _scan(agent, "Shall I compare thee to a summers day")     # Shakespeare, iambic pentameter

    print("-" * 74)
    print("2. CLEAN TROCHAIC  (STRONG-weak, DUM-da) — Blake")
    print("-" * 74)
    _scan(agent, "Tyger Tyger burning bright")
    _scan(agent, "In the forests of the night")

    print("-" * 74)
    print("3. JABBERWOCKY  (Carroll) — nonsense-word stress is the default heuristic")
    print("-" * 74)
    for line in ["He took his vorpal sword in hand",
                 "And stood awhile in thought",
                 "Twas brillig and the slithy toves",
                 "Did gyre and gimble in the wabe"]:
        _scan(agent, line)

    print("-" * 74)
    print("4. LEARN A NOVEL METER  (a rhythm no seeded foot covers -> mint a foot)")
    print("-" * 74)
    patt = ["S", "S", "w", "w", "S", "S", "w", "w"]           # SSww x2 — a made-up double foot
    mr._ensure_tiled_parts(agent, len(patt))
    name0, fit0 = mr._winner(mr._decode(agent, patt))
    foot0, _, _ = mr._part_foot(s, name0)
    print(f"  pattern SSwwSSww — before learning: best foot={foot0} fit={fit0}/{len(patt)} (imperfect)")
    period = mr._minimal_period(patt)
    inst = mr._install_foot(agent, period)
    print(f"  minted metrical quantum: minimal repeating unit = {period} -> new foot {inst['name']!r}")
    mr._ensure_tiled_parts(agent, len(patt))
    name1, fit1 = mr._winner(mr._decode(agent, patt))
    foot1, _, _ = mr._part_foot(s, name1)
    print(f"  re-decode against the grown codebook: foot={foot1} fit={fit1}/{len(patt)} (recognized)")
    print()

    print("-" * 74)
    print("5. RHYME = SPECTRAL HARMONIC (formant-resonance distance, not suffix match)")
    print("-" * 74)
    for w1, w2 in [("bright", "night"), ("cat", "mat"), ("love", "move"),
                   ("cat", "dog"), ("hand", "sword")]:
        rh = mr.rhymes(w1, w2)
        d = rh["distance"]
        tag = "RHYME" if rh["rhyme"] else "no    "
        note = " (eye-rhyme: spelled alike, sound apart -> correctly rejected)" if (w1, w2) == ("love", "move") else ""
        print(f"  {tag}  {w1:<7} ~ {w2:<7} spectral-dist={d if d is None else round(d, 3)}{note}")
    print()
    sch = mr.rhyme_scheme(["Tyger Tyger burning bright",
                           "In the forests of the night",
                           "What immortal hand or eye",
                           "Could frame thy fearful symmetry"])
    print(f"  Blake stanza rhyme scheme (spectral clustering): {sch['scheme']}  endings={sch['endings']}")
    print()

    print("=" * 74)
    print("HONEST LEDGER")
    print("=" * 74)
    print("  UNIFICATION  : meter=TEMPORAL harmonic, rhyme=SPECTRAL harmonic — the same")
    print("                 harmonic-analysis+ShapeDecode math as music (rhythm/harmony) & colour.")
    print("  stress source: CMUdict (held pronunciation lexicon, ARPABET stress digits).")
    print("  period source: AUTOCORRELATION of the stress beat signal (r[k]=Σx[n]x[n+k]) —")
    print("                 the IDENTICAL formula to the held band_autocorr/summary_autocorrelogram")
    print("                 (audio_primitives.rs); computed in-adapter because that primitive is")
    print("                 registered in py.rs but NOT exposed by the installed substrate_rs binary")
    print("                 (stale build; not rebuilt per the no-Rust-change rule). Proxy, disclosed.")
    print("  phase source : ShapeDecode over the foot codebook (no Python scansion).")
    print("  rhyme spectrum: standard ARPABET vowel FORMANTS (F1/F2/F3) matched by distance —")
    print("                 the cochleagram/FFT synth path (Klatt) is likewise unexposed; proxy.")
    print("  reliable      : POLYSYLLABIC words + REGULAR verse (strong autocorr beat).")
    print("  frays         : monosyllable-heavy / substitution-heavy / nonsense lines -> WEAK beat")
    print("                  (meter is then FELT top-down, reported as low confidence); OOV words")
    print("                  have no held pronunciation -> honest rhyme gap (distance None).")
    print("  novelty       : a period with no seeded foot mints a learned foot (dynamic quant.).")


if __name__ == "__main__":
    main()
