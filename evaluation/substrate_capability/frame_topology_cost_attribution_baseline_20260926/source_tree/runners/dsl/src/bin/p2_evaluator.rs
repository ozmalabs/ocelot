//! Fixed evaluator-native reconstruction and clone scoring entrypoint.
//! It rebuilds expected records from sealed graph mechanics rather than
//! trusting submitted witness strings, predictions, or selection claims.
use std::io::{self, Read, Write};
use substrate_rs::p2_native::evaluator_reply;
fn main() {
    let mut input = Vec::new();
    if io::stdin().read_to_end(&mut input).is_err() || input.len() > 65_536 {
        std::process::exit(64);
    }
    let reply = serde_json::from_slice(&input)
        .map_err(|_| ())
        .and_then(|request| evaluator_reply(request).map_err(|_| ()));
    match reply.and_then(|v| serde_json::to_vec(&v).map_err(|_| ())) {
        Ok(bytes) if bytes.len() <= 65_536 => {
            if io::stdout().write_all(&bytes).is_err() {
                std::process::exit(65);
            }
        }
        _ => {
            let _ =
                io::stdout().write_all(br#"{"accepted":false,"classification":"protocol_error"}"#);
            std::process::exit(65);
        }
    }
}
