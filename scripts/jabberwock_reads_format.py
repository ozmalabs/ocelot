"""jabberwock_reads_format — the jabberwock reads a file's FORMAT as a signal
channel PARALLEL to its content.

Formatting is one GENERIC function at every order-N scale: PROSODY (line breaks =
rhythm, format-AS-content), MEDIUM (a hard-wrap = a file laid out for a terminal),
STRUCTURE (indentation = code/nesting), REGISTER (a plain block = a letter). The
reader had only prosody, so it mistook a hard-wrapped Grimm tale for verse. This
script shows the generic format faculty (a ShapeDecode collapse over a layout-
function codebook) decoding four format kinds, and the CONSEQUENCE: the raw
hard-wrapped Grimm corpus now reads as prose and the antagonist chain fires.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_format.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                        # noqa: E402
from domains import dictionary_lexicon as dl                     # noqa: E402
from domains import format_channel as fc                         # noqa: E402
import domains.reading_corpus as rc                              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


JABBERWOCKY = (
    "'Twas brillig, and the slithy toves\n"
    "Did gyre and gimble in the wabe:\n"
    "All mimsy were the borogoves,\n"
    "And the mome raths outgrabe."
)
CODE = ("def solve(xs):\n"
        "    total = 0\n"
        "    for x in xs:\n"
        "        if x > 0:\n"
        "            total += x\n"
        "    return total")
LETTER = ("Dear Sir,\n\n"
          "I am writing to inform you that the shipment has arrived.\n"
          "Please find enclosed the invoice for your records.\n\n"
          "Yours faithfully,\nJ. Smith")


def main() -> None:
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)

    grimm = [src for src in rc.SOURCES if src["key"] == "grimm"]
    by = {u["label"]: u["text"] for u in rc.load_units(sources=grimm)}

    print("=" * 70)
    print("FORMAT AS A GENERIC SIGNAL CHANNEL — one collapse, four functions")
    print("=" * 70)
    samples = [
        ("Grimm tale (raw hard-wrap)", by["OLD SULTAN"]),
        ("Jabberwocky (verse)", JABBERWOCKY),
        ("Python source (code)", CODE),
        ("A letter (register)", LETTER),
    ]
    for label, text in samples:
        v = fc.decode_format(ag, text, record=False)
        f = v["features"]
        print(f"\n{label}")
        print(f"  features: wrap_pressure={f['wrap_pressure']} "
              f"local_rhyme={f['local_rhyme']} indent={f['indent']} "
              f"(mean_len={f['mean_len']} max_len={f['max_len']})")
        print(f"  tokens:   {v['tokens']}")
        print(f"  FORMAT -> {v['format'].upper()}  (is_prosody={v['is_prosody']}, "
              f"fit={v['fit']}/3)")

    print("\n" + "=" * 70)
    print("CONSEQUENCE — the agent reflows the MEDIUM wrap; the chain fires on RAW")
    print("=" * 70)
    import jabberwock_reads_a_tale as jt
    recs = jt.run()
    for r in recs:
        a = r["arc_antagonist"]
        print(f"  {r['label']:32s} decided_by={a['decided_by']}")
    print("\n(NOTE: decided_by=opposition is the verified-correct mechanism the "
          "format\n fix unmasks. The antagonist NAMING still rides on the "
          "parse/coref layer\n below format — a separate, documented frontier.)")


if __name__ == "__main__":
    main()
