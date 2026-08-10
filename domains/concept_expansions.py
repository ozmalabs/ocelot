"""concept_expansions — discover + install concept-decomposition packs.

A concept-expansion pack is a JSON file under `seeds/expansions/` that
decomposes ONE high-level concept (e.g. multi_symbol_arithmetic_coder,
asymmetric_numeral_systems, motion_estimation) into its sub-mechanisms +
the derivation rules that link them. Drop a new pack in the directory
and `install_all_concept_expansions` picks it up — no Python edit.

Pack shape:

    {
      "id": "ms_ac_decomposition",
      "version": "1.0.0",
      "expands_concept": "multi_symbol_arithmetic_coder",
      "in_microtheory": "video_coding_theory",
      "description": "...",
      "sub_mechanisms": [
        { "name": "...", "definition": "...", "why": "...",
          "category": "ms_ac_mechanism" },
        ...
      ],
      "derivation_rules": [
        { "name": "...", "if": [...], "then": [...], "why": "...",
          "soundness_category": "..." },
        ...
      ]
    }

The loader is mechanical JSON-to-graph translation — no decisions, no
agent state in Python. It:
  · finds the target Microtheory by name
  · finds the parent concept the pack expands
  · for each sub_mechanism: mints a Concept under the Mt's has_concept,
    annotates with why/category/expansion_pack/origin, and adds a
    `decomposes` edge pointing at the parent concept
  · for each derivation_rule: mints a Rule under has_rule with any
    extra fields the pack declares (soundness_category, etc.)
  · is idempotent (re-running on the same substrate is a no-op)
"""
from __future__ import annotations

import json
from pathlib import Path

from .code_authoring import _install_concept


_EXPANSIONS_DIR = (Path(__file__).resolve().parent.parent
                   / "seeds" / "expansions")


def _find_mt(substrate, name: str):
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == name:
            return n
    return None


def _find_concept_in_mt(substrate, mt_nid: int, name: str):
    for c in substrate.neighbours(mt_nid, "has_concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            return c
    return None


def install_concept_expansion(substrate, pack_path: Path) -> int | None:
    """Install one expansion pack. Returns the parent concept's NodeID,
    or None if the target Mt or parent concept doesn't exist.

    Idempotent — sub-mechanisms and rules with names that already exist
    in the substrate are skipped."""
    with pack_path.open() as f:
        pack = json.load(f)

    pack_id = pack["id"]
    target_mt_name = pack["in_microtheory"]
    parent_concept_name = pack["expands_concept"]

    mt = _find_mt(substrate, target_mt_name)
    if mt is None:
        return None
    parent = _find_concept_in_mt(substrate, mt, parent_concept_name)
    if parent is None:
        # The expansion can still install — the decomposes edges just
        # won't have a parent to point at.
        pass

    for sm in pack.get("sub_mechanisms", []):
        existing = _find_concept_in_mt(substrate, mt, sm["name"])
        if existing is not None:
            continue
        cid = _install_concept(substrate, mt, sm["name"], sm["definition"])
        substrate.set_attr(cid, "why", sm.get("why", ""))
        substrate.set_attr(cid, "category", sm.get("category", ""))
        substrate.set_attr(cid, "expansion_pack", pack_id)
        substrate.set_attr(cid, "origin", "concept_expansion")
        # Persist any other fields the sub-mechanism declares.
        for key, value in sm.items():
            if key in ("name", "definition", "why", "category"):
                continue
            substrate.set_attr(cid, key, value)
        # Wire the decomposes edge to the parent concept (if found).
        if parent is not None:
            try:
                substrate.add_edge(cid, "decomposes", parent, {})
            except Exception:
                pass

    existing_rules = {substrate.node(n)["attrs"].get("name")
                      for n in substrate.nodes("Rule")}
    for r in pack.get("derivation_rules", []):
        if r["name"] in existing_rules:
            continue
        attrs = {
            "name": r["name"],
            "if_clauses": list(r.get("if", [])),
            "then_clauses": list(r.get("then", [])),
            "why": r.get("why", ""),
            "origin": "concept_expansion",
            "expansion_pack": pack_id,
        }
        for key, value in r.items():
            if key in ("name", "if", "then", "why"):
                continue
            attrs[key] = value
        rid = substrate.add_node("Rule", attrs)
        try:
            substrate.add_edge(mt, "has_rule", rid, {})
        except Exception:
            pass

    return parent


def install_all_concept_expansions(substrate,
                                   expansions_dir: Path | None = None
                                   ) -> list[str]:
    """Discover and install every *.json pack under seeds/expansions/.
    Returns the list of pack ids installed."""
    if expansions_dir is None:
        expansions_dir = _EXPANSIONS_DIR
    if not expansions_dir.exists():
        return []
    installed = []
    for pack_path in sorted(expansions_dir.glob("*.json")):
        with pack_path.open() as f:
            pack_id = json.load(f).get("id", pack_path.stem)
        install_concept_expansion(substrate, pack_path)
        installed.append(pack_id)
    return installed


__all__ = ["install_concept_expansion", "install_all_concept_expansions"]
