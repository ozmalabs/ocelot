"""self_authored — DURABLE self-authored faculties: the persist-on-WIRE loop the
agent OWNS, generalizing capability_compose's persist/install machinery.

THE GAP THIS CLOSES (the agent's own prior assessment). The agent owns the self-
extension loop in PIECES across paths: capability_compose composes summation
Term-trees AND already persists them (``persist_composed_capabilities`` ->
``seeds/composed_capabilities.json`` -> ``install_composed_capabilities`` reloads on
boot); but Path A (``compute_grounding.ground_computation``) and Path B
(``self_extension.extend``) WIRE a self-authored faculty into the LIVE ``caps`` dict
ONLY — it is gone after a restart (ephemeral). The deepest gap was PERSISTENCE: only
``capability_compose`` durably owned author->validate->persist->reload->use.

THIS MODULE generalizes that ONE working loop to ANY self-authored faculty, and
COUPLES the persist step to the EXISTING self-verify gate — the durability reuses the
reviewer the agent already had (the known-value check), so no human reviews what is
written. Two faculty TIERS are carried, mirroring the two the agent already builds:

  · TERM-TREE tier (capability_compose's kind): a self-contained Term-tree over one
    variable (the inlined summation trees). Reload = evaluate the tree directly on a
    fresh engine. This is EXACTLY capability_compose's persisted shape; the manifest
    schema below is a strict superset, so the composed capabilities load through the
    same loader (back-compat).

  · COMPOSITION tier (compute_grounding's kind, e.g. ``betti_number``): a faculty the
    agent READ as a gloss and COMPOSED over HELD primitives (boundary_matrix /
    matrix_rank / cardinality / simplices_of_dim). Its durable artifact is the
    agent's READ + COMPOSED definition, with the held primitives it bottoms out at and
    the textbook KNOWNS it self-verified against. Reload = re-RUN the SAME composition
    (``ground_computation``) on a fresh substrate's caps — the agent re-grounds its own
    read, deterministically, over the held basis. Faithful: the durable artifact is the
    agent's authored read, not a hand-authored answer; the reload recomposes it.

THE MANAGED DIR. ``seeds/self_authored/`` — UNDER ``seeds/`` so a self-authored faculty
COMMITS with the repo (``data/`` is gitignored; a faculty that survives a restart must
be a committed seed, not transient data). One JSON manifest per faculty:

    {name, tier, version, composed_by, verified_against:[...known checks...],
     superseded_by, var|definition, term|params|primitives, ...}

THE BOOT LOADER. ``install_self_authored()`` GENERALIZES
``install_composed_capabilities``: it walks ``seeds/self_authored/*.json``, and for each
faculty installs a Term-tree router (term tier) or re-grounds the composition (composition
tier) into the LIVE ``reason.CAPABILITIES`` — additive, idempotent, best-effort. Wired
into the boot path next to the existing ``install_composed_capabilities`` call
(``conversation_world.py``).

THE SELF-VERIFY COUPLING (the gate IS the reviewer). ``persist_self_authored`` accepts a
faculty record + its self-verify result and WRITES THE MANIFEST ONLY IF THE FACULTY
SELF-VERIFIED. An unverified faculty is REJECTED (never persisted) — the durability is
coupled to the same known-value gate ``self_extension._self_verify`` /
``ground_definition.verify_vs_known`` / the tier's known check already enforce. No human
reviews; the gate the agent already had does.

INTEGRITY (CLAUDE.md / the ownership axis). The DONKEY is EXTERNAL authoring — an LLM
hand-writing the faculty or the loop. This module reuses the agent's OWN machinery
(capability_compose's persist/install loop; ground_computation's compose; the held
self-verify gate); the faculties it writes are the agent's COMPOSED/READ artifacts, not
hand-authored math. The persist is coupled to the self-verify gate (the agent's reviewer).
NO LLM, NO Rust, NO build. Math/reading + agent-core domain ONLY — the speech/audio path
is untouched.

See capability_compose (the loop generalized) / self_extension (the WIRE step) /
compute_grounding (the composition tier) / [[ozma_agent_writes_its_own_code]] /
[[ozma_capability_is_binary_admissibility]] / [[ozma_synthesizes_own_gaps]].
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Optional


# seeds/ COMMITS (data/ is gitignored). A self-authored faculty that must survive a
# restart lives here as a committed seed — the same reasoning capability_compose's
# COMPOSED_PATH uses, generalized to a managed DIR (one manifest per faculty).
SELF_AUTHORED_DIR = (Path(__file__).resolve().parent.parent
                     / "seeds" / "self_authored")

TIER_TERM = "term_tree"          # a self-contained Term-tree over one var (summation)
TIER_COMPOSITION = "composition"  # a read+composed faculty over held primitives (betti)


# ---------------------------------------------------------------------------
# Term-tree tier — EXACTLY capability_compose's persisted shape, evaluated on the
# engine. Reused verbatim so the composed capabilities load through this same loader.
# ---------------------------------------------------------------------------

def _term_dispatcher(substrate, tree: dict, var: str, arg_role: str):
    """A thin router that evaluates the stored Term-tree on the engine for a bound
    query {arg_role: x}. The capability IS the composed Term-tree — no Python math.
    Mirrors capability_compose._native_dispatcher (the loop being generalized)."""
    def run(a: dict):
        x = int(a[arg_role])
        v = substrate.evaluate(tree, {var: float(x)})
        fv = float(v)
        return int(round(fv)) if abs(fv - round(fv)) < 1e-9 else fv
    return run


# ---------------------------------------------------------------------------
# Composition tier — a read+composed faculty (e.g. betti_number) re-grounded on a
# fresh substrate over the HELD primitives. The durable artifact is the agent's READ
# gloss (definition); reload RE-RUNS the SAME composition (ground_computation) — the
# agent re-grounds its own read deterministically over the held basis.
# ---------------------------------------------------------------------------

def _reground_composition(substrate, name: str, definition: str,
                          capabilities: dict) -> bool:
    """Re-ground a composition-tier faculty on `substrate` into `capabilities` by
    re-RUNNING ground_computation over the held primitives. Returns True iff it
    re-grounded + installed (the same self-composition the faculty was authored by).
    """
    from domains import compute_grounding as _cg
    res = _cg.ground_computation(substrate, name, definition,
                                 capabilities=capabilities)
    return bool(res.get("grounded") and res.get("installed"))


# ---------------------------------------------------------------------------
# SELF-VERIFY-COUPLED PERSIST. The durability is gated by the agent's OWN reviewer
# (the known-value check). An unverified faculty is REJECTED — never written.
# ---------------------------------------------------------------------------

def _safe_name(name: str) -> str:
    """A filesystem-safe manifest stem from a faculty name (mechanical I/O)."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(name)) or "faculty"


def manifest_path(name: str, directory: Path = SELF_AUTHORED_DIR) -> Path:
    return directory / (_safe_name(name) + ".json")


def persist_self_authored(faculty: dict, *, self_verified: bool,
                          verified_against: Optional[list] = None,
                          directory: Path = SELF_AUTHORED_DIR) -> Optional[Path]:
    """WRITE a self-authored faculty's manifest to ``seeds/self_authored/`` — ONLY
    IF it self-verified. This is the persist-on-WIRE step, coupled to the EXISTING
    self-verify gate (the agent's reviewer; no human). An unverified faculty is
    REJECTED (returns None, nothing written) — the loop does not persist what the
    gate did not pass, mirroring how self_extension refuses to WIRE an unverified
    structure.

    `faculty` carries {name, tier, ...tier-specific fields}. For TIER_TERM:
    {var, arg_role, term, term_str?}. For TIER_COMPOSITION: {definition, params,
    primitives}. `verified_against` records the KNOWN checks the gate ran (the
    provenance of the durability — what reviewed it).

    Returns the written manifest Path, or None when rejected (not self-verified).
    """
    if not self_verified:
        return None                      # the gate rejected it -> NOT persisted.
    name = faculty["name"]
    tier = faculty.get("tier", TIER_TERM)
    out = {
        "name": name,
        "tier": tier,
        "version": faculty.get("version", "1.0.0"),
        "composed_by": faculty.get("composed_by", "agent"),
        # the self-verify gate's verdict + the known checks it ran — the provenance of
        # the durability (what reviewed this faculty before it was made durable).
        "self_verified": True,
        "verified_against": list(verified_against or
                                 faculty.get("verified_against", [])),
        "superseded_by": faculty.get("superseded_by"),
    }
    if tier == TIER_TERM:
        out["var"] = faculty.get("var", "n")
        out["arg_role"] = faculty.get("arg_role", "of")
        out["term"] = faculty["term"]
        if faculty.get("term_str"):
            out["term_str"] = faculty["term_str"]
    elif tier == TIER_COMPOSITION:
        out["definition"] = faculty["definition"]
        out["params"] = list(faculty.get("params", []))
        out["primitives"] = list(faculty.get("primitives", []))
    else:
        raise ValueError(f"unknown faculty tier {tier!r}")
    directory.mkdir(parents=True, exist_ok=True)
    p = manifest_path(name, directory)
    p.write_text(json.dumps(out, indent=2))
    return p


def load_self_authored(directory: Path = SELF_AUTHORED_DIR) -> list[dict]:
    """Load every self-authored faculty manifest in ``directory`` (the managed dir).
    A faculty marked superseded_by another is skipped (the newer version wins, like a
    seed's version resolution). Returns the list of live manifest dicts. Empty if the
    dir is absent."""
    if not directory.exists():
        return []
    facs = []
    for f in sorted(directory.glob("*.json")):
        try:
            facs.append(json.loads(f.read_text()))
        except Exception:
            continue
    superseded = {m.get("superseded_by") for m in facs if m.get("superseded_by")}
    return [m for m in facs if m.get("name") not in superseded]


def install_self_authored(substrate, capabilities=None,
                          directory: Path = SELF_AUTHORED_DIR) -> dict:
    """LIVE, ADDITIVE install of the persisted self-authored faculties — the BOOT
    LOADER, generalizing ``install_composed_capabilities``.

    Walks ``seeds/self_authored/*.json``; for each self-verified faculty installs it
    into ``capabilities`` (defaults to ``reason.CAPABILITIES`` — the LIVE registry the
    conversation path dispatches to):
      · TIER_TERM        -> a router that evaluates the stored Term-tree on the engine
                            (capability_compose's persisted shape; identical loop).
      · TIER_COMPOSITION -> re-GROUND the read gloss via ground_computation over the
                            held primitives (the agent re-composes its own read).
    EXISTING entries are never altered; IDEMPOTENT (re-install overwrites only the
    self-authored concepts). Best-effort per faculty (a failed reground is skipped, the
    rest still load). Returns {name: 'term'|'composition'} for what installed."""
    if capabilities is None:
        from domains import reason
        capabilities = reason.CAPABILITIES
    installed: dict = {}
    for m in load_self_authored(directory):
        if not m.get("self_verified"):
            continue                     # never install an unverified faculty.
        name = m["name"]
        tier = m.get("tier", TIER_TERM)
        try:
            if tier == TIER_TERM:
                capabilities[name] = _term_dispatcher(
                    substrate, m["term"], m.get("var", "n"),
                    m.get("arg_role", "of"))
                installed[name] = "term"
            elif tier == TIER_COMPOSITION:
                if _reground_composition(substrate, name, m["definition"],
                                         capabilities):
                    installed[name] = "composition"
        except Exception:
            continue
    return installed


# ---------------------------------------------------------------------------
# PERSIST-ON-WIRE — the single highest-value change: the WIRE step (where a self-
# authored faculty is installed into live caps) ALSO persists, coupled to the self-
# verify gate. These wrap a freshly-WIRED faculty: run the agent's OWN known-value
# self-verify, then persist ONLY on pass (an unverified faculty is wired-live but NOT
# made durable — exactly self_extension's "do not wire an unverified structure",
# lifted to "do not PERSIST an unverified structure").
# ---------------------------------------------------------------------------

def wire_and_persist_composition(substrate, name: str, definition: str,
                                 capabilities: dict, *, knowns: list,
                                 directory: Path = SELF_AUTHORED_DIR) -> dict:
    """WIRE a composition-tier faculty (ground its read gloss over held primitives so
    it is live in `capabilities`), SELF-VERIFY it on the supplied textbook KNOWNS, and
    PERSIST it ONLY IF every known checks out — the persist-on-WIRE step for Path A
    (compute_grounding). `knowns` is a list of ((bound-arg dict), expected-value)
    pairs the gate runs through the freshly-wired capability (the agent's own reviewer:
    the known-value check; NONE a question's answer). Returns
    {wired, self_verified, persisted, path, checks}."""
    from domains import compute_grounding as _cg
    res = _cg.ground_computation(substrate, name, definition,
                                 capabilities=capabilities)
    wired = bool(res.get("grounded") and res.get("installed"))
    out = {"wired": wired, "self_verified": False, "persisted": False,
           "path": None, "checks": []}
    if not wired:
        return out
    # SELF-VERIFY on the knowns — RUN the wired capability, check vs the known values.
    ok = True
    checks = []
    for arg, expected in knowns:
        try:
            got = capabilities[name](dict(arg))
        except Exception as e:           # noqa: BLE001
            got, ok = f"error:{e}", False
            checks.append({"arg": arg, "expected": expected, "got": got, "ok": False})
            break
        passed = (str(got) == str(expected))
        ok = ok and passed
        checks.append({"arg": arg, "expected": expected, "got": got, "ok": passed})
    out["self_verified"] = ok
    out["checks"] = checks
    if not ok:
        return out                       # gate REJECTED -> live but NOT persisted.
    faculty = {
        "name": name, "tier": TIER_COMPOSITION, "definition": definition,
        "params": list(res.get("params", [])),
        "primitives": list(res.get("parts", [])),
        "composed_by": "ground_computation",
    }
    verified = [{"arg": c["arg"], "expected": c["expected"]} for c in checks]
    p = persist_self_authored(faculty, self_verified=True,
                              verified_against=verified, directory=directory)
    out["persisted"] = p is not None
    out["path"] = str(p) if p else None
    return out


def wire_and_persist_term(substrate, name: str, tree: dict, var: str,
                          arg_role: str, *, knowns: list, term_str: str = "",
                          directory: Path = SELF_AUTHORED_DIR) -> dict:
    """WIRE a term-tree-tier faculty (install a router that evaluates the stored Term-
    tree), SELF-VERIFY on the supplied KNOWNS, PERSIST only on pass — the persist-on-
    WIRE step for the capability_compose tier, generalized. `knowns` is
    [((arg dict), expected), ...]. Returns {wired, self_verified, persisted, path,
    checks}."""
    capabilities = {}
    capabilities[name] = _term_dispatcher(substrate, tree, var, arg_role)
    out = {"wired": True, "self_verified": False, "persisted": False,
           "path": None, "checks": []}
    ok, checks = True, []
    for arg, expected in knowns:
        try:
            got = capabilities[name](dict(arg))
        except Exception as e:           # noqa: BLE001
            got, ok = f"error:{e}", False
            checks.append({"arg": arg, "expected": expected, "got": got, "ok": False})
            break
        passed = (str(got) == str(expected))
        ok = ok and passed
        checks.append({"arg": arg, "expected": expected, "got": got, "ok": passed})
    out["self_verified"], out["checks"] = ok, checks
    if not ok:
        return out
    faculty = {"name": name, "tier": TIER_TERM, "var": var, "arg_role": arg_role,
               "term": tree, "term_str": term_str, "composed_by": "generator"}
    verified = [{"arg": c["arg"], "expected": c["expected"]} for c in checks]
    p = persist_self_authored(faculty, self_verified=True,
                              verified_against=verified, directory=directory)
    out["persisted"] = p is not None
    out["path"] = str(p) if p else None
    return out


__all__ = [
    "SELF_AUTHORED_DIR", "TIER_TERM", "TIER_COMPOSITION",
    "manifest_path", "persist_self_authored", "load_self_authored",
    "install_self_authored",
    "wire_and_persist_composition", "wire_and_persist_term",
]
