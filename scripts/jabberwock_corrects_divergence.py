#!/usr/bin/env python3
"""jabberwock_self_corrects -- THE CAPSTONE, console form.

Companion to tests/test_self_correction.py (the fast pytest regression this
script's narrative mirrors). Demonstrates, on real fast-fixture agents, the
closed autonomous self-correction loop `domains/self_correction.py` builds:

  imagine_and_check_convergence -- tier-3 (imagine a candidate fix) composed
      with tier-4 (predict whether the imagined, intervened graph converges)
      -- entirely reversible, nothing live is touched.

  intervene_on_divergence -- the loop: locate the diverging rule, generate a
      small candidate space (REUSE domains/edit_ops.py's structural appliers
      + a domain-shaped "novelty/dedup identity fix" candidate -- the exact
      shape that fixed the real 2026-07-03 axis-mint runaway incident by
      hand), try each in imagination, and either:
        (a) ADOPT the first validated fix directly on the live graph, if its
            provenance is NOT frozen-core -- ticks-only, zero human; or
        (b) PROPOSE it for human review (mint a SelfCorrectionProposal + a
            rung-5 Impasse) and touch NOTHING live, if the driving rule's
            provenance IS frozen-core (`domains/frozen_core.py`'s closed
            set) -- the headline safety result: the agent can imagine and
            validate a fix to its own frozen core, but can never apply one
            itself.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_self_corrects.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                    # noqa: E402
import domains.reflective_faculty as rf                       # noqa: E402
from domains import self_model as sm                          # noqa: E402
from domains.collapse_model import predict_collapse           # noqa: E402
from domains.self_correction import (                         # noqa: E402
    intervene_on_divergence, imagine_and_check_convergence, _default_candidates,
)


def _shape_decode_agent():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _seed_runaway(s, ag, *, tag: str):
    obs = []
    for i in range(3):
        o = s.add_node("Observation", {"signature": [[f"zzz{tag}{i}", "X"]],
                                        "key": [f"zzz{tag}{i}"], "status": "pending"})
        s.add_edge(ag, "observed", o)
        obs.append(o)
    return obs


def _banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    _banner("1. AUTONOMOUS LOOP -- NON-FROZEN divergence: diverging -> fix -> adopt -> converged")
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="nf")
    # Test-only provenance substitution isolating the SAME real rule mechanics
    # (sd_mint_quantum / sd_dedup_existing) under a deliberately-skippable
    # seed id, on THIS agent's own isolated graph -- see tests/
    # test_self_correction.py's module docstring for why this is honest, not
    # a claim about the real shape_decode_loop seed's own frozen status.
    s.add_node("RuleSummary", {"name": "sd_mint_quantum", "from_seed": "self_correction_demo_seed"})
    s.add_node("RuleSummary", {"name": "sd_dedup_existing", "from_seed": "self_correction_demo_seed"})
    s.add_node("SeedSummary", {"seed_id": "self_correction_demo_seed", "skippable": 1.0})

    before = predict_collapse(s, horizon=3, imagine_steps=2)
    print(f"diverging: converged={before.converged} growth_rate={before.frontier_growth_rate} "
          f"trajectory={before.counts_trajectory}")

    result = intervene_on_divergence(s, target_rule="sd_mint_quantum", horizon=3, imagine_steps=2,
                                      model_before=before)
    print(f"candidates tried: {[(c['label'], c['inert'], c['converges']) for c in result['candidates_tried']]}")
    print(f"chosen fix: {result['chosen']!r}")
    print(f"adopted (autonomous, ticks-only, zero human): {result['adopted']}")
    print(f"model after adopting: converged={result['model_final'].converged} "
          f"growth_rate={result['model_final'].frontier_growth_rate} "
          f"trajectory={result['model_final'].counts_trajectory}")
    assert result["adopted"] is True and result["model_final"].converged is True

    _banner("2. FROZEN SAFETY BOUNDARY -- imagines a working fix, adoption DENIED, proposal raised")
    s2, ag2, native2 = _shape_decode_agent()
    _seed_runaway(s2, ag2, tag="fr")

    class _A:
        def __init__(self):
            self.s = s2
            self.inner = s2._inner
            self.agent = ag2

    sm.ensure_self_model(_A())  # real disk-scan: sd_mint_quantum genuinely comes from shape_decode_loop
    s2.add_node("SeedSummary", {"seed_id": "shape_decode_loop", "skippable": 0.0})
    before_rule_count = s2._inner.rule_count()

    before2 = predict_collapse(s2, horizon=3, imagine_steps=2)
    print(f"diverging: converged={before2.converged} growth_rate={before2.frontier_growth_rate}")

    result2 = intervene_on_divergence(s2, target_rule="sd_mint_quantum", horizon=3, imagine_steps=2,
                                       model_before=before2)
    print(f"chosen fix (imagined, validated): {result2['chosen']!r}  "
          f"model_after_candidate.converged={result2['model_after_candidate'].converged}")
    print(f"adopted: {result2['adopted']}  escalated: {result2['escalated']}")
    print(f"denied: {result2['denied']}")
    print(f"proposal node: {result2['proposal']}  (status="
          f"{s2.node(result2['proposal'])['attrs']['status']!r})")
    print(f"impasse node: {result2['impasse']}  (kind={s2.node(result2['impasse'])['attrs']['kind']!r}, "
          f"to={s2.node(result2['impasse'])['attrs']['to']!r})")
    after_rule_count = s2._inner.rule_count()
    print(f"live rule_count before/after: {before_rule_count}/{after_rule_count} "
          f"({'UNCHANGED -- no frozen rule mutated' if after_rule_count == before_rule_count else 'CHANGED (BUG)'})")
    assert result2["adopted"] is False and result2["escalated"] is True
    assert after_rule_count == before_rule_count

    _banner("3. REVERSIBILITY -- imagine_and_check_convergence never touches the live graph")
    s3, ag3, native3 = _shape_decode_agent()
    _seed_runaway(s3, ag3, tag="rev")
    before_rc = s3._inner.rule_count()
    for cand in _default_candidates(native3, "sd_mint_quantum"):
        imagine_and_check_convergence(s3, cand, horizon=3, imagine_steps=2)
    after_rc = s3._inner.rule_count()
    print(f"live rule_count before/after checking every candidate: {before_rc}/{after_rc} "
          f"({'reversible' if before_rc == after_rc else 'BUG'})")
    assert before_rc == after_rc

    _banner("ALL THREE HEADLINE RESULTS CONFIRMED")
    print("1. autonomous adopt on non-frozen divergence: converged after adoption, zero human")
    print("2. frozen divergence: fix imagined+validated, adoption DENIED, human proposal raised, "
          "no live mutation")
    print("3. imagine-and-check is reversible (rule_count / graph unchanged by exploration alone)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
