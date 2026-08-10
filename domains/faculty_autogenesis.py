"""Mechanical world-adapter rim for graph-native faculty autogenesis."""
from __future__ import annotations

import json

from domains import prog_synthesis


def pump(agent) -> None:
    """Translate requested FacultyNeed evidence into synthesis I/O, then pump.

    Status transitions, acceptance, installation, escalation, and retry are
    graph rules.  This function only serializes already-selected graph facts.
    """
    sub = agent.s
    native = agent.inner
    prog_synthesis.ensure_program_synthesis(sub, native, agent.agent)
    # Let graph rules publish any newly perceived need before the adapter
    # serializes requested evidence. This is the ordinary ingest boundary:
    # graph decides/request -> adapter translates -> graph synthesizes.
    native.run_rules(400000)
    for need in tuple(sub.nodes("FacultyNeed")):
        attrs = sub.node(need)["attrs"]
        if attrs.get("status") != "requested":
            continue
        examples = []
        for example in native.neighbours(need, "has_faculty_example"):
            example_attrs = sub.node(example)["attrs"]
            examples.append((
                json.loads(str(example_attrs["inputs_json"])),
                example_attrs["expected"],
            ))
        message = prog_synthesis.ingest_spec(
            sub,
            agent.agent,
            str(attrs["request"]),
            examples,
            name=str(attrs["program_name"]),
        )
        native.add_edge_unchecked(
            need, "has_faculty_synthesis_message", message
        )
        native.set_attr(need, "status", "synthesizing")
    prog_synthesis.pump(sub, agent.agent)
