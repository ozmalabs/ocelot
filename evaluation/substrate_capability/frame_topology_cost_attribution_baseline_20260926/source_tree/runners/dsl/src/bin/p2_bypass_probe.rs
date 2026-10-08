//! Fixed hostile-surface probe for the separately pinned P2 bypass image.
//! It attempts only the declared routes and emits fixed tokens, never errors.
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::net::TcpStream;
#[cfg(unix)]
use std::os::unix::net::UnixStream;
use std::process::Command;

fn blocked(result: std::io::Result<impl Sized>) -> bool { result.is_err() }

fn main() {
    let shell = Command::new("/bin/sh").arg("-c").arg("exit 0").status().is_err();
    let undeclared_binary = Command::new("/runtime/undeclared-binary").status().is_err();
    let agent_write = blocked(OpenOptions::new().write(true).create(true).open("/agent/escape"));
    let input_write = blocked(OpenOptions::new().write(true).create(true).open("/input/escape"));
    let evaluator_path = File::open("/evaluator-only-host-path").is_err();
    let network = TcpStream::connect("127.0.0.1:9").is_err();
    #[cfg(unix)]
    let host_protocol = UnixStream::connect("/run/podman/podman.sock").is_err();
    #[cfg(not(unix))]
    let host_protocol = true;
    let callback = Command::new("/runtime/undeclared-callback").status().is_err();
    let id_only_route = File::open("/input/id-only-route").is_err();
    let contained = shell && undeclared_binary && agent_write && input_write && evaluator_path
        && network && host_protocol && callback && id_only_route;
    let status = if contained { "contained" } else { "breach" };
    let report = format!(
        r#"{{"attempts":{{"agent_write":"{}","callback":"{}","evaluator_path":"{}","host_protocol":"{}","id_only_route":"{}","input_write":"{}","network":"{}","shell":"{}","undeclared_binary":"{}"}},"schema":"P2BypassProbeReportV1","status":"{}"}}"#,
        if agent_write { "blocked" } else { "succeeded" }, if callback { "blocked" } else { "succeeded" },
        if evaluator_path { "blocked" } else { "succeeded" }, if host_protocol { "blocked" } else { "succeeded" },
        if id_only_route { "blocked" } else { "succeeded" }, if input_write { "blocked" } else { "succeeded" },
        if network { "blocked" } else { "succeeded" }, if shell { "blocked" } else { "succeeded" },
        if undeclared_binary { "blocked" } else { "succeeded" }, status);
    let _ = std::io::stdout().write_all(report.as_bytes());
    if !contained { std::process::exit(70); }
}
