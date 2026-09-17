//! Fixed native P2 worker. It derives every witness and prediction from a
//! sealed public graph; it never accepts caller-provided predictions as proof.
use std::io::{self, Read, Write};
use substrate_rs::p2_native::{worker_failure_reason, worker_reply};

const PROBE_NONCE: &str = "p2-native-runtime-probe-v1";

fn diagnostic(reason_code: &str) -> Vec<u8> {
    // Fixed vocabulary only: no parse errors, envelope fragments, paths, ids,
    // environment, or authority are ever returned to the caller.
    format!(
        r#"{{"reason_code":"{}","schema":"P2NativeWorkerDiagnosticV1","status":"unestablished"}}"#,
        reason_code
    )
    .into_bytes()
}

fn main() {
    let mut input = Vec::new();
    if io::stdin().read_to_end(&mut input).is_err() || input.len() > 65_536 {
        std::process::exit(64);
    }
    let parsed: serde_json::Value = match serde_json::from_slice(&input) {
        Ok(value) => value,
        Err(_) => {
            let _ = io::stdout().write_all(&diagnostic("input_frame_invalid"));
            std::process::exit(65);
        }
    };
    if parsed.get("schema").and_then(serde_json::Value::as_str) == Some("P2NativeRuntimeProbeV1") {
        if parsed.get("nonce").and_then(serde_json::Value::as_str) == Some(PROBE_NONCE)
            && parsed.as_object().is_some_and(|object| object.len() == 2)
        {
            let _ = io::stdout().write_all(
                br#"{"abi":"p2-native-v1","schema":"P2NativeRuntimeProbeReplyV1","status":"ready"}"#,
            );
            return;
        }
        let _ = io::stdout().write_all(&diagnostic("request_schema_invalid"));
        std::process::exit(65);
    }
    match worker_reply(parsed) {
        Ok(value) => match serde_json::to_vec(&value) {
            Ok(bytes) if bytes.len() <= 65_536 => {
                if io::stdout().write_all(&bytes).is_err() {
                    std::process::exit(65);
                }
            }
            _ => {
                let _ = io::stdout().write_all(&diagnostic("output_write_failed"));
                std::process::exit(65);
            }
        },
        Err(error) => {
            let _ = io::stdout().write_all(&diagnostic(worker_failure_reason(&error)));
            std::process::exit(65);
        }
    }
}
