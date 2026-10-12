//! Native, bounded P2 graph construction shared by the worker and evaluator.
//!
//! This module deliberately accepts only a signed-envelope shaped public graph.
//! Transition witnesses and predictions are produced here from graph mechanics;
//! they are never accepted from the caller as evidence.
use crate::p2_bounded::{
    revise_belief, select_all_actions, simulate_one_action, CounterfactualPrediction, P2Bounds,
    P2Terminal, WorldModelAction, WorldModelObservation,
};
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;

const MAX_ACTIONS: usize = 4;
const MAX_NODES: usize = 8;
const BP: u16 = 10_000;

#[derive(Clone, Debug, PartialEq, Eq)]
struct Binding {
    action_id: String,
    node_id: String,
    effect: String,
    cost: u32,
}

fn text(v: Option<&Value>) -> Result<String, String> {
    v.and_then(Value::as_str)
        .filter(|s| !s.is_empty() && s.len() <= 256)
        .map(ToOwned::to_owned)
        .ok_or_else(|| "invalid graph text".into())
}
fn strings(v: Option<&Value>, max: usize) -> Result<Vec<String>, String> {
    let a = v
        .and_then(Value::as_array)
        .ok_or_else(|| "missing graph array".to_string())?;
    if a.is_empty() || a.len() > max {
        return Err("graph bound".into());
    }
    let out: Result<Vec<_>, _> = a.iter().map(|x| text(Some(x))).collect();
    let out = out?;
    if out.iter().collect::<BTreeSet<_>>().len() != out.len() {
        return Err("duplicate graph identifier".into());
    }
    Ok(out)
}
/// A small self-contained SHA-256 implementation avoids a runtime dependency
/// or network fetch in the sealed release image.
pub fn sha256_hex(bytes: &[u8]) -> String {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut msg = bytes.to_vec();
    let bit_len = (msg.len() as u64).wrapping_mul(8);
    msg.push(0x80);
    while msg.len() % 64 != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bit_len.to_be_bytes());
    let mut h = [
        0x6a09e667u32,
        0xbb67ae85,
        0x3c6ef372,
        0xa54ff53a,
        0x510e527f,
        0x9b05688c,
        0x1f83d9ab,
        0x5be0cd19,
    ];
    for chunk in msg.chunks_exact(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes(chunk[i * 4..i * 4 + 4].try_into().unwrap());
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let t1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }
    let mut out = String::from("sha256:");
    for x in h {
        out.push_str(&format!("{x:08x}"));
    }
    out
}
/// Render the finite P2 protocol value exactly as the evaluator's canonical
/// JSON contract does: sorted object keys, compact UTF-8 JSON, and no floats.
/// This is intentionally local so the native sealed runtime has no parser or
/// serializer dependency beyond serde_json already linked into the binary.
fn canonical_bytes(value: &Value) -> Result<Vec<u8>, String> {
    fn render(value: &Value, out: &mut String) -> Result<(), String> {
        match value {
            Value::Null | Value::Bool(_) | Value::String(_) => out.push_str(
                &serde_json::to_string(value).map_err(|_| "canonical scalar".to_string())?,
            ),
            Value::Number(number) => {
                if !(number.is_i64() || number.is_u64()) {
                    return Err("canonical float".into());
                }
                out.push_str(&number.to_string());
            }
            Value::Array(items) => {
                out.push('[');
                for (index, item) in items.iter().enumerate() {
                    if index != 0 {
                        out.push(',');
                    }
                    render(item, out)?;
                }
                out.push(']');
            }
            Value::Object(items) => {
                out.push('{');
                let mut keys: Vec<_> = items.keys().collect();
                keys.sort_unstable();
                for (index, key) in keys.iter().enumerate() {
                    if index != 0 {
                        out.push(',');
                    }
                    out.push_str(
                        &serde_json::to_string(*key).map_err(|_| "canonical key".to_string())?,
                    );
                    out.push(':');
                    render(&items[*key], out)?;
                }
                out.push('}');
            }
        }
        Ok(())
    }

    let mut output = String::new();
    render(value, &mut output)?;
    Ok(output.into_bytes())
}

fn digest(v: &Value) -> String {
    // Every caller only supplies protocol-shaped finite JSON.  A failure here
    // is a programmer error; untrusted request values are rejected through
    // `locked_envelope_digest` before they can reach reconstruction.
    sha256_hex(&canonical_bytes(v).expect("canonical protocol value"))
}

/// Bind a native frame to the sealed artifact identity before any graph work.
/// The frame's `verified_input_digest` is the evaluator-locked digest; it is
/// not an attestation the native side may merely copy.  Recomputing from the
/// received envelope also makes key order and whitespace immaterial while
/// rejecting every alternate canonical envelope.
pub fn canonical_envelope_digest(envelope: &Value) -> Result<String, String> {
    Ok(sha256_hex(&canonical_bytes(envelope)?))
}

fn locked_envelope_digest(request: &Value, envelope: &Value) -> Result<String, String> {
    let locked_digest = verified_input_digest(request)?;
    let received_digest = canonical_envelope_digest(envelope)?;
    if received_digest != locked_digest {
        return Err("sealed input digest mismatch".into());
    }
    Ok(locked_digest)
}

fn graph(
    envelope: &Value,
) -> Result<(Vec<String>, Vec<String>, Vec<String>, Vec<Binding>, u32), String> {
    if envelope.get("schema").and_then(Value::as_str) != Some("P2ObservationEnvelopeV1") {
        return Err("envelope schema".into());
    }
    let actions = strings(envelope.get("legal_action_ids"), MAX_ACTIONS)?;
    let obs = strings(envelope.get("observation_atoms"), MAX_NODES)?;
    let goals = strings(envelope.get("goal_atoms"), MAX_NODES)?;
    let maximum_intervention = envelope
        .get("cost_bounds")
        .and_then(Value::as_object)
        .filter(|bounds| bounds.len() == 1)
        .and_then(|bounds| bounds.get("maximum_intervention"))
        .and_then(Value::as_u64)
        .filter(|cost| *cost <= 1_000_000)
        .ok_or_else(|| "maximum intervention".to_string())? as u32;
    let bundle = envelope
        .get("training_bundle")
        .and_then(Value::as_object)
        .ok_or_else(|| "public graph absent".to_string())?;
    if bundle.get("schema").and_then(Value::as_str) != Some("P2PublicGraphV1") {
        return Err("sealed public graph required".into());
    }
    let raw = bundle
        .get("action_bindings")
        .and_then(Value::as_array)
        .ok_or_else(|| "bindings absent".to_string())?;
    if raw.len() != actions.len() {
        return Err("binding completeness".into());
    }
    let mut bindings = Vec::new();
    for item in raw {
        let o = item
            .as_object()
            .ok_or_else(|| "binding object".to_string())?;
        let action_id = text(o.get("action_id"))?;
        let node_id = text(o.get("node_id"))?;
        let effect = text(o.get("effect"))?;
        if !matches!(
            effect.as_str(),
            "advance" | "hold" | "unsafe" | "stale" | "correlated"
        ) {
            return Err("unknown sealed transition".into());
        }
        let cost = o
            .get("cost")
            .and_then(Value::as_u64)
            .filter(|x| *x <= 1_000_000)
            .ok_or_else(|| "binding cost".to_string())? as u32;
        bindings.push(Binding {
            action_id,
            node_id,
            effect,
            cost,
        });
    }
    if bindings
        .iter()
        .map(|b| &b.action_id)
        .collect::<BTreeSet<_>>()
        != actions.iter().collect()
        || bindings
            .iter()
            .map(|b| &b.node_id)
            .collect::<BTreeSet<_>>()
            .len()
            != bindings.len()
    {
        return Err("binding graph identity".into());
    }
    Ok((actions, obs, goals, bindings, maximum_intervention))
}
fn distribution(obs: &[String], confidence: u16) -> Value {
    let mut result = Map::new();
    let rest = BP - confidence;
    let n = (obs.len() - 1) as u16;
    for (i, atom) in obs.iter().enumerate() {
        result.insert(
            atom.clone(),
            Value::from(if i == 0 {
                confidence
            } else {
                rest / n + if (i as u16) <= rest % n { 1 } else { 0 }
            }),
        );
    }
    Value::Object(result)
}
fn make_prediction(
    envelope: &Value,
    binding: &Binding,
    obs: &[String],
    goals: &[String],
    maximum_intervention: u32,
) -> Value {
    let epoch = envelope.get("step").and_then(Value::as_u64).unwrap_or(0);
    let belief =
        json!({"kind":"BeliefState","epoch":epoch,"observations":envelope["observation_atoms"]});
    let source = digest(&belief);
    let witness = digest(
        &json!({"kind":"SealedTransition","node_id":binding.node_id,"effect":binding.effect,"epoch":epoch}),
    );
    let (status, conf, predicted, support, resolved, loss) = match binding.effect.as_str() {
        "advance" => ("predicted", 9000, goals.to_vec(), true, true, 0),
        "hold" => ("predicted", 6000, Vec::new(), true, true, 0),
        "unsafe" => ("infeasible", 0, Vec::new(), false, false, 1),
        "stale" => ("unestablished", 0, Vec::new(), false, false, 1),
        _ => ("unestablished", 0, Vec::new(), false, false, 1),
    };
    let (status, conf, predicted, support, resolved, loss) = if binding.cost > maximum_intervention
    {
        ("infeasible", 0, Vec::new(), false, false, 1)
    } else {
        (status, conf, predicted, support, resolved, loss)
    };
    // `goal_probability_bp` is intentionally distinct from confidence in the
    // bounded selector contract. In this finite graph, a predicted complete
    // goal set has the same graph-derived o0 probability as its confidence;
    // incomplete/terminal failures have no goal probability.
    let goal_probability = if !predicted.is_empty() { conf } else { 0 };
    json!({"action_id":binding.action_id,"source_belief_digest":source,"transition_witness_digests":[witness],"trajectory_export":{"nodes":[{"kind":"WorldModelAction","node_id":binding.node_id},{"kind":"SimulationRequest","horizon":1,"branching":1},{"kind":"PredictionTrajectory","depth":1},{"kind":"PredictedBeliefState","provenance":"imagined"}]},"outcome_basis_points":distribution(obs, conf),"predicted_goal_atoms":predicted,"intervention_cost":binding.cost,"manifold":{"support":support,"resolved":resolved,"loss":loss,"information_loss":loss,"earliest_decisive_tick":1},"goal_probability_bp":goal_probability,"confidence_bp":conf,"uncertainty_bp":BP-conf,"terminal_status":status})
}
/// Adapt sealed JSON predictions into the declared bounded future-manifold
/// selector. This is the only action-selection implementation on the native
/// worker/evaluator path: exported selection fields are a projection of
/// `select_all_actions`, never a second local comparator.
fn select(
    predictions: &[Value],
    actions: &[String],
    goals: &[String],
    outcome_atoms: usize,
    maximum_intervention: u32,
) -> Result<Value, String> {
    let mut bounded_predictions = Vec::with_capacity(predictions.len());
    for prediction in predictions {
        let manifold = prediction
            .get("manifold")
            .and_then(Value::as_object)
            .ok_or_else(|| "selection manifold".to_string())?;
        let outcome = prediction
            .get("outcome_basis_points")
            .and_then(Value::as_object)
            .ok_or_else(|| "selection outcome".to_string())?;
        let outcome_basis_points: Result<Vec<u16>, String> = outcome
            .values()
            .map(|value| {
                value
                    .as_u64()
                    .filter(|value| *value <= BP as u64)
                    .map(|value| value as u16)
                    .ok_or_else(|| "selection outcome".to_string())
            })
            .collect();
        let predicted_goals = prediction
            .get("predicted_goal_atoms")
            .and_then(Value::as_array)
            .ok_or_else(|| "selection goals".to_string())?
            .iter()
            .map(Value::as_str)
            .collect::<Option<BTreeSet<_>>>()
            .ok_or_else(|| "selection goals".to_string())?;
        let terminal = match prediction.get("terminal_status").and_then(Value::as_str) {
            Some("predicted") => P2Terminal::Predicted,
            Some("unestablished") => P2Terminal::Unestablished,
            Some("infeasible") => P2Terminal::Infeasible,
            _ => return Err("selection terminal".into()),
        };
        bounded_predictions.push(CounterfactualPrediction {
            action_id: text(prediction.get("action_id"))?,
            source_belief_digest: text(prediction.get("source_belief_digest"))?,
            transition_witness_digests: prediction
                .get("transition_witness_digests")
                .and_then(Value::as_array)
                .ok_or_else(|| "selection witness".to_string())?
                .iter()
                .map(|value| text(Some(value)))
                .collect::<Result<Vec<_>, _>>()?,
            trajectory_nodes: prediction["trajectory_export"]["nodes"]
                .as_array()
                .map(Vec::len)
                .filter(|count| *count <= MAX_NODES)
                .ok_or_else(|| "selection trajectory".to_string())?,
            outcome_basis_points: outcome_basis_points?,
            all_goals_predicted: predicted_goals == goals.iter().map(String::as_str).collect(),
            intervention_cost: prediction
                .get("intervention_cost")
                .and_then(Value::as_u64)
                .filter(|value| *value <= u32::MAX as u64)
                .ok_or_else(|| "selection cost".to_string())? as u32,
            manifold_support: manifold
                .get("support")
                .and_then(Value::as_bool)
                .ok_or_else(|| "selection manifold".to_string())?,
            manifold_resolved: manifold
                .get("resolved")
                .and_then(Value::as_bool)
                .ok_or_else(|| "selection manifold".to_string())?,
            manifold_loss: manifold
                .get("loss")
                .and_then(Value::as_u64)
                .filter(|value| *value <= u16::MAX as u64)
                .ok_or_else(|| "selection manifold".to_string())? as u16,
            manifold_information_loss: manifold
                .get("information_loss")
                .and_then(Value::as_u64)
                .filter(|value| *value <= u16::MAX as u64)
                .ok_or_else(|| "selection manifold".to_string())?
                as u16,
            goal_probability_bp: prediction
                .get("goal_probability_bp")
                .and_then(Value::as_u64)
                .filter(|value| *value <= BP as u64)
                .ok_or_else(|| "selection goal probability".to_string())?
                as u16,
            confidence_bp: prediction
                .get("confidence_bp")
                .and_then(Value::as_u64)
                .filter(|value| *value <= BP as u64)
                .ok_or_else(|| "selection confidence".to_string())?
                as u16,
            uncertainty_bp: prediction
                .get("uncertainty_bp")
                .and_then(Value::as_u64)
                .filter(|value| *value <= BP as u64)
                .ok_or_else(|| "selection uncertainty".to_string())?
                as u16,
            terminal,
        });
    }
    let bounded = select_all_actions(
        &P2Bounds {
            horizon: 1,
            branching: 1,
            action_count: actions.len(),
            nodes_per_action: MAX_NODES,
        },
        actions,
        &bounded_predictions,
        outcome_atoms,
        maximum_intervention,
    );
    let selected = if bounded.terminal == P2Terminal::Predicted && bounded.native_tie_set.len() == 1
    {
        Value::String(bounded.native_tie_set[0].clone())
    } else {
        Value::Null
    };
    let classification = match bounded.terminal {
        P2Terminal::Predicted if bounded.native_tie_set.len() == 1 => "selected",
        P2Terminal::Predicted => "sealed_enactment_rank_required",
        P2Terminal::Unestablished => "no_goal_satisfying_candidate",
        _ => "protocol_error",
    };
    Ok(json!({
        "selected_action_id": selected,
        "classification": classification,
        "selection_path": "P2BoundedFutureManifoldV1",
        "feasible_action_ids": bounded.feasible,
        "minimal_action_ids": bounded.minimal,
        "native_tie_set": bounded.native_tie_set,
    }))
}

fn verified_input_digest(request: &Value) -> Result<String, String> {
    request
        .get("verified_input_digest")
        .and_then(Value::as_str)
        .filter(|digest| {
            digest.len() == 71
                && digest.starts_with("sha256:")
                && digest[7..].bytes().all(|byte| byte.is_ascii_hexdigit())
        })
        .map(ToOwned::to_owned)
        .ok_or_else(|| "verified input digest".to_string())
}

pub fn worker_failure_reason(error: &str) -> &'static str {
    match error {
        "worker schema" | "envelope absent" | "verified input digest" => "request_schema_invalid",
        "sealed input digest mismatch" => "sealed_digest_mismatch",
        "belief revision" | "one-step graph simulation" => "bounded_simulation_failed",
        "missing epoch" => "sealed_graph_invalid",
        _ if error.starts_with("envelope")
            || error.starts_with("graph")
            || error.starts_with("binding")
            || error.starts_with("public graph")
            || error.starts_with("unknown sealed")
            || error.starts_with("maximum intervention")
            || error.starts_with("invalid graph")
            || error.starts_with("duplicate graph") =>
        {
            "sealed_graph_invalid"
        }
        _ => "unknown_native_failure",
    }
}

/// Accept only the evaluator-framed sealed envelope and copy its verified
/// artifact digest into the proposal. The worker never derives this binding.
pub fn worker_reply(request: Value) -> Result<Value, String> {
    if request.get("schema").and_then(Value::as_str) != Some("P2NativeWorkerRequestV1") {
        return Err("worker schema".into());
    }
    let envelope = request
        .get("envelope")
        .cloned()
        .ok_or_else(|| "envelope absent".to_string())?;
    let verified_input_digest = locked_envelope_digest(&request, &envelope)?;
    let (actions, obs, goals, bindings, maximum_intervention) = graph(&envelope)?;
    let epoch = envelope
        .get("step")
        .and_then(Value::as_u64)
        .ok_or_else(|| "missing epoch".to_string())?;
    let observation = WorldModelObservation {
        epoch,
        public_atoms: obs.clone(),
        confidence_bp: 9_000,
        uncertainty_bp: 1_000,
    };
    let belief = revise_belief(
        None,
        &observation,
        digest(&json!({"kind":"WorldModelObservation","epoch":epoch,"observations":&obs})),
    )
    .map_err(|_| "belief revision".to_string())?;
    let bounds = P2Bounds {
        horizon: 1,
        branching: 1,
        action_count: actions.len(),
        nodes_per_action: MAX_NODES,
    };
    for binding in &bindings {
        let witness = digest(
            &json!({"kind":"SealedTransition","node_id":binding.node_id,"effect":binding.effect,"epoch":epoch}),
        );
        simulate_one_action(
            &bounds,
            &belief,
            WorldModelAction {
                action_id: binding.action_id.clone(),
                legal: true,
            },
            vec![witness],
        )
        .map_err(|_| "one-step graph simulation".to_string())?;
    }
    let predictions: Vec<Value> = bindings
        .iter()
        .map(|b| make_prediction(&envelope, b, &obs, &goals, maximum_intervention))
        .collect();
    let selection = select(
        &predictions,
        &actions,
        &goals,
        obs.len(),
        maximum_intervention,
    )?;
    let mut proposal = json!({"schema":"P2NativePlanProposalV1","run_id":text(envelope.get("run_id"))?,"episode_id":text(envelope.get("episode_id"))?,"envelope_digest":verified_input_digest.clone(),"verified_input_digest":verified_input_digest,"predictions":predictions,"selection":selection});
    let d = digest(&proposal);
    proposal
        .as_object_mut()
        .unwrap()
        .insert("proposal_digest".into(), Value::String(d));
    Ok(proposal)
}

fn metric(
    predictions: &[Value],
    bindings: &[Binding],
    selected: Option<&str>,
    maximum_intervention: u32,
) -> Value {
    let mut squared = 0u64;
    let mut total = 0u64;
    let mut calibration = 0u64;
    let mut feasible = 0u64;
    let mut minimal = 0u64;
    let mut safe = 0u64;
    for p in predictions {
        let b = bindings
            .iter()
            .find(|b| Some(b.action_id.as_str()) == p.get("action_id").and_then(Value::as_str))
            .unwrap();
        for bp in p["outcome_basis_points"].as_object().unwrap().values() {
            let q = bp.as_u64().unwrap();
            let y = if b.effect == "advance" && q >= 7_500 {
                10_000u64
            } else {
                0
            };
            squared += (q as i64 - y as i64).unsigned_abs().pow(2);
            total += 1;
            calibration += (q as i64 - y as i64).unsigned_abs();
        }
        if b.effect == "advance" && b.cost <= maximum_intervention {
            feasible += 1;
        }
        if selected == Some(b.action_id.as_str())
            && b.effect == "advance"
            && b.cost <= maximum_intervention
        {
            minimal = 1;
        }
        if b.effect != "unsafe" {
            safe += 1;
        }
    }
    let denom = (total * 100_000_000).max(1);
    let brier = 1000u64.saturating_sub(squared * 1000 / denom);
    let ece = calibration * 1000 / (total * 10_000).max(1);
    json!({"brier_milli":brier,"ece_milli":ece,"feasibility_milli":feasible*1000/bindings.len() as u64,"minimality_milli":minimal*1000,"safety_milli":safe*1000/bindings.len() as u64,"abstention_milli":if selected.is_none(){1000}else{0}})
}

/// Reconstruct and score evaluator-owned one-step clones from the sealed
/// envelope before inspecting the worker reply.  This deliberately does not
/// call `worker_reply`: a worker defect must not become evaluator truth.
fn evaluator_plan(
    envelope: &Value,
    verified_input_digest: &str,
) -> Result<(Value, Vec<Binding>, u32), String> {
    let (actions, obs, goals, bindings, maximum_intervention) = graph(envelope)?;
    let epoch = envelope
        .get("step")
        .and_then(Value::as_u64)
        .ok_or_else(|| "missing epoch".to_string())?;
    let observation = WorldModelObservation {
        epoch,
        public_atoms: obs.clone(),
        confidence_bp: 9_000,
        uncertainty_bp: 1_000,
    };
    let belief = revise_belief(
        None,
        &observation,
        digest(&json!({"kind":"WorldModelObservation","epoch":epoch,"observations":&obs})),
    )
    .map_err(|_| "belief revision".to_string())?;
    let bounds = P2Bounds {
        horizon: 1,
        branching: 1,
        action_count: actions.len(),
        nodes_per_action: MAX_NODES,
    };
    for binding in &bindings {
        let witness = digest(
            &json!({"kind":"SealedTransition","node_id":binding.node_id,"effect":binding.effect,"epoch":epoch}),
        );
        simulate_one_action(
            &bounds,
            &belief,
            WorldModelAction {
                action_id: binding.action_id.clone(),
                legal: true,
            },
            vec![witness],
        )
        .map_err(|_| "one-step graph simulation".to_string())?;
    }
    let predictions: Vec<Value> = bindings
        .iter()
        .map(|b| make_prediction(envelope, b, &obs, &goals, maximum_intervention))
        .collect();
    let selection = select(
        &predictions,
        &actions,
        &goals,
        obs.len(),
        maximum_intervention,
    )?;
    let mut expected = json!({"schema":"P2NativePlanProposalV1","run_id":text(envelope.get("run_id"))?,"episode_id":text(envelope.get("episode_id"))?,"envelope_digest":verified_input_digest,"verified_input_digest":verified_input_digest,"predictions":predictions,"selection":selection});
    let proposal_digest = digest(&expected);
    expected
        .as_object_mut()
        .unwrap()
        .insert("proposal_digest".into(), Value::String(proposal_digest));
    Ok((expected, bindings, maximum_intervention))
}

/// Score authoritative clones before treating the worker's reply as an
/// untrusted consistency check. A mismatch preserves the authoritative score
/// in the response so the evaluator can receipt the scored failure.
pub fn evaluator_reply(request: Value) -> Result<Value, String> {
    if request.get("schema").and_then(Value::as_str) != Some("P2NativeEvaluationRequestV1") {
        return Err("evaluation schema".into());
    }
    let envelope = request
        .get("envelope")
        .cloned()
        .ok_or_else(|| "envelope absent".to_string())?;
    let verified_input_digest = locked_envelope_digest(&request, &envelope)?;
    let proposal = request
        .get("proposal")
        .cloned()
        .ok_or_else(|| "proposal absent".to_string())?;
    let (expected, bindings, maximum_intervention) =
        evaluator_plan(&envelope, &verified_input_digest)?;
    let predictions = expected["predictions"]
        .as_array()
        .ok_or_else(|| "evaluator predictions".to_string())?;
    let selected = expected["selection"]["selected_action_id"].as_str();
    let scores = metric(predictions, &bindings, selected, maximum_intervention);
    let matched = proposal == expected;
    Ok(
        json!({"accepted":matched,"classification":if matched {"accepted"} else {"worker_mismatch"},"selected_action_id":selected,"metrics":scores,"clone_count":bindings.len(),"verified_input_digest":verified_input_digest,"reconstruction_digest":digest(&expected)}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    fn frame_digest(envelope: &Value) -> String {
        sha256_hex(&canonical_bytes(envelope).unwrap())
    }
    fn envelope(actions: Vec<&str>, bindings: Vec<Value>) -> Value {
        json!({"schema":"P2ObservationEnvelopeV1","run_id":"r","episode_id":"e","step":0,"observation_atoms":["o0","o1"],"legal_action_ids":actions,"goal_atoms":["g"],"cost_bounds":{"maximum_intervention":1},"training_bundle":{"schema":"P2PublicGraphV1","action_bindings":bindings}})
    }
    fn worker_request(envelope: Value) -> Value {
        let digest = frame_digest(&envelope);
        json!({"schema":"P2NativeWorkerRequestV1","envelope":envelope,"verified_input_digest":digest})
    }
    fn evaluator_request(envelope: Value, proposal: Value) -> Value {
        let digest = frame_digest(&envelope);
        json!({"schema":"P2NativeEvaluationRequestV1","envelope":envelope,"proposal":proposal,"verified_input_digest":digest})
    }
    #[test]
    fn sha256_is_standard() {
        assert_eq!(
            sha256_hex(b"abc"),
            "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }
    #[test]
    fn mechanics_control_real_transition_and_not_submitted_witnesses() {
        let p = worker_reply(worker_request(envelope(
            vec!["a", "b"],
            vec![
                json!({"action_id":"a","node_id":"n0","effect":"advance","cost":1}),
                json!({"action_id":"b","node_id":"n1","effect":"correlated","cost":0}),
            ],
        )))
        .unwrap();
        assert_eq!(p["selection"]["selected_action_id"], "a");
        assert_eq!(p["predictions"][1]["terminal_status"], "unestablished");
        let expected_digest = frame_digest(&envelope(
            vec!["a", "b"],
            vec![
                json!({"action_id":"a","node_id":"n0","effect":"advance","cost":1}),
                json!({"action_id":"b","node_id":"n1","effect":"correlated","cost":0}),
            ],
        ));
        assert_eq!(p["verified_input_digest"], expected_digest);
        assert_eq!(p["envelope_digest"], expected_digest);
    }
    #[test]
    fn evaluator_scores_authoritative_clones_before_worker_mismatch() {
        let env = envelope(
            vec!["a", "b"],
            vec![
                json!({"action_id":"a","node_id":"n0","effect":"advance","cost":1}),
                json!({"action_id":"b","node_id":"n1","effect":"unsafe","cost":0}),
            ],
        );
        let mut worker = worker_reply(worker_request(env.clone())).unwrap();
        worker["selection"]["selected_action_id"] = Value::String("b".into());
        let scored = evaluator_reply(evaluator_request(env, worker)).unwrap();
        assert_eq!(scored["accepted"], false);
        assert_eq!(scored["classification"], "worker_mismatch");
        assert_eq!(scored["clone_count"], 2);
        assert_eq!(scored["metrics"]["feasibility_milli"], 500);
        assert_eq!(
            scored["verified_input_digest"],
            frame_digest(&envelope(
                vec!["a", "b"],
                vec![
                    json!({"action_id":"a","node_id":"n0","effect":"advance","cost":1}),
                    json!({"action_id":"b","node_id":"n1","effect":"unsafe","cost":0}),
                ],
            ))
        );
        assert!(scored["reconstruction_digest"]
            .as_str()
            .unwrap()
            .starts_with("sha256:"));
    }
    #[test]
    fn maximum_intervention_excludes_over_budget_actions_in_worker_and_evaluator() {
        let mut env = envelope(
            vec!["over", "within"],
            vec![
                json!({"action_id":"over","node_id":"n0","effect":"advance","cost":2}),
                json!({"action_id":"within","node_id":"n1","effect":"advance","cost":1}),
            ],
        );
        let worker = worker_reply(worker_request(env.clone())).unwrap();
        assert_eq!(worker["selection"]["selected_action_id"], "within");
        assert_eq!(worker["predictions"][0]["terminal_status"], "infeasible");
        let scored = evaluator_reply(evaluator_request(env.clone(), worker)).unwrap();
        assert_eq!(scored["accepted"], true);
        assert_eq!(scored["selected_action_id"], "within");
        assert_eq!(scored["metrics"]["feasibility_milli"], 500);
        env["cost_bounds"]["maximum_intervention"] = Value::from(0);
        let worker = worker_reply(worker_request(env.clone())).unwrap();
        assert!(worker["selection"]["selected_action_id"].is_null());
        let scored = evaluator_reply(evaluator_request(env, worker)).unwrap();
        assert_eq!(scored["accepted"], true);
        assert!(scored["selected_action_id"].is_null());
        assert_eq!(scored["metrics"]["feasibility_milli"], 0);
        assert_eq!(scored["metrics"]["abstention_milli"], 1000);
    }
    #[test]
    fn rejects_missing_or_mismatched_verified_input_digest_before_reconstruction() {
        let env = envelope(
            vec!["a"],
            vec![json!({"action_id":"a","node_id":"n0","effect":"advance","cost":1})],
        );
        assert!(worker_reply(env.clone()).is_err());
        let mut mismatched_worker = worker_request(env.clone());
        mismatched_worker["verified_input_digest"] = Value::String(
            "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".into(),
        );
        assert!(worker_reply(mismatched_worker).is_err());
        let proposal = worker_reply(worker_request(env.clone())).unwrap();
        let request = json!({"schema":"P2NativeEvaluationRequestV1","envelope":env,"proposal":proposal,"verified_input_digest":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"});
        assert!(evaluator_reply(request).is_err());
    }
    #[test]
    fn canonical_envelope_digest_is_independent_of_received_key_order() {
        let received: Value = serde_json::from_str(r#"{"training_bundle":{"action_bindings":[{"effect":"advance","cost":1,"node_id":"n0","action_id":"a"}],"schema":"P2PublicGraphV1"},"goal_atoms":["g"],"legal_action_ids":["a"],"observation_atoms":["o0","o1"],"step":0,"episode_id":"e","run_id":"r","cost_bounds":{"maximum_intervention":1},"schema":"P2ObservationEnvelopeV1"}"#).unwrap();
        let ordered = envelope(
            vec!["a"],
            vec![json!({"action_id":"a","node_id":"n0","effect":"advance","cost":1})],
        );
        assert_eq!(frame_digest(&received), frame_digest(&ordered));
        assert!(worker_reply(json!({"schema":"P2NativeWorkerRequestV1","envelope":received,"verified_input_digest":frame_digest(&ordered)})).is_ok());
    }
}

#[cfg(test)]
mod selection_route_tests {
    use super::*;

    #[test]
    fn bounded_future_manifold_path_is_the_only_order_and_label_invariant_selector() {
        for reverse_labels in [false, true] {
            for reverse_bindings in [false, true] {
                let mut labels = vec!["opaque_low", "opaque_high"];
                if reverse_labels {
                    labels.reverse();
                }
                let mut bindings = vec![
                    json!({"action_id":labels[0],"node_id":"n0","effect":"advance","cost":1}),
                    json!({"action_id":labels[1],"node_id":"n1","effect":"advance","cost":2}),
                ];
                if reverse_bindings {
                    bindings.reverse();
                }
                let env = json!({
                    "schema":"P2ObservationEnvelopeV1","run_id":"r","episode_id":"e","step":0,
                    "observation_atoms":["o0","o1"],"legal_action_ids":labels,"goal_atoms":["g"],
                    "cost_bounds":{"maximum_intervention":2},
                    "training_bundle":{"schema":"P2PublicGraphV1","action_bindings":bindings}
                });
                let request = json!({"schema":"P2NativeWorkerRequestV1","verified_input_digest":canonical_envelope_digest(&env).unwrap(),"envelope":env});
                let proposal = worker_reply(request).unwrap();
                let selection = &proposal["selection"];
                assert_eq!(selection["selection_path"], "P2BoundedFutureManifoldV1");
                assert_eq!(
                    selection["selected_action_id"],
                    proposal["predictions"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .find(|prediction| prediction["intervention_cost"] == 1)
                        .unwrap()["action_id"]
                );
                assert_eq!(selection["minimal_action_ids"].as_array().unwrap().len(), 1);
                assert_eq!(selection["native_tie_set"].as_array().unwrap().len(), 1);
            }
        }
    }
}
