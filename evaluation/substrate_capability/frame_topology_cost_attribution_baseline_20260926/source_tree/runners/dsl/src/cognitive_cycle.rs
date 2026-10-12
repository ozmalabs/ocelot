//! Explicit cognitive-cycle phase plans.
//!
//! The runtime historically exposed several non-equivalent "tick" paths.  This
//! module makes their native phases data instead of leaving their ordering
//! implicit in unrelated Python/Rust methods.  Every legacy plan preserves its
//! old phase order; new scheduling semantics are exposed only through explicit
//! opt-in plans such as `dual_process`.

use crate::graph::{Attrs, NodeID};
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CyclePlan {
    /// Default host/background dispatch.  Substrates containing an enabled
    /// DualProcessPolicy use the gated System-1/System-2 schedule; substrates
    /// without that core retain the historical unrestricted rule settlement.
    Default,
    /// `WorldAdapter.tick` / `inner.run_rules`.
    StructRulesOnly,
    /// Native `Substrate.tick`: graph Rule nodes, then persistent struct rules.
    GraphThenStruct,
    /// `WorldAdapter.cognitive_tick`: struct rules, then host reflex boundary.
    CognitiveLegacy,
    /// `WorldAdapter.master_tick`: clock fold, host reflex/thread/result boundary.
    MasterLegacy,
    /// Graph-decided tasks, one native worker, deterministic fold.
    AreaSerial,
    /// Graph-decided tasks, bounded native workers, deterministic fold.
    AreaParallel,
    /// Settle the authored hard-real-time sheet first.  Only an explicit
    /// graph-minted SystemTwoEscalation admits the remaining rule population.
    DualProcess,
}

impl CyclePlan {
    pub fn parse(name: &str) -> Option<Self> {
        match name {
            "default" => Some(Self::Default),
            "struct_rules_only" => Some(Self::StructRulesOnly),
            "graph_then_struct" => Some(Self::GraphThenStruct),
            "cognitive_legacy" => Some(Self::CognitiveLegacy),
            "master_legacy" => Some(Self::MasterLegacy),
            "area_serial" => Some(Self::AreaSerial),
            "area_parallel" => Some(Self::AreaParallel),
            "dual_process" => Some(Self::DualProcess),
            _ => None,
        }
    }
}

#[derive(Clone, Debug)]
pub struct CycleTraceEvent {
    pub sequence: usize,
    pub phase: &'static str,
    pub progressed: usize,
    pub fingerprint: Option<u64>,
}

#[derive(Clone, Debug, Default)]
pub struct CycleReport {
    pub steps: usize,
    pub clock_commits: usize,
    pub needs_reflex_dispatch: bool,
    /// Autonomous (order-0) reflexes the ENGINE fired this cycle, with no host
    /// involvement.  Distinct from `needs_reflex_dispatch`, which asks the host
    /// to enact a response it owns.
    pub reflexes_fired: usize,
    pub needs_thread_dispatch: bool,
    pub needs_result_fold: bool,
    pub needs_system_two: bool,
    pub system_one_commits: usize,
    pub system_two_escalations: usize,
    pub system_two_stale: usize,
    pub system_two_lease_blocked: usize,
    pub system_two_steps: usize,
    pub task_summary: Option<crate::cognitive_tasks::TaskRunSummary>,
    pub trace: Vec<CycleTraceEvent>,
}

/// Advance the graph-authored cognition clock exactly once at an outer cycle
/// boundary. Disabled, absent, or malformed policies preserve legacy runtime.
/// Every process may own an independent policy clock; each strict enabled
/// integer clock advances once.
pub fn advance_cognitive_epoch(substrate: &mut Substrate) -> usize {
    let policy_type = substrate.interner.intern("CognitiveSupervisionPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let epoch_key = substrate.interner.intern("cognitive_epoch");
    let enabled: Vec<(NodeID, i64)> = substrate
        .graph
        .nodes_of_type(policy_type)
        .into_iter()
        .filter_map(|node| {
            let attrs = &substrate.graph.node(node).attrs;
            if attrs.get(&enabled_key) != Some(&Value::Int(1)) {
                return None;
            }
            match attrs.get(&epoch_key) {
                Some(Value::Int(epoch)) => Some((node, *epoch)),
                _ => None,
            }
        })
        .collect();
    let advanced = enabled.len();
    for (policy, epoch) in enabled {
        substrate.set_attr(policy, epoch_key, Value::Int(epoch.saturating_add(1)));
    }
    advanced
}

fn push_trace(
    report: &mut CycleReport,
    substrate: &Substrate,
    phase: &'static str,
    progressed: usize,
    trace: bool,
) {
    if trace {
        report.trace.push(CycleTraceEvent {
            sequence: report.trace.len(),
            phase,
            progressed,
            fingerprint: Some(substrate.graph.state_fingerprint()),
        });
    }
}

/// The lawful non-monotone clock down-stroke, shared by the explicit cycle
/// plans and the legacy PyO3 method.
pub fn fold_clock_edge(substrate: &mut Substrate) -> usize {
    let clocked_key = substrate.interner.intern("clocked");
    let mut todo: Vec<(NodeID, String, Value)> = Vec::new();
    for nid in substrate.graph.all_nodes() {
        let node = substrate.graph.node(nid);
        let clocked = match node.attrs.get(&clocked_key) {
            Some(Value::Float(v)) => *v == 1.0,
            Some(Value::Int(v)) => *v == 1,
            Some(Value::Bool(v)) => *v,
            _ => false,
        };
        if !clocked {
            continue;
        }
        for (key, value) in &node.attrs {
            if let Some(stripped) = substrate.interner.resolve(*key).strip_prefix("next_") {
                if !stripped.is_empty() {
                    todo.push((nid, stripped.to_owned(), value.clone()));
                }
            }
        }
    }
    let committed = todo.len();
    for (nid, key, value) in todo {
        let key = substrate.interner.intern(&key);
        substrate.set_attr(nid, key, value);
    }
    committed
}

fn node_status_count(substrate: &mut Substrate, node_type: &str, status: &str) -> usize {
    let node_type = substrate.interner.intern(node_type);
    let status_key = substrate.interner.intern("status");
    let status = substrate.interner.intern(status);
    substrate
        .graph
        .nodes_of_type(node_type)
        .into_iter()
        .filter(|node| {
            substrate.graph.node(*node).attrs.get(&status_key) == Some(&Value::Str(status))
        })
        .count()
}

fn enabled_attr(value: Option<&Value>) -> bool {
    match value {
        Some(Value::Bool(value)) => *value,
        Some(Value::Int(value)) => *value != 0,
        Some(Value::Float(value)) => *value != 0.0,
        _ => false,
    }
}

fn has_enabled_dual_process_policy(substrate: &mut Substrate) -> bool {
    let policy_type = substrate.interner.intern("DualProcessPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    substrate
        .graph
        .nodes_of_type(policy_type)
        .into_iter()
        .any(|node| enabled_attr(substrate.graph.node(node).attrs.get(&enabled_key)))
}

/// Read the graph-resident fair-phase cursor for the dual-process scheduler.
///
/// A continuous System-1 sheet and a held System-2 escalation are both real
/// residuals.  Giving the whole one-step budget to the hard sheet forever
/// makes the latter unreachable; giving it permanently to System 2 makes the
/// former unreachable.  The cursor is therefore state in the enabled
/// `DualProcessPolicy`, rather than hidden host cadence: `0` gives the next
/// bounded turn to System 1 and `1` gives it to an already-requested System 2
/// continuation.  Absent legacy attrs mean the historical System-1-first
/// phase.  Every enabled policy receives the same committed cursor because
/// this runtime has one global rule sheet, not one scheduler per policy.
fn system_two_turn_owed(substrate: &mut Substrate) -> bool {
    let policy_type = substrate.interner.intern("DualProcessPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let cursor_key = substrate.interner.intern("system_two_turn_owed");
    substrate
        .graph
        .nodes_of_type(policy_type)
        .into_iter()
        .any(|node| {
            let attrs = &substrate.graph.node(node).attrs;
            enabled_attr(attrs.get(&enabled_key)) && attrs.get(&cursor_key) == Some(&Value::Int(1))
        })
}

/// Commit the next fair phase into graph state.  This is scheduler mechanics,
/// not a domain choice: the graph still decides whether any System-2 request
/// exists and which areas it recruits.
fn set_system_two_turn_owed(substrate: &mut Substrate, owed: bool) {
    let policy_type = substrate.interner.intern("DualProcessPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let cursor_key = substrate.interner.intern("system_two_turn_owed");
    let policies: Vec<NodeID> = substrate
        .graph
        .nodes_of_type(policy_type)
        .into_iter()
        .filter(|node| enabled_attr(substrate.graph.node(*node).attrs.get(&enabled_key)))
        .collect();
    let value = Value::Int(i64::from(owed));
    for policy in policies {
        substrate.set_attr(policy, cursor_key, value.clone());
    }
}

fn read_i64(attrs: &Attrs, key: Sym) -> Option<i64> {
    match attrs.get(&key) {
        Some(Value::Int(value)) => Some(*value),
        Some(Value::Float(value)) if value.is_finite() => Some(*value as i64),
        _ => None,
    }
}

#[derive(Debug)]
struct SystemTwoAdmission {
    request: NodeID,
    areas: FxHashSet<Sym>,
    parallel_contexts: bool,
}

#[derive(Debug)]
struct SystemTwoAdmissionGroup {
    requests: Vec<NodeID>,
    areas: FxHashSet<Sym>,
}

#[derive(Debug, Default)]
struct SystemTwoAdmissions {
    admitted: Vec<SystemTwoAdmission>,
    stale: usize,
    lease_blocked: usize,
}

/// Validate the continuation lease of a process-bound scheduling request.
///
/// Unbound requests retain legacy behavior. A bound request is different: its
/// edge opts it into a strict graph contract and malformed or ambiguous graph
/// state therefore fails closed. Check-in work uses a disjoint structural edge
/// and is admitted only for the held process, avoiding an infinite supervisor
/// lease regress.
fn process_lease_allows_request(substrate: &mut Substrate, request: NodeID) -> bool {
    let continues = substrate.interner.intern("continues_cognitive_process");
    let checks = substrate.interner.intern("checks_cognitive_process");
    let governed_by = substrate
        .interner
        .intern("governed_by_cognitive_supervision_policy");
    let policy_type = substrate.interner.intern("CognitiveSupervisionPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let epoch_key = substrate.interner.intern("cognitive_epoch");
    let authority_key = substrate.interner.intern("continuation_authority");
    let generation_key = substrate.interner.intern("lease_generation");
    let renew_key = substrate.interner.intern("renew_before_epoch");

    let continuation_processes = substrate.graph.neighbours(request, Some(continues));
    let checkin_processes = substrate.graph.neighbours(request, Some(checks));
    if continuation_processes.is_empty() && checkin_processes.is_empty() {
        return true;
    }
    let (process, is_checkin) = match (
        continuation_processes.as_slice(),
        checkin_processes.as_slice(),
    ) {
        ([process], []) => (*process, false),
        ([], [process]) => (*process, true),
        _ => return false,
    };
    if !substrate.graph.has_node(process) {
        return false;
    }
    let policies = substrate.graph.neighbours(process, Some(governed_by));
    if policies.len() != 1 {
        return false;
    }
    let policy = policies[0];
    if !substrate.graph.has_node(policy) {
        return false;
    }
    let policy_node = substrate.graph.node(policy);
    if policy_node.type_ != policy_type
        || policy_node.attrs.get(&enabled_key) != Some(&Value::Int(1))
    {
        return false;
    }
    let Some(Value::Int(epoch)) = policy_node.attrs.get(&epoch_key) else {
        return false;
    };
    let process_attrs = &substrate.graph.node(process).attrs;
    let Some(Value::Int(authority)) = process_attrs.get(&authority_key) else {
        return false;
    };
    let Some(Value::Int(process_generation)) = process_attrs.get(&generation_key) else {
        return false;
    };
    let Some(Value::Int(renew_before)) = process_attrs.get(&renew_key) else {
        return false;
    };
    let Some(Value::Int(request_generation)) =
        substrate.graph.node(request).attrs.get(&generation_key)
    else {
        return false;
    };
    if request_generation != process_generation {
        return false;
    }
    let held = *authority == 0 || *epoch >= *renew_before;
    if is_checkin {
        held
    } else {
        *authority == 1 && *epoch < *renew_before
    }
}

/// An explicit request may declare `input_epoch` and/or `deadline_epoch`.
/// Those attributes are optional for compatibility. When present, they are
/// checked against the request's graph-linked context rather than a host
/// clock, keeping staleness a property of graph provenance.
fn request_is_stale(substrate: &mut Substrate, request: NodeID, about_context: Sym) -> bool {
    let input_epoch_key = substrate.interner.intern("input_epoch");
    let deadline_epoch_key = substrate.interner.intern("deadline_epoch");
    let epoch_key = substrate.interner.intern("epoch");
    let status_key = substrate.interner.intern("status");
    let stale = substrate.interner.intern("stale");
    let cancelled = substrate.interner.intern("cancelled");
    let retired = substrate.interner.intern("retired");
    let continued = substrate.interner.intern("continued");
    let replan_required = substrate.interner.intern("replan_required");
    let motor_program_revised = substrate.interner.intern("motor_program_revised");

    let request_attrs = &substrate.graph.node(request).attrs;
    let input_epoch = read_i64(request_attrs, input_epoch_key);
    let deadline_epoch = read_i64(request_attrs, deadline_epoch_key);
    if input_epoch.is_none() && deadline_epoch.is_none() {
        return false;
    }

    let contexts = substrate.graph.neighbours(request, Some(about_context));
    if contexts.len() != 1 {
        return true;
    }
    let context_attrs = &substrate.graph.node(contexts[0]).attrs;
    if matches!(
        context_attrs.get(&status_key),
        Some(Value::Str(value))
            if *value == stale
                || *value == cancelled
                || *value == retired
                || *value == continued
                || *value == replan_required
                || *value == motor_program_revised
    ) {
        return true;
    }
    let Some(context_epoch) = read_i64(context_attrs, epoch_key) else {
        return true;
    };
    input_epoch.is_some_and(|value| value != context_epoch)
        || deadline_epoch.is_some_and(|value| context_epoch > value)
}

/// Collect graph-requested escalations that name at least one explicit
/// task-set area. Requests remain `requested` here and are admitted one at a
/// time immediately before their scoped settlement. That status transition is
/// the request-local execution token: concurrent requests never all appear
/// admitted while one request's area is running.
fn admit_system_two(substrate: &mut Substrate) -> SystemTwoAdmissions {
    let escalation_type = substrate.interner.intern("SystemTwoEscalation");
    let task_set_type = substrate.interner.intern("SystemTwoTaskSet");
    let status_key = substrate.interner.intern("status");
    let area_key = substrate.interner.intern("area");
    let enabled_key = substrate.interner.intern("enabled");
    let parallel_contexts_key = substrate.interner.intern("parallel_contexts");
    let recruits_task_set = substrate.interner.intern("recruits_task_set");
    let about_context = substrate.interner.intern("about_context");
    let requested = substrate.interner.intern("requested");
    let stale = substrate.interner.intern("stale");
    let requests: Vec<NodeID> = substrate
        .graph
        .nodes_of_type(escalation_type)
        .into_iter()
        .filter(|node| {
            substrate.graph.node(*node).attrs.get(&status_key) == Some(&Value::Str(requested))
        })
        .collect();
    let mut admissions = SystemTwoAdmissions::default();
    for request in requests {
        // Context termination is stronger than a superseded lease. Check it
        // first so completed check-ins do not remain an immortal blocked
        // backlog after their process advances to a newer generation.
        if request_is_stale(substrate, request, about_context) {
            substrate.set_attr(request, status_key, Value::Str(stale));
            admissions.stale += 1;
            continue;
        }
        if !process_lease_allows_request(substrate, request) {
            admissions.lease_blocked += 1;
            continue;
        }
        let request_areas: Vec<Sym> = substrate
            .graph
            .neighbours(request, Some(recruits_task_set))
            .iter()
            .filter_map(|task_set| {
                let task_set = substrate.graph.node(*task_set);
                if task_set.type_ != task_set_type
                    || !enabled_attr(task_set.attrs.get(&enabled_key))
                {
                    return None;
                }
                match task_set.attrs.get(&area_key) {
                    Some(Value::Str(area)) => Some(*area),
                    _ => None,
                }
            })
            .collect();
        if request_areas.is_empty() {
            continue;
        }
        let mut areas = FxHashSet::default();
        for area in request_areas {
            areas.insert(area);
        }
        admissions.admitted.push(SystemTwoAdmission {
            request,
            areas,
            parallel_contexts: substrate
                .graph
                .node(request)
                .attrs
                .get(&parallel_contexts_key)
                == Some(&Value::Int(1)),
        });
    }
    admissions
}

/// Opted-in requests with the same enabled area mask expose the same rule
/// sheet. One settlement over that sheet processes every graph context in
/// parallel, so rerunning it once per request is redundant and makes cost
/// scale with the number of concurrent thoughts rather than with graph work.
/// Non-opted requests and distinct masks retain isolated bounded fair shares.
fn group_system_two_admissions(admissions: &[SystemTwoAdmission]) -> Vec<SystemTwoAdmissionGroup> {
    let mut groups: Vec<SystemTwoAdmissionGroup> = Vec::new();
    for admission in admissions {
        if admission.parallel_contexts {
            if let Some(group) = groups
                .iter_mut()
                .find(|group| group.areas == admission.areas)
            {
                group.requests.push(admission.request);
                continue;
            }
        }
        groups.push(SystemTwoAdmissionGroup {
            requests: vec![admission.request],
            areas: admission.areas.clone(),
        });
    }
    groups
}

fn reserved_motor_steps(substrate: &mut Substrate, available: usize) -> usize {
    if available <= 1 {
        return 0;
    }
    let policy_type = substrate.interner.intern("DualProcessPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let budget_key = substrate.interner.intern("motor_reserve_steps");
    let authored = substrate
        .graph
        .nodes_of_type(policy_type)
        .into_iter()
        .filter_map(|node| {
            let attrs = &substrate.graph.node(node).attrs;
            if !enabled_attr(attrs.get(&enabled_key)) {
                return None;
            }
            read_i64(attrs, budget_key).and_then(|value| usize::try_from(value).ok())
        })
        .max()
        .unwrap_or(0);
    authored.min(available.saturating_sub(1))
}

/// Settle only the non-hard-real-time rule areas explicitly recruited by an
/// admitted task set. Rules outside the scope retain their dirty bits. The
/// temporary `active` mask is scheduler state, restored before returning, and
/// cannot change graph semantics or make a domain decision.
fn run_scoped_system_two(
    substrate: &mut Substrate,
    areas: &FxHashSet<Sym>,
    max_steps: usize,
    detect_cycles: bool,
) -> usize {
    if areas.is_empty() || max_steps == 0 {
        return 0;
    }
    let hard_realtime = substrate.interner.intern("hard_realtime");
    let active_before: Vec<bool> = substrate.rules.iter().map(|rule| rule.active).collect();
    for rule in &mut substrate.rules {
        if rule.active && (rule.latency_class == hard_realtime || !areas.contains(&rule.area)) {
            rule.active = false;
        }
    }
    let progressed = substrate.run_rules_opts(max_steps, detect_cycles);
    for (rule, active) in substrate.rules.iter_mut().zip(active_before) {
        rule.active = active;
    }
    progressed
}

/// ORDER 0 FIRES BEFORE ANYTHING ELSE, ON EVERY PLAN.
///
/// A reflex is involuntary: it cannot be conditional on which cycle plan the
/// host picked, and it cannot wait for the rule fixpoint that it exists to buy
/// time for.  So autonomous reflexes fire here, at the top of the cycle,
/// before a single rule is matched -- and their stamps are therefore visible
/// to every rule in the settle that follows.  That ordering is the whole
/// mechanism: the engine does not know what a reflex MEANS, it only records
/// that one fired, and the meaning is a rule that reads the stamp.
///
/// Absent `autonomous` reads 0, so a tree with no autonomous reflex runs a
/// no-op lookup here and is byte-unchanged.
pub fn execute(
    substrate: &mut Substrate,
    plan: CyclePlan,
    max_steps: usize,
    detect_cycles: bool,
    trace: bool,
    task_workers: usize,
) -> CycleReport {
    let fired = crate::reflex_runtime::fire_autonomous(substrate);
    let mut report = execute_plan(
        substrate,
        plan,
        max_steps,
        detect_cycles,
        trace,
        task_workers,
    );
    report.reflexes_fired = report.reflexes_fired.saturating_add(fired);
    report
}

fn execute_plan(
    substrate: &mut Substrate,
    plan: CyclePlan,
    max_steps: usize,
    detect_cycles: bool,
    trace: bool,
    task_workers: usize,
) -> CycleReport {
    let mut report = CycleReport::default();
    match plan {
        CyclePlan::Default => {
            let selected = if has_enabled_dual_process_policy(substrate) {
                CyclePlan::DualProcess
            } else {
                CyclePlan::StructRulesOnly
            };
            // `execute_plan`, NOT `execute`: the reflex pass has already run
            // at the outer boundary and must not fire twice for one cycle.
            report = execute_plan(
                substrate,
                selected,
                max_steps,
                detect_cycles,
                trace,
                task_workers,
            );
        }
        CyclePlan::StructRulesOnly => {
            let n = substrate.run_rules_opts(max_steps, detect_cycles);
            report.steps = n;
            push_trace(&mut report, substrate, "struct_rules", n, trace);
            let adjusted = substrate.apply_trajectory_control();
            push_trace(
                &mut report,
                substrate,
                "trajectory_quantized_feedback",
                adjusted,
                trace,
            );
        }
        CyclePlan::GraphThenStruct => {
            let graph_n =
                crate::graph_rules::run_graph_rules_opts(substrate, max_steps, detect_cycles);
            report.steps = graph_n;
            push_trace(&mut report, substrate, "graph_rules", graph_n, trace);
            let adjusted = substrate.apply_trajectory_control();
            push_trace(
                &mut report,
                substrate,
                "trajectory_quantized_feedback",
                adjusted,
                trace,
            );
            let remaining = max_steps.saturating_sub(report.steps);
            if remaining > 0 {
                let struct_n = substrate.run_rules_opts(remaining, detect_cycles);
                report.steps = report.steps.saturating_add(struct_n);
                push_trace(&mut report, substrate, "struct_rules", struct_n, trace);
            }
        }
        CyclePlan::CognitiveLegacy => {
            let n = substrate.run_rules_opts(max_steps, detect_cycles);
            report.steps = n;
            push_trace(&mut report, substrate, "struct_rules", n, trace);
            report.needs_reflex_dispatch = true;
            push_trace(&mut report, substrate, "reflex_boundary", 0, trace);
        }
        CyclePlan::MasterLegacy => {
            let n = fold_clock_edge(substrate);
            report.clock_commits = n;
            push_trace(&mut report, substrate, "clock_fold", n, trace);
            report.needs_reflex_dispatch = true;
            report.needs_thread_dispatch = true;
            report.needs_result_fold = true;
            push_trace(&mut report, substrate, "reflex_boundary", 0, trace);
            push_trace(&mut report, substrate, "thread_boundary", 0, trace);
            push_trace(&mut report, substrate, "result_fold_boundary", 0, trace);
        }
        CyclePlan::AreaSerial | CyclePlan::AreaParallel => {
            let first = substrate.run_rules_opts(max_steps, detect_cycles);
            report.steps = first;
            push_trace(&mut report, substrate, "area_rules_pre", first, trace);
            let workers = if plan == CyclePlan::AreaSerial {
                1
            } else {
                task_workers.max(1)
            };
            let task_summary = crate::cognitive_tasks::run_requested(substrate, workers);
            let task_progress = task_summary.completed + task_summary.failed + task_summary.stale;
            push_trace(
                &mut report,
                substrate,
                "task_result_fold",
                task_progress,
                trace,
            );
            report.task_summary = Some(task_summary);
            let remaining = max_steps.saturating_sub(report.steps);
            if remaining > 0 {
                let second = substrate.run_rules_opts(remaining, detect_cycles);
                report.steps = report.steps.saturating_add(second);
                push_trace(&mut report, substrate, "area_rules_post", second, trace);
            }
        }
        CyclePlan::DualProcess => {
            let hard_realtime = substrate.interner.intern("hard_realtime");
            // A persistent graph-requested System-2 continuation gets the
            // next bounded outer-cycle turn after System 1 has consumed the
            // preceding one.  This matters at max_steps=1: reserving a soft
            // remainder after giving all of that one step to the hard sheet
            // is a starvation proof, not a scheduler.
            let requested_before = node_status_count(substrate, "SystemTwoEscalation", "requested");
            let system_two_first =
                max_steps > 0 && requested_before > 0 && system_two_turn_owed(substrate);
            let commits_before = node_status_count(substrate, "SystemOneCommit", "committed");
            let fast = substrate.run_rules_latency_opts(
                hard_realtime,
                if system_two_first { 0 } else { max_steps },
                detect_cycles,
            );
            report.steps = fast;
            push_trace(&mut report, substrate, "system_one_settle", fast, trace);

            // The hard sheet has first claim on the cycle. Only after native
            // reflex settlement do we consume graph-resident deviation and
            // adjust tangent width in integer quanta.
            let adjusted = substrate.apply_trajectory_control();
            push_trace(
                &mut report,
                substrate,
                "trajectory_quantized_feedback",
                adjusted,
                trace,
            );

            let commits_after = node_status_count(substrate, "SystemOneCommit", "committed");
            report.system_one_commits = commits_after.saturating_sub(commits_before);

            let requested = node_status_count(substrate, "SystemTwoEscalation", "requested");
            report.needs_system_two = requested > 0;
            let remaining = max_steps.saturating_sub(report.steps);

            if requested > 0 && remaining > 0 {
                let admissions = admit_system_two(substrate);
                report.system_two_stale = admissions.stale;
                report.system_two_lease_blocked = admissions.lease_blocked;
                if !admissions.admitted.is_empty() {
                    // Reserve a graph-authored portion of the remaining
                    // budget before soft work. Graph-opted identical area
                    // masks share one parallel settlement; all other masks
                    // retain independent fair shares and are never widened.
                    let motor_reserve = reserved_motor_steps(substrate, remaining);
                    let mut deep_remaining = remaining.saturating_sub(motor_reserve);
                    let groups = group_system_two_admissions(&admissions.admitted);
                    let group_count = groups.len();
                    let status_key = substrate.interner.intern("status");
                    let admitted_status = substrate.interner.intern("admitted");
                    let requested_status = substrate.interner.intern("requested");
                    let serviced_status = substrate.interner.intern("serviced");
                    for (index, group) in groups.iter().enumerate() {
                        if deep_remaining == 0 {
                            break;
                        }
                        let outstanding = group_count.saturating_sub(index).max(1);
                        let request_budget =
                            deep_remaining.saturating_add(outstanding - 1) / outstanding;
                        for request in &group.requests {
                            substrate.set_attr(*request, status_key, Value::Str(admitted_status));
                        }
                        report.system_two_escalations = report
                            .system_two_escalations
                            .saturating_add(group.requests.len());
                        let deep = run_scoped_system_two(
                            substrate,
                            &group.areas,
                            request_budget,
                            detect_cycles,
                        );
                        report.steps = report.steps.saturating_add(deep);
                        report.system_two_steps = report.system_two_steps.saturating_add(deep);
                        deep_remaining = deep_remaining.saturating_sub(deep);
                        // `admitted` is an execution token, not a durable
                        // historical state. Preserve any terminal status a
                        // graph rule authored; otherwise yield a saturated
                        // request for another cycle or close a quiescent one.
                        let next = if deep == request_budget {
                            requested_status
                        } else {
                            serviced_status
                        };
                        for request in &group.requests {
                            if substrate.graph.node(*request).attrs.get(&status_key)
                                == Some(&Value::Str(admitted_status))
                            {
                                substrate.set_attr(*request, status_key, Value::Str(next));
                            }
                        }
                        push_trace(
                            &mut report,
                            substrate,
                            "system_two_request_settle",
                            deep,
                            trace,
                        );
                    }
                    let admitted_count = report.system_two_escalations;
                    push_trace(
                        &mut report,
                        substrate,
                        "system_two_admit",
                        admitted_count,
                        trace,
                    );
                    let system_two_steps = report.system_two_steps;
                    push_trace(
                        &mut report,
                        substrate,
                        "system_two_settle",
                        system_two_steps,
                        trace,
                    );
                    // Deliberation may publish a selected control that a
                    // hard-real-time motor/bundle rule consumes. Give that
                    // fast sheet its reserved fold in the same cognitive
                    // tick; scoped soft rules remain closed.
                    let motor_budget = max_steps.saturating_sub(report.steps);
                    if motor_budget > 0 {
                        let motor = substrate.run_rules_latency_opts(
                            hard_realtime,
                            motor_budget,
                            detect_cycles,
                        );
                        report.steps = report.steps.saturating_add(motor);
                        push_trace(
                            &mut report,
                            substrate,
                            "system_two_motor_fold",
                            motor,
                            trace,
                        );
                    }
                } else if admissions.lease_blocked > 0 {
                    push_trace(
                        &mut report,
                        substrate,
                        "system_two_lease_blocked",
                        admissions.lease_blocked,
                        trace,
                    );
                } else {
                    push_trace(
                        &mut report,
                        substrate,
                        "system_two_unscoped_deferred",
                        requested,
                        trace,
                    );
                }
            } else if requested > 0 {
                // Do not consume an escalation when this cycle has no budget
                // left to service it.  The graph request remains `requested`
                // and can be admitted by the next cycle.
                push_trace(
                    &mut report,
                    substrate,
                    "system_two_deferred",
                    requested,
                    trace,
                );
            } else {
                let commits = report.system_one_commits;
                let phase = if commits > 0 {
                    "system_one_commit"
                } else {
                    "system_one_quiescent"
                };
                push_trace(&mut report, substrate, phase, commits, trace);
            }
            // The cursor is graph-visible scheduler state.  It advances only
            // when a real bounded turn exists: a hard turn leaves an extant
            // continuation owed, while a System-2 turn yields the next one to
            // the hard sheet.  No wall-clock cadence or domain-specific host
            // policy participates.
            if max_steps > 0 {
                let requested_after =
                    node_status_count(substrate, "SystemTwoEscalation", "requested");
                set_system_two_turn_owed(substrate, !system_two_first && requested_after > 0);
            }
        }
    }
    report
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::grammar::Grammar;

    fn fresh() -> Substrate {
        Substrate::new(ConsistencyChecker::new(Grammar::new()))
    }

    fn add_edge(substrate: &mut Substrate, src: NodeID, edge: &str, tgt: NodeID) {
        let edge = substrate.interner.intern(edge);
        substrate
            .graph
            .insert_edge(src, edge, tgt, rustc_hash::FxHashMap::default())
            .expect("test edge");
    }

    fn trajectory_state(substrate: &mut Substrate, width: i64, deviation: i64) -> NodeID {
        let state_type = substrate.interner.intern("TrajectoryControlState");
        let mut attrs = rustc_hash::FxHashMap::default();
        attrs.insert(substrate.interner.intern("enabled"), Value::Int(1));
        attrs.insert(
            substrate.interner.intern("deviation_count"),
            Value::Int(deviation),
        );
        attrs.insert(
            substrate.interner.intern("deviation_wide_quanta"),
            Value::Int(2),
        );
        attrs.insert(
            substrate.interner.intern("deviation_converge_quanta"),
            Value::Int(0),
        );
        attrs.insert(
            substrate.interner.intern("tangent_width"),
            Value::Int(width),
        );
        attrs.insert(
            substrate.interner.intern("min_tangent_width"),
            Value::Int(0),
        );
        attrs.insert(
            substrate.interner.intern("max_tangent_width"),
            Value::Int(2),
        );
        attrs.insert(substrate.interner.intern("widen_step"), Value::Int(1));
        attrs.insert(substrate.interner.intern("narrow_step"), Value::Int(1));
        substrate.add_node(state_type, attrs)
    }

    fn add_request(
        substrate: &mut Substrate,
        process: Option<(NodeID, &str)>,
        generation: i64,
    ) -> NodeID {
        let request_type = substrate.interner.intern("SystemTwoEscalation");
        let status = substrate.interner.intern("status");
        let requested = substrate.interner.intern("requested");
        let lease_generation = substrate.interner.intern("lease_generation");
        let mut attrs = rustc_hash::FxHashMap::default();
        attrs.insert(status, Value::Str(requested));
        attrs.insert(lease_generation, Value::Int(generation));
        let request = substrate.add_node(request_type, attrs);
        let task_type = substrate.interner.intern("SystemTwoTaskSet");
        let enabled = substrate.interner.intern("enabled");
        let area = substrate.interner.intern("area");
        let planning = substrate.interner.intern("planning");
        let mut task_attrs = rustc_hash::FxHashMap::default();
        task_attrs.insert(enabled, Value::Int(1));
        task_attrs.insert(area, Value::Str(planning));
        let task = substrate.add_node(task_type, task_attrs);
        add_edge(substrate, request, "recruits_task_set", task);
        if let Some((process, edge)) = process {
            add_edge(substrate, request, edge, process);
        }
        request
    }

    fn supervised_process(
        substrate: &mut Substrate,
        epoch: i64,
        authority: Value,
        renew_before: i64,
    ) -> (NodeID, NodeID) {
        let policy_type = substrate.interner.intern("CognitiveSupervisionPolicy");
        let enabled = substrate.interner.intern("enabled");
        let cognitive_epoch = substrate.interner.intern("cognitive_epoch");
        let mut policy_attrs = rustc_hash::FxHashMap::default();
        policy_attrs.insert(enabled, Value::Int(1));
        policy_attrs.insert(cognitive_epoch, Value::Int(epoch));
        let policy = substrate.add_node(policy_type, policy_attrs);

        let process_type = substrate.interner.intern("CognitiveProcess");
        let continuation_authority = substrate.interner.intern("continuation_authority");
        let lease_generation = substrate.interner.intern("lease_generation");
        let renew_before_epoch = substrate.interner.intern("renew_before_epoch");
        let mut process_attrs = rustc_hash::FxHashMap::default();
        process_attrs.insert(continuation_authority, authority);
        process_attrs.insert(lease_generation, Value::Int(7));
        process_attrs.insert(renew_before_epoch, Value::Int(renew_before));
        let process = substrate.add_node(process_type, process_attrs);
        add_edge(
            substrate,
            process,
            "governed_by_cognitive_supervision_policy",
            policy,
        );
        (policy, process)
    }

    #[test]
    fn master_legacy_folds_before_host_boundaries() {
        let mut substrate = fresh();
        let t = substrate.interner.intern("Clocked");
        let clocked = substrate.interner.intern("clocked");
        let current = substrate.interner.intern("level");
        let next = substrate.interner.intern("next_level");
        let mut attrs = rustc_hash::FxHashMap::default();
        attrs.insert(clocked, Value::Int(1));
        attrs.insert(current, Value::Int(9));
        attrs.insert(next, Value::Int(3));
        let n = substrate.add_node(t, attrs);

        let report = execute(&mut substrate, CyclePlan::MasterLegacy, 100, false, true, 1);
        assert_eq!(
            substrate.graph.node(n).attrs.get(&current),
            Some(&Value::Int(3))
        );
        assert_eq!(report.clock_commits, 1);
        let phases: Vec<_> = report.trace.iter().map(|e| e.phase).collect();
        assert_eq!(
            phases,
            vec![
                "clock_fold",
                "reflex_boundary",
                "thread_boundary",
                "result_fold_boundary"
            ]
        );
    }

    #[test]
    fn default_tick_uses_native_quantized_trajectory_feedback() {
        let mut substrate = fresh();
        let state = trajectory_state(&mut substrate, 1, 2);

        let report = execute(&mut substrate, CyclePlan::Default, 1, false, true, 1);
        let width = substrate.interner.intern("tangent_width");
        let adjustment = substrate.interner.intern("tangent_width_adjustment");
        assert_eq!(
            substrate.graph.node(state).attrs.get(&width),
            Some(&Value::Int(2))
        );
        assert_eq!(
            substrate.graph.node(state).attrs.get(&adjustment),
            Some(&Value::Int(1))
        );
        assert!(report
            .trace
            .iter()
            .any(|event| event.phase == "trajectory_quantized_feedback"));

        let deviation_key = substrate.interner.intern("deviation_count");
        substrate.set_attr(state, deviation_key, Value::Int(0));
        execute(&mut substrate, CyclePlan::Default, 1, false, false, 1);
        assert_eq!(
            substrate.graph.node(state).attrs.get(&width),
            Some(&Value::Int(1))
        );
    }

    #[test]
    fn dual_process_trace_commits_hard_sheet_before_trajectory_feedback() {
        let mut substrate = fresh();
        let policy_type = substrate.interner.intern("DualProcessPolicy");
        let enabled = substrate.interner.intern("enabled");
        let mut attrs = rustc_hash::FxHashMap::default();
        attrs.insert(enabled, Value::Int(1));
        substrate.add_node(policy_type, attrs);
        trajectory_state(&mut substrate, 0, 2);

        let report = execute(&mut substrate, CyclePlan::Default, 1, false, true, 1);
        let phases: Vec<_> = report.trace.iter().map(|event| event.phase).collect();
        assert_eq!(phases[0], "system_one_settle");
        assert_eq!(phases[1], "trajectory_quantized_feedback");
    }

    #[test]
    fn graph_cognitive_epoch_advances_each_strict_enabled_policy_once() {
        let mut substrate = fresh();
        let (policy, _) = supervised_process(&mut substrate, 3, Value::Int(1), 9);
        assert_eq!(advance_cognitive_epoch(&mut substrate), 1);
        let epoch = substrate.interner.intern("cognitive_epoch");
        assert_eq!(
            substrate.graph.node(policy).attrs.get(&epoch),
            Some(&Value::Int(4))
        );

        let enabled = substrate.interner.intern("enabled");
        substrate.set_attr(policy, enabled, Value::Float(2.0));
        assert_eq!(advance_cognitive_epoch(&mut substrate), 0);
        assert_eq!(
            substrate.graph.node(policy).attrs.get(&epoch),
            Some(&Value::Int(4))
        );
    }

    #[test]
    fn active_integer_process_lease_admits_and_exact_expiry_blocks() {
        let mut substrate = fresh();
        let (policy, process) = supervised_process(&mut substrate, 4, Value::Int(1), 5);
        let request = add_request(
            &mut substrate,
            Some((process, "continues_cognitive_process")),
            7,
        );
        let first = admit_system_two(&mut substrate);
        assert_eq!(first.admitted.len(), 1);
        assert_eq!(first.admitted[0].request, request);
        assert_eq!(first.lease_blocked, 0);

        let epoch = substrate.interner.intern("cognitive_epoch");
        substrate.set_attr(policy, epoch, Value::Int(5));
        let expired = admit_system_two(&mut substrate);
        assert!(expired.admitted.is_empty());
        assert_eq!(expired.lease_blocked, 1);
    }

    #[test]
    fn only_matching_checkin_can_cross_a_held_process_boundary() {
        let mut substrate = fresh();
        let (_, process) = supervised_process(&mut substrate, 8, Value::Int(0), 8);
        let continuation = add_request(
            &mut substrate,
            Some((process, "continues_cognitive_process")),
            7,
        );
        let checkin = add_request(
            &mut substrate,
            Some((process, "checks_cognitive_process")),
            7,
        );
        let admissions = admit_system_two(&mut substrate);
        assert_eq!(admissions.lease_blocked, 1);
        assert_eq!(admissions.admitted.len(), 1);
        assert_eq!(admissions.admitted[0].request, checkin);
        assert_ne!(admissions.admitted[0].request, continuation);
    }

    #[test]
    fn bound_float_authority_fails_closed_while_legacy_request_is_compatible() {
        let mut substrate = fresh();
        let (_, process) = supervised_process(&mut substrate, 1, Value::Float(1.0), 3);
        add_request(
            &mut substrate,
            Some((process, "continues_cognitive_process")),
            7,
        );
        let legacy = add_request(&mut substrate, None, 0);
        let admissions = admit_system_two(&mut substrate);
        assert_eq!(admissions.lease_blocked, 1);
        assert_eq!(admissions.admitted.len(), 1);
        assert_eq!(admissions.admitted[0].request, legacy);
    }

    #[test]
    fn terminal_checkin_is_retired_before_its_superseded_lease_is_blocked() {
        let mut substrate = fresh();
        let (_, process) = supervised_process(&mut substrate, 8, Value::Int(1), 12);
        let request = add_request(
            &mut substrate,
            Some((process, "checks_cognitive_process")),
            6,
        );
        let checkin_type = substrate.interner.intern("CognitiveCheckIn");
        let status = substrate.interner.intern("status");
        let continued = substrate.interner.intern("continued");
        let epoch = substrate.interner.intern("epoch");
        let input_epoch = substrate.interner.intern("input_epoch");
        let mut attrs = rustc_hash::FxHashMap::default();
        attrs.insert(status, Value::Str(continued));
        attrs.insert(epoch, Value::Int(8));
        let checkin = substrate.add_node(checkin_type, attrs);
        substrate.set_attr(request, input_epoch, Value::Int(8));
        add_edge(&mut substrate, request, "about_context", checkin);

        let admissions = admit_system_two(&mut substrate);

        assert!(admissions.admitted.is_empty());
        assert_eq!(admissions.stale, 1);
        assert_eq!(admissions.lease_blocked, 0);
        let stale = substrate.interner.intern("stale");
        assert_eq!(
            substrate.graph.node(request).attrs.get(&status),
            Some(&Value::Str(stale))
        );
    }

    #[test]
    fn identical_area_masks_form_one_parallel_settlement_group() {
        let mut substrate = fresh();
        let planning = substrate.interner.intern("planning");
        let reflection = substrate.interner.intern("reflection");
        let first = add_request(&mut substrate, None, 0);
        let second = add_request(&mut substrate, None, 0);
        let third = add_request(&mut substrate, None, 0);
        let admissions = vec![
            SystemTwoAdmission {
                request: first,
                areas: FxHashSet::from_iter([planning]),
                parallel_contexts: true,
            },
            SystemTwoAdmission {
                request: second,
                areas: FxHashSet::from_iter([planning]),
                parallel_contexts: true,
            },
            SystemTwoAdmission {
                request: third,
                areas: FxHashSet::from_iter([reflection]),
                parallel_contexts: true,
            },
        ];

        let groups = group_system_two_admissions(&admissions);

        assert_eq!(groups.len(), 2);
        assert_eq!(groups[0].requests, vec![first, second]);
        assert_eq!(groups[0].areas, FxHashSet::from_iter([planning]));
        assert_eq!(groups[1].requests, vec![third]);
        assert_eq!(groups[1].areas, FxHashSet::from_iter([reflection]));
    }
}
