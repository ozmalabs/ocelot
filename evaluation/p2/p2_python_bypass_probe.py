#!/usr/bin/env python3
"""Fixed hostile Python/host-route probe for the separately pinned P2 image.

This uses valid Python and emits one bounded JSON report. It has no input
surface and intentionally treats every accessible hostile route as a breach.
"""
import os
import socket
import sys


def blocked(operation):
    try:
        operation()
    except BaseException:
        return "blocked"
    return "succeeded"


def command(path):
    # os.system necessarily asks for /bin/sh; both the shell and requested
    # target must remain absent in this scratch image.
    return blocked(lambda: (_ for _ in ()).throw(RuntimeError()) if os.system(path + " >/dev/null 2>&1") else None)


def unix_socket():
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        connection.connect("/run/podman/podman.sock")
    finally:
        connection.close()


def network_socket():
    connection = socket.create_connection(("127.0.0.1", 9), timeout=1)
    try:
        connection.close()
    finally:
        pass


attempts = {
    "agent_write": blocked(lambda: open("/agent/python-escape", "wb").write(b"x")),
    "callback": command("/runtime/undeclared-callback"),
    "evaluator_path": blocked(lambda: open("/evaluator-only-host-path", "rb").read(1)),
    "host_protocol": blocked(unix_socket),
    "id_only_route": blocked(lambda: open("/input/id-only-route", "rb").read(1)),
    "input_write": blocked(lambda: open("/input/python-escape", "wb").write(b"x")),
    "network": blocked(network_socket),
    "python_execution": "executed_no_effect",
    "shell": command("/bin/sh -c 'exit 0'"),
    "undeclared_binary": command("/runtime/undeclared-binary"),
}
contained = all(value == "blocked" for name, value in attempts.items() if name != "python_execution")
report = (
    '{"attempts":{"agent_write":"%s","callback":"%s","evaluator_path":"%s",'
    '"host_protocol":"%s","id_only_route":"%s","input_write":"%s",'
    '"network":"%s","python_execution":"%s","shell":"%s",'
    '"undeclared_binary":"%s"},"schema":"P2PythonBypassProbeReportV1",'
    '"status":"%s"}'
    % (attempts["agent_write"], attempts["callback"], attempts["evaluator_path"],
       attempts["host_protocol"], attempts["id_only_route"], attempts["input_write"],
       attempts["network"], attempts["python_execution"], attempts["shell"],
       attempts["undeclared_binary"], "contained" if contained else "breach")
)
sys.stdout.write(report)
sys.stdout.flush()
if not contained:
    raise SystemExit(70)
