"""arc3_full_seed — mechanically install the FULL relevant seed set + the
grounded ARC frame onto a play agent, so the ARC-AGI-3 play agent boots
FULLY FEATURED (hundreds-to-thousands of concepts) instead of as a near-blank
``CuriousAgent()`` stub (~49 stale concepts).

This is a SEED LOADER, not agent logic. It is purely mechanical: it discovers
the EXISTING ``install_*_seed`` functions across ``domains/*.py`` by reflection
(the same enumerate-by-signature pattern as
``scripts/ask_jabberwock_whats_missing.install_all``) and calls each one. It
authors NO new concepts, builds NO reasoner, makes NO conditional over graph
state beyond mechanical translation. Every installer it calls already exists.

The ARC-AGI-3 benchmark is explicitly about reasoning ON TOP OF core-knowledge
priors (objectness, geometry, agency, goals, number, etc.). A blank agent has
none of those. This loader installs the whole relevant prior set so the agent
holds the foundation the benchmark assumes.

Three mechanical steps:

  1. SUBSTRATE-STYLE SEEDS — every ``install_<x>_seed(substrate)`` in
     ``domains/*.py``. These installers are written against the ``_native``
     Substrate API (``substrate.node(n)["attrs"]`` / NodeID-valued
     ``substrate.nodes(...)``), so they are handed the agent's UNDERLYING
     native substrate (``_native_substrate(agent.mind_graph)``) — exactly the
     object they were written for. ~158 seeds: physics, vision (object/colour/
     scene/motion/computer-vision), spatial/geometry, psychology (cognitive/
     developmental/social/...), embodiment/proprioception, logic, language,
     and every other foundational domain.

  2. AGENT-STYLE INSTALLERS — the handful whose canonical entry point takes the
     CuriousAgent itself and updates its own ``_concept_nodes`` index:
     ``install_relations`` (binary semantic relations), ``install_psychology``
     (mental-state / ToM vocabulary), and ``install_core_vocabulary`` (top
     Brown-corpus content words). These are the explicit core-vocabulary /
     core-knowledge installers the task names.

  3. REINDEX — the substrate-style seeds add Concept nodes directly to the
     graph but do not touch the agent's ``_concept_nodes`` lookup (the index the
     agent's own machinery reads). We rebuild that index from the graph's
     Concept nodes by name — the SAME mechanical reindex-from-graph that
     ``CuriousAgent.load`` does for reflexes / microtheories / frames /
     impasses. No new concepts; pure indexing of EXISTING graph data.

  4. GROUNDED ARC FRAME — offer the persisted grounded ARC-AGI concepts
     (``data/arc_agi_grounded_context.json``) to the agent's OWN ``consider()``
     faculty, byte-identical to ``jabberwock_plays_arc_with_grounded_frame``.
     The agent grounds what it can and HOLDS the rest; the loader never decides.

Returns a report dict so a caller can verify the install without reaching into
graph internals.
"""
from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path
from typing import Any

_DOMAINS_DIR = Path(__file__).resolve().parent
_ROOT = _DOMAINS_DIR.parent
_GROUNDED_CONTEXT = _ROOT / "data" / "arc_agi_grounded_context.json"

# The grounded ARC-frame concepts most load-bearing for PLAY — copied verbatim
# from jabberwock_plays_arc_with_grounded_frame so the two stay identical.
_ARC_FRAME = (
    "arc-agi-3", "interactive_reasoning_benchmark", "arc-agi",
    "object_permanence", "feature_hierarchy_visual",
    "agent", "action", "goal", "perception_visual", "cognition", "volition",
)


def _discover_substrate_seed_installers() -> list:
    """Enumerate every ``install_<x>_seed`` in ``domains/*.py`` whose single
    required positional argument is the substrate (named ``substrate`` or
    ``s``). Reflection only — the same enumeration
    ``ask_jabberwock_whats_missing.install_all`` uses. Returns a list of
    (name, fn) in stable sorted order."""
    out: list = []
    seen: set = set()
    for f in sorted(_DOMAINS_DIR.glob("*.py")):
        if f.name.startswith("__") or f.name == "arc3_full_seed.py":
            continue
        try:
            src = f.read_text()
        except Exception:
            continue
        names = [m.group(1) for m in
                 re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE)]
        if not names:
            continue
        try:
            mod = importlib.import_module(f"domains.{f.stem}")
        except Exception:
            continue
        for name in names:
            if name in seen:
                continue
            fn = getattr(mod, name, None)
            if fn is None:
                continue
            try:
                sig = inspect.signature(fn)
            except (TypeError, ValueError):
                continue
            pos = [p for p in sig.parameters.values()
                   if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                 inspect.Parameter.POSITIONAL_OR_KEYWORD)
                   and p.default is inspect.Parameter.empty]
            if len(pos) == 1 and pos[0].name in ("substrate", "s"):
                seen.add(name)
                out.append((name, fn))
    return out


def install_full_seed_set(agent) -> dict:
    """Install the full relevant seed set + grounded ARC frame onto ``agent``.

    Mechanical and (per-installer) idempotent. Returns a report:
    ``{seeds_installed, seeds_failed, failed_names, agent_style, core_vocab,
    concepts_before, concepts_after, arc_frame_carried}``.
    """
    from substrate.persistence import _native_substrate

    report: dict[str, Any] = {
        "concepts_before": len(agent._concept_nodes),
        "seeds_installed": 0,
        "seeds_failed": 0,
        "failed_names": [],
        "agent_style": [],
        "core_vocab": 0,
        "arc_frame_carried": [],
    }

    nat = _native_substrate(agent.mind_graph)

    # 1. substrate-style seeds (the bulk: ~158 foundational domains).
    for name, fn in _discover_substrate_seed_installers():
        try:
            fn(nat)
            report["seeds_installed"] += 1
        except Exception as e:  # noqa: BLE001 — record, never abort the boot.
            report["seeds_failed"] += 1
            report["failed_names"].append(f"{name}: {type(e).__name__}")

    # 2. agent-style installers (update the agent's own concept index).
    try:
        from domains.relations import install_relations
        report["agent_style"].append(("relations", len(install_relations(agent))))
    except Exception as e:  # noqa: BLE001
        report["agent_style"].append(("relations", f"FAIL:{type(e).__name__}"))
    try:
        from domains.psychology import install_psychology
        report["agent_style"].append(("psychology", len(install_psychology(agent))))
    except Exception as e:  # noqa: BLE001
        report["agent_style"].append(("psychology", f"FAIL:{type(e).__name__}"))
    try:
        from domains.core_vocabulary import install_core_vocabulary
        report["core_vocab"] = install_core_vocabulary(agent)
    except Exception as e:  # noqa: BLE001
        report["core_vocab"] = f"FAIL:{type(e).__name__}"

    # 3. reindex _concept_nodes from the graph (mechanical, like load() does for
    #    the other indices) so the agent's machinery sees the seeded concepts.
    for n in agent.mind_graph.nodes("Concept"):
        nm = n.attrs.get("name")
        if nm and nm not in agent._concept_nodes:
            agent._concept_nodes[nm] = n.id

    # 4. grounded ARC frame — offer each grounded concept to the agent's OWN
    #    consider() faculty (byte-identical to the grounded-frame play driver).
    report["arc_frame_carried"] = _install_grounded_arc_frame(agent)

    report["concepts_after"] = len(agent._concept_nodes)
    return report


def _install_grounded_arc_frame(agent) -> list:
    """Offer the persisted grounded ARC-AGI concepts to ``agent.consider()``.
    Returns the frame concepts the agent now carries (grounded or held)."""
    if not _GROUNDED_CONTEXT.exists():
        return []
    try:
        from substrate_rs import _native
        from domains import self_persistence as sp
    except Exception:
        return []
    s = _native.Substrate()
    if not sp.load_state(s, str(_GROUNDED_CONTEXT)):
        return []
    present: set = set()
    for nid in s.nodes("Concept"):
        nm = s.node(nid)["attrs"].get("name")
        if nm:
            present.add(nm)
    for nm in _ARC_FRAME:
        if nm not in present:
            continue
        try:
            agent.consider({
                "kind": "concept", "word": nm,
                "definition": {"type": "Var", "name": nm},
            })
        except Exception:  # noqa: BLE001
            continue
    held = {h["name"] for h in agent.held_predicates()}
    return [n for n in _ARC_FRAME
            if n in agent._concept_nodes or n in held]


__all__ = ["install_full_seed_set"]
