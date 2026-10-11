#!/usr/bin/env python3
"""composer_dispatch v1.2.0 (tranche 21): the 'replay' ComposerCue outranks
EVERY composer (priority 0.5).

A 'replay' relation head is grounded only by the conversation-experiment
bundle (jabberwock_daemon._promote_relations_for_concern), so a StandingConcern
carrying it has already been routed to the experiment pipeline. Tranche 7 set
priority 4.5 so it beat 'communicate' (5). Measured on the production path in
tranche 21: a self-filed `comprehension` concern ("comprehension classified
this as 'instruction' but the deep reader heard 'statement' …") also grounds
'comprehend' (priority 1) from its own content words. composer_pick then chose
the comprehension composer, which minted an inert comprehend_describe_directive_*
rule, marked the concern processed, and authored no experiment. Every
comprehension concern dead-ended there. Content words must not re-route a
concern whose pipeline is already decided. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/composer_dispatch.json"
VERSION = "1.2.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
cue = next(n for n in d["nodes"] if n["type"] == "ComposerCue" and n["attrs"].get("relation_head") == "replay")
cue["attrs"]["priority"] = 0.5
cue["attrs"]["note"] += (" tranche 21: priority 0.5 -- outranks every composer; a comprehension concern's own content "
                         "words ground 'comprehend' (1), which had sent it to the comprehension composer (inert rule, no "
                         "experiment). A concern already routed to the experiment pipeline is not re-routed by its content.")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("composer_dispatch", VERSION)
