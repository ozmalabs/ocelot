#!/usr/bin/env python3
"""conversation_steering v2.1.0 -- the steering aperture resolves definitional qualia.

Tranche 17 grounds a held word with no WordNet sense through its held
definition (seeds/lexical_qualia.json v1.1.0): its quale is
`Quale{name:"definition:<word>", dimension:"lexical:definition", genus}`,
whose has_quale parents are the genus's noun senses. That quale replaces the
word's former `lexical:identity` quale, so the steering aperture must resolve
`lexical:definition` for parity: the word still meets itself (the definition
quale has extent 1) and now also meets other words through its genus senses
(already resolved as `lexical:sense`). Data-only change to the QualiaAperture
node; the rules are unchanged. Idempotent; preserves indent=1 + newline.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/conversation_steering.json"
VERSION = "2.1.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
ap = [n for n in d["nodes"] if n["type"] == "QualiaAperture" and n["attrs"].get("name") == "steering"]
assert len(ap) == 1, len(ap)
res = list(ap[0]["attrs"]["resolves"])
if "lexical:definition" not in res:
    res.insert(res.index("lexical:identity"), "lexical:definition")
ap[0]["attrs"]["resolves"] = res
ap[0]["attrs"]["description"] = (
    "which qualia decide a steer match: WordNet senses, the definition quale of a held word grounded "
    "through its definition's genus, and the identity quale of an ungrounded held word; a shared quale "
    "counts only if at most max_extent_per_mille/1000 of held words share it. Agent-editable data.")
d["_steering_note"] = (d.get("_steering_note", "") + " || v2.1.0 (tranche 17): the steering aperture also "
                       "resolves lexical:definition qualia -- see scripts/gen_steer_aperture_definition.py.")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("conversation_steering", VERSION, res)
