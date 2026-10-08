//! Executable-boundary regressions for the sealed input digest contract.
//! These tests deliberately launch the native programs rather than calling the
//! library API, so a future stdin framing change cannot restore digest copying.
use serde_json::{json, Value};
use std::io::Write;
use std::process::{Command, Stdio};
use substrate_rs::p2_native::canonical_envelope_digest;

fn envelope() -> Value {
    json!({
        "schema":"P2ObservationEnvelopeV1",
        "run_id":"r",
        "episode_id":"e",
        "step":0,
        "observation_atoms":["o0","o1"],
        "legal_action_ids":["a"],
        "goal_atoms":["g"],
        "cost_bounds":{"maximum_intervention":1},
        "training_bundle":{"schema":"P2PublicGraphV1","action_bindings":[
            {"action_id":"a","node_id":"n0","effect":"advance","cost":1}
        ]}
    })
}

fn run(binary: &str, request: Value) -> std::process::Output {
    let mut child = Command::new(binary)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("native binary must launch");
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(request.to_string().as_bytes())
        .unwrap();
    child.wait_with_output().unwrap()
}

#[test]
fn worker_binary_rejects_alternate_envelope_before_planning() {
    let request = json!({
        "schema":"P2NativeWorkerRequestV1",
        "envelope":envelope(),
        "verified_input_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    });
    let output = run(env!("CARGO_BIN_EXE_p2_native_worker"), request);
    assert!(
        !output.status.success(),
        "worker accepted an envelope not matching its locked digest"
    );
}

#[test]
fn evaluator_binary_rejects_alternate_envelope_before_scoring() {
    let request = json!({
        "schema":"P2NativeEvaluationRequestV1",
        "envelope":envelope(),
        "proposal":{},
        "verified_input_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    });
    let output = run(env!("CARGO_BIN_EXE_p2_evaluator"), request);
    assert!(
        !output.status.success(),
        "evaluator reached scoring for an alternate envelope"
    );
}

#[test]
fn native_worker_to_evaluator_round_trip_requires_the_measured_envelope_digest() {
    let sealed = envelope();
    let locked_digest = canonical_envelope_digest(&sealed).unwrap();
    let worker = run(
        env!("CARGO_BIN_EXE_p2_native_worker"),
        json!({
            "schema":"P2NativeWorkerRequestV1",
            "envelope":sealed,
            "verified_input_digest":locked_digest
        }),
    );
    assert!(
        worker.status.success(),
        "worker rejected its own measured sealed envelope"
    );
    let proposal: Value = serde_json::from_slice(&worker.stdout).unwrap();
    let sealed = envelope();
    let evaluator = run(
        env!("CARGO_BIN_EXE_p2_evaluator"),
        json!({
            "schema":"P2NativeEvaluationRequestV1",
            "envelope":sealed,
            "proposal":proposal,
            "verified_input_digest":canonical_envelope_digest(&envelope()).unwrap()
        }),
    );
    assert!(
        evaluator.status.success(),
        "evaluator rejected the locked native proposal"
    );
    let scored: Value = serde_json::from_slice(&evaluator.stdout).unwrap();
    assert_eq!(scored["accepted"], true);
}

#[test]
fn worker_binary_returns_only_fixed_diagnostic_for_preplan_digest_failure() {
    let request = json!({
        "schema":"P2NativeWorkerRequestV1", "envelope":envelope(),
        "verified_input_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    });
    let output = run(env!("CARGO_BIN_EXE_p2_native_worker"), request);
    assert!(!output.status.success());
    let diagnostic: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(
        diagnostic,
        json!({
            "schema":"P2NativeWorkerDiagnosticV1", "status":"unestablished",
            "reason_code":"sealed_digest_mismatch"
        })
    );
}

#[test]
fn worker_binary_runtime_probe_has_no_context_or_filesystem_oracle() {
    let output = run(
        env!("CARGO_BIN_EXE_p2_native_worker"),
        json!({
            "schema":"P2NativeRuntimeProbeV1", "nonce":"p2-native-runtime-probe-v1"
        }),
    );
    assert!(output.status.success());
    let reply: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(
        reply,
        json!({
            "schema":"P2NativeRuntimeProbeReplyV1", "status":"ready", "abi":"p2-native-v1"
        })
    );
}

#[test]
fn worker_binary_proves_bounded_selection_route_under_label_and_order_controls() {
    for reverse_labels in [false, true] {
        for reverse_bindings in [false, true] {
            let mut labels = vec!["opaque-low", "opaque-high"];
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
            let sealed = json!({
                "schema":"P2ObservationEnvelopeV1", "run_id":"route-control", "episode_id":"route-control",
                "step":0, "observation_atoms":["o0","o1"], "legal_action_ids":labels,
                "goal_atoms":["g"], "cost_bounds":{"maximum_intervention":2},
                "training_bundle":{"schema":"P2PublicGraphV1","action_bindings":bindings}
            });
            let output = run(
                env!("CARGO_BIN_EXE_p2_native_worker"),
                json!({
                    "schema":"P2NativeWorkerRequestV1", "verified_input_digest":canonical_envelope_digest(&sealed).unwrap(),
                    "envelope":sealed
                }),
            );
            assert!(output.status.success());
            let proposal: Value = serde_json::from_slice(&output.stdout).unwrap();
            let selection = &proposal["selection"];
            assert_eq!(selection["selection_path"], "P2BoundedFutureManifoldV1");
            assert_eq!(selection["minimal_action_ids"].as_array().unwrap().len(), 1);
            assert_eq!(selection["native_tie_set"].as_array().unwrap().len(), 1);
            let selected = selection["selected_action_id"].as_str().unwrap();
            assert_eq!(
                proposal["predictions"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .find(|prediction| prediction["intervention_cost"] == 1)
                    .unwrap()["action_id"],
                selected
            );
        }
    }
}
