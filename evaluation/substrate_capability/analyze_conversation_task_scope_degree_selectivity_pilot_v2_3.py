#!/usr/bin/env python3
"""Independent analysis for degree-skew and partial-decoy matcher stress."""
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_3_lock_20261004.json'
CAP = ROOT / 'evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_3_20261004.json.gz'
OUT = ROOT / 'evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_3_analysis_20261004.json'
POLICIES = ('ascending', 'descending', 'outside_in')
BASE_CELLS = (('common_ground_stress', None), ('concurrent_goals', 2), ('concurrent_goals', 4), ('concurrent_goals', 8))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    errors = []
    def req(ok, msg):
        if not ok:
            errors.append(msg)
    lock = json.loads(LOCK.read_text())['locked_inputs']
    with gzip.open(CAP, 'rt', encoding='utf-8') as f:
        cap = json.load(f)
    req(cap.get('locked_inputs') == lock == cap.get('post_run_inputs'), 'source-lock drift')
    req(cap.get('checks', {}).get('nine_fresh_workers') is True, 'nine-worker runner gate failed')
    req(cap.get('checks', {}).get('source_stable') is True, 'runner source-stability gate failed')
    runs = cap.get('runs', [])
    req(len(runs) == 9 and len({r['pid'] for r in runs}) == 9, 'fresh worker coverage mismatch')
    rows = []
    candidate = defaultdict(int)
    terms = defaultdict(int)
    path_counts = defaultdict(Counter)
    rule_metrics = defaultdict(Counter)
    edge_metrics = defaultdict(Counter)
    edge_expansions = defaultdict(Counter)
    trace_events = 0
    for run in runs:
        wi = int(run['worker_index'])
        req(wi in range(9), 'unexpected worker index')
        req(run['replicate'] == wi // 3, 'replicate assignment mismatch')
        policy = POLICIES[wi % 3]
        req(run['scope_order_policy'] == policy, 'scope-order assignment mismatch')
        req(len(run['cases']) == 14, 'per-worker case count mismatch')
        for case in run['cases']:
            variant = case['ownership_variant']
            mono = case['monolithic']
            fallback = case['partition_fallback']
            anchor = case['partition_anchor']
            traced = case['partition_anchor_trace']
            pairs = case['paired']
            for arm_name, arm in (('fallback', fallback), ('anchor', anchor), ('anchor_trace', traced)):
                req(len(arm['checkpoints']) == len(mono['checkpoints']), f'{arm_name} checkpoint count mismatch')
                req(all(cp['closure']['status'] == 'fixed_point' for cp in arm['checkpoints']), f'{arm_name} non-fixed-point closure')
                req(all(not cp.get('deferred_effects_pending', False) for cp in arm['checkpoints']), f'{arm_name} deferred work remains')
            fallback_eq = [a['graph_digest'] == b['graph_digest'] for a, b in zip(mono['checkpoints'], fallback['checkpoints'])]
            anchor_eq = [a['graph_digest'] == b['graph_digest'] for a, b in zip(mono['checkpoints'], anchor['checkpoints'])]
            trace_eq = [a['graph_digest'] == b['graph_digest'] for a, b in zip(anchor['checkpoints'], traced['checkpoints'])]
            req(pairs['fallback_checkpoint_equal'] == fallback_eq, 'fallback checkpoint flags incorrect')
            req(pairs['anchor_checkpoint_equal'] == anchor_eq, 'anchor checkpoint flags incorrect')
            req(pairs['fallback_final_equal'] == (mono['final_graph_digest'] == fallback['final_graph_digest']), 'fallback final flag incorrect')
            req(pairs['anchor_final_equal'] == (mono['final_graph_digest'] == anchor['final_graph_digest']), 'anchor final flag incorrect')
            req(all(fallback_eq) and pairs['fallback_final_equal'], 'fallback state mismatch')
            req(all(anchor_eq) and pairs['anchor_final_equal'], 'anchor state mismatch')
            req(pairs['goal_status_equal'], 'goal lifecycle state mismatch')
            req(pairs['trace_arm_final_equal'] == (anchor['final_graph_digest'] == traced['final_graph_digest']), 'trace final flag incorrect')
            req(pairs['trace_arm_checkpoint_equal'] == trace_eq, 'trace checkpoint flags incorrect')
            req(pairs['trace_arm_final_equal'] and all(trace_eq), 'trace-on/off state mismatch')
            if variant in ('cross_frame', 'orphan_goal'):
                req(all(fallback_eq) and all(anchor_eq), f'{variant} exact-state control failed')
            case_edge_metrics = {'fallback': Counter(), 'anchor': Counter()}
            for arm_name, arm in (('monolithic', mono), ('fallback', fallback), ('anchor', anchor)):
                for cp in arm['checkpoints']:
                    candidate[arm_name] += int(cp.get('candidate_pairs', 0))
                    terms[arm_name] += int(cp.get('term_evaluations', 0))
            for cp in fallback['checkpoints']:
                c = cp.get('scale_counters', {})
                path_counts['fallback']['full_fallback'] += int(c.get('scoped_full_fallback_rule_matches', 0))
                fallback_anchor_attempts = int(c.get('scoped_declared_anchor_rule_matches', 0)) + int(c.get('scoped_anchor_rejected_rule_matches', 0))
                req(fallback_anchor_attempts == 0, 'fallback checkpoint entered declared-anchor path')
                req(int(c.get('scoped_full_fallback_rule_matches', 0)) > 0, 'fallback checkpoint did not invoke full matcher')
                req(isinstance(cp.get('candidate_expansions_by_match_edge'), list), 'fallback semantic-edge expansion data missing')
                for r in cp.get('scale_counters_by_rule', []):
                    rule_metrics['fallback'][(r['rule_name'], r['metric'])] += int(r['count'])
                for r in cp.get('candidate_expansions_by_match_edge', []):
                    key = (r['rule_name'], r['src_var'], r['edge_type'], r['tgt_var'])
                    edge_metrics['fallback'][key] += int(r['candidate_pairs'])
                    case_edge_metrics['fallback'][key] += int(r['candidate_pairs'])
                    edge_expansions['fallback'][key] += int(r['expansion_calls'])
            for cp in anchor['checkpoints']:
                c = cp.get('scale_counters', {})
                path_counts['anchor']['declared_anchor'] += int(c.get('scoped_declared_anchor_rule_matches', 0))
                path_counts['anchor']['anchor_rejected'] += int(c.get('scoped_anchor_rejected_rule_matches', 0))
                path_counts['anchor']['full_fallback'] += int(c.get('scoped_full_fallback_rule_matches', 0))
                req(isinstance(cp.get('candidate_expansions_by_match_edge'), list), 'anchor semantic-edge expansion data missing')
                for r in cp.get('scale_counters_by_rule', []):
                    rule_metrics['anchor'][(r['rule_name'], r['metric'])] += int(r['count'])
                for r in cp.get('candidate_expansions_by_match_edge', []):
                    key = (r['rule_name'], r['src_var'], r['edge_type'], r['tgt_var'])
                    edge_metrics['anchor'][key] += int(r['candidate_pairs'])
                    case_edge_metrics['anchor'][key] += int(r['candidate_pairs'])
                    edge_expansions['anchor'][key] += int(r['expansion_calls'])
            for cp in traced['checkpoints']:
                req(cp.get('trace_dropped') == 0, 'trace rows dropped')
                trace_events += len(cp.get('runtime_access_trace_events', []))
            rows.append({
                'worker_index': wi, 'replicate': run['replicate'], 'scope_order_policy': policy,
                'case_id': case['case_id'], 'requested_goal_count': case['requested_goal_count'],
                'ownership_variant': variant, 'decoy_count': int(case.get('decoy_count', 0)), 'decoy_profile': case.get('decoy_profile', 'none'), 'frame_count': mono['frame_count'],
                'checkpoint_count': len(mono['checkpoints']),
                'fallback_final_equal': pairs['fallback_final_equal'], 'anchor_final_equal': pairs['anchor_final_equal'],
                'fallback_candidate_pairs': sum(int(x.get('candidate_pairs', 0)) for x in fallback['checkpoints']),
                'anchor_candidate_pairs': sum(int(x.get('candidate_pairs', 0)) for x in anchor['checkpoints']),
                'monolithic_candidate_pairs': sum(int(x.get('candidate_pairs', 0)) for x in mono['checkpoints']),
                'fallback_term_evaluations': sum(int(x.get('term_evaluations', 0)) for x in fallback['checkpoints']),
                'anchor_term_evaluations': sum(int(x.get('term_evaluations', 0)) for x in anchor['checkpoints']),
                'monolithic_term_evaluations': sum(int(x.get('term_evaluations', 0)) for x in mono['checkpoints']),
                'fallback_candidate_expansions_by_match_edge': {
                    '|'.join(key): value for key, value in sorted(case_edge_metrics['fallback'].items())
                },
                'anchor_candidate_expansions_by_match_edge': {
                    '|'.join(key): value for key, value in sorted(case_edge_metrics['anchor'].items())
                },
            })
    req(len(rows) == 126, 'independent paired row count mismatch')
    coverage = Counter((r['case_id'], r['requested_goal_count'], r['ownership_variant'], r['scope_order_policy'], r['decoy_count'], r['decoy_profile']) for r in rows)
    expected = Counter({(case, n, 'aligned', policy, 0, 'none'): 3 for case, n in BASE_CELLS for policy in POLICIES})
    expected.update({('concurrent_goals', 2, 'aligned', policy, 256, 'isolated_complete'): 3 for policy in POLICIES})
    expected.update({('concurrent_goals', 2, 'aligned', policy, count, 'shared_event_complete'): 3 for count in (32, 256, 1024) for policy in POLICIES})
    expected.update({('concurrent_goals', 2, 'aligned', policy, 256, f'missing_{edge}'): 3 for edge in ('has_active_goal', 'originated_in', 'has_event', 'for_goal') for policy in POLICIES})
    expected.update({('concurrent_goals', 2, control, policy, 0, 'none'): 3 for control in ('cross_frame', 'orphan_goal') for policy in POLICIES})
    req(coverage == expected, 'locked workload/control/order matrix mismatch')
    aligned_anchor = sum(path_counts['anchor']['declared_anchor'] for _ in (0,))
    req(aligned_anchor > 0, 'declared-anchor path not exercised')
    controls = [r for r in rows if r['ownership_variant'] in ('cross_frame', 'orphan_goal')]
    # Re-evaluate unsafe-ownership proof rejection from the native counters in the capture.
    guard_rejections = 0
    for run in runs:
        for case in run['cases']:
            if case['ownership_variant'] in ('cross_frame', 'orphan_goal'):
                guard_rejections += sum(int(cp.get('scale_counters', {}).get('scoped_anchor_rejected_rule_matches', 0)) for cp in case['partition_anchor']['checkpoints'])
    req(guard_rejections > 0, 'unsafe ownership controls did not trigger proof-guard fallback')
    req(trace_events > 0, 'anchor trace arm empty')
    req(path_counts['fallback']['full_fallback'] > 0, 'fallback control did not use full matcher')
    profile_summary = {}
    dose_success = True
    profile_cells = [('isolated_complete',256),('shared_event_complete',32),('shared_event_complete',256),('shared_event_complete',1024)] + [(f'missing_{edge}',256) for edge in ('has_active_goal','originated_in','has_event','for_goal')]
    for profile,dose in profile_cells:
        selected = [r for r in rows if r['case_id'] == 'concurrent_goals' and r['requested_goal_count'] == 2 and r['ownership_variant'] == 'aligned' and r['decoy_count'] == dose and r['decoy_profile'] == profile]
        values = {
            'paired_cases': len(selected),
            'fallback_candidate_pairs': sum(r['fallback_candidate_pairs'] for r in selected),
            'anchor_candidate_pairs': sum(r['anchor_candidate_pairs'] for r in selected),
            'fallback_term_evaluations': sum(r['fallback_term_evaluations'] for r in selected),
            'anchor_term_evaluations': sum(r['anchor_term_evaluations'] for r in selected),
        }
        values['candidate_reduction'] = 1 - values['anchor_candidate_pairs'] / values['fallback_candidate_pairs'] if values['fallback_candidate_pairs'] else None
        values['term_reduction'] = 1 - values['anchor_term_evaluations'] / values['fallback_term_evaluations'] if values['fallback_term_evaluations'] else None
        profile_summary[f'{profile}:{dose}'] = values
        if not (values['anchor_candidate_pairs'] < values['fallback_candidate_pairs'] and values['anchor_term_evaluations'] < values['fallback_term_evaluations']):
            dose_success = False
    work_reduction = candidate['anchor'] < candidate['fallback'] and terms['anchor'] < terms['fallback']
    summary = {
        'paired_case_count': len(rows), 'checkpoint_count': sum(r['checkpoint_count'] for r in rows),
        'final_state_matches': sum(r['anchor_final_equal'] for r in rows),
        'fallback_candidate_pairs': candidate['fallback'], 'anchor_candidate_pairs': candidate['anchor'],
        'monolithic_candidate_pairs': candidate['monolithic'],
        'fallback_term_evaluations': terms['fallback'], 'anchor_term_evaluations': terms['anchor'],
        'monolithic_term_evaluations': terms['monolithic'],
        'fallback_candidate_ratio_vs_monolithic': candidate['fallback'] / candidate['monolithic'] if candidate['monolithic'] else None,
        'anchor_candidate_ratio_vs_monolithic': candidate['anchor'] / candidate['monolithic'] if candidate['monolithic'] else None,
        'fallback_term_ratio_vs_monolithic': terms['fallback'] / terms['monolithic'] if terms['monolithic'] else None,
        'anchor_term_ratio_vs_monolithic': terms['anchor'] / terms['monolithic'] if terms['monolithic'] else None,
        'candidate_reduction_vs_fallback': 1 - candidate['anchor'] / candidate['fallback'] if candidate['fallback'] else None,
        'term_reduction_vs_fallback': 1 - terms['anchor'] / terms['fallback'] if terms['fallback'] else None,
        'work_reduction_gate_pass': work_reduction,
        'path_counts': {arm: dict(counts) for arm, counts in path_counts.items()},
        'guard_rejections_on_unsafe_controls': guard_rejections,
        'trace_event_rows': trace_events,
        'top_anchor_rules_by_candidate_pairs': dict(sorted(((name, count) for (name, metric), count in rule_metrics['anchor'].items() if metric == 'candidate_pairs'), key=lambda x: (-x[1], x[0]))[:20]),
        'top_anchor_rules_by_term_evaluations': dict(sorted(((name, count) for (name, metric), count in rule_metrics['anchor'].items() if metric == 'term_evaluations'), key=lambda x: (-x[1], x[0]))[:20]),
        'fallback_candidate_expansions_by_match_edge': {
            '|'.join(key): value for key, value in sorted(edge_metrics['fallback'].items())
        },
        'anchor_candidate_expansions_by_match_edge': {
            '|'.join(key): value for key, value in sorted(edge_metrics['anchor'].items())
        },
        'semantic_edge_candidate_accounting': {
            arm: {
                'candidate_pairs_attributed': sum(edge_metrics[arm].values()),
                'candidate_pairs_from_scale_counter': candidate[arm],
                'unattributed_candidate_pair_delta': candidate[arm] - sum(edge_metrics[arm].values()),
                'expansion_calls': sum(edge_expansions[arm].values()),
                'edge_breakdown_candidate_pairs': {
                    '|'.join(key): value for key, value in sorted(edge_metrics[arm].items())
                },
                'edge_breakdown_expansion_calls': {
                    '|'.join(key): value for key, value in sorted(edge_expansions[arm].items())
                },
            }
            for arm in ('fallback', 'anchor')
        },
        'decoy_profile_summary': profile_summary,
    }
    out = {'schema': 'ConversationTaskScopeDegreeSelectivityPilotV2_3Analysis', 'gates_pass': not errors, 'errors': errors,
           'performance_success': not errors and work_reduction and dose_success, 'paired_cases': rows, 'summary': summary,
           'analysis_script_sha256': sha(__file__),
           'claim_boundary': cap.get('claim_boundary')}
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'gates_pass': out['gates_pass'], 'performance_success': out['performance_success'], 'errors': errors, 'summary': summary}, indent=2))
    return int(bool(errors))

if __name__ == '__main__':
    raise SystemExit(main())
