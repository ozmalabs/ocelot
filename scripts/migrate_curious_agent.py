"""Run the mechanical AST->Rule migrator over curious_agent.py: produce real RewriteRules.

For every method, `ast_to_rule.Migrator` assembles a RewriteRule (where from a guard, effects from
state mutations; expressions composed by the AST->Term rules + serialised). A method is:
  CLEAN    — a valid Rule with effects and NO residual statement (fully mechanical).
  PARTIAL  — has mechanical effects but also residual statements (the ~10% judgment) OR a value
             expression that doesn't compose (a self.method() call, etc.).
  QUERY    — no state mutation (a getter/derivation; a query, not a Rule).
Every CLEAN rule is fed to `add_rule` to prove the engine accepts it. Fresh substrate per method so
each composition stays small.

Run:  python -m scripts.migrate_curious_agent
"""
from __future__ import annotations

import ast
import json

import substrate_rs as srs

from domains.ast_to_rule import Migrator


def main() -> None:
    defs = [n for n in ast.walk(ast.parse(open("domains/curious_agent.py").read()))
            if isinstance(n, ast.FunctionDef)]
    clean = mechquery = partial = opaque = skip = 0
    accepted = 0
    eff_total = resid_total = 0                   # per-statement yield: translated vs untranslated
    samples = []
    for d in defs:
        try:
            r = Migrator().method_to_rule(d)
        except Exception:
            skip += 1
            continue
        eff_total += len(r["effects"]) + (1 if r["returns"] is not None else 0)
        resid_total += len(r["residual"])
        if r["rule"] is not None:                 # effects, no residual -> a full Rule
            clean += 1
            try:
                srs.Substrate()._inner.add_rule(r["rule"])
                accepted += 1
            except Exception:
                pass
        elif not r["effects"] and not r["residual"] and r["returns"] is not None:
            mechquery += 1                         # pure query whose returned Term composes (factory)
        elif r["effects"] or r["returns"] is not None:
            partial += 1                           # some mechanical + a residue
        else:
            opaque += 1                            # faculty composition / un-translatable
        if len(samples) < 6 and r["returns"] is not None and not r["effects"]:
            samples.append((d.name, "returns", r["returns"], r["residual"]))

    total = len(defs)
    print("=" * 76)
    print(f"MIGRATE curious_agent.py -> RewriteRules ({total} methods)")
    print("=" * 76)
    fully = clean + mechquery
    print(f"  CLEAN     {clean:>4}  ({100*clean/total:4.1f}%)  full Rule (effects, no residual); "
          f"{accepted} engine-accepted")
    print(f"  MECH-QUERY{mechquery:>4}  ({100*mechquery/total:4.1f}%)  pure query, returned Term composes "
          f"(a Term factory -> derived attr)")
    print(f"  PARTIAL   {partial:>4}  ({100*partial/total:4.1f}%)  some mechanical + a residue")
    print(f"  OPAQUE    {opaque:>4}  ({100*opaque/total:4.1f}%)  faculty composition / un-translatable")
    print(f"  SKIP      {skip:>4}")
    print(f"\n  FULLY MECHANICAL methods (CLEAN + MECH-QUERY): {fully} ({100*fully/total:.1f}%)"
          "  <- mixing-limited; the WRONG unit")
    den = eff_total + resid_total
    print(f"  PER-STATEMENT yield: {eff_total} effects/values translated vs {resid_total} residual "
          f"-> {100*eff_total/den:.0f}% of state-touching statements mechanised  <- the RIGHT unit")
    print("\n  sample migrated Term factories (real curious_agent.py methods -> a Term):")
    for nm, _, ret, resid in samples:
        print(f"   {nm}: {json.dumps(ret)[:150]}")
    print("\n" + "=" * 76)
    print("  Expressions composed by the graph rules; statement shells -> engine Effects. The")
    print("  CLEAN set migrates with zero hand work; PARTIAL needs the residue resolved; QUERY")
    print("  methods become derived attrs. The match/trigger (placeholder is_a Agent) is the judgment.")
    print("=" * 76)


if __name__ == "__main__":
    main()
