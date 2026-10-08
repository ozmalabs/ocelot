#!/usr/bin/env python3
"""Denial-only runtime probe for the local P0-A compatibility interceptors.

No registered handler is invoked and every attempted low-level process,
network, or file read is intercepted before the original operation. This is
not an OS sandbox test or evaluator-custody attestation.
"""
from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import os
import platform
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from evaluation.p0a.entrypoint import intercept_legacy_process_io
from evaluation.p0a.legacy_io_guard import (ROUTE_INVENTORY, DirectIODenied,
                                            activated, deny_direct_io)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "evaluation/reports/substrate_p0a_denial_probe_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_probe(output: Path) -> dict:
    # Imports are intentionally completed before the activated guard.
    from domains import tool_use
    import substrate_rs._native as native
    from domains.agent_tools import ToolBox
    from substrate.world_adapter import WorldAdapter

    native_registry_count = native.tool_handler_count()
    native_fire_count_before = native.tool_fire_count()
    native_path = Path(native.__file__).resolve()
    build_manifest = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
    manifest_doc = json.loads(build_manifest.read_text(encoding="utf-8"))
    python_registry = sorted(tool_use._HANDLERS)
    if native_registry_count != 0 or python_registry:
        raise RuntimeError("registry baseline requires a fresh process")
    toolbox = object.__new__(ToolBox)  # avoid __init__ workspace creation
    toolbox_capability_names = sorted(toolbox.capabilities())
    # Seed-load the default core adapter but do not tick rules, start the
    # agent, install tools, or dispatch any graph request.
    adapter = WorldAdapter(shadow_read=False, deep_ingest=False)
    boot_registry_count = native.tool_handler_count()
    tool_specs = [adapter.s.node(n)["attrs"] for n in adapter.s.nodes("ToolSpec")]
    boot_snapshot = {
        "boot_mode": "WorldAdapter default core seed load only; no rule tick or action",
        "graph_node_count": adapter.s.node_count(),
        "tool_spec_count": len(tool_specs),
        "tool_specs": [{"name": str(a.get("name", "")),
                        "handler_key": str(a.get("handler_key", "")),
                        "kind": str(a.get("kind", ""))} for a in tool_specs],
        "runtime_capability_names": sorted(adapter.runtime_capabilities()),
        "native_use_tool_handler_count_after_boot": boot_registry_count,
        "python_tool_use_handler_keys_after_boot": sorted(tool_use._HANDLERS),
    }
    # Register the repository's explicit demo ToolSpec pack on an isolated
    # substrate. Registration is configuration only; no ToolSpec is called.
    demo_substrate = __import__("substrate_rs").Substrate()
    tool_use.install_tool_use(demo_substrate)
    registered_specs = tool_use.register_real_tools(demo_substrate)
    native_registered = tool_use.register_native_handlers(demo_substrate, native)
    demo_spec_rows = [demo_substrate.node(n)["attrs"] for n in demo_substrate.nodes("ToolSpec")]
    demo_snapshot = {
        "profile": "domains.tool_use.register_real_tools demo pack",
        "graph_tool_specs": [{"name": str(a.get("name", "")),
                               "handler_key": str(a.get("handler_key", "")),
                               "kind": str(a.get("kind", "")),
                               "external": bool(a.get("external", False))}
                              for a in demo_spec_rows],
        "register_real_tools_returned": sorted(registered_specs),
        "python_handler_keys": sorted(tool_use._HANDLERS),
        "native_handlers_registered": native_registered,
        "native_handler_count": native.tool_handler_count(),
        "tool_call_count": len(demo_substrate.nodes("ToolCall")),
        "handler_invocations": 0,
    }
    if native_registered != len(registered_specs) or len(demo_spec_rows) != 5:
        raise RuntimeError("explicit demo registry did not match its five-tool contract")
    if demo_snapshot["native_handler_count"] != 5 or demo_snapshot["tool_call_count"] != 0:
        raise RuntimeError("demo registry snapshot is inconsistent")
    route_names = sorted(ROUTE_INVENTORY)
    reports: list[str] = []
    attempts: list[dict] = []

    def attempt(label, operation):
        try:
            operation()
            attempts.append({"label": label, "result": "returned"})
        except DirectIODenied as exc:
            attempts.append({"label": label, "result": "blocked", "reason": str(exc)})
        except BaseException as exc:  # record unexpected failures, including unusual control flow
            attempts.append({"label": label, "result": "unexpected_exception",
                             "exception_type": type(exc).__name__, "reason": str(exc)})

    with tempfile.TemporaryDirectory(prefix="substrate-denial-probe-") as tmp:
        file_path = Path(tmp) / "read-control.txt"
        file_path.write_text("control", encoding="utf-8")
        fd = os.open(file_path, os.O_RDONLY)
        operations = [
            ("socket.socket", lambda: socket.socket()),
            ("urllib.request.urlopen", lambda: urllib.request.urlopen("http://127.0.0.1:1/")),
            ("subprocess.Popen", lambda: subprocess.Popen(["true"])),
            ("builtins.open", lambda: builtins.open(file_path, "rb")),
            ("Path.read_text", lambda: file_path.read_text(encoding="utf-8")),
            ("os.read", lambda: os.read(fd, 1)),
            ("os.system", lambda: os.system("true")),
            ("os.execv", lambda: os.execv("/bin/true", ["true"])),
            ("os.execve", lambda: os.execve("/bin/true", ["true"], {})),
        ]
        try:
            with activated(reporter=reports.append), intercept_legacy_process_io():
                for route in route_names:
                    attempt(f"guard-route:{route}", lambda r=route: deny_direct_io(r))
                for label, operation in operations:
                    attempt(f"primitive:{label}", operation)
        finally:
            os.close(fd)

    native_fire_count_after = native.tool_fire_count()

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    source_files = [
        ROOT / "evaluation/p0a/entrypoint.py",
        ROOT / "evaluation/p0a/legacy_io_guard.py",
        ROOT / "domains/tool_use.py",
        ROOT / "domains/agent_tools.py",
        ROOT / "domains/tool_use.py",
    ]
    payload = {
        "schema_version": 1,
        "run_id": "substrate-p0a-denial-probe-20260925",
        "measured_at_utc": timestamp,
        "method": "fresh-process registry snapshot plus P0-A activated in-process compatibility interception; no handler invocation",
        "scope_boundary": "Local guard/interceptor behavior only. Not OS sandbox, independent custody, authorized run, or production handler registry.",
        "registry_snapshot": {
            "tool_use_python_handler_keys": python_registry,
            "tool_use_python_handler_count": len(python_registry),
            "native_use_tool_handler_count": native_registry_count,
            "explicit_toolbox_capabilities": toolbox_capability_names,
            "p0a_route_inventory": route_names,
        },
        "booted_adapter_snapshot": boot_snapshot,
        "explicit_demo_tool_profile_snapshot": demo_snapshot,
        "attempts": attempts,
        "guard_reported_routes": reports,
        "summary": {
            "attempted": len(attempts),
            "blocked": sum(a["result"] == "blocked" for a in attempts),
            "unexpected": [a for a in attempts if a["result"] != "blocked"],
            "handler_invocations": 0,
            "native_tool_fire_count_before": native_fire_count_before,
            "native_tool_fire_count_after": native_fire_count_after,
            "native_tool_fire_count_delta": native_fire_count_after - native_fire_count_before,
        },
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "native_build": {
            "extension_path": str(native_path),
            "extension_sha256": sha(native_path),
            "manifest_sha256": sha(build_manifest),
            "extension_matches_manifest": sha(native_path) == manifest_doc.get("engine_sha256"),
            "manifest_engine_sha256": manifest_doc.get("engine_sha256"),
        },
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files},
        "probe_script_sha256": sha(Path(__file__).resolve()),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    payload = run_probe(args.output.resolve())
    print(json.dumps({"output": str(args.output.resolve()), **payload["summary"],
                      "registry_snapshot": payload["registry_snapshot"]}, indent=2))
    if payload["summary"]["unexpected"]:
        raise SystemExit("one or more denial probes were not blocked")
    if payload["summary"]["native_tool_fire_count_delta"] != 0:
        raise SystemExit("native UseTool handler fired during denial probe")


if __name__ == "__main__":
    main()
