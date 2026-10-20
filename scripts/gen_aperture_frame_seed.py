"""Emit `seeds/aperture_frame.json` — APERTURE IS A FRAME (with P2.C4 graded relax & questioning trigger).

Supports:
- `build_seed(graded_relax=False, questioning_trigger=False)`: byte-identical to
  the v1.1.0 pre-P2.C4 `seeds/aperture_frame.json`.
- `build_seed()` (default, v1.2.0):
  (a) P2.C4.3: `af_relax_chosen` checks residual magnitude
      `Max(Count(pv.ap_residual), Sum(rel in pv.ap_residual, Count(cell == "·"))) >= obs.ap_relax_tolerance`
      (where `obs.ap_relax_tolerance` defaults to `1`).
  (b) P2.C4.4: Non-residual questioning trigger (`af_count_chosen_dwell`,
      `af_probe_project_held`, `af_probe_project_percept`,
      `af_question_drop_hiding_frame`, `af_question_keep_honest_frame`) that probes
      at `ap_probe_resolves` (bypassing `chose_aperture` while still honouring
      `forced_aperture` and `agreed_aperture`) after `obs.ap_question_after`
      (default `1.0`) generations with a chosen frame whose framed residual did not
      trigger `af_relax_chosen`. If the probe view's residual is larger than the
      framed view's residual, `af_question_drop_hiding_frame` drops `chose_aperture`
      and files no `SelfConcern`.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "aperture_frame.json"
UNRESOLVED = "·"

COMMENT = (
    "Emit seeds/aperture_frame.json -- APERTURE IS A FRAME: chosen, forced, or negotiated.\n\n"
    "`observer_aperture` made aperture graph data, but as a single authored list on the\n"
    "observer -- an acuity it simply HAS. That is incomplete. An aperture is a FRAME\n"
    "you are viewing in, and a frame has provenance: you can choose it, it can be\n"
    "forced on you, or you can negotiate it with someone else.\n\n"
    "This is the reference-frame sense, not the Fillmore `Frame` (which is language\n"
    "semantics and is left alone). And it is not a metaphor here: `CLAUDE.md`'s\n"
    "frame/continuum invariant puts every lossy or real-valued map in\n"
    "`Hom(frame, frame)` rather than inside a frame's coordinates, and the projection\n"
    "`observer_aperture` performs IS such a map -- world frame to observer frame, with\n"
    "the collapse marker naming exactly what the map discards.\n\n"
    "Two things follow, and the second is the whole point.\n\n"
    "**The effective aperture is a MEET.** Every frame in force narrows what you\n"
    "resolve, so `resolves` stops being authored and becomes derived: the fold of\n"
    "`Intersect` over your own maximum acuity and every frame currently on you. An\n"
    "observer declares its PHYSIOLOGY (`ap_full`); the frames decide the rest.\n\n"
    "**The three modes decode identically and differ entirely in RECOURSE.** This is\n"
    "the testable content -- same residual, three different things you may do about it:\n\n"
    "  * CHOSEN -- you narrowed your own attention, so you may widen it unilaterally.\n"
    "    An outstanding residual is a reason to look harder, and `ap_relax_chosen`\n"
    "    drops the frame and re-arms the decode. Attention, mechanically.\n"
    "  * FORCED -- someone or something else narrowed it, and you cannot lift it. An\n"
    "    outstanding residual here is a gap you can DETECT and cannot close alone, so\n"
    "    it opens a `SelfConcern` on the existing human-gated spine. This is the\n"
    "    knowing-THAT-without-knowing-WHAT case from `ONE_LOOP_MANY_GRAINS.md`, one\n"
    "    level up: not merely unresolved, but unresolvable BY YOU.\n"
    "  * NEGOTIATED -- it binds several parties, so no one may change it alone. A\n"
    "    proposal takes effect only when every bound party has accepted; a unilateral\n"
    "    accept does nothing at all.\n\n"
    "An agent that can only be forced has no attention; one that can only choose has\n"
    "no social constraint; one that cannot negotiate cannot establish common ground.\n"
)


def V(name: str) -> dict:
    return {"type": "Var", "name": name}


def L(value) -> dict:
    return {"type": "Lit", "value": value}


def A(node_var: str, key: str) -> dict:
    return {"type": "Attr", "node": V(node_var), "key": key}


def T(term: dict) -> dict:
    return {"__term__": term}


def _all_frames_union(obs_var: str = "obs") -> dict:
    return {
        "type": "Union",
        "a": {
            "type": "Union",
            "a": {"type": "Neighbours", "node": V(obs_var), "edge_type": "chose_aperture"},
            "b": {"type": "Neighbours", "node": V(obs_var), "edge_type": "forced_aperture"},
        },
        "b": {"type": "Neighbours", "node": V(obs_var), "edge_type": "agreed_aperture"},
    }


def _non_chosen_frames_union(obs_var: str = "obs") -> dict:
    """Frames the observer CANNOT unilaterally drop (`forced_aperture` ∪ `agreed_aperture`)."""
    return {
        "type": "Union",
        "a": {"type": "Neighbours", "node": V(obs_var), "edge_type": "forced_aperture"},
        "b": {"type": "Neighbours", "node": V(obs_var), "edge_type": "agreed_aperture"},
    }


def _probe_resolves(obs_var: str = "obs") -> dict:
    """The observer's effective aperture when chosen frames are bypassed."""
    return {
        "type": "Fold",
        "source": _non_chosen_frames_union(obs_var),
        "var_name": "fr",
        "acc_name": "acc",
        "init": A(obs_var, "ap_full"),
        "body": {
            "type": "Intersect",
            "a": V("acc"),
            "b": A("fr", "resolves"),
        },
    }


def _project_signature(sh_var: str, resolves_term: dict) -> dict:
    """Project `sh.signature` onto the dimensions in `resolves_term`."""
    return {
        "type": "MapList",
        "source": A(sh_var, "signature"),
        "var_name": "rel",
        "value": {
            "type": "ZipWith",
            "a": V("rel"),
            "b": A(sh_var, "dim_types"),
            "a_name": "slot",
            "b_name": "dt",
            "value": {
                "type": "IfThenElse",
                "cond": {
                    "type": "In",
                    "member": V("dt"),
                    "container": resolves_term,
                },
                "then": V("slot"),
                "other": L(UNRESOLVED),
            },
        },
    }


def _relax_tolerance(obs_var: str = "obs") -> dict:
    return {
        "type": "IfThenElse",
        "cond": {"type": "Eq", "a": A(obs_var, "ap_relax_tolerance"), "b": L(None)},
        "then": L(1),
        "other": A(obs_var, "ap_relax_tolerance"),
    }


def _question_after(obs_var: str = "obs") -> dict:
    return {
        "type": "IfThenElse",
        "cond": {"type": "Eq", "a": A(obs_var, "ap_question_after"), "b": L(None)},
        "then": L(1.0),
        "other": A(obs_var, "ap_question_after"),
    }


def _chosen_dwell(obs_var: str = "obs") -> dict:
    return {
        "type": "IfThenElse",
        "cond": {"type": "Eq", "a": A(obs_var, "ap_chosen_dwell"), "b": L(None)},
        "then": L(0.0),
        "other": A(obs_var, "ap_chosen_dwell"),
    }


def _residual_magnitude(pv_var: str = "pv") -> dict:
    """Magnitude of `pv.ap_residual`: max of relation count and count of collapsed `'·'` cells."""
    return {
        "type": "Max",
        "items": [
            {"type": "Count", "source": A(pv_var, "ap_residual")},
            {
                "type": "Sum",
                "source": A(pv_var, "ap_residual"),
                "var_name": "rel",
                "value": {
                    "type": "Count",
                    "source": {
                        "type": "FilterList",
                        "source": V("rel"),
                        "var_name": "cell",
                        "predicate": {"type": "Eq", "a": V("cell"), "b": L(UNRESOLVED)},
                    },
                },
            },
        ],
    }


def _current_probe_parts(obs_var: str = "obs") -> dict:
    return {
        "type": "FilterList",
        "source": {"type": "Neighbours", "node": V(obs_var), "edge_type": "probe_projected_part"},
        "var_name": "q",
        "predicate": {"type": "Eq", "a": A("q", "ap_gen"), "b": A(obs_var, "ap_gen")},
    }


def _current_probe_scope(obs_var: str = "obs") -> dict:
    return {
        "type": "MapList",
        "source": _current_probe_parts(obs_var),
        "var_name": "q",
        "value": A("q", "name"),
    }


def build_seed(*, graded_relax: bool = True, questioning_trigger: bool = True) -> dict:
    productions = [
        {
            "provenance": "seed:aperture_frame:max",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "holds_aperture_max",
            "tgt": {"type": "ApertureConfig", "var": "cfg"},
        },
        {
            "provenance": "seed:aperture_frame:chose",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "chose_aperture",
            "tgt": {"type": "Aperture", "var": "ap"},
        },
        {
            "provenance": "seed:aperture_frame:forced",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "forced_aperture",
            "tgt": {"type": "Aperture", "var": "ap"},
        },
        {
            "provenance": "seed:aperture_frame:agreed",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "agreed_aperture",
            "tgt": {"type": "Aperture", "var": "ap"},
        },
        {
            "provenance": "seed:aperture_frame:offers",
            "src": {"type": "ApertureProposal", "var": "p"},
            "edge_type": "offers",
            "tgt": {"type": "Aperture", "var": "ap"},
        },
        {
            "provenance": "seed:aperture_frame:binds",
            "src": {"type": "ApertureProposal", "var": "p"},
            "edge_type": "binds",
            "tgt": {"type": "Observer", "var": "obs"},
        },
        {
            "provenance": "seed:aperture_frame:retracts",
            "src": {"type": "ApertureRetraction", "var": "r"},
            "edge_type": "retracts",
            "tgt": {"type": "Aperture", "var": "ap"},
        },
        {
            "provenance": "seed:aperture_frame:retraction-binds",
            "src": {"type": "ApertureRetraction", "var": "r"},
            "edge_type": "binds",
            "tgt": {"type": "Observer", "var": "obs"},
        },
        {
            "provenance": "seed:aperture_frame:accepts-retraction",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "accepts_retraction",
            "tgt": {"type": "ApertureRetraction", "var": "r"},
        },
        {
            "provenance": "seed:aperture_frame:accepts",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "accepts",
            "tgt": {"type": "ApertureProposal", "var": "p"},
        },
        {
            "provenance": "seed:aperture_frame:concern",
            "src": {"type": "Observer", "var": "obs"},
            "edge_type": "has_self_concern",
            "tgt": {"type": "SelfConcern", "var": "sc"},
        },
    ]

    if questioning_trigger:
        productions.extend(
            [
                {
                    "provenance": "seed:aperture_frame:probe-projected-part",
                    "src": {"type": "Observer", "var": "obs"},
                    "edge_type": "probe_projected_part",
                    "tgt": {"type": "ObservedShape", "var": "pp"},
                },
                {
                    "provenance": "seed:aperture_frame:probe-projected",
                    "src": {"type": "Observer", "var": "obs"},
                    "edge_type": "probe_projected",
                    "tgt": {"type": "ObservedShape", "var": "qv"},
                },
            ]
        )

    relax_where: dict = {
        "type": "And",
        "items": [
            {"type": "Eq", "a": A("pv", "ap_gen"), "b": A("obs", "ap_gen")},
            A("pv", "ap_residual"),
        ],
    }
    if graded_relax:
        relax_where = {
            "type": "And",
            "items": [
                {"type": "Eq", "a": A("pv", "ap_gen"), "b": A("obs", "ap_gen")},
                A("pv", "ap_residual"),
                {
                    "type": "Gte",
                    "a": _residual_magnitude("pv"),
                    "b": _relax_tolerance("obs"),
                },
            ],
        }

    rules = [
        {
            "name": "af_effective_aperture",
            "comment": (
                "The effective aperture is the MEET of the observer's own maximum acuity and "
                "every frame in force on it, whatever the provenance. `resolves` is therefore "
                "DERIVED, not authored: an observer declares its physiology (`ap_full`) and "
                "the frames decide the rest. Re-arms on any change in how many frames are in "
                "force -- which is what makes dropping a chosen frame actually widen perception."
            ),
            "match": [["obs", "holds_aperture_max", "cfg"]],
            "where": {
                "type": "Not",
                "arg": {
                    "type": "Eq",
                    "a": {"type": "Count", "source": _all_frames_union("obs")},
                    "b": A("obs", "af_n"),
                },
            },
            "effects": [
                [
                    "set_attr",
                    "obs",
                    "resolves",
                    T(
                        {
                            "type": "Fold",
                            "source": _all_frames_union("obs"),
                            "var_name": "fr",
                            "acc_name": "acc",
                            "init": A("obs", "ap_full"),
                            "body": {
                                "type": "Intersect",
                                "a": V("acc"),
                                "b": A("fr", "resolves"),
                            },
                        }
                    ),
                ],
                [
                    "set_attr",
                    "obs",
                    "af_n",
                    T({"type": "Count", "source": _all_frames_union("obs")}),
                ],
                [
                    "set_attr",
                    "obs",
                    "ap_gen",
                    T({"type": "Plus", "items": [A("obs", "ap_gen"), L(1.0)]}),
                ],
            ],
        },
        {
            "name": "af_relax_chosen",
            "comment": (
                "CHOSEN recourse. You narrowed your own attention, so an outstanding residual "
                "is a reason to widen it -- and you may, unilaterally. Dropping the frame "
                "re-arms `af_effective_aperture`, which re-arms the decode. Attention as a "
                "graph move rather than a parameter."
            ),
            "match": [
                ["obs", "chose_aperture", "ap"],
                ["obs", "projected", "pv"],
            ],
            "where": relax_where,
            "effects": [["del_edge", "obs", "chose_aperture", "ap"]],
        },
        {
            "name": "af_forced_residual_is_a_concern",
            "comment": (
                "FORCED recourse -- there is none, and that is the point. The residual is "
                "identical to the chosen case; what differs is that the observer cannot lift "
                "the frame. So it files what it CAN do: record that something here is "
                "unresolved and not resolvable by it alone. Knowing THAT without knowing WHAT, "
                "one level up -- and it lands on the existing human-gated spine (promote -> "
                "StandingConcern -> experiment), so another party can act on it."
            ),
            "match": [
                ["obs", "forced_aperture", "ap"],
                ["obs", "projected", "pv"],
            ],
            "where": {
                "type": "And",
                "items": [
                    {
                        "type": "And",
                        "items": [
                            {"type": "Eq", "a": A("pv", "ap_gen"), "b": A("obs", "ap_gen")},
                            A("pv", "ap_residual"),
                        ],
                    },
                    {
                        "type": "Not",
                        "arg": {
                            "type": "Exists",
                            "source": {
                                "type": "Neighbours",
                                "node": V("obs"),
                                "edge_type": "has_self_concern",
                            },
                            "var_name": "c",
                            "predicate": {
                                "type": "Eq",
                                "a": A("c", "content"),
                                "b": A("ap", "name"),
                            },
                        },
                    },
                ],
            },
            "effects": [
                [
                    "add_node",
                    "sc",
                    "SelfConcern",
                    {
                        "status": "noted",
                        "source": "forced_aperture",
                        "kind": "capability_gap",
                        "content": T(A("ap", "name")),
                    },
                ],
                ["add_edge", "obs", "has_self_concern", "sc"],
            ],
        },
        {
            "name": "af_adopt_when_every_party_accepts",
            "comment": (
                "NEGOTIATED recourse. The frame binds several parties, so no one may change it "
                "alone: the offered aperture attaches only once every bound party has "
                "accepted. A unilateral accept does nothing -- which is the whole difference "
                "from `chose_aperture`, and the reason common ground is not the same operation "
                "as attention."
            ),
            "match": [
                ["p", "binds", "obs"],
                ["p", "offers", "ap"],
            ],
            "where": {
                "type": "And",
                "items": [
                    {
                        "type": "Gte",
                        "a": {
                            "type": "Count",
                            "source": {
                                "type": "InNeighbours",
                                "node": V("p"),
                                "edge_type": "accepts",
                            },
                        },
                        "b": {
                            "type": "Count",
                            "source": {
                                "type": "Neighbours",
                                "node": V("p"),
                                "edge_type": "binds",
                            },
                        },
                    },
                    {
                        "type": "Not",
                        "arg": {
                            "type": "Exists",
                            "source": {
                                "type": "Neighbours",
                                "node": V("obs"),
                                "edge_type": "agreed_aperture",
                            },
                            "var_name": "a",
                            "predicate": {"type": "Eq", "a": V("a"), "b": V("ap")},
                        },
                    },
                ],
            },
            "effects": [["add_edge", "obs", "agreed_aperture", "ap"]],
        },
        {
            "name": "af_retract_when_every_party_accepts",
            "comment": (
                "RENEGOTIATION -- the only way out of a negotiated frame, and the exact mirror "
                "of adoption: it comes off when every bound party accepts that it should, and "
                "not before. A frame one party could drop alone would just be a chosen frame "
                "with extra steps, which is why `af_relax_chosen` deliberately never touches "
                "this edge.\n\nRecorded because it was not designed: this rule was missing "
                "until APERTURE_PATHOLOGIES.md asked what the SECOND intervention on a shared "
                "blind spot would be. The rule the machinery lacked turned out to be the "
                "treatment the mechanism implies. Dropping the edge re-arms "
                "`af_effective_aperture` (the frame count changes), which bumps the "
                "generation, which invalidates every view taken through the retracted frame "
                "-- so perception genuinely widens rather than the edge merely disappearing."
            ),
            "match": [
                ["r", "binds", "obs"],
                ["r", "retracts", "ap"],
                ["obs", "agreed_aperture", "ap"],
            ],
            "where": {
                "type": "Gte",
                "a": {
                    "type": "Count",
                    "source": {
                        "type": "InNeighbours",
                        "node": V("r"),
                        "edge_type": "accepts_retraction",
                    },
                },
                "b": {
                    "type": "Count",
                    "source": {
                        "type": "Neighbours",
                        "node": V("r"),
                        "edge_type": "binds",
                    },
                },
            },
            "effects": [["del_edge", "obs", "agreed_aperture", "ap"]],
        },
    ]

    if questioning_trigger:
        dwell_ready_cond = {
            "type": "And",
            "items": [
                {"type": "Gte", "a": _chosen_dwell("obs"), "b": _question_after("obs")},
                {
                    "type": "Not",
                    "arg": {"type": "Eq", "a": A("obs", "ap_questioned_gen"), "b": A("obs", "ap_gen")},
                },
            ],
        }
        rules.extend(
            [
                {
                    "name": "af_count_chosen_dwell",
                    "comment": (
                        "P2.C4.4 questioning counter: when a chosen frame is in force and the "
                        "current generation's percept has been decoded without triggering "
                        "`af_relax_chosen` (residual magnitude below `ap_relax_tolerance`), "
                        "increment `obs.ap_chosen_dwell` once for this generation."
                    ),
                    "match": [
                        ["obs", "chose_aperture", "ap"],
                        ["obs", "projected", "pv"],
                    ],
                    "where": {
                        "type": "And",
                        "items": [
                            {"type": "Eq", "a": A("pv", "ap_gen"), "b": A("obs", "ap_gen")},
                            {"type": "Eq", "a": A("pv", "ap_seen"), "b": A("obs", "ap_scope_n")},
                            {"type": "Gt", "a": A("obs", "ap_scope_n"), "b": L(0.0)},
                            {
                                "type": "Lt",
                                "a": _residual_magnitude("pv"),
                                "b": _relax_tolerance("obs"),
                            },
                            {
                                "type": "Not",
                                "arg": {
                                    "type": "Eq",
                                    "a": A("obs", "ap_last_dwell_gen"),
                                    "b": A("obs", "ap_gen"),
                                },
                            },
                        ],
                    },
                    "effects": [
                        [
                            "set_attr",
                            "obs",
                            "ap_chosen_dwell",
                            T({"type": "Plus", "items": [_chosen_dwell("obs"), L(1.0)]}),
                        ],
                        ["set_attr", "obs", "ap_last_dwell_gen", T(A("obs", "ap_gen"))],
                    ],
                },
                {
                    "name": "af_probe_project_held",
                    "comment": (
                        "P2.C4.4 probe codebook projection: once `ap_chosen_dwell >= ap_question_after`, "
                        "project each held part through `ap_probe_resolves` (bypassing `chose_aperture` "
                        "while still honouring `forced_aperture` and `agreed_aperture`)."
                    ),
                    "match": [
                        ["obs", "chose_aperture", "ap"],
                        ["obs", "holds_part", "sh"],
                    ],
                    "where": {
                        "type": "And",
                        "items": [
                            dwell_ready_cond,
                            {
                                "type": "Not",
                                "arg": {
                                    "type": "Exists",
                                    "source": {
                                        "type": "Neighbours",
                                        "node": V("obs"),
                                        "edge_type": "probe_projected_part",
                                    },
                                    "var_name": "p",
                                    "predicate": {
                                        "type": "And",
                                        "items": [
                                            {"type": "Eq", "a": A("p", "of_name"), "b": A("sh", "name")},
                                            {"type": "Eq", "a": A("p", "ap_gen"), "b": A("obs", "ap_gen")},
                                        ],
                                    },
                                },
                            },
                        ],
                    },
                    "effects": [
                        [
                            "add_node",
                            "pp",
                            "ObservedShape",
                            {
                                "ap_gen": T(A("obs", "ap_gen")),
                                "name": T(
                                    {
                                        "type": "StringConcat",
                                        "parts": [
                                            A("obs", "name"),
                                            L("/probe/"),
                                            {"type": "ToJsonString", "value": A("obs", "ap_gen")},
                                            L("/"),
                                            A("sh", "name"),
                                        ],
                                    }
                                ),
                                "of_name": T(A("sh", "name")),
                                "observer": T(A("obs", "name")),
                                "kind": "probe_held",
                                "signature": T(_project_signature("sh", _probe_resolves("obs"))),
                            },
                        ],
                        ["add_edge", "obs", "probe_projected_part", "pp"],
                    ],
                },
                {
                    "name": "af_probe_project_percept",
                    "comment": (
                        "P2.C4.4 probe percept projection & decode: once all held parts are "
                        "probe-projected for the current generation, project the percept through "
                        "`ap_probe_resolves` and decode its residual against the probe codebook."
                    ),
                    "match": [
                        ["obs", "chose_aperture", "ap"],
                        ["obs", "perceives", "sh"],
                    ],
                    "where": {
                        "type": "And",
                        "items": [
                            dwell_ready_cond,
                            {
                                "type": "Eq",
                                "a": {"type": "Count", "source": _current_probe_parts("obs")},
                                "b": {
                                    "type": "Count",
                                    "source": {
                                        "type": "Neighbours",
                                        "node": V("obs"),
                                        "edge_type": "holds_part",
                                    },
                                },
                            },
                            {
                                "type": "Not",
                                "arg": {
                                    "type": "Exists",
                                    "source": {
                                        "type": "Neighbours",
                                        "node": V("obs"),
                                        "edge_type": "probe_projected",
                                    },
                                    "var_name": "q",
                                    "predicate": {
                                        "type": "And",
                                        "items": [
                                            {"type": "Eq", "a": A("q", "of_name"), "b": A("sh", "name")},
                                            {"type": "Eq", "a": A("q", "ap_gen"), "b": A("obs", "ap_gen")},
                                        ],
                                    },
                                },
                            },
                        ],
                    },
                    "effects": [
                        [
                            "add_node",
                            "qv",
                            "ObservedShape",
                            {
                                "ap_gen": T(A("obs", "ap_gen")),
                                "of_name": T(A("sh", "name")),
                                "observer": T(A("obs", "name")),
                                "kind": "probe_percept",
                                "signature": T(_project_signature("sh", _probe_resolves("obs"))),
                                "ap_residual": T(
                                    {
                                        "type": "ShapeDecode",
                                        "goal": _project_signature("sh", _probe_resolves("obs")),
                                        "codebook_type": "ObservedShape",
                                        "codebook_scope": _current_probe_scope("obs"),
                                        "field": "residual",
                                        "wild_objects": False,
                                    }
                                ),
                            },
                        ],
                        ["add_edge", "obs", "probe_projected", "qv"],
                    ],
                },
                {
                    "name": "af_question_drop_hiding_frame",
                    "comment": (
                        "P2.C4.4 questioning verdict (drop): if the probe view (bypassing chosen "
                        "frames) reveals a larger residual than the framed view, the chosen frame "
                        "is hiding an unresolved distinction (`APERTURE_PATHOLOGIES.md` §1). Drop "
                        "`chose_aperture` unilaterally and file no `SelfConcern`."
                    ),
                    "match": [
                        ["obs", "chose_aperture", "ap"],
                        ["obs", "projected", "pv"],
                        ["obs", "probe_projected", "qv"],
                    ],
                    "where": {
                        "type": "And",
                        "items": [
                            {"type": "Eq", "a": A("pv", "ap_gen"), "b": A("obs", "ap_gen")},
                            {"type": "Eq", "a": A("qv", "ap_gen"), "b": A("obs", "ap_gen")},
                            {"type": "Eq", "a": A("pv", "of_name"), "b": A("qv", "of_name")},
                            {"type": "Eq", "a": A("pv", "ap_seen"), "b": A("obs", "ap_scope_n")},
                            {
                                "type": "Gt",
                                "a": {"type": "Count", "source": A("qv", "ap_residual")},
                                "b": {"type": "Count", "source": A("pv", "ap_residual")},
                            },
                        ],
                    },
                    "effects": [
                        ["del_edge", "obs", "chose_aperture", "ap"],
                        ["set_attr", "obs", "ap_chosen_dwell", T(L(0.0))],
                        ["set_attr", "obs", "ap_questioned_gen", T(A("obs", "ap_gen"))],
                    ],
                },
                {
                    "name": "af_question_keep_honest_frame",
                    "comment": (
                        "P2.C4.4 questioning verdict (keep): if the probe view's residual is no "
                        "larger than the framed view's residual, the chosen frame is not hiding "
                        "an unresolved distinction; keep the frame and reset `ap_chosen_dwell`."
                    ),
                    "match": [
                        ["obs", "chose_aperture", "ap"],
                        ["obs", "projected", "pv"],
                        ["obs", "probe_projected", "qv"],
                    ],
                    "where": {
                        "type": "And",
                        "items": [
                            {"type": "Eq", "a": A("pv", "ap_gen"), "b": A("obs", "ap_gen")},
                            {"type": "Eq", "a": A("qv", "ap_gen"), "b": A("obs", "ap_gen")},
                            {"type": "Eq", "a": A("pv", "of_name"), "b": A("qv", "of_name")},
                            {"type": "Eq", "a": A("pv", "ap_seen"), "b": A("obs", "ap_scope_n")},
                            {
                                "type": "Not",
                                "arg": {
                                    "type": "Eq",
                                    "a": A("obs", "ap_questioned_gen"),
                                    "b": A("obs", "ap_gen"),
                                },
                            },
                            {
                                "type": "Lte",
                                "a": {"type": "Count", "source": A("qv", "ap_residual")},
                                "b": {"type": "Count", "source": A("pv", "ap_residual")},
                            },
                        ],
                    },
                    "effects": [
                        ["set_attr", "obs", "ap_chosen_dwell", T(L(0.0))],
                        ["set_attr", "obs", "ap_questioned_gen", T(A("obs", "ap_gen"))],
                    ],
                },
            ]
        )

    return {
        "id": "aperture_frame",
        "version": "1.2.0" if (graded_relax or questioning_trigger) else "1.1.0",
        "comment": COMMENT,
        "depends_on": ["observer_aperture"],
        "productions": productions,
        "rules": rules,
    }


def main() -> None:
    seed = build_seed()
    OUT.write_text(json.dumps(seed, indent=2) + "\n")
    print(f"wrote {OUT} ({len(seed['rules'])} rules)")


if __name__ == "__main__":
    main()
