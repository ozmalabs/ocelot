"""Emit graph policy for the native asynchronous cognitive-task runtime."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "cognitive_scheduler.json")


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Neighbours(n, et): return {"type": "Neighbours", "node": n, "edge_type": et, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def NodesOfType(node_type): return {"type": "NodesOfType", "node_type": node_type}
def Filter(src, var, pred): return {
    "type": "Filter", "source": src, "var_name": var, "predicate": pred,
}
def IfThenElse(cond, then, other): return {
    "type": "IfThenElse", "cond": cond, "then": then, "other": other,
}
def Argmax(src, var, value, default): return {
    "type": "Argmax", "source": src, "var_name": var,
    "value": value, "default": default,
}
def MaxOver(src, var, value, default): return {
    "type": "MaxOver", "source": src, "var_name": var,
    "value": value, "default": default,
}
def Count(src): return {"type": "Count", "source": src}


def set_if(var, key, value, computed=False):
    return ["set_attr_if_different", var, key, {"__term__": value} if computed else value]


TASKS = Neighbours(V("area"), "has_task")
MAX_SALIENCE = MaxOver(TASKS, "candidate", A("candidate", "salience"), L(0))

RULES = [
    {
        "name": "ct_advance_area_clock_on_result",
        "area": "scheduler",
        "order": 1,
        "latency_class": "soft_realtime",
        "match": [["area", "has_task", "task"]],
        "where": And(
            Eq(A("task", "status"), L("done")),
            Not(Eq(A("task", "clock_accounted"), L(1))),
        ),
        "effects": [
            set_if("area", "logical_tick", Plus(A("area", "logical_tick"), L(1)), True),
            set_if("task", "clock_accounted", 1),
        ],
    },
    {
        "name": "ct_area_input_epoch_tracks_completed_material",
        "area": "scheduler",
        "order": 1,
        "latency_class": "soft_realtime",
        "match": [["area", "has_task", "task"]],
        "where": And(
            Eq(A("task", "status"), L("done")),
            Gt(A("task", "input_epoch"), A("area", "input_epoch")),
        ),
        "effects": [
            set_if("area", "input_epoch", A("task", "input_epoch"), True),
        ],
    },
    {
        "name": "ct_supersede_older_uncommitted_task",
        "area": "scheduler",
        "order": 1,
        "latency_class": "soft_realtime",
        "match": [["newer", "supersedes", "older"]],
        "where": Or(
            Eq(A("older", "status"), L("pending")),
            Eq(A("older", "status"), L("requested")),
        ),
        "effects": [set_if("older", "status", "superseded")],
    },
    {
        "name": "ct_ready_when_dependencies_settle",
        "area": "scheduler",
        "order": 1,
        "latency_class": "soft_realtime",
        "match": [["area", "has_task", "task"]],
        "where": And(
            Eq(A("task", "status"), L("pending")),
            Not(Exists(
                Neighbours(V("task"), "depends_on"), "dependency",
                Not(Eq(A("dependency", "status"), L("done"))))),
        ),
        "effects": [set_if("task", "status", "requested")],
    },
    {
        "name": "ct_rearm_stale_on_area_epoch",
        "area": "scheduler",
        "order": 1,
        "latency_class": "soft_realtime",
        "match": [["area", "has_task", "task"]],
        "where": And(
            Eq(A("task", "status"), L("stale")),
            Lt(A("task", "input_epoch"), A("area", "input_epoch")),
        ),
        "effects": [
            set_if("task", "input_epoch", A("area", "input_epoch"), True),
            set_if("task", "status", "pending"),
        ],
    },
    {
        "name": "ct_area_effort_tracks_live_salience",
        "area": "scheduler",
        "order": 2,
        "latency_class": "best_effort",
        "match": [["area", "has_task", "task"]],
        "where": Not(Eq(A("area", "effort"), MAX_SALIENCE)),
        "effects": [set_if("area", "effort", MAX_SALIENCE, True)],
    },
    {
        "name": "ct_expand_workers_while_backpressure_clean",
        "area": "scheduler",
        "order": 2,
        "latency_class": "best_effort",
        "match": [["area", "has_area_load", "load"]],
        "where": And(
            Gt(A("load", "queued"), L(0)),
            Eq(A("load", "failed"), L(0)),
            Eq(A("load", "fold_conflicts"), L(0)),
            Lt(A("area", "desired_workers"), A("load", "capacity_workers")),
        ),
        "effects": [
            set_if("area", "desired_workers", Plus(A("area", "desired_workers"), L(1)), True)
        ],
    },
    {
        "name": "ct_backoff_workers_on_failure_or_conflict",
        "area": "scheduler",
        "order": 1,
        "latency_class": "hard_realtime",
        "match": [["area", "has_area_load", "load"]],
        "where": And(
            Or(Gt(A("load", "failed"), L(0)), Gt(A("load", "fold_conflicts"), L(0))),
            Gt(A("area", "desired_workers"), L(1)),
        ),
        "effects": [
            set_if("area", "desired_workers", Minus(A("area", "desired_workers"), L(1)), True)
        ],
    },
    {
        "name": "ct_shed_below_max_salience_when_queue_exceeds_capacity",
        "area": "scheduler",
        "order": 1,
        "latency_class": "hard_realtime",
        "match": [["area", "has_area_load", "load"], ["area", "has_task", "task"]],
        "where": And(
            Gt(A("load", "queued"), A("load", "capacity_workers")),
            Eq(A("task", "status"), L("pending")),
            Lt(A("task", "salience"), MAX_SALIENCE),
        ),
        "effects": [set_if("task", "status", "shed")],
    },
    {
        "name": "ct_broadcast_residual_once_per_destination_epoch",
        "area": "scheduler",
        "order": 1,
        "latency_class": "soft_realtime",
        "match": [["src", "projects_to", "dst"], ["src", "has_residual", "residual"]],
        "where": Gt(A("residual", "epoch"), A("dst", "last_residual_epoch")),
        "effects": [
            ["add_edge", "dst", "surprised_by", "residual", {}],
            set_if("dst", "last_residual_epoch", A("residual", "epoch"), True),
        ],
    },
]

# ---------------------------------------------------------------------------
# HOST-ACTION SUPERVISION
#
# A host action is never scheduled by a daemon counter.  A graph fact which
# says that external work is ready mints a pending HostActionRequest paired
# with a CognitiveTask.  The graph then advances that pair to requested; the
# world adapter is only an executor for the requested action and writes a
# HostActionReceipt afterwards.  ``host_requested`` deliberately is not a
# native-kernel status: these tasks describe I/O work, not pure Rust kernels.
#
# The four numeric dimensions are integer graph coordinates. Every legacy
# source begins with the SAME neutral bootstrap. Learned graph rules may alter
# an individual request before release; direct Action/HostAction requests can
# carry their own graph-derived coordinates. There is deliberately no
# per-action number table hidden in this seed.
# ---------------------------------------------------------------------------

def node_has(node_type, var, predicate):
    return Exists(NodesOfType(node_type), var, predicate)


def action_open(action):
    return node_has("HostActionRequest", "request", And(
        Eq(A("request", "action"), L(action)),
        Or(
            Eq(A("request", "status"), L("pending")),
            Eq(A("request", "status"), L("requested")),
            Eq(A("request", "status"), L("running")),
        ),
    ))


def source_not_previously_requested(action):
    """A source is serviced once; renewed demand is represented by a new node."""
    return Not(node_has("HostActionRequest", "prior", And(
        Eq(A("prior", "action"), L(action)),
        Eq(A("prior", "source"), V("source")),
    )))


def host_action_effects(action, source_type, selected):
    return [
        ["add_node", "request", "HostActionRequest", {
            "action": action,
            "source_type": source_type,
            "source": {"__term__": selected},
            "status": "pending",
            "urgency": 1,
            "residual": 1,
            "estimated_cost": 1,
            "deadline": 0,
            "priority": 1,
        }],
        ["add_node", "task", "CognitiveTask", {
            "kind": "host_action",
            "action": action,
            "area": "supervision",
            "status": "pending",
            "urgency": 1,
            "residual": 1,
            "estimated_cost": 1,
            "deadline": 0,
            "priority": 1,
            "input_epoch": 0,
            "logical_time": 0,
        }],
        ["add_edge", "request", "scheduled_as", "task", {}],
    ]


def host_action_rule(name, action, source_type, source_predicate):
    eligible = And(source_predicate, source_not_previously_requested(action))
    candidates = Filter(NodesOfType(source_type), "source", eligible)

    def source_coordinate(node_var, key, default, *, positive=True):
        attr = A(node_var, key)
        return IfThenElse(Gt(attr, L(0 if positive else -1)), attr, L(default))

    # A learned supervisory rule may write this integer value from urgency,
    # residual, cost, deadline, and evidence. Legacy demand facts share the
    # neutral value, keeping this bridge compact and non-prescriptive.
    candidate_priority = source_coordinate("candidate", "supervision_priority", 1)
    selected = Argmax(
        candidates, "candidate", candidate_priority, None)
    return {
        "name": name,
        "area": "supervision",
        "order": 1,
        # A demand fact is an external/supervisory event boundary.  The bridge
        # must remain observable even when System 1 has no reason to escalate;
        # selection still happens in the graph below.
        "latency_class": "hard_realtime",
        "match": [],
        "where": And(
            node_has(source_type, "source", eligible),
            # Backpressure is per action class. Heterogeneous demands coexist
            # so the generic graph priority rule, not bridge/rule order,
            # decides which one the host receives next.
            Not(action_open(action)),
        ),
        "effects": host_action_effects(action, source_type, selected),
    }


def host_action_rearm_rule(name, action, source_type, source_predicate):
    """A completed request is the concrete binding that rearms its action class.

    The empty-match bridge supplies the first request. Empty bindings fire only
    once, so every later request must be driven by a completed request/task
    pair. This makes supervision recurrent without a host cadence or counter.
    """
    eligible = And(source_predicate, source_not_previously_requested(action))
    candidates = Filter(NodesOfType(source_type), "source", eligible)
    selected = Argmax(
        candidates, "candidate",
        IfThenElse(Gt(A("candidate", "supervision_priority"), L(0)),
                   A("candidate", "supervision_priority"), L(1)),
        None)
    return {
        "name": name + "_rearm",
        "area": "supervision",
        "order": 1,
        "latency_class": "hard_realtime",
        "match": [["previous", "scheduled_as", "previous_task"]],
        "where": And(
            Eq(A("previous", "action"), L(action)),
            Or(Eq(A("previous", "status"), L("done")),
               Eq(A("previous", "status"), L("failed")),
               Eq(A("previous", "status"), L("unavailable"))),
            node_has(source_type, "source", eligible),
            Not(action_open(action)),
        ),
        "effects": host_action_effects(action, source_type, selected),
    }


HOST_ACTION_SPECS = [
    # Existing graph-native request objects are the demand facts.  The host
    # does not inspect them to choose a service: it only receives the action
    # label that this supervisory policy selected.
    (
        "supervise_dispatch_requested_experiment", "dispatch", "Experiment",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_fetch_requested_document", "fetch", "FetchRequest",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_search_requested_topic", "search", "SearchRequest",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_detail_requested_topic", "detail", "DetailRequest",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_browse_requested_url", "browse", "BrowseRequest",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_imagine_requested_impasse", "imagine", "ImagineRequest",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_correct_ready_divergence", "self_correct", "Impasse",
        And(Eq(A("source", "kind"), L("predicted_divergence")),
            Gt(A("source", "correct_ready"), L(0)))),
    (
        "supervise_pending_concern", "concern", "StandingConcern",
        Eq(A("source", "status"), L("pending"))),
    (
        "supervise_ready_experiment_close", "close", "Experiment",
        And(Gt(A("source", "conclusion_ready"), L(0)),
            Not(Eq(A("source", "taught"), L(1))))),
    (
        "supervise_requested_steering", "steer", "SelfConcern",
        And(Eq(A("source", "status"), L("noted")),
            Gt(A("source", "promote_requested"), L(0)))),
    (
        "supervise_queued_study", "study", "StudyLesson",
        Eq(A("source", "status"), L("queued"))),
    # Teacher work is supplied by the teacher slice.  Keeping its demand fact
    # here makes it a normal part of the same supervisor rather than a second
    # daemon loop.
    (
        "supervise_requested_teacher", "teacher", "TeacherRequest",
        Eq(A("source", "status"), L("requested"))),
    (
        "supervise_requested_embodied_trial", "embodied_trial",
        "EmbodiedExternalTrialRequest",
        Eq(A("source", "status"), L("requested"))),
]

HOST_ACTION_RULES = [host_action_rule(*spec) for spec in HOST_ACTION_SPECS]
HOST_ACTION_RULES.extend(host_action_rearm_rule(*spec) for spec in HOST_ACTION_SPECS)

RULES.extend(HOST_ACTION_RULES)

SOURCE_OF_REQUEST = {"type": "Attr", "node": V("request"), "key": "source"}
SOURCE_PRIORITY = {"type": "Attr", "node": SOURCE_OF_REQUEST,
                   "key": "supervision_priority"}

RULES.append({
    "name": "supervise_copy_graph_source_priority",
    "area": "supervision",
    "order": 1,
    "latency_class": "hard_realtime",
    "match": [["request", "scheduled_as", "task"]],
    # Direct/manual HostActionRequests have no source node and retain their
    # explicitly supplied priority. Legacy bridge requests change only when a
    # graph-resident supervisory rule has supplied a positive integer score.
    "where": And(
        Gt(SOURCE_PRIORITY, L(0)),
        Not(Eq(A("request", "priority"), SOURCE_PRIORITY)),
    ),
    "effects": [
        set_if("request", "priority", SOURCE_PRIORITY, True),
        set_if("task", "priority", SOURCE_PRIORITY, True),
    ],
})

PENDING_HOST_ACTIONS = Filter(
    NodesOfType("HostActionRequest"), "candidate",
    Eq(A("candidate", "status"), L("pending")))
def request_is_selected(request_var):
    """Maximum priority, with graph identity as the symmetry breaker.

    Identity is insertion order, not a policy score: it only decides between
    otherwise indistinguishable pending demands.  Expressing selection as
    dominance avoids comparing an Argmax's restored scalar NodeID encoding to
    a bound NodeID after checkpoint reload.
    """
    return Not(node_has("HostActionRequest", "other", And(
        Eq(A("other", "status"), L("pending")),
        Or(
            Gt(A("other", "priority"), A(request_var, "priority")),
            And(Eq(A("other", "priority"), A(request_var, "priority")),
                Lt(V("other"), V(request_var))),
        ),
    )))

# Fast path for the overwhelmingly common one-option case.  Apart from being
# cheaper than arbitration, this gives a newly-installed scheduler rule a
# concrete way to release a lone request restored from an older checkpoint;
# no ordering choice exists to make.  Multiple options still go through the
# Argmax rule below.
RULES.append({
    "name": "supervise_release_only_pending_host_action",
    "area": "supervision",
    "order": 1,
    "latency_class": "hard_realtime",
    "match": [["request", "scheduled_as", "task"]],
    "where": And(
        Eq(A("request", "status"), L("pending")),
        Eq(A("task", "status"), L("pending")),
        Gt(A("request", "priority"), L(0)),
        Eq(Count(PENDING_HOST_ACTIONS), L(1)),
        Not(node_has("HostActionRequest", "active",
                     Or(Eq(A("active", "status"), L("requested")),
                        Eq(A("active", "status"), L("running"))))),
    ),
    "effects": [
        set_if("request", "status", "requested"),
        set_if("task", "status", "host_requested"),
    ],
})

RULES.append({
    # Version the activation identity: restored checkpoints may carry the
    # retired rule's fired-binding cache even though seed reconciliation has
    # installed new bridge requests.  A new identity makes post-upgrade work
    # eligible without putting cadence or host policy back into the daemon.
    "name": "supervise_release_positive_value_host_action_v3",
    "area": "supervision",
    "order": 1,
    "latency_class": "hard_realtime",
    "match": [["request", "scheduled_as", "task"]],
    "where": And(
        Eq(A("request", "status"), L("pending")),
        Eq(A("task", "status"), L("pending")),
        Gt(A("request", "priority"), L(0)),
        Not(node_has("HostActionRequest", "active",
                     Or(Eq(A("active", "status"), L("requested")),
                        Eq(A("active", "status"), L("running"))))),
        request_is_selected("request"),
    ),
    "effects": [
        set_if("request", "status", "requested"),
        set_if("task", "status", "host_requested"),
    ],
})

# A HostActionReceipt is the external completion EVENT.  Matching it gives
# the scheduler a fresh binding after an active request settles, so a pending
# request that was previously inhibited by backpressure is reconsidered.  A
# rule matched only on the pending request can otherwise have seen that
# binding while the predecessor was still active and have no new structural
# event on which to wake.
RULES.append({
    "name": "supervise_release_after_host_receipt_v2",
    "area": "supervision",
    "order": 1,
    "latency_class": "hard_realtime",
    "match": [["previous", "has_receipt", "receipt"],
              ["request", "scheduled_as", "task"]],
    "where": And(
        Or(Eq(A("receipt", "status"), L("done")),
           Eq(A("receipt", "status"), L("failed")),
           Eq(A("receipt", "status"), L("unavailable"))),
        Eq(A("request", "status"), L("pending")),
        Eq(A("task", "status"), L("pending")),
        Gt(A("request", "priority"), L(0)),
        Not(node_has("HostActionRequest", "active",
                     Or(Eq(A("active", "status"), L("requested")),
                        Eq(A("active", "status"), L("running"))))),
        request_is_selected("request"),
    ),
    "effects": [
        set_if("request", "status", "requested"),
        set_if("task", "status", "host_requested"),
    ],
})

MANIFEST = {
    "id": "cognitive_scheduler",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["cognitive_areas"],
    "area": "scheduler",
    "description": (
        "Graph-native policy for asynchronous cognition: dependency readiness, "
        "epoch rearm, salience-driven effort, backpressure worker feedback, "
        "graph-visible shedding, bounded residual projection, and graph-selected "
        "host-action supervision."
    ),
    "microtheory": {
        "name": "cognitive_scheduler",
        "description": "surprise/effort/backpressure policy over native CognitiveTasks",
    },
    "nodes": [],
    "edges": [],
    "productions": [
        {
            "provenance": "seed:cognitive_scheduler:area-residual",
            "src": {"type": "CognitiveArea", "var": "area"},
            "edge_type": "has_residual",
            "tgt": {"type": "Residual", "var": "residual"},
        },
        {
            "provenance": "seed:cognitive_scheduler:area-surprise",
            "src": {"type": "CognitiveArea", "var": "area"},
            "edge_type": "surprised_by",
            "tgt": {"type": "Residual", "var": "residual"},
        },
        {
            "provenance": "seed:cognitive_scheduler:host-action-task",
            "src": {"type": "HostActionRequest", "var": "request"},
            "edge_type": "scheduled_as",
            "tgt": {"type": "CognitiveTask", "var": "task"},
        },
        {
            "provenance": "seed:cognitive_scheduler:host-action-receipt",
            "src": {"type": "HostActionRequest", "var": "request"},
            "edge_type": "has_receipt",
            "tgt": {"type": "HostActionReceipt", "var": "receipt"},
        },
    ],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
    print(f"wrote {OUT} with {len(RULES)} rules")
