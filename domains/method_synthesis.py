"""synthesise_rule_from_method (K2) - compile a read MethodModel into real
RewriteRule JSON that RUNS.

This is a RULE-JSON BUILDER, exactly the same legal category as the seven
_compose_*_rule builders in domains/reflective_faculty.py: it ASSEMBLES graph
data (RewriteRule dicts) from a structured MethodModel + a binding, and makes NO
runtime decision over graph state. The synthesised rules run in Rust via
inner.run_rules - the agent then EXECUTES the procedure it read.

The mapping is STRUCTURAL over the bounded procedural grammar, not per-method:
it dispatches on the MethodStep's effect KIND (recompute / add_edge / set_attr /
del_edge), and within each kind builds match/where/effects from the extracted
patient / roles / relation / condition / trigger. Two different read methods ->
two different rule sets (the generality the K3 gate proves), the direct analogue
of "different goal -> different transferred plan".

BINDING (abstract-noun -> concrete graph vocabulary). Comprehension gives the
STRUCTURE; the binding gives the concrete edge/attr/aggregate names a domain uses
(supplied here as a slot_map - the task permits grounded concepts OR a provided
slot_map). Fields (all optional; sensible defaults derived from the model):
  relations   {abstract_rel: concrete_edge}    default: identity
  role_relation  concrete edge reaching a possessive target ("its owner")
  value_attr  the recompute view's stored-value attr        default "val"
  aggregate   {"op":"Count","edge":<edge>,"value_attr":<attr>}  (Count/Sum/Mean/
              Max/Min; Mean is COMPOSED as Sum/Count, not a primitive Term)
  state_attr  {abstract_state: concrete_attr}                default: identity
  edge_types  {abstract_edge: concrete_edge}                 default: identity
  subject_relation  anchor edge (hub -> subject) for an add_node mint
  node_types  {abstract_type: ConcreteType}   default: TitleCase of the noun
  carry_attrs [attr, ...]  keys COPIED from the matched subject onto the minted
              node (attr-propagation from a matched var)
  literal_attrs {k: v}  literal attrs set on the minted node
  link_edge   edge added from subject to the minted node (optional)
"""
from __future__ import annotations

from typing import Any, Optional


# --- DSL term constructors (same helpers the _compose_*_rule builders use) --- #
def _V(n): return {"type": "Var", "name": n}
def _L(v): return {"type": "Lit", "value": v}
def _Attr(nd, k): return {"type": "Attr", "node": nd, "key": k}
def _Nb(nd, et): return {"type": "Neighbours", "node": nd, "edge_type": et}
def _Count(x): return {"type": "Count", "source": x}
def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _Not(x): return {"type": "Not", "arg": x}
def _And(*xs): return {"type": "And", "items": list(xs)}
def _In(m, c): return {"type": "In", "member": m, "container": c}


def _titlecase(noun: str) -> str:
    """Derive a graph node TYPE name from a read role noun: 'replacement target'
    -> 'ReplacementTarget', 'ticket' -> 'Ticket'. A mechanical name transform (the
    binding may override via node_types); confirmed against the domain graph
    upstream when a node of that type already exists."""
    return "".join(w[:1].upper() + w[1:] for w in str(noun).split())


def _steps(model) -> list:
    return model.get("steps", []) if isinstance(model, dict) else list(model)


def _relations(model) -> dict:
    """{(subject, object): relation} collected from the model's relation steps."""
    out = {}
    for st in _steps(model):
        m = st.get("main") or {}
        if m.get("kind") == "relation" and m.get("subject") and m.get("object"):
            out[(m["subject"], m["object"])] = m["relation"]
    return out


def _action_step(model) -> Optional[dict]:
    for st in _steps(model):
        if (st.get("main") or {}).get("kind") == "action":
            return st
    return None


def _state_trigger_for(model, patient) -> Optional[dict]:
    """A state-transition step whose main-clause subject is `patient` (IVM: 'the
    view becomes stale' feeds the recompute step's staleness condition)."""
    for st in _steps(model):
        m = st.get("main") or {}
        if m.get("kind") == "state" and m.get("subject") == patient:
            return {"state": m.get("state"), "trigger": st.get("trigger")}
    return None


def _aggregate_term(src_var: str, binding: dict):
    """The aggregate over the source's collection as a DSL Term. The OP is the
    agent's READ aggregate_op (Count / Sum / Max / Min — a graph-Term CHOICE,
    not per-method code); Count reduces the edge set, Sum/Max/Min reduce a
    per-element numeric value. The value attr (which numeric slot to reduce over
    — the one piece a bare 'count of X' definition does not name) is the
    binding's aggregate.value_attr, defaulting to 'value'."""
    agg = binding.get("aggregate") or {"op": "Count", "edge": "has_mention"}
    op = agg.get("op", "Count")
    source = _Nb(_V(src_var), agg["edge"])
    if op == "Count":
        return _Count(source)
    vattr = agg.get("value_attr", "value")
    if op == "Mean":
        # Mean is NOT a primitive reducer — COMPOSE it from the two that are:
        # Mean(v) = Sum(v) / Count. Div is a DSL arithmetic Term, Sum + Count
        # are the primitive reducers over the SAME collection source. (The
        # honest wall the old code raised is lifted precisely because the DSL
        # DOES offer Div — no new Rust, pure composition of held Terms.)
        return {"type": "Div",
                "a": {"type": "Sum", "source": source, "var_name": "e",
                      "value": _Attr(_V("e"), vattr)},
                "b": _Count(source)}
    # Sum / Max / Min: reduce a per-element numeric value over the collection.
    reducer = {"Sum": "Sum", "Max": "MaxOver", "Min": "MinOver"}.get(op)
    if reducer is None:
        raise ValueError("unsupported aggregate op %r (no DSL reducer Term)" % op)
    return {"type": reducer, "source": source, "var_name": "e",
            "value": _Attr(_V("e"), vattr)}


def synthesise_rule_from_method(agent, model, binding: Optional[dict] = None,
                                *, install: bool = True) -> dict:
    """Compile `model` (a read MethodModel) into RewriteRule JSON and (optionally)
    install it. Returns {rules, rule_idx, effect, how, ...} or {wall: ...}."""
    binding = dict(binding or {})
    rels = _relations(model)
    rel_map = binding.get("relations", {})
    role_relation = binding.get("role_relation")
    state_attr = binding.get("state_attr", {})
    edge_types = binding.get("edge_types", {})
    value_attr = binding.get("value_attr", "val")
    tag = str(model.get("name", "method")) if isinstance(model, dict) else "method"

    act = _action_step(model)
    if act is None:
        return {"wall": "no action step in method (nothing to synthesise)",
                "model": model.get("name") if isinstance(model, dict) else None}
    main = act["main"]
    effect = main.get("effect")
    patient = main.get("patient")
    roles = main.get("roles") or {}

    # -------------------------------------------------------------- recompute
    if effect == "recompute":
        source = roles.get("source")
        if not source:
            return {"wall": "recompute: no source role extracted", "effect": effect}
        # the relation linking patient(view) -> source, from a relation step
        rel = rels.get((patient, source)) or rels.get((source, patient))
        if rel is None:
            return {"wall": "recompute: no dependency relation between %r and %r "
                            "(needs a 'X depends on Y' step)" % (patient, source),
                    "effect": effect}
        concrete_rel = rel_map.get(rel, rel)
        vview, vsrc = patient or "view", source or "src"
        agg = _aggregate_term(vsrc, binding)
        # staleness condition: aggregate(source) != view.value_attr
        cond = _Not(_Eq(agg, _Attr(_V(vview), value_attr)))
        rule = {
            "name": "synth_recompute_%s" % tag,
            "match": [[vview, concrete_rel, vsrc]],
            "where": cond,
            "effects": [["set_attr", vview, value_attr, {"__term__": agg}]],
        }
        return _finish(agent, [rule], effect, install,
                       how=("Read 'recompute a stale <view> from its <source>' + '<view> depends on "
                            "<source>' + '<view> becomes stale' -> match the dependency edge "
                            "[%s -%s-> %s], guard on staleness (aggregate(%s) != %s.%s), effect "
                            "set_attr %s.%s = aggregate(%s). The materialized view self-heals to "
                            "fixpoint." % (vview, concrete_rel, vsrc, vsrc, vview, value_attr,
                                           vview, value_attr, vsrc)))

    # -------------------------------------------------------------- add / del edge
    if effect in ("add_edge", "del_edge"):
        source = roles.get("source")
        target = roles.get("target")
        etype = edge_types.get(main.get("edge_type"), main.get("edge_type"))
        if not (source and target and etype):
            return {"wall": "%s: need source+target roles and an edge type (got "
                            "source=%r target=%r edge=%r)" % (effect, source, target, etype),
                    "effect": effect}
        # anchor: a relation reaching the (possessive) target from the source
        rel = rels.get((source, target)) or role_relation
        if rel is None:
            return {"wall": "%s: no relation binds target %r to source %r (supply "
                            "binding.role_relation for a possessive target)" % (effect, target, source),
                    "effect": effect}
        concrete_rel = rel_map.get(rel, rel)
        vsrc, vtgt = source, target
        conds = []
        # trigger state predicate ("when a task is marked done" -> task.done == 1)
        trig = act.get("trigger") or {}
        if trig.get("kind") == "state" and trig.get("state"):
            sattr = state_attr.get(trig["state"], trig["state"])
            conds.append(_Eq(_Attr(_V(vsrc), sattr), _L(1.0)))
        if effect == "add_edge":
            # idempotence: do not re-add an existing edge
            conds.append(_Not(_In(_V(vtgt), _Nb(_V(vsrc), etype))))
            eff = [["add_edge", vsrc, etype, vtgt]]
        else:
            conds.append(_In(_V(vtgt), _Nb(_V(vsrc), etype)))
            eff = [["del_edge", vsrc, etype, vtgt]]
        where = conds[0] if len(conds) == 1 else _And(*conds)
        rule = {
            "name": "synth_%s_%s" % (effect, tag),
            "match": [[vsrc, concrete_rel, vtgt]],
            "where": where,
            "effects": eff,
        }
        return _finish(agent, [rule], effect, install,
                       how=("Read '<when %s is %s>, %s a <%s> edge from <%s> to <%s>' -> match the "
                            "role edge [%s -%s-> %s], guard on the trigger state, effect %s(%s, %s, %s)."
                            % (trig.get("subject"), trig.get("state"), main.get("verb"), etype, vsrc, vtgt,
                               vsrc, concrete_rel, vtgt, effect, vsrc, etype, vtgt)))

    # -------------------------------------------------------------- add_node
    if effect == "add_node":
        # "<when a SUBJECT is TRIGGER>, create a <TYPE> from the <subject>" ->
        # MINT a fresh node of TYPE, carrying named attrs FROM the subject
        # (attr-propagation), gated by the trigger, mint-once via a marker.
        # This is the NEW effect the bridge family needs: a rule that CREATES a
        # node whose attrs are SOURCED from the matched subject var.
        source = roles.get("source")
        node_type_abs = main.get("node_type") or patient
        if not (source and node_type_abs):
            return {"wall": "add_node: need a source role (the subject to mint "
                            "from) and a created node type (got source=%r type=%r)"
                            % (source, node_type_abs), "effect": effect}
        # the anchor: an edge (hub -REL-> subject) so the rule can MATCH the
        # subject. A relation step naming it, else binding.subject_relation
        # (grounded against the domain graph, exactly like role_relation).
        subj_rel = None
        hub = "hub"
        for (a, b), r in rels.items():
            if b == source:
                subj_rel, hub = r, a
                break
        if subj_rel is None:
            subj_rel = binding.get("subject_relation")
        if subj_rel is None:
            return {"wall": "add_node: no relation reaches the subject %r (supply "
                            "binding.subject_relation, an edge hub->subject)" % source,
                    "effect": effect}
        subj_rel = rel_map.get(subj_rel, subj_rel)
        node_types = binding.get("node_types", {})
        concrete_type = node_types.get(node_type_abs) or _titlecase(node_type_abs)
        vsubj = source
        vnew = "new_" + "".join(c if c.isalnum() else "_" for c in str(node_type_abs))
        marker = "synth_minted_%s" % tag
        # the new node's attrs: literals + carried-from-subject (attr-propagation)
        carry = list(binding.get("carry_attrs", []))
        new_attrs = dict(binding.get("literal_attrs", {}))
        for k in carry:
            new_attrs[k] = {"__term__": _Attr(_V(vsubj), k)}
        conds = [_Not(_Eq(_Attr(_V(vsubj), marker), _L(1.0)))]
        trig = act.get("trigger") or {}
        if trig.get("kind") == "state" and trig.get("state"):
            sattr = state_attr.get(trig["state"], trig["state"])
            conds.append(_Eq(_Attr(_V(vsubj), sattr), _L(1.0)))
        where = conds[0] if len(conds) == 1 else _And(*conds)
        eff = [["set_attr", vsubj, marker, 1.0],
               ["add_node", vnew, concrete_type, new_attrs]]
        link_edge = binding.get("link_edge")
        if link_edge:
            eff.append(["add_edge", vsubj, link_edge, vnew])
        rule = {
            "name": "synth_add_node_%s" % tag,
            "match": [[hub, subj_rel, vsubj]],
            "where": where,
            "effects": eff,
        }
        return _finish(agent, [rule], effect, install,
                       how=("Read '<when %s is %s>, create a <%s> from <%s>' -> match "
                            "the anchor edge [%s -%s-> %s], guard on the trigger + a "
                            "mint-once marker, effect add_node(%s) carrying %s from %s%s."
                            % (trig.get("subject"), trig.get("state"), concrete_type,
                               vsubj, hub, subj_rel, vsubj, concrete_type,
                               carry or "no attrs", vsubj,
                               (" + link %s -%s-> %s" % (vsubj, link_edge, vnew))
                               if link_edge else "")))

    # -------------------------------------------------------------- set_attr
    if effect == "set_attr":
        # "<when trigger>, mark <patient> <state>" -> set patient.state = 1
        state = main.get("condition") or (main.get("roles") or {}).get("state")
        if not (patient and state):
            return {"wall": "set_attr: need patient + state (got patient=%r state=%r)"
                            % (patient, state), "effect": effect}
        sattr = state_attr.get(state, state)
        rel = None
        for (a, b), r in rels.items():
            if a == patient or b == patient:
                rel = r; other = b if a == patient else a; break
        else:
            return {"wall": "set_attr: no anchor relation for patient %r" % patient, "effect": effect}
        concrete_rel = rel_map.get(rel, rel)
        rule = {
            "name": "synth_set_attr_%s" % tag,
            "match": [[patient, concrete_rel, other]],
            "where": _Not(_Eq(_Attr(_V(patient), sattr), _L(1.0))),
            "effects": [["set_attr", patient, sattr, 1.0]],
        }
        return _finish(agent, [rule], effect, install,
                       how="Read a mark/set action -> set_attr %s.%s = 1." % (patient, sattr))

    # -------------------------------------------------------------- classify
    if effect == "classify":
        # "when a <FACT>'s <key> matches a <CODEBOOK>'s <key>, classify a <TYPE>"
        # -> the CLASSIFY-BY-CODEBOOK-JOIN shape: match TWO held collections
        # (agent -has_FACT-> f, agent -has_CODEBOOK-> c), JOIN them by Eq on the
        # shared field(s), optionally scalar-guard the fact, dedup via Not-Exists,
        # and MINT a fresh typed classification node carrying fields FROM BOTH
        # matched vars + literals, linked off the agent. This is the recurring
        # media_analysis/actor_goals slice (mint_agent_deletion / mint_actor_goal):
        # match-2 + Eq-join(s) + scalar guards + Not-Exists dedup + add_node +
        # add_edge. The JOIN comes from the READ trigger clause (kind=='join');
        # the classification TYPE from the main clause; the concrete edges + the
        # copied-field detail from the BINDING (grounded / supplied), exactly the
        # reader=structure / binding=vocab split every other branch uses.
        trig = act.get("trigger") or {}
        if trig.get("kind") != "join":
            return {"wall": "classify: no join trigger clause (need 'when a <fact>'s "
                            "<key> matches a <codebook>'s <key>, classify a <type>')",
                    "effect": effect}
        fact_abs = trig.get("fact_type")
        cb_abs = trig.get("codebook_type")
        fk = trig.get("fact_key")
        ck = trig.get("codebook_key")
        cls_abs = main.get("node_type") or patient
        fact_edge = binding.get("fact_edge")
        cb_edge = binding.get("codebook_edge")
        cls_edge = binding.get("classification_edge")
        missing = [nm for nm, v in (("fact_type", fact_abs), ("fact_key", fk),
                                    ("codebook_type", cb_abs), ("codebook_key", ck),
                                    ("classification_type", cls_abs),
                                    ("fact_edge", fact_edge), ("codebook_edge", cb_edge),
                                    ("classification_edge", cls_edge)) if not v]
        if missing:
            return {"wall": "classify: missing %s (read fact/codebook/key from the "
                            "join clause + classification type from the main clause; "
                            "fact_edge/codebook_edge/classification_edge from the "
                            "binding)" % ", ".join(missing), "effect": effect}
        node_types = binding.get("node_types", {})
        fact_type = node_types.get(fact_abs) or _titlecase(fact_abs)
        cls_type = node_types.get(cls_abs) or _titlecase(cls_abs)
        # JOIN pair(s): the read (fact_key, codebook_key) by default; binding may
        # add/override with more join pairs.
        joins = binding.get("join") or [[fk, ck]]
        # scalar guards Eq(f.attr, lit) — e.g. actor_role == 'agent'.
        guards = binding.get("guards", [])
        # copied fields: fact_carry [attr,...] from f; codebook_carry {new_key:
        # cb_attr} from c (rename supported, e.g. goal -> surface_goal).
        fact_carry = list(binding.get("fact_carry", []))
        cb_carry = dict(binding.get("codebook_carry", {}))
        literal_attrs = dict(binding.get("literal_attrs", {}))
        # dedup identity: the fact fields that make a classification unique; default
        # to the carried fact fields, else the join key.
        dedup_keys = list(binding.get("dedup_keys") or fact_carry or [fk])

        conds = []
        for (a_k, b_k) in joins:
            conds.append(_Eq(_Attr(_V("f"), a_k), _Attr(_V("c"), b_k)))
        for (attr, lit) in guards:
            conds.append(_Eq(_Attr(_V("f"), attr), _L(lit)))
        dpred = [_Eq(_Attr(_V("cls2"), k), _Attr(_V("f"), k)) for k in dedup_keys]
        dpred_t = dpred[0] if len(dpred) == 1 else _And(*dpred)
        conds.append(_Not({"type": "Exists",
                           "source": {"type": "NodesOfType", "node_type": cls_type},
                           "var_name": "cls2", "predicate": dpred_t}))
        where = conds[0] if len(conds) == 1 else _And(*conds)

        new_attrs = dict(literal_attrs)
        for k in fact_carry:
            new_attrs[k] = {"__term__": _Attr(_V("f"), k)}
        for newk, cba in cb_carry.items():
            new_attrs[newk] = {"__term__": _Attr(_V("c"), cba)}
        rule = {
            "name": "synth_classify_%s" % tag,
            "batch": False,
            "match": [["agent", fact_edge, "f"], ["agent", cb_edge, "c"]],
            "where": where,
            "effects": [["add_node", "cls", cls_type, new_attrs],
                        ["add_edge", "agent", cls_edge, "cls"]],
        }
        return _finish(agent, [rule], effect, install,
                       how=("Read 'when a <%s>'s <%s> matches a <%s>'s <%s>, classify a "
                            "<%s>' -> match [agent -%s-> f] & [agent -%s-> c], JOIN by %s, "
                            "guard %s, dedup Not-Exists over %s on %s, effect add_node(%s) "
                            "carrying %s from f + %s from c%s, link agent -%s-> it."
                            % (fact_abs, fk, cb_abs, ck, cls_abs, fact_edge, cb_edge,
                               " & ".join("f.%s==c.%s" % (a_k, b_k) for (a_k, b_k) in joins),
                               guards or "none", cls_type, dedup_keys, cls_type,
                               fact_carry or "no attrs", list(cb_carry.items()) or "no attrs",
                               (" + literals %s" % literal_attrs) if literal_attrs else "",
                               cls_edge)))

    return {"wall": "unsupported effect kind %r" % effect, "effect": effect}


def _finish(agent, rules, effect, install, *, how) -> dict:
    if not install:
        return {"rules": rules, "effect": effect, "how": how, "installed": False}
    inner = getattr(agent, "inner", None)
    idxs = []
    for r in rules:
        try:
            idxs.append(inner.add_rule(r))
        except Exception as e:
            return {"wall": "rule install failed: %s: %s" % (type(e).__name__, e),
                    "rules": rules, "effect": effect}
    return {"rules": rules, "rule_idx": idxs, "effect": effect, "how": how, "installed": True}


__all__ = ["synthesise_rule_from_method"]
