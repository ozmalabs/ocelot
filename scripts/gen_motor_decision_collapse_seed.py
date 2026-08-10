"""Generate the domain-neutral graph-native motor decision-collapse core.

This is the reusable scalar-value counterpart of Bigville's compiled-net
decision collapse.  The generator only authors graph data; all proposal,
residual, deeper valuation, deterministic collapse, and internalization run as
Rust-evaluated Terms and rewrite rules.
"""
from __future__ import annotations

import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def AttrOf(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def P0(var, key):
    return Plus(A(var, key), L(0.0))


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Abs(arg):
    return {"type": "Abs", "arg": arg}


def Max(*items):
    return {"type": "Max", "items": list(items)}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Neighbours(var, edge_type):
    return {
        "type": "Neighbours",
        "node": V(var),
        "edge_type": edge_type,
        "any_type": False,
    }


def Union(a, b):
    return {"type": "Union", "a": a, "b": b}


def Filter(source, var_name, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Count(source):
    return {"type": "Count", "source": source}


def Argmax(source, var_name, value, default):
    return {
        "type": "Argmax",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def InNeighbours(var, edge_type):
    return {
        "type": "InNeighbours",
        "node": V(var),
        "edge_type": edge_type,
        "any_type": False,
    }


def T(term):
    return {"__term__": term}


OPTIONS = Union(
    Neighbours("state", "in_scene"),
    Neighbours("state", "in_episode"),
)
AVAILABLE = Filter(
    OPTIONS,
    "option",
    Gt(P0("option", "available"), L(0.5)),
)


def fast_value(var):
    """A learned value when supported by experience, otherwise its prior."""
    return Ite(
        Gt(P0(var, "decision_experience_count"), L(0.0)),
        P0(var, "learned_value"),
        P0(var, "default_value"),
    )


def ranked(value, var):
    """Stable total ordering without importing semantic action names."""
    return Plus(value, Times(L(-0.000000001), P0(var, "ordinal")))


def fast_best():
    return Argmax(
        AVAILABLE,
        "option",
        ranked(fast_value("option"), "option"),
        V("state"),
    )


def deep_score(var):
    return Plus(
        P0(var, "grounded_value"),
        Times(P0("state", "rationalise_gain"), fast_value(var)),
    )


def deep_best():
    return Argmax(
        AVAILABLE,
        "option",
        ranked(deep_score("option"), "option"),
        V("state"),
    )


def fast_propose_rule():
    best = fast_best()
    grounded_best = deep_best()
    fast = AttrOf(best, "learned_value")
    prior = AttrOf(best, "default_value")
    selected_fast = Ite(
        Gt(AttrOf(best, "decision_experience_count"), L(0.0)),
        Plus(fast, L(0.0)),
        Plus(prior, L(0.0)),
    )
    grounded = Plus(AttrOf(best, "grounded_value"), L(0.0))
    prediction_residual = Abs(Minus(selected_fast, grounded))
    counterfactual_regret = Max(
        L(0.0),
        Minus(
            Plus(AttrOf(grounded_best, "grounded_value"), L(0.0)),
            grounded,
        ),
    )
    rank_reversal_signal = Ite(
        Gt(counterfactual_regret, L(0.0)),
        Plus(P0("state", "settle_tolerance"), counterfactual_regret),
        L(0.0),
    )
    return {
        "name": "mdc_fast_propose",
        "area": "motor_decision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Order-0 proposal from the state-local option set. An "
        "experienced option uses its learned value; a novel option falls back "
        "to its graph-held default. Stable ordinal resolves exact ties.",
        "match": [["agent", "has_motor_decision", "state"]],
        "where": And(
            Eq(A("state", "stage"), L("ready")),
            Eq(P0("state", "collapse_armed"), L(1.0)),
            Gt(Count(AVAILABLE), L(0.0)),
        ),
        "effects": [
            ["set_attr", "state", "proposed_option_ref", T(best)],
            ["set_attr", "state", "proposed_token", T(AttrOf(best, "token"))],
            ["set_attr", "state", "proposed_ordinal", T(AttrOf(best, "ordinal"))],
            ["set_attr", "state", "proposed_fast_value", T(selected_fast)],
            ["set_attr", "state", "proposed_grounded_value", T(grounded)],
            ["set_attr", "state", "prediction_residual", T(prediction_residual)],
            ["set_attr", "state", "counterfactual_regret", T(
                counterfactual_regret
            )],
            ["set_attr", "state", "rank_reversal_signal", T(
                rank_reversal_signal
            )],
            ["set_attr", "state", "residual", T(Max(
                prediction_residual,
                rank_reversal_signal,
            ))],
            ["set_attr", "state", "order", 0.0],
            ["set_attr", "state", "deepened", 0.0],
            ["set_attr", "state", "deeper_authorized", 0.0],
            ["set_attr", "state", "internalization_required", 0.0],
            ["set_attr", "state", "internalization_complete", 1.0],
            ["set_attr", "state", "collapse_armed", 0.0],
            ["set_attr", "state", "stage", "residual_check"],
        ],
    }


def shallow_settle_rule():
    return {
        "name": "mdc_shallow_settle",
        "area": "motor_decision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A small residual means the fast/default proposal is already "
        "settled. Disabling depth also caps the same collapse at order zero.",
        "match": [["agent", "has_motor_decision", "state"]],
        "where": And(
            Eq(A("state", "stage"), L("residual_check")),
            Or(
                Not(Gt(P0("state", "residual"), P0("state", "settle_tolerance"))),
                Not(Eq(P0("state", "deeper_enabled"), L(1.0))),
            ),
        ),
        "effects": [
            ["set_attr", "state", "chosen_option_ref",
             T(A("state", "proposed_option_ref"))],
            ["set_attr", "state", "chosen_token", T(A("state", "proposed_token"))],
            ["set_attr", "state", "chosen_ordinal", T(P0("state", "proposed_ordinal"))],
            ["set_attr", "state", "chosen_via", "order0"],
            ["set_attr", "state", "deeper_authorized", 0.0],
            ["set_attr", "state", "stage", "settled"],
            ["set_attr", "state", "done", 1.0],
        ],
    }


def deepen_rule():
    best = deep_best()
    return {
        "name": "mdc_residual_authorized_deepen",
        "area": "motor_decision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "There is no separate escalation policy: only a residual "
        "above tolerance authorizes grounded order-N valuation. The same stable "
        "ordinal total-orders ties.",
        "match": [["agent", "has_motor_decision", "state"]],
        "where": And(
            Eq(A("state", "stage"), L("residual_check")),
            Gt(P0("state", "residual"), P0("state", "settle_tolerance")),
            Eq(P0("state", "deeper_enabled"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "state", "chosen_option_ref", T(best)],
            ["set_attr", "state", "chosen_token", T(AttrOf(best, "token"))],
            ["set_attr", "state", "chosen_ordinal", T(AttrOf(best, "ordinal"))],
            ["set_attr", "state", "chosen_grounded_value", T(AttrOf(best, "grounded_value"))],
            ["set_attr", "state", "chosen_via", "orderN"],
            ["set_attr", "state", "deeper_authorized", 1.0],
            ["set_attr", "state", "deepened", 1.0],
            ["set_attr", "state", "order", 1.0],
            ["set_attr", "state", "internalization_required", 1.0],
            ["set_attr", "state", "internalization_complete", 0.0],
            ["set_attr", "state", "stage", "internalizing"],
        ],
    }


def internalize_rule(edge_type):
    current = fast_value("option")
    revised = Plus(
        current,
        Times(
            P0("state", "internalization_gain"),
            Minus(P0("option", "grounded_value"), current),
        ),
    )
    suffix = "scene" if edge_type == "in_scene" else "episode"
    return {
        "name": f"mdc_internalize_{suffix}_option",
        "area": "motor_decision_learning",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": f"Settle the grounded valuation back into each {suffix}-scoped "
        "option's fast learned value. An epoch stamp makes the Union idempotent "
        "when an option is linked through both scopes.",
        "match": [
            ["agent", "has_motor_decision", "state"],
            ["state", edge_type, "option"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("internalizing")),
            Gt(P0("option", "available"), L(0.5)),
            Or(
                Eq(V("option"), A("state", "proposed_option_ref")),
                Eq(V("option"), A("state", "chosen_option_ref")),
            ),
            Not(Eq(P0("option", "internalized_epoch"), P0("state", "decision_epoch"))),
        ),
        "effects": [
            ["set_attr", "option", "learned_value", T(revised)],
            ["set_attr", "option", "decision_experience_count",
             T(Plus(
                 P0("option", "decision_experience_count"),
                 L(1.0),
             ))],
            ["set_attr", "option", "internalized_epoch", T(P0("state", "decision_epoch"))],
            ["set_attr", "option", "learning_provenance", "grounded_settle_back"],
        ],
    }


def finish_internalization_rule():
    pending = Filter(
        AVAILABLE,
        "option",
        And(
            Or(
                Eq(V("option"), A("state", "proposed_option_ref")),
                Eq(V("option"), A("state", "chosen_option_ref")),
            ),
            Not(Eq(
                P0("option", "internalized_epoch"),
                P0("state", "decision_epoch"),
            )),
        ),
    )
    return {
        "name": "mdc_finish_internalization",
        "area": "motor_decision_learning",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The decision becomes externally readable only after the "
        "fast proposal and grounded winner have settled back into the fast "
        "substrate. Unchosen non-competitors receive no fictitious action credit.",
        "match": [["agent", "has_motor_decision", "state"]],
        "where": And(
            Eq(A("state", "stage"), L("internalizing")),
            Eq(Count(pending), L(0.0)),
        ),
        "effects": [
            ["set_attr", "state", "internalization_complete", 1.0],
            ["set_attr", "state", "stage", "settled"],
            ["set_attr", "state", "done", 1.0],
        ],
    }


def episode_provision_rule():
    return {
        "name": "mdc_episode_provision_state",
        "area": "motor_decision_lifecycle",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Provision one reusable graph decision slot while an episode "
        "exposes options, before any request arms it. AddNodeIfAbsent keys the "
        "slot by episode identity; the same rule scopes every exposed option. "
        "A later request opens this dormant slot, avoiding host lifecycle code.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_motor_decision_option", "option"],
        ],
        "where": Gt(P0("option", "available"), L(-1.0)),
        "effects": [
            ["add_node_if_absent", "state", "MotorDecisionState", {
                "episode_ref": T(V("episode")),
                "bridge_slot": 1.0,
            }],
            ["add_edge", "agent", "has_motor_decision", "state"],
            ["add_edge", "episode", "has_motor_decision_state", "state"],
            ["add_edge", "state", "for_embodied_motor_episode", "episode"],
            ["add_edge", "state", "in_episode", "option"],
        ],
    }


def episode_open_rule():
    active = Filter(
        Neighbours("episode", "has_motor_decision_state"),
        "existing",
        Gt(P0("existing", "active"), L(0.5)),
    )
    return {
        "name": "mdc_episode_open_state",
        "area": "motor_decision_lifecycle",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A graph-authored, monotonically newer episode request opens "
        "the episode's one provisioned state using domain-neutral policy values. "
        "The scope-count equality forbids opening on a partial option set.",
        "match": [
            ["agent", "has_motor_decision_policy", "policy"],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_motor_decision_state", "state"],
        ],
        "where": And(
            Eq(P0("episode", "decision_armed"), L(1.0)),
            Gt(
                P0("episode", "decision_request_epoch"),
                P0("episode", "last_opened_decision_epoch"),
            ),
            Eq(Count(active), L(0.0)),
            Gt(
                Count(Neighbours("episode", "has_motor_decision_option")),
                L(0.0),
            ),
            Eq(
                Count(Neighbours("state", "in_episode")),
                Count(Neighbours("episode", "has_motor_decision_option")),
            ),
        ),
        "effects": [
            ["set_attr", "state", "stage", "ready"],
            ["set_attr", "state", "active", 1.0],
            ["set_attr", "state", "collapse_armed", 1.0],
            ["set_attr", "state", "done", 0.0],
            ["set_attr", "state", "publication_status", "pending"],
            ["set_attr", "state", "decision_epoch",
             T(P0("episode", "decision_request_epoch"))],
            ["set_attr", "state", "settle_tolerance",
             T(P0("policy", "settle_tolerance"))],
            ["set_attr", "state", "deeper_enabled",
             T(P0("policy", "deeper_enabled"))],
            ["set_attr", "state", "internalization_gain",
             T(P0("policy", "internalization_gain"))],
            ["set_attr", "state", "rationalise_gain",
             T(P0("policy", "rationalise_gain"))],
            ["set_attr", "state", "internalization_required", 0.0],
            ["set_attr", "state", "internalization_complete", 0.0],
            ["set_attr", "state", "provenance_kind",
             "episode_bridge_graph_authored"],
            ["set_attr", "episode", "last_opened_decision_epoch",
             T(P0("episode", "decision_request_epoch"))],
            ["set_attr", "episode", "decision_status", "collapsing"],
        ],
    }


def episode_unscope_removed_option_rule():
    still_exposed = Filter(
        Neighbours("episode", "has_motor_decision_option"),
        "exposed",
        Eq(V("exposed"), V("option")),
    )
    return {
        "name": "mdc_episode_unscope_removed_option",
        "area": "motor_decision_lifecycle",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Between decisions, remove an option no longer exposed by "
        "the episode. Provisioning adds new options; this complement keeps the "
        "one reusable state's scope bounded and exact.",
        "match": [
            ["state", "in_episode", "option"],
            ["episode", "has_motor_decision_state", "state"],
        ],
        "where": And(
            Not(Eq(P0("state", "active"), L(1.0))),
            Eq(Count(still_exposed), L(0.0)),
        ),
        "effects": [["del_edge", "state", "in_episode", "option"]],
    }


def episode_refuse_empty_rule():
    return {
        "name": "mdc_episode_refuse_empty",
        "area": "motor_decision_lifecycle",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An armed epoch with no exposed options refuses explicitly "
        "instead of fabricating a token or leaving an unbounded active state.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "decision_armed"), L(1.0)),
            Gt(
                P0("episode", "decision_request_epoch"),
                P0("episode", "last_opened_decision_epoch"),
            ),
            Eq(
                Count(Neighbours("episode", "has_motor_decision_option")),
                L(0.0),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "decision_status", "refused_no_options"],
            ["set_attr", "episode", "decision_armed", 0.0],
            ["set_attr", "episode", "last_opened_decision_epoch",
             T(P0("episode", "decision_request_epoch"))],
        ],
    }


def episode_disarm_stale_request_rule():
    active = Filter(
        Neighbours("episode", "has_motor_decision_state"),
        "state",
        Gt(P0("state", "active"), L(0.5)),
    )
    return {
        "name": "mdc_episode_disarm_stale_request",
        "area": "motor_decision_lifecycle",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A duplicate or older epoch cannot reopen or republish a "
        "decision. Once no state is active, consume the stale armed flag while "
        "leaving the last published opaque verdict intact.",
        "match": [["agent", "has_embodied_motor_episode", "episode"]],
        "where": And(
            Eq(P0("episode", "decision_armed"), L(1.0)),
            Not(Gt(
                P0("episode", "decision_request_epoch"),
                P0("episode", "last_opened_decision_epoch"),
            )),
            Eq(Count(active), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "decision_armed", 0.0],
            ["set_attr", "episode", "decision_status", "stale_request_ignored"],
        ],
    }


def episode_publish_rule():
    return {
        "name": "mdc_episode_publish_once",
        "area": "motor_decision_lifecycle",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Publish exactly once and only from a settled state whose "
        "required settle-back is complete. Copy the opaque verdict and audit "
        "trace to the episode, disarm it, and make the transient inactive.",
        "match": [
            ["episode", "has_motor_decision_state", "state"],
        ],
        "where": And(
            Eq(A("state", "stage"), L("settled")),
            Eq(P0("state", "done"), L(1.0)),
            Eq(P0("state", "internalization_complete"), L(1.0)),
            Eq(A("state", "publication_status"), L("pending")),
            Gt(
                P0("state", "decision_epoch"),
                P0("episode", "last_published_decision_epoch"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "selected_option_ref",
             T(A("state", "chosen_option_ref"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(
                A("state", "chosen_option_ref"), "token"
            ))],
            ["set_attr", "episode", "selected_ordinal", T(AttrOf(
                A("state", "chosen_option_ref"), "ordinal"
            ))],
            ["set_attr", "episode", "selected_via", T(A("state", "chosen_via"))],
            ["set_attr", "episode", "decision_residual", T(P0("state", "residual"))],
            ["set_attr", "episode", "decision_order", T(P0("state", "order"))],
            ["set_attr", "episode", "decision_deepened", T(P0("state", "deepened"))],
            ["set_attr", "episode", "selected_decision_epoch",
             T(P0("state", "decision_epoch"))],
            ["set_attr", "episode", "last_published_decision_epoch",
             T(P0("state", "decision_epoch"))],
            ["set_attr", "episode", "decision_status", "published"],
            ["set_attr", "episode", "decision_armed", 0.0],
            ["set_attr", "state", "publication_status", "published"],
            ["set_attr", "state", "active", 0.0],
        ],
    }


def manifest():
    return {
        "id": "motor_decision_collapse",
        "version": "1.1.0",
        "depends_on": ["capability_collapse"],
        "self_load_only": True,
        "area": "motor_decision",
        "latency_class": "hard_realtime",
        "description": "Domain-neutral motor decision as one graph-native "
        "collapse: state-scoped learned/default order-0 proposal; proposal-versus-"
        "grounded residual as the sole authorization for deeper valuation; stable "
        "ordinal collapse; and grounded settle-back into each option's fast value. "
        "Options are the Union of a decision state's in_scene and in_episode "
        "neighbours. A domain-neutral episode bridge provisions one bounded state, "
        "fully scopes, publishes once, and safely rearms it for any "
        "has_embodied_motor_episode. "
        "Contains no body, actuator-meaning, or physics model.",
        "microtheory": {
            "name": "motor_decision_collapse",
            "description": "Fast defaults become learned habits; residual keeps "
            "the same collapse open for grounded valuation until it can settle.",
        },
        "nodes": [
            {
                "local_id": 1,
                "type": "MotorDecisionPolicy",
                "attrs": {
                    "name": "generic_motor_decision_policy",
                    "settle_tolerance": 0.15,
                    "deeper_enabled": 1.0,
                    "internalization_gain": 0.35,
                    "rationalise_gain": 0.0,
                },
            }
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_motor_decision_policy",
                "tgt": {"local": 1},
                "attrs": {},
            }
        ],
        "productions": [
            {
                "provenance": "motor_decision_collapse:agent_state",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_motor_decision",
                "tgt": {"type": "MotorDecisionState", "var": "state"},
            },
            {
                "provenance": "motor_decision_collapse:scene_option",
                "src": {"type": "MotorDecisionState", "var": "state"},
                "edge_type": "in_scene",
                "tgt": {"type": "DecisionOption", "var": "option"},
            },
            {
                "provenance": "motor_decision_collapse:episode_option",
                "src": {"type": "MotorDecisionState", "var": "state"},
                "edge_type": "in_episode",
                "tgt": {"type": "DecisionOption", "var": "option"},
            },
            {
                "provenance": "motor_decision_collapse:embodied_episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_motor_episode",
                "tgt": {"type": "EmbodiedMotorEpisode", "var": "episode"},
            },
            {
                "provenance": "motor_decision_collapse:episode_exposes_option",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "has_motor_decision_option",
                "tgt": {"type": "DecisionOption", "var": "option"},
            },
            {
                "provenance": "motor_decision_collapse:episode_transient_state",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "has_motor_decision_state",
                "tgt": {"type": "MotorDecisionState", "var": "state"},
            },
        ],
        "rules": [
            fast_propose_rule(),
            shallow_settle_rule(),
            deepen_rule(),
            internalize_rule("in_scene"),
            internalize_rule("in_episode"),
            finish_internalization_rule(),
            episode_provision_rule(),
            episode_open_rule(),
            episode_unscope_removed_option_rule(),
            episode_refuse_empty_rule(),
            episode_disarm_stale_request_rule(),
            episode_publish_rule(),
        ],
    }


def main():
    out = os.path.join(ROOT, "seeds", "motor_decision_collapse.json")
    payload = manifest()
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    with open(out, encoding="utf-8") as handle:
        json.load(handle)
    print(f"wrote {os.path.relpath(out, ROOT)} ({len(payload['rules'])} rules)")


if __name__ == "__main__":
    main()
