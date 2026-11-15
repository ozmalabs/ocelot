import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.ocelot_research_service import ResearchService


def test_cross_root_claim_evidence_and_stale_source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    path = root / "evidence.md"
    path.write_text("# Residual\nAn arbitrary residual remains.\n", encoding="utf-8")
    svc = ResearchService(tmp_path)
    state = svc.call("init", {"question": "Is residual eliminated?", "roots": [{"root_id": "ge", "path": str(root), "files": ["evidence.md"]}]})
    sid = state["investigation_id"]
    context = svc.call("context", {"session_id": sid, "query": "arbitrary residual"})
    locator = context["results"][0]["citation"]
    src = svc.call("record", {"session_id": sid, "kind": "Source", "fields": {"locator": locator}})
    claim = svc.call("record", {"session_id": sid, "kind": "Claim", "fields": {"wording": "Residual disappears", "scope": "arbitrary CNF", "claim_type": "hypothesis", "author": "researcher", "status": "open"}})
    svc.call("link", {"session_id": sid, "src": src["id"], "relation": "opposes", "tgt": claim["id"]})
    assert svc.call("inspect", {"session_id": sid, "node_id": claim["id"]})["edges"][0]["type"] == "opposes"
    assert svc.call("check", {"session_id": sid})["citations"][0]["status"] == "current"
    path.write_text("# Residual\nChanged.\n", encoding="utf-8")
    result = ResearchService(tmp_path).call("export", {"session_id": sid})
    assert result["checks"]["citations"][0]["status"] == "stale"
    assert "Residual disappears" in result["markdown"]
    assert result["checks"]["truth_assessed"] is False


def test_mcp_newline_fresh_process(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "research_init", "arguments": {"question": "Why?"}}},
    ]
    env = dict(os.environ, PYTHONPATH=str(repo))
    proc = subprocess.run([sys.executable, "-m", "scripts.ocelot_research_mcp", "--workspace", str(tmp_path)], input="".join(json.dumps(m) + "\n" for m in messages), text=True, capture_output=True, cwd=repo, env=env, check=True)
    replies = [json.loads(line) for line in proc.stdout.splitlines()]
    assert replies[0]["result"]["serverInfo"]["name"] == "ocelot-research"
    result = replies[1]["result"]
    assert not result["isError"]
    sid = json.loads(result["content"][0]["text"])["investigation_id"]
    assert ResearchService(tmp_path).call("inspect", {"session_id": sid})["nodes"][0]["wording"] == "Why?"


def test_manual_receipt_and_late_prereg_cannot_be_confirmatory(tmp_path):
    svc = ResearchService(tmp_path)
    sid = svc.call("init", {"question": "test", "mode": "confirmatory"})["investigation_id"]
    protocol = {"hypothesis": "two sided", "two_sided": True, "readout": "score", "sample_size_justification": "power", "independent_unit": "run", "seed_allocation": "fresh", "controls": ["positive"], "decision_rule": "rule", "fixed_analysis": "analysis", "revision": "abc", "immutable": True, "recorded_at": "2000-01-01T00:00:00Z"}
    svc.call("record", {"session_id": sid, "kind": "Protocol", "fields": protocol})
    svc.call("record", {"session_id": sid, "kind": "Run", "fields": {"protocol_revision": "abc", "started_at": "2001-01-01T00:00:00Z", "receipt_status": "captured", "controls": {"positive": "pass"}, "exit_status": 0}})
    check = svc.call("check", {"session_id": sid})["workflow"]
    assert not check["confirmatory_eligible"]
    assert any("not recorded before" in b for b in check["blockers"])
    assert any("unverified" in b for b in check["blockers"])


def test_mcp_content_length_framing(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
    data = b'Content-Length: ' + str(len(msg)).encode() + b'\r\n\r\n' + msg
    result = subprocess.run([sys.executable, '-m', 'scripts.ocelot_research_mcp', '--workspace', str(tmp_path)], input=data, capture_output=True, cwd=repo, check=True)
    header, body = result.stdout.split(b'\r\n\r\n', 1)
    assert int(header.split(b':')[1]) == len(body)
    assert any(t['name'] == 'research_export' for t in json.loads(body)['result']['tools'])


def test_provenance_adapters_are_explicit_and_respect_manifest(tmp_path, monkeypatch):
    import scripts.ocelot_research_service as service
    root = tmp_path / 'sources'
    root.mkdir()
    (root / 'prereg.md').write_text('prereg', encoding='utf-8')
    monkeypatch.setattr(service, 'verify_prereg_git', lambda root, rev, path: {'status': 'inspected', 'commit_oid': rev, 'path': path})
    monkeypatch.setattr(service, 'verify_prereg', lambda path, repo_root: {'status': 'inspected', 'seed_claim': {'status': 'stale_or_conflict'}})
    monkeypatch.setattr(service, 'verify_engine_provenance', lambda stamp: {'status': 'unverified', 'matches_recorded': False})
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'test', 'mode': 'confirmatory', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['prereg.md']}]})['investigation_id']
    svc.call('record', {'session_id': sid, 'kind': 'Protocol', 'fields': {'revision': 'r1', 'prereg_git': {'root_id': 'r', 'path': 'prereg.md', 'commit_oid': 'abc'}, 'check_seed_claim': True}})
    svc.call('record', {'session_id': sid, 'kind': 'Run', 'fields': {'protocol_revision': 'r1', 'uses_ocelot': True, 'engine_stamp': {'sha256': 'x'}}})
    check = svc.call('check', {'session_id': sid})
    assert check['provenance']['seed_claim']['seed_claim']['status'] == 'stale_or_conflict'
    assert check['provenance']['engine']['status'] == 'unverified'
    assert not check['workflow']['confirmatory_eligible']


def test_native_three_step_research_chain_and_lean_export(tmp_path):
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'compute a chain'})['investigation_id']
    def rec(term, bindings=None):
        return svc.call('record', {'session_id': sid, 'kind': 'Claim', 'fields': {'wording': 'explicit computation', 'term': term, 'bindings': bindings or {}}})
    def link(src, dep):
        svc.call('link', {'session_id': sid, 'src': src['id'], 'relation': 'derived_from', 'tgt': dep['id']})
    first = rec({'type': 'Var', 'name': 'x'})
    second = rec({'type': 'Not', 'arg': {'type': 'EvalSubgraph', 'node': {'type': 'Var', 'name': 'first'}}}, {'first': first['id']})
    link(second, first)
    third = rec({'type': 'And', 'items': [{'type': 'EvalSubgraph', 'node': {'type': 'Var', 'name': 'second'}}, {'type': 'Lit', 'value': True}]}, {'second': second['id']})
    link(third, second)
    trace = svc.call('trace', {'session_id': sid, 'node_id': third['id']})
    assert set(n['id'] for n in trace['nodes']) == {first['id'], second['id'], third['id']}
    result = svc.call('execute', {'session_id': sid, 'node_id': third['id'], 'env': {'x': False}})
    assert result['value'] is True
    assert result['truth_assessed'] is False
    assert result['engine_provenance']['source_match'] in {'own', 'shared'}
    lean = svc.call('export_lean', {'session_id': sid, 'node_id': third['id']})
    assert lean['kernel_checked'] is False
    assert 'Bool' in lean['lean'] and first['id'] in lean['lean'] and third['id'] in lean['lean']


def test_lean_cli_outputs_source_and_mcp_exposes_execution(tmp_path):
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'simple term'})['investigation_id']
    claim = svc.call('record', {'session_id': sid, 'kind': 'Claim', 'fields': {'term': {'type': 'Lit', 'value': True}}})
    repo = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, '-m', 'scripts.ocelot_research_service', 'export_lean', '--workspace', str(tmp_path), '--args', json.dumps({'session_id': sid, 'node_id': claim['id']}), '--lean']
    output = subprocess.run(cmd, text=True, capture_output=True, cwd=repo, check=True).stdout
    assert output.startswith('-- Generated')
    assert ': Bool := true' in output
    from scripts.ocelot_research_mcp import ResearchServer
    server = ResearchServer(svc)
    response = server.handle({'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call', 'params': {'name': 'research_execute', 'arguments': {'session_id': sid, 'node_id': claim['id']}}})
    assert not response['result']['isError']
    assert json.loads(response['result']['content'][0]['text'])['value'] is True


def test_paper_to_claim_to_native_model_and_lean(tmp_path):
    root = tmp_path / 'paper_source'
    root.mkdir()
    (root / 'sample.tex').write_text(r'\begin{theorem}\label{t:one} For every Boolean x, x is either true or false.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'read and model', 'roots': [{'root_id': 'paper', 'path': str(root), 'files': ['sample.tex']}]})['investigation_id']
    args = {'session_id': sid, 'root_id': 'paper', 'path': 'sample.tex'}
    preview = svc.call('paper_preview', args)
    assert len(preview['records']) == 1
    assert len(svc.call('inspect', {'session_id': sid})['nodes']) == 1
    imported = svc.call('paper_ingest', args)
    claim = imported['claims'][0]
    assert claim['semantics_verified'] is False
    projection = svc.call('native_graph', {'session_id': sid})
    assert claim['id'] in projection['node_id_map']
    assert any(n['type'] == 'Claim' for n in projection['graph']['nodes'])
    assert projection['engine_provenance']['source_match'] in {'own', 'shared'}
    candidate = svc.call('model_candidate', {'session_id': sid, 'claim_id': claim['id'], 'term': {'type': 'Or', 'items': [{'type': 'Var', 'name': 'x'}, {'type': 'Not', 'arg': {'type': 'Var', 'name': 'x'}}]}, 'residuals': ['The source-to-Term mapping requires review.'], 'reviewer': 'test researcher', 'review_note': 'Explicit Boolean interpretation, not proof of the paper.'})
    node = candidate['candidate']['id']
    assert candidate['truth_assessed'] is False
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'x': False}})['value'] is True
    assert svc.call('export_lean', {'session_id': sid, 'node_id': node})['kernel_checked'] is False
    assert svc.call('paper_ingest', args)['duplicate'] is True


def test_formula_from_paper_translates_to_executable_candidate(tmp_path):
    root = tmp_path / 'papers'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{prop} For Boolean p, $p \lor \neg p$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'model formula', 'roots': [{'root_id': 'paper', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'paper', 'path': 'case.tex'})['claims'][0]
    result = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': r'p \lor \neg p', 'reviewer': 'researcher', 'review_note': 'Assume p has Boolean domain.'})
    assert result['found_verbatim_in_claim']
    assert result['translation']['variables'] == ('p',)
    model_id = result['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': model_id, 'env': {'p': True}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': model_id, 'env': {'p': False}})['value'] is True
    assert svc.call('export_lean', {'session_id': sid, 'node_id': model_id})['kernel_checked'] is False


def test_formula_models_check_runtime_sorts(tmp_path):
    import pytest
    from scripts.ocelot_research import ResearchError
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} The expression $x + 1 = 2$ is an example.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'formula', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    model = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': 'x + 1 = 2', 'reviewer': 'researcher', 'review_note': 'Integer interpretation.'})
    node = model['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'x': 1}})['value'] is True
    with pytest.raises(ResearchError, match='numeric'):
        svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'x': True}})
    with pytest.raises(ResearchError, match='missing'):
        svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {}})


def test_unsupported_formula_reports_residual_without_recording(tmp_path):
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'formula'})['investigation_id']
    before = svc.call('inspect', {'session_id': sid})
    result = svc.call('formula_translate', {'session_id': sid, 'formula': r'\sin{x}'})
    assert result['status'] == 'unsupported'
    assert result['residuals']
    assert svc.call('inspect', {'session_id': sid}) == before


def test_formula_chain_validates_dependency_inputs(tmp_path):
    import pytest
    from scripts.ocelot_research import ResearchError
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} Consider $x + 1$ and $v = 2$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'chain', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    common = {'session_id': sid, 'claim_id': claim['id'], 'reviewer': 'researcher', 'review_note': 'Integer interpretation.'}
    first = svc.call('formula_model', {**common, 'formula': 'x + 1'})['candidate']['id']
    second = svc.call('formula_model', {**common, 'formula': 'v = 2', 'bindings': {'v': first}})['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': second, 'env': {'x': 1}})['value'] is True
    with pytest.raises(ResearchError, match='numeric'):
        svc.call('execute', {'session_id': sid, 'node_id': second, 'env': {'x': True}})


def test_finite_quantifier_paper_model_executes_on_named_domain(tmp_path):
    import pytest
    from scripts.ocelot_research import ResearchError
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} A finite check: $forall(x, D, x >= 0)$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'finite test', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    candidate = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': 'forall(x, D, x >= 0)', 'reviewer': 'researcher', 'review_note': 'Only over the supplied finite domain.'})
    assert candidate['translation']['domains'] == ('D',)
    node = candidate['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'D': [0, 1, 2]}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'D': [0, -1, 2]}})['value'] is False
    with pytest.raises(ResearchError, match='domain'):
        svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'D': [0, True]}})


def test_extended_formula_execution_refuses_undefined_and_overflow(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} Examples: $x/y > 1$, $x^2 > 1$, $x * 1e308 > 0$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'safe numeric', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    common = {'session_id': sid, 'claim_id': claim['id'], 'reviewer': 'researcher', 'review_note': 'Native numeric interpretation.'}
    div = svc.call('formula_model', {**common, 'formula': 'x/y > 1'})['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': div, 'env': {'x': 4, 'y': 2}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': div, 'env': {'x': 4, 'y': 0}})['status'] == 'unresolved'
    power = svc.call('formula_model', {**common, 'formula': 'x^2 > 1'})['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': power, 'env': {'x': 2**62}})['status'] == 'unresolved'
    real = svc.call('formula_model', {**common, 'formula': 'x * 1e308 > 0'})['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': real, 'env': {'x': 2.0}})['status'] == 'unresolved'


def test_formula_equality_checks_bound_and_external_sort(tmp_path):
    import pytest
    from scripts.ocelot_research import ResearchError
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} Consider $p$ and $a = b$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'bound sorts', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    common = {'session_id': sid, 'claim_id': claim['id'], 'reviewer': 'researcher', 'review_note': 'Explicit candidate.'}
    first = svc.call('formula_model', {**common, 'formula': 'p or False'})['candidate']['id']
    second = svc.call('formula_model', {**common, 'formula': 'a = b', 'bindings': {'a': first}})['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': second, 'env': {'p': True, 'b': True}})['value'] is True
    with pytest.raises(ResearchError, match='compatible sorts'):
        svc.call('execute', {'session_id': sid, 'node_id': second, 'env': {'p': True, 'b': 1}})


def test_unconstrained_equality_respects_declared_same_sort(tmp_path):
    import pytest
    from scripts.ocelot_research import ResearchError
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} Consider $a = b$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'equality', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    result = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': 'a = b', 'reviewer': 'researcher', 'review_note': 'Explicit equality model.'})
    with pytest.raises(ResearchError, match='compatible sorts'):
        svc.call('execute', {'session_id': sid, 'node_id': result['candidate']['id'], 'env': {'a': 1, 'b': 1.0}})


def test_translated_abs_minimum_is_unresolved(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} Consider $abs(x)$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'absolute value', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    model = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': 'abs(x)', 'reviewer': 'researcher', 'review_note': 'Native numeric interpretation.'})['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': model, 'env': {'x': -(2**63)}})['status'] == 'unresolved'


def test_lean_check_compiles_generated_definitions_when_installed(tmp_path):
    import pytest
    repo = Path(__file__).resolve().parents[1]
    if not (repo / 'var/tools/lean/lean-4.33.1-linux/bin/lean').is_file():
        pytest.skip('project-local Lean is not installed')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'Lean check'})['investigation_id']
    node = svc.call('record', {'session_id': sid, 'kind': 'Claim', 'fields': {'term': {'type': 'Gte', 'a': {'type': 'Plus', 'items': [{'type': 'Lit', 'value': 2}, {'type': 'Lit', 'value': 3}]}, 'b': {'type': 'Lit', 'value': 1}}}})
    result = svc.call('check_lean', {'session_id': sid, 'node_id': node['id']})
    assert result['status'] == 'accepted', result['stdout'] + result['stderr']
    assert result['kernel_checked'] is True
    assert '4.33.1' in result['lean_version']


def test_unicode_finite_arithmetic_checks_domain_overflow(tmp_path):
    import pytest
    from scripts.ocelot_research import ResearchError
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text('\\begin{theorem} Consider $∀ x ∈ D: (x + 1 > x)$.\\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'finite formula', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    model = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': '∀ x ∈ D: (x + 1 > x)', 'reviewer': 'researcher', 'review_note': 'Finite integer domain only.'})
    assert model['translation']['domains'] == ('D',)
    node = model['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'D': [0, 1, 2]}})['value'] is True
    with pytest.raises(ResearchError, match='overflow'):
        svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'D': [2**63 - 1]}})


def test_lean_check_compiles_parameterized_integer_chain_when_installed(tmp_path):
    import pytest
    repo = Path(__file__).resolve().parents[1]
    if not (repo / 'var/tools/lean/lean-4.33.1-linux/bin/lean').is_file():
        pytest.skip('project-local Lean is not installed')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'Lean chain'})['investigation_id']
    leaf = svc.call('record', {'session_id': sid, 'kind': 'Claim', 'fields': {'term': {'type': 'Plus', 'items': [{'type': 'Var', 'name': 'n'}, {'type': 'Lit', 'value': 1}]}}})
    root = svc.call('record', {'session_id': sid, 'kind': 'Claim', 'fields': {'term': {'type': 'Gt', 'a': {'type': 'EvalSubgraph', 'node': {'type': 'Var', 'name': 'prev'}}, 'b': {'type': 'Lit', 'value': 0}}, 'bindings': {'prev': leaf['id']}}})
    svc.call('link', {'session_id': sid, 'src': root['id'], 'relation': 'derived_from', 'tgt': leaf['id']})
    result = svc.call('check_lean', {'session_id': sid, 'node_id': root['id']})
    assert result['status'] == 'accepted', result['stdout'] + result['stderr']


def test_real_shape_finite_membership_to_native_and_lean(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    formula = r'\epsilon,\mu\in\{0,1\}'
    (root / 'case.tex').write_text(r'\begin{theorem}\label{t} Consider $' + formula + r'$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'membership', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['claims'][0]
    result = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': formula, 'reviewer': 'researcher', 'review_note': 'Finite integer set.'})
    assert result['found_verbatim_in_claim']
    node = result['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'epsilon': 1, 'mu': 0}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'epsilon': 2, 'mu': 0}})['value'] is False
    assert svc.call('export_lean', {'session_id': sid, 'node_id': node})['kernel_checked'] is False


def test_model_directly_from_sourced_displayed_formula_candidate(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    formula = r'\epsilon,\mu\in\{0,1\}'
    (root / 'case.tex').write_text('A finite example.\n\\[' + formula + '\\]\n', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'model display', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    imported = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})
    evidence = imported['formula_evidence'][0]
    model = svc.call('formula_model', {'session_id': sid, 'claim_id': evidence['id'], 'formula': formula, 'reviewer': 'researcher', 'review_note': 'Integer membership.'})
    assert model['found_verbatim_in_claim']
    node = model['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'epsilon': 0, 'mu': 1}})['value'] is True
    import shutil
    repo = Path(__file__).resolve().parents[1]
    if (repo / 'var/tools/lean/lean-4.33.1-linux/bin/lean').is_file() or shutil.which('lean'):
        assert svc.call('check_lean', {'session_id': sid, 'node_id': node})['status'] == 'accepted'


def test_source_symbol_labels_execute_as_explicit_opaque_values(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    f = r'x = \mathrm{NULL}'
    (root / 'case.tex').write_text(r'\begin{theorem} Consider $' + f + r'$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'symbols', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    claim = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex', 'max_formula_candidates': 0})['claims'][0]
    result = svc.call('formula_model', {'session_id': sid, 'claim_id': claim['id'], 'formula': f, 'reviewer': 'researcher', 'review_note': 'Interpret NULL as an opaque symbol.'})
    assert result['translation']['variable_sorts']['x'] == 'symbol'
    node = result['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'x': 'NULL'}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'x': 'OTHER'}})['value'] is False


def test_service_paginates_paper_formula_candidates(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text('First $x=1$ then $x=2$ then $x=3$.\n', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'pages', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    common = {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'}
    first = svc.call('paper_ingest', {**common, 'max_formula_candidates': 1})
    assert first['formula_has_more']
    assert first['formula_next_offset'] == 1
    second = svc.call('paper_ingest', {**common, 'formula_offset': 1, 'max_formula_candidates': 1})
    assert second['formula_evidence'][0]['wording'] == 'x=2'
    assert first['formula_evidence'][0]['id'] != second['formula_evidence'][0]['id']


def test_service_natural_membership_requires_explicit_domain(tmp_path):
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'naturals'})['investigation_id']
    args = {'session_id': sid, 'formula': r'm,n\in\NN'}
    assert svc.call('formula_translate', args)['status'] == 'unsupported'
    out = svc.call('formula_translate', {**args, 'domain_assumptions': {'natural_minimum': 0}})
    assert out['status'] == 'translated'
    assert any('i64' in r for r in out['residuals'])


def test_sourced_implicit_product_requires_explicit_mapping(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    formula = 'E_0=mc^2'
    (root / 'case.tex').write_text('Example $' + formula + '$.', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'product', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    evidence = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['formula_evidence'][0]
    result = svc.call('formula_model', {'session_id': sid, 'claim_id': evidence['id'], 'formula': formula, 'reviewer': 'researcher', 'review_note': 'Explicit product interpretation.', 'domain_assumptions': {'implicit_products': {'mc': ['m', 'c']}}})
    assert any('caller' in residual for residual in result['translation']['residuals'])
    node = result['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'E_0': 18, 'm': 2, 'c': 3}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'E_0': 36, 'm': 2, 'c': 3}})['value'] is False
    import shutil
    repo = Path(__file__).resolve().parents[1]
    if (repo / 'var/tools/lean/lean-4.33.1-linux/bin/lean').is_file() or shutil.which('lean'):
        assert svc.call('check_lean', {'session_id': sid, 'node_id': node})['status'] == 'accepted'


def test_scoped_graph_context_selects_and_traces_executable_product(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    formula = 'E_0=mc^2'
    (root / 'case.tex').write_text('The equation is $' + formula + '$.', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'context', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    evidence = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})['formula_evidence'][0]
    frame = svc.call('record', {'session_id': sid, 'kind': 'Frame', 'fields': {'wording': 'paper scope'}})
    def link(src, relation, tgt):
        svc.call('link', {'session_id': sid, 'src': src, 'relation': relation, 'tgt': tgt})
    link(evidence['id'], 'scoped_by', frame['id'])
    symbol_ids = []
    for name in ('m', 'c'):
        symbol = svc.call('record', {'session_id': sid, 'kind': 'MathematicalSymbol', 'fields': {'name': name, 'arity': 0, 'sort': 'number'}})
        symbol_ids.append(symbol['id'])
        link(symbol['id'], 'scoped_by', frame['id'])
    common = {'session_id': sid, 'claim_id': evidence['id'], 'formula': formula, 'context_scope_id': frame['id'], 'reviewer': 'researcher', 'review_note': 'Compare notation with scoped paper symbols.'}
    result = svc.call('formula_model', common)
    assert 'context_resolution' in result, result
    assert result['context_resolution']['implicit_products'] == {'mc': ['m', 'c']}
    node = result['candidate']['id']
    assert svc.call('execute', {'session_id': sid, 'node_id': node, 'env': {'E_0': 18, 'm': 2, 'c': 3}})['value'] is True
    trace = svc.call('trace', {'session_id': sid, 'node_id': node})
    assert set(symbol_ids).issubset({n['id'] for n in trace['nodes']})
    conflict = svc.call('record', {'session_id': sid, 'kind': 'MathematicalSymbol', 'fields': {'name': 'mc', 'arity': 0, 'sort': 'number'}})
    link(conflict['id'], 'scoped_by', frame['id'])
    before = len(svc.call('inspect', {'session_id': sid})['nodes'])
    tied = svc.call('formula_model', common)
    assert tied['status'] == 'unresolved_context'
    assert len(svc.call('inspect', {'session_id': sid})['nodes']) == before


def test_paper_macro_context_models_naturals_with_explicit_convention(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    formula = r'm,n\in\NN'
    (root / 'case.tex').write_text('\\newcommand\\NN{\\mathbb{N}}\nLater $' + formula + '$.\n', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'source context', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    imported = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})
    evidence = next(e for e in imported['formula_evidence'] if e['wording'] == formula)
    scope = next(e['tgt'] for e in svc.call('inspect', {'session_id': sid})['edges'] if e['type'] == 'scoped_by' and e['src'] == evidence['id'])
    common = {'session_id': sid, 'claim_id': evidence['id'], 'formula': formula, 'context_scope_id': scope, 'reviewer': 'researcher', 'review_note': 'Use the sourced macro declaration.'}
    missing = svc.call('formula_model', common)
    assert missing['status'] == 'unsupported'
    model = svc.call('formula_model', {**common, 'domain_assumptions': {'natural_minimum': 0}})
    macro = model['context_resolution']['applied_macro_expansion']['symbol_id']
    assert svc.call('execute', {'session_id': sid, 'node_id': model['candidate']['id'], 'env': {'m': 0, 'n': 2}})['value'] is True
    assert svc.call('execute', {'session_id': sid, 'node_id': model['candidate']['id'], 'env': {'m': -1, 'n': 2}})['value'] is False
    trace = svc.call('trace', {'session_id': sid, 'node_id': model['candidate']['id']})
    assert macro in {n['id'] for n in trace['nodes']}


def test_source_declared_symbols_select_product_in_same_statement(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    (root / 'case.tex').write_text(r'\begin{theorem}Let $m,c$ be real numbers. Then $E=mc^2$.\end{theorem}', encoding='utf-8')
    svc = ResearchService(tmp_path)
    sid = svc.call('init', {'question': 'local source context', 'roots': [{'root_id': 'r', 'path': str(root), 'files': ['case.tex']}]})['investigation_id']
    imported = svc.call('paper_ingest', {'session_id': sid, 'root_id': 'r', 'path': 'case.tex'})
    evidence = next(e for e in imported['formula_evidence'] if e['wording'] == 'E=mc^2')
    state = svc.call('inspect', {'session_id': sid})
    scope = next(e['tgt'] for e in state['edges'] if e['type'] == 'scoped_by' and e['src'] == evidence['id'])
    result = svc.call('formula_model', {'session_id': sid, 'claim_id': evidence['id'], 'formula': 'E=mc^2', 'context_scope_id': scope, 'reviewer': 'researcher', 'review_note': 'Use the declaration in the same theorem.'})
    assert result['context_resolution']['implicit_products'] == {'mc': ['m', 'c']}
    assert svc.call('execute', {'session_id': sid, 'node_id': result['candidate']['id'], 'env': {'E': 18, 'm': 2, 'c': 3}})['value'] is True
    trace = svc.call('trace', {'session_id': sid, 'node_id': result['candidate']['id']})
    assert any(n['type'] == 'MathematicalDefinition' for n in trace['nodes'])


def test_formula_parse_candidates_is_explicit_optional_and_nonrecording(tmp_path, monkeypatch):
    from scripts import ocelot_formula_sympy
    calls = []

    def unavailable(formula):
        calls.append(formula)
        return {"adapter": "sympy_lark", "status": "unavailable",
                "verified": False, "is_claim": False, "reason": "test absence"}

    monkeypatch.setattr(ocelot_formula_sympy, "sympy_lark_candidate", unavailable)
    svc = ResearchService(tmp_path)
    sid = svc.call("init", {"question": "optional parse"})["investigation_id"]
    before = svc.call("inspect", {"session_id": sid})
    translated = svc.call("formula_translate", {"session_id": sid, "formula": "x + 1 = 2"})
    assert translated["status"] == "translated"
    assert calls == []

    result = svc.call("formula_parse_candidates", {
        "session_id": sid, "formulas": ["x^2 + 1", "\\frac{a}{b}"]})
    assert result["status"] == "candidate_parses"
    assert result["truth_assessed"] is False and result["recorded"] is False
    assert [candidate["status"] for candidate in result["candidates"]] == ["unavailable"] * 2
    assert calls == ["x^2 + 1", "\\frac{a}{b}"]
    assert svc.call("inspect", {"session_id": sid}) == before


def test_formula_parse_candidates_mcp_schema_and_invocation(tmp_path, monkeypatch):
    from scripts import ocelot_formula_sympy
    from scripts.ocelot_research_mcp import ResearchServer

    monkeypatch.setattr(ocelot_formula_sympy, "sympy_lark_candidate", lambda formula: {
        "adapter": "sympy_lark", "status": "unavailable", "verified": False,
        "is_claim": False, "reason": "optional dependency absent"})
    svc = ResearchService(tmp_path)
    sid = svc.call("init", {"question": "MCP parser"})["investigation_id"]
    server = ResearchServer(svc)
    listing = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tool = next(t for t in listing["result"]["tools"] if t["name"] == "research_formula_parse_candidates")
    assert tool["inputSchema"]["required"] == ["session_id", "formulas"]
    assert tool["inputSchema"]["properties"]["formulas"]["maxItems"] == 256
    reply = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "research_formula_parse_candidates",
        "arguments": {"session_id": sid, "formulas": ["x^2"]}}})
    assert not reply["result"]["isError"]
    body = json.loads(reply["result"]["content"][0]["text"])
    assert body["candidates"][0]["status"] == "unavailable"
