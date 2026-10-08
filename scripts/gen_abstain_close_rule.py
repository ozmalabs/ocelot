#!/usr/bin/env python3
"""Tranche 11: seeds/self_optimisation.json v1.4.0 gains
`close_abstained_variant` (the rule body is CLOSE_ABSTAINED in
scripts/gen_variation_credit_seed.py). An experiment whose delta carries
`variant_abstained` (the picked builder honestly abstained, or no family is
eligible -- an empty delta) is closed before dispatch: status 'done', outcome
'abstained'. Never replayed, never credited (credit counts only
supported/refuted/inconclusive). Lives in self_optimisation because that seed
loads on every boot; variation_credit is self_load_only. Idempotent; keeps
the file's indent=1 / no-trailing-newline format."""
import importlib.util, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gvc", ROOT / "scripts/gen_variation_credit_seed.py")
gvc = importlib.util.module_from_spec(spec); spec.loader.exec_module(gvc)
rule = dict(gvc.CLOSE_ABSTAINED, name="close_abstained_variant")
P = ROOT / "seeds/self_optimisation.json"
d = json.loads(P.read_text())
d["rules"] = [r for r in d["rules"] if r["name"] != rule["name"]] + [rule]
d["version"] = max(d["version"], "1.4.0", key=lambda v: tuple(map(int, v.split("."))))
P.write_text(json.dumps(d, indent=1, ensure_ascii=True)); print("self_optimisation", d["version"])
