#!/usr/bin/env python3
"""Tranche 8: boot_metacognition v1.1.0 -- assess a compromised boot ONCE per
BootCycle, not once per anomaly. v1.0.0 matched
[cycle has_seed_anomaly anomaly], so a boot with N failed seeds produced N
bindings in one rule pass; the Exists(SelfConcern) dedup guard is read before
any effect lands, so N SelfConcerns were minted (11 on every full boot, 10
later retired as duplicates). Now both assessment rules match the cycle only
and require an anomaly in `where`; bind_boot_anomaly_evidence (unchanged) still
links every anomaly. Textual patch of the hand-formatted seed; idempotent."""
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "seeds/boot_metacognition.json"
t = P.read_text()
if '"version": "1.1.0"' in t:
    print("already applied"); raise SystemExit(0)
HAS = ('''          {
            "type": "Exists",
            "source": {"type": "Neighbours", "node": {"type": "Var", "name": "cycle"}, "edge_type": "has_seed_anomaly", "any_type": false},
            "var_name": "anomaly",
            "predicate": {"type": "Lit", "value": true}
          },
''')
for name, old, new in (
    ("assess_compromised_boot",
     '''        ["agent", "observed_boot", "cycle"],
        ["cycle", "has_seed_anomaly", "anomaly"]
      ],''',
     '''        ["agent", "observed_boot", "cycle"]
      ],'''),
    ("reuse_boot_integrity_concern",
     '''        ["agent", "observed_boot", "cycle"],
        ["cycle", "has_seed_anomaly", "anomaly"],
        ["agent", "has_self_concern", "concern"]
      ],''',
     '''        ["agent", "observed_boot", "cycle"],
        ["agent", "has_self_concern", "concern"]
      ],''')):
    i = t.index(f'"name": "{name}"')
    j = t.index(old, i); assert j - i < 200, name
    t = t[:j] + new + t[j + len(old):]
    k = t.index('"items": [\n', j) + len('"items": [\n')
    t = t[:k] + HAS + t[k:]
t = t.replace('"version": "1.0.0"', '"version": "1.1.0"', 1)
import json; json.loads(t)
P.write_text(t); print("boot_metacognition 1.1.0")
