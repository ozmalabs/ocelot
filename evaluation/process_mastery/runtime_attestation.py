"""Runtime identity for native execution freezes.

The extension digest is taken from the module object already loaded by Python;
the package wrapper is recorded independently and never stands in for it.
"""
from __future__ import annotations

import hashlib
import importlib.machinery
import json
import subprocess
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attest(*, package: Any, native_module: Any | None = None,
           build_receipt: str | Path | None = None,
           expected: dict[str, str] | None = None,
           require_clean: bool = False) -> dict[str, Any]:
    """Describe loaded wrapper/extension/build bytes; missing evidence is UNKNOWN.

    ``package`` is the imported ``substrate_rs`` package. ``native_module`` is
    injectable for tests; production callers should omit it and use the exact
    ``package._native`` object imported by the package.
    """
    native = native_module if native_module is not None else getattr(package, "_native", None)
    wrapper_path = Path(getattr(package, "__file__", "")).resolve()
    native_path_text = getattr(native, "__file__", None)
    native_path = Path(native_path_text).resolve() if native_path_text else None
    receipt_path = Path(build_receipt).resolve() if build_receipt else None
    result: dict[str, Any] = {
        "status": "ATTESTED", "wrapper_path": str(wrapper_path),
        "wrapper_sha256": None, "loaded_extension_path": str(native_path) if native_path else None,
        "loaded_extension_sha256": None, "build_receipt_path": str(receipt_path) if receipt_path else None,
        "build_receipt_sha256": None, "build_source_fingerprint": None,
        "native_symbols_bound": False, "issues": [],
    }
    if wrapper_path.is_file():
        result["wrapper_sha256"] = _sha256(wrapper_path)
    else:
        result["issues"].append("wrapper_unavailable")
    if native_path and native_path.is_file():
        result["loaded_extension_sha256"] = _sha256(native_path)
        result["native_symbols_bound"] = all(
            getattr(package, name, None) is getattr(native, name, object())
            for name in ("NodeID", "Substrate")
        )
        if not any(str(native_path).endswith(suffix)
                   for suffix in importlib.machinery.EXTENSION_SUFFIXES):
            result["issues"].append("loaded_module_not_native_extension")
    else:
        result["issues"].append("loaded_extension_unavailable")
    if not result["native_symbols_bound"]:
        result["issues"].append("native_symbol_binding_unverified")
    if receipt_path and receipt_path.is_file():
        result["build_receipt_sha256"] = _sha256(receipt_path)
        try:
            receipt = json.loads(receipt_path.read_text())
            result["build_source_fingerprint"] = receipt.get("source_fingerprint")
            if receipt.get("engine_sha256") and receipt["engine_sha256"] != result["loaded_extension_sha256"]:
                result["issues"].append("build_extension_mismatch")
        except (OSError, json.JSONDecodeError):
            result["issues"].append("build_receipt_invalid")
    else:
        result["issues"].append("build_receipt_unknown")
    if expected:
        for key, value in expected.items():
            if result.get(key) != value:
                result["issues"].append(f"freeze_mismatch:{key}")
    if require_clean:
        if not result["build_source_fingerprint"]:
            result["issues"].append("clean_build_not_proven")
        if receipt_path:
            try:
                repo = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                               cwd=receipt_path.parent, text=True).strip()
                paths = [wrapper_path, native_path, receipt_path]
                relpaths = [str(p.relative_to(repo)) for p in paths if p]
                try:
                    receipt = json.loads(receipt_path.read_text())
                    relpaths.extend(receipt.get("files", {}).keys())
                except (OSError, json.JSONDecodeError):
                    pass
                dirty = subprocess.check_output(["git", "status", "--porcelain", "--", *relpaths],
                                                cwd=repo, text=True)
                if dirty:
                    result["issues"].append("artifact_tree_dirty")
            except (OSError, subprocess.CalledProcessError, ValueError):
                result["issues"].append("artifact_cleanliness_unknown")
    if result["issues"]:
        result["status"] = "UNKNOWN" if any(x.endswith("unknown") or x.endswith("unavailable")
                                              or x.endswith("unverified") for x in result["issues"]) else "MISMATCH"
        if require_clean:
            result["status"] = "DEVELOPMENT_ONLY"
    return result


def assert_freeze_matches(actual: dict[str, Any], frozen: dict[str, Any]) -> None:
    """Fail closed if loaded artifacts differ from a previously frozen record."""
    fields = ("wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
              "build_source_fingerprint")
    mismatches = [field for field in fields if not frozen.get(field) or actual.get(field) != frozen[field]]
    if mismatches or actual.get("status") != "ATTESTED" or not actual.get("native_symbols_bound"):
        raise RuntimeError("runtime attestation does not match freeze: " + ", ".join(mismatches or actual.get("issues", [])))
