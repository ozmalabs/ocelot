"""P13.03 graph-native learning from repeated, verified solved traces."""

from evaluation.process_mastery.harness import Agent


def _agent(enabled=True):
    agent = Agent(track_i=False, extra_seeds=("library_learning",))
    agent.s.set_attr(agent.nodes("LibraryLearningPolicy")[0], "enabled", 1.0 if enabled else 0.0)
    receipt = agent.s.add_node("SleepStageReceipt", {
        "stage": "library", "status": "deferred", "model_epoch": 0,
        "probe_epoch": 0,
    })
    agent.s.add_edge(agent.ag, "has_sleep_stage_receipt", receipt, {})
    return agent, receipt


def _repeated_solved_traces(agent):
    # Eight real process schemas solve a nine-cycle in eight improving steps.
    domain = agent.s.add_node("ProcessDomain", {
        "name": "trace-domain", "kind": "permutation", "probes": [list(range(9))],
        "probe_epoch": 0, "model_epoch": 0, "source_epoch": 0, "frame_epoch": 0,
    })
    agent.s.add_edge(agent.ag, "has_process_domain", domain, {})
    steps = []
    for index in range(8):
        params = list(range(9))
        params[index], params[8] = params[8], params[index]
        schema = agent.s.add_node("ProcessSchema", {
            "kind": "permutation", "domain": "trace-domain", "domain_kind": "permutation",
            "name": f"swap-{index}", "params": params, "cost": 1.0,
            "provenance": "held", "status": "active", "owner_agent": agent.ag,
            "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0,
        })
        agent.s.add_edge(agent.ag, "has_process_schema", schema, {})
        steps.append(schema)
    tasks = []
    for _ in range(2):
        task = agent.s.add_node("SolveTask", {
            "domain": "trace-domain", "initial_state": [1, 2, 3, 4, 5, 6, 7, 8, 0],
            "state": [0, 1, 2, 3, 4, 5, 6, 7, 8], "goal": [0, 1, 2, 3, 4, 5, 6, 7, 8],
            "status": "solved", "steps": 8, "moves": 8.0, "trace": steps,
        })
        agent.s.add_edge(agent.ag, "has_solve_task", task, {})
        agent.s.add_edge(task, "about_domain", domain, {})
        tasks.append(task)
    return domain, tasks, steps


def _learn(agent):
    # Focus on the native production rules; no Python strategy or rewrite.
    for _ in range(3):
        if not agent.native.run_rules(10_000):
            break


def test_shared_chunk_lowers_total_cost():
    agent, receipt = _agent()
    _domain, _tasks, _steps = _repeated_solved_traces(agent)
    _learn(agent)
    chunks = agent.nodes("ProcessLibraryChunk")
    assert len(chunks) == 1
    attrs = agent.attrs(chunks[0])
    assert attrs["inline_cost"] == 16
    assert attrs["library_cost"] == 15
    assert attrs["definition_cost"] == 8
    assert attrs["reference_cost"] == 2
    assert attrs["decoder_cost"] == attrs["exception_cost"] == 1
    assert attrs["dispatch_cost"] == attrs["retrieval_cost"] == attrs["validation_cost"] == 1
    assert attrs["cost_savings"] == 1
    assert agent.attrs(receipt)["status"] == "completed"


def test_rewritten_trace_same_effect():
    agent, _receipt = _agent()
    domain, tasks, source_steps = _repeated_solved_traces(agent)
    source_traces = [list(agent.attrs(task)["trace"]) for task in tasks]
    _learn(agent)
    chunk = agent.nodes("ProcessLibraryChunk")[0]
    executable = agent.s.neighbours(chunk, "has_library_process")[0]
    assert agent.attrs(chunk)["equivalence_witness"] == "native_process_repair_verify_on_both_source_tasks"
    assert tuple(agent.attrs(chunk)["rewritten_trace"]) == (executable,)
    assert [list(agent.attrs(task)["trace"]) for task in tasks] == source_traces
    assert all(tuple(agent.attrs(task)["compressed_trace"]) == (executable,) for task in tasks)
    assert all(agent.attrs(task)["compression_witness"] == chunk for task in tasks)
    assert agent.attrs(executable)["verification_receipt"] == "native_process_repair_verify_on_both_source_tasks"
    assert agent.attrs(executable)["domain"] == agent.attrs(domain)["name"]
    assert len(source_steps) == 8
    # Recheck the executable library process on a distinct state after growth.
    fresh = [2, 3, 4, 5, 6, 7, 8, 0, 1]
    result = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": agent.attrs(executable)["params"], "state": fresh},
    )
    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 0]


def test_failure_evidence_preserved():
    agent, _receipt = _agent()
    _domain, _tasks, steps = _repeated_solved_traces(agent)
    failed = agent.s.add_node("SolveTask", {
        "domain": "trace-domain", "status": "stuck", "initial_state": [8, 7, 6, 5, 4, 3, 2, 1, 0],
        "state": [8, 7, 6, 5, 4, 3, 2, 1, 0], "goal": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "steps": 1, "trace": steps,
    })
    agent.s.add_edge(agent.ag, "has_solve_task", failed, {})
    before = dict(agent.attrs(failed))
    _learn(agent)
    assert agent.attrs(failed) == before
    assert failed not in [source for chunk in agent.nodes("ProcessLibraryChunk")
                          for source in agent.s.neighbours(chunk, "has_source_task")]


def test_later_unseen_task_reuses_chunk():
    agent, _receipt = _agent()
    domain, _tasks, _steps = _repeated_solved_traces(agent)
    _learn(agent)
    executable = next(schema for schema in agent.schemas("trace-domain")
                      if agent.attrs(schema).get("provenance") == "library_learned")
    agent.s.set_attr(agent.nodes("SolverPolicy")[0], "enabled", 1.0)
    unseen = agent.s.add_node("SolveTask", {
        "domain": "trace-domain", "initial_state": [2, 3, 4, 5, 6, 7, 8, 0, 1],
        "state": [2, 3, 4, 5, 6, 7, 8, 0, 1], "goal": [1, 2, 3, 4, 5, 6, 7, 8, 0],
        "status": "active", "steps": 0, "moves": 0.0, "trace": [],
    })
    agent.s.add_edge(agent.ag, "has_solve_task", unseen, {})
    agent.s.add_edge(unseen, "about_domain", domain, {})
    _learn(agent)
    assert agent.attrs(unseen)["status"] == "solved"
    assert tuple(agent.attrs(unseen)["trace"]) == (executable,)
    assert agent.attrs(unseen)["steps"] == 1
    assert agent.attrs(executable)["domain"] == agent.attrs(domain)["name"]


def test_default_off_and_empty_stage_are_explicit():
    agent, receipt = _agent(enabled=False)
    assert agent.attrs(agent.nodes("LibraryLearningPolicy")[0])["enabled"] == 0.0
    _learn(agent)
    assert not agent.nodes("ProcessLibraryChunk")
    assert agent.attrs(receipt)["status"] == "deferred"

    enabled, empty_receipt = _agent(enabled=True)
    _learn(enabled)
    assert not enabled.nodes("ProcessLibraryChunk")
    assert enabled.attrs(empty_receipt)["status"] == "completed"
    assert enabled.attrs(empty_receipt)["completion_reason"] == "no_eligible_cost_positive_sequence_within_bound"
