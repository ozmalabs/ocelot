#!/usr/bin/env python3
"""Tranche 7: add ComposerCue{relation_head:'replay', composer:'experiment',
priority:4.5} to seeds/composer_dispatch.json (v1.1.0). A 'replay' head is
grounded only by the conversation-experiment bundle, so a concern carrying it
is a conversation experiment by construction; it must outrank 'communicate'
(priority 5), whose RelationCue keywords substring-match ordinary content
words in reported concerns ("speaker" contains "speak"), which sent
"you trust that speaker too much..." to compose_communicate_rule and authored
no experiment. Idempotent."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "seeds/composer_dispatch.json"
d = json.loads(P.read_text())
if any(n["type"] == "ComposerCue" and n["attrs"].get("relation_head") == "replay" for n in d["nodes"]):
    print("already present"); raise SystemExit(0)
lid = max(n.get("local_id", 0) for n in d["nodes"]) + 1
d["nodes"].append({"local_id": lid, "type": "ComposerCue", "attrs": {"relation_head": "replay", "composer": "experiment", "priority": 4.5,
    "note": "tranche 7: a 'replay' head is only grounded by the conversation-experiment bundle, so it is a conversation experiment by construction; it outranks communicate (5), whose cue keywords substring-match ordinary content words in reported concerns ('speaker' contains 'speak')."}})
d["version"] = "1.1.0"
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n"); print("composer_dispatch 1.1.0")
