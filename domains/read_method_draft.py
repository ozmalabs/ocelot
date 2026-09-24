"""read_method_draft — the READ→SYNTHESIZE path as a code_authoring DRAFT SOURCE.

This wires the agent's read-and-implement faculties into the existing autonomous
self-authoring loop (`code_authoring` / `code_writing_cortex`) as a NEW,
teacher-free draft source, ALONGSIDE the mechanical primitive emitter. The
`code_authoring` cortex is already **identify gap → draft → validate → install**;
this module supplies the read-method DRAFT and the rule-draft VALIDATE + ADOPT so
the SAME machinery closes the read→implement→verify→adopt loop.

Three mechanical functions (world-adapter / builder category — the same legal
class as the `_compose_*_rule` builders and `compile_and_test`). None makes a
decision over graph state that PICKS agent behaviour; every DECISION (what shape,
what rule, whether the effect matches, whether to adopt) is the agent's own
faculty (read/ground/synthesise) or the cortex's reflex reading these returned
data:

  draft_from_reading   — the DRAFT. The agent READS the method
                         (procedural_reader.read_method), GROUNDS the binding
                         (binding_resolver.derive_binding, against its own domain
                         graph), and SYNTHESISES the rule
                         (method_synthesis.synthesise_rule_from_method,
                         install=False). Pure composition of three faculties.

  validate_by_running  — the VALIDATE (the compile_and_test analogue for a
                         rule-draft). Builds a MINIMAL test instance FROM the read
                         MethodModel + the synthesised rule ON AN ISOLATED
                         throwaway substrate, RUNS the rule, and reads back
                         whether the DESCRIBED EFFECT occurred — and, where the
                         method carries a trigger, that it does NOT occur without
                         it. The expected effect is DERIVED from the model + the
                         rule the agent produced: the agent verifying its own
                         read-and-implement. Returns a datum; the reflex decides
                         adoption.

  adopt                — the ADOPT. Installs the validated rule LIVE (the
                         capability RUNS now) and persists it as seed `rules` data
                         (append to a manifest under a category) so a fresh boot
                         re-installs it — the existing seed-rule channel
                         load_all_seeds / load_seed_manifest already executes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from domains import procedural_reader as pr
from domains import method_synthesis as ms
from domains import binding_resolver as br


# --------------------------------------------------------------------------- #
#  resolve (accept a WorldAdapter or a bare Substrate)
# --------------------------------------------------------------------------- #
def _resolve(agent):
    s = getattr(agent, "s", agent)
    inner = getattr(agent, "inner", None)
    if inner is None:
        inner = getattr(s, "_inner", None)
    return s, inner


# --------------------------------------------------------------------------- #
#  DRAFT — read + ground + synthesise (all three agent faculties)
# --------------------------------------------------------------------------- #
def draft_from_reading(agent, method_text: str, name: str = "method",
                       binding: Optional[dict] = None) -> dict:
    """Compose the agent's read → ground → synthesise faculties into a rule
    draft. Returns {kind:'read_method_rule', model, binding, rules, effect, how,
    ...} or {wall: ...} on a synthesis wall. `binding=None` -> the agent grounds
    it itself against its own domain graph (derive_binding); pass a dict to
    supply it directly (the domain-adapter path)."""
    model = pr.read_method(agent, method_text, name=name)          # READS
    prov: list = []
    underspecified: list = []
    if binding is None:
        gd = br.derive_binding(agent, model)                        # GROUNDS
        binding = gd.get("binding", {})
        prov = gd.get("provenance", [])
        underspecified = gd.get("underspecified", [])
    syn = ms.synthesise_rule_from_method(agent, model, binding,     # SYNTHESISES
                                         install=False)
    if syn.get("wall"):
        return {"wall": syn["wall"], "name": name, "method_text": method_text,
                "model": model, "binding": binding,
                "binding_provenance": prov, "underspecified": underspecified}
    return {"kind": "read_method_rule", "name": name, "method_text": method_text,
            "model": model, "binding": binding, "binding_provenance": prov,
            "underspecified": underspecified, "rules": syn["rules"],
            "effect": syn["effect"], "how": syn["how"]}


# --------------------------------------------------------------------------- #
#  rule-JSON reads (mechanical structural extraction — no decision)
# --------------------------------------------------------------------------- #
def _match_edge(rule: dict):
    m = rule["match"][0]
    return m[0], m[1], m[2]            # (var_a, edge_type, var_b)


def _scan_state_eqs(where) -> list:
    """Every Eq(Attr(Var v, key k), Lit val) in the where-tree — the trigger
    state predicates the synthesiser emitted (e.g. task.done == 1). Recurses
    through And / Not. Returns [(var, key, val)]."""
    out: list = []
    if not isinstance(where, dict):
        return out
    t = where.get("type")
    if t == "Eq":
        a, b = where.get("a"), where.get("b")
        if (isinstance(a, dict) and a.get("type") == "Attr"
                and isinstance(a.get("node"), dict)
                and a["node"].get("type") == "Var"
                and isinstance(b, dict) and b.get("type") == "Lit"):
            out.append((a["node"]["name"], a.get("key"), b.get("value")))
    elif t == "And":
        for it in where.get("items", []):
            out.extend(_scan_state_eqs(it))
    elif t == "Not":
        out.extend(_scan_state_eqs(where.get("arg")))
    return out


def _positive_state_eqs(where) -> list:
    """Every Eq(Attr(Var v, k), Lit val) that is NOT under a Not — the POSITIVE
    trigger predicates (add_node's mint-once marker guard lives under a Not and
    must be excluded, else validation would pre-set the marker and block the
    mint). Recurses through And only. Returns [(var, key, val)]."""
    out: list = []
    if not isinstance(where, dict):
        return out
    t = where.get("type")
    if t == "Eq":
        a, b = where.get("a"), where.get("b")
        if (isinstance(a, dict) and a.get("type") == "Attr"
                and isinstance(a.get("node"), dict)
                and a["node"].get("type") == "Var"
                and isinstance(b, dict) and b.get("type") == "Lit"):
            out.append((a["node"]["name"], a.get("key"), b.get("value")))
    elif t == "And":
        for it in where.get("items", []):
            out.extend(_positive_state_eqs(it))
    return out


def _agg_spec_from_effect(effect) -> dict:
    """The aggregate spec inside a recompute set_attr effect: effect is
    ['set_attr', view, attr, {'__term__': <reducer>(Neighbours(src, EDGE), ...)}]
    for reducer in Count / Sum / MaxOver / MinOver. Returns {op, edge,
    value_attr}."""
    out = {"op": None, "edge": None, "value_attr": None}
    if len(effect) < 4 or not isinstance(effect[3], dict):
        return out
    term = effect[3].get("__term__")
    if not isinstance(term, dict):
        return out
    # Mean is COMPOSED as Div(Sum(v), Count) — read the op back as 'Mean' and pull
    # the edge/value_attr from the Sum numerator (the two share one source).
    if term.get("type") == "Div":
        num = term.get("a")
        out["op"] = "Mean"
        term = num if isinstance(num, dict) else {}
    else:
        out["op"] = term.get("type")
    src = term.get("source")
    if isinstance(src, dict) and src.get("type") == "Neighbours":
        out["edge"] = src.get("edge_type")
    v = term.get("value")
    if isinstance(v, dict) and v.get("type") == "Attr":
        out["value_attr"] = v.get("key")
    return out


# --------------------------------------------------------------------------- #
#  VALIDATE — run the rule on a minimal instance, check the described effect
# --------------------------------------------------------------------------- #
def validate_by_running(draft: dict) -> dict:
    """The compile_and_test analogue for a rule-draft: on an ISOLATED throwaway
    substrate, install the synthesised rule, build a minimal test instance FROM
    the read model, RUN, and read back whether the DESCRIBED EFFECT occurred.

    Returns {compile_ok, tests_pass, effect_matches, observed, expected, how}.
    `compile_ok` = the rule installed; `effect_matches` (mirrored into
    `tests_pass` for the generic gate) = the effect happened under the trigger
    AND — where there is a trigger — did NOT happen without it."""
    result = {"compile_ok": False, "tests_pass": False, "effect_matches": False,
              "observed": {}, "expected": "", "how": ""}
    if draft.get("wall") or not draft.get("rules"):
        result["observed"] = {"wall": draft.get("wall")}
        return result
    rule = draft["rules"][0]
    effect = draft.get("effect")

    # isolated substrate (no seeds -> no other rules can interfere).
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=())
    s, inner = wa.s, wa.inner
    try:
        inner.add_rule(rule)
    except Exception as e:
        result["observed"] = {"install_error": "%s: %s" % (type(e).__name__, e)}
        return result
    result["compile_ok"] = True

    def _n(attrs=None):
        return s.add_node("T", dict(attrs or {}))

    def _edge(a, et, b):
        inner.add_edge_unchecked(a, et, b)

    try:
        if effect in ("add_edge", "del_edge"):
            vsrc, rel, vtgt = _match_edge(rule)
            eff = rule["effects"][0]
            etype = eff[2]
            states = [(v, k, val) for (v, k, val) in _scan_state_eqs(rule.get("where"))
                      if v == vsrc]
            # positive: satisfy the trigger; del_edge starts WITH the edge.
            src, tgt = _n(), _n()
            _edge(src, rel, tgt)
            if effect == "del_edge":
                _edge(src, etype, tgt)
            for (_, k, val) in states:
                s.set_attr(src, k, val)
            inner.run_rules(10000)
            present = tgt in inner.neighbours(src, etype)
            pos_ok = present if effect == "add_edge" else (not present)
            # negative (guard): a trigger exists -> without it, no change.
            neg_ok = True
            if states:
                src2, tgt2 = _n(), _n()
                _edge(src2, rel, tgt2)
                if effect == "del_edge":
                    _edge(src2, etype, tgt2)
                inner.run_rules(10000)
                present2 = tgt2 in inner.neighbours(src2, etype)
                neg_ok = (not present2) if effect == "add_edge" else present2
            result["effect_matches"] = bool(pos_ok and neg_ok)
            result["observed"] = {"trigger_fires_effect": pos_ok,
                                  "guard_blocks_without_trigger": neg_ok}
            result["expected"] = ("%s(%s -%s-> %s) iff %s"
                                  % (effect, vsrc, etype, vtgt,
                                     " & ".join("%s.%s==%s" % (v, k, val)
                                                for (v, k, val) in states) or "always"))
        elif effect == "recompute":
            vview, rel, vsrc = _match_edge(rule)
            eff = rule["effects"][0]
            value_attr = eff[2]
            spec = _agg_spec_from_effect(eff)
            op, agg_edge, vattr = spec["op"], spec["edge"], spec["value_attr"]
            view = _n({value_attr: -1.0})
            src = _n()
            _edge(view, rel, src)
            elem_vals = [2.0, 5.0, 3.0]
            for x in elem_vals:
                _edge(src, agg_edge, _n({vattr: x} if vattr else {}))
            inner.run_rules(10000)
            got = s.node(view)["attrs"].get(value_attr)
            expected = {"Count": float(len(elem_vals)), "Sum": sum(elem_vals),
                        "Mean": sum(elem_vals) / len(elem_vals),
                        "MaxOver": max(elem_vals),
                        "MinOver": min(elem_vals)}.get(op)
            result["effect_matches"] = (expected is not None and got == expected)
            result["observed"] = {"value_after_recompute": got,
                                  "op": op, "expected": expected}
            result["expected"] = ("%s.%s == %s(%s.%s%s)  (=%s)"
                                  % (vview, value_attr, op, vsrc, agg_edge,
                                     ".%s" % vattr if vattr else "", expected))
        elif effect == "add_node":
            hub, rel, vsubj = _match_edge(rule)
            add_eff = next((e for e in rule["effects"] if e[0] == "add_node"), None)
            if add_eff is None:
                result["observed"] = {"error": "no add_node effect in rule"}
                result["tests_pass"] = False
                return result
            node_type = add_eff[2]
            new_attrs = add_eff[3] if len(add_eff) > 3 and isinstance(add_eff[3], dict) else {}
            carry_keys = [k for k, v in new_attrs.items()
                          if isinstance(v, dict) and "__term__" in v]
            literals = {k: v for k, v in new_attrs.items()
                        if not (isinstance(v, dict) and "__term__" in v)}
            states = [(k, val) for (v, k, val) in _positive_state_eqs(rule.get("where"))
                      if v == vsubj]
            before = set(s.nodes(node_type))
            # positive: build hub -rel-> subject, subject carries sentinel values +
            # the trigger; run; a node of node_type must be minted carrying them.
            sentinels = {k: float(1000 + i) for i, k in enumerate(carry_keys)}
            h, subj = _n(), _n(dict(sentinels))
            _edge(h, rel, subj)
            for (k, val) in states:
                s.set_attr(subj, k, val)
            inner.run_rules(10000)
            minted = [n for n in s.nodes(node_type) if n not in before]
            carried_ok = False
            literal_ok = False
            if minted:
                ma = s.node(minted[0])["attrs"]
                # compare against the subject's ACTUAL post-setup value (a trigger
                # attr may also be carried, overwriting its sentinel — the copy
                # must equal whatever the subject holds, not the pre-set sentinel).
                sa = s.node(subj)["attrs"]
                carried_ok = all(ma.get(k) == sa.get(k) for k in carry_keys)
                literal_ok = all(ma.get(k) == v for k, v in literals.items())
            pos_ok = bool(minted) and carried_ok and literal_ok
            # mint-once: a second run must NOT mint a duplicate for the same subject.
            n_after_first = len([n for n in s.nodes(node_type) if n not in before])
            inner.run_rules(10000)
            n_after_second = len([n for n in s.nodes(node_type) if n not in before])
            once_ok = (n_after_second == n_after_first)
            # negative (guard): a trigger exists -> without it, no mint.
            neg_ok = True
            if states:
                before2 = set(s.nodes(node_type))
                h2, subj2 = _n(), _n(dict(sentinels))
                _edge(h2, rel, subj2)
                inner.run_rules(10000)
                neg_ok = not [n for n in s.nodes(node_type) if n not in before2]
            result["effect_matches"] = bool(pos_ok and once_ok and neg_ok)
            result["observed"] = {"minted": bool(minted), "carried_ok": carried_ok,
                                  "literal_ok": literal_ok, "mint_once_ok": once_ok,
                                  "guard_blocks_without_trigger": neg_ok}
            result["expected"] = ("add_node(%s) carrying %s from %s iff %s, minted once"
                                  % (node_type, carry_keys or "no attrs", vsubj,
                                     " & ".join("%s.%s==%s" % (vsubj, k, val)
                                                for (k, val) in states) or "always"))
        elif effect == "set_attr":
            patient, rel, other = _match_edge(rule)
            eff = rule["effects"][0]
            sattr, val = eff[2], eff[3]
            p, o = _n(), _n()
            _edge(p, rel, o)
            inner.run_rules(10000)
            got = s.node(p)["attrs"].get(sattr)
            result["effect_matches"] = (got == val)
            result["observed"] = {"attr_after": got, "expected": val}
            result["expected"] = "%s.%s == %s" % (patient, sattr, val)
        else:
            result["observed"] = {"unsupported_effect": effect}
    except Exception as e:
        result["observed"] = {"run_error": "%s: %s" % (type(e).__name__, e)}

    result["tests_pass"] = result["effect_matches"]
    inner.add_node("NativeReadMethodValidationReceipt", {
        "schema": "native_read_method_validation_receipt_v1",
        "cluster": "read_method_draft.native_validation",
        "provenance": "native_rule_readback:read_method_validation",
        "native_rule": "read_method_draft_synthesized_rule",
        "native_steps": ["install_draft_rule", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    result["how"] = ("built a minimal instance from the read model, ran the "
                     "synthesised rule, checked the described effect")
    # `notes` is what attach_validation persists (effect_matches/observed are not),
    # so fold the verdict into it for read-back.
    result["notes"] = ("read_method_rule: effect_matches=%s; expected[%s]; "
                       "observed=%s" % (result["effect_matches"],
                                        result["expected"], result["observed"]))
    return result


# --------------------------------------------------------------------------- #
#  ADOPT — install live + persist as seed `rules` data
# --------------------------------------------------------------------------- #
def adopt(agent, draft: dict, *, category: str = "read_method_rules",
          seeds_dir: Optional[Path] = None,
          persist: bool = True) -> dict:
    """Install the validated rule LIVE (the capability runs now) and persist it
    as seed `rules` data (append to `<seeds_dir>/<category>.json`) so a fresh
    boot re-installs it via load_all_seeds / load_seed_manifest. Mechanical:
    the DECISION to adopt was already made by the reflex reading the
    validation."""
    _, inner = _resolve(agent)
    rule = draft["rules"][0]
    idx = inner.add_rule(rule)
    out = {"installed": True, "rule_idx": idx, "rule_name": rule.get("name"),
           "persisted": False, "seed_path": None}
    if persist:
        p = _persist_rule_seed(rule, draft, category, seeds_dir)
        out["persisted"] = bool(p)
        out["seed_path"] = str(p) if p else None
    return out


def _persist_rule_seed(rule: dict, draft: dict, category: str,
                       seeds_dir: Optional[Path]) -> Optional[Path]:
    """Append the rule to `<seeds_dir>/<category>.json`'s `rules` array
    (create if absent). A durable seed the native loader installs as an
    executable rule on a fresh boot. Guarded off the real seed dir the same way
    domains.teach guards its writes."""
    root = Path(__file__).resolve().parent.parent
    real_seeds = root / "seeds"
    sd = Path(seeds_dir) if seeds_dir else real_seeds
    # never clobber the real boot seeds when the durable-safety guard is armed.
    if (os.environ.get("OZMA_SEED_PERSIST_DISABLED")
            and sd.resolve() == real_seeds.resolve()):
        return None
    sd.mkdir(parents=True, exist_ok=True)
    path = sd / ("%s.json" % category)
    if path.exists():
        m = json.loads(path.read_text())
    else:
        m = {"id": category, "version": "1.0.0", "depends_on": [],
             "description": "Rules the agent authored by reading a method.",
             "nodes": [], "edges": [], "productions": [], "rules": []}
    m.setdefault("rules", [])
    if any(isinstance(r, dict) and r.get("name") == rule.get("name")
           for r in m["rules"]):
        return path                      # idempotent — already persisted.
    m["rules"].append(rule)
    path.write_text(json.dumps(m, indent=1))
    return path


__all__ = ["draft_from_reading", "validate_by_running", "adopt"]
