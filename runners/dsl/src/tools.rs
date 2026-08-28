//! Tool-dispatch boundary as a first-class engine primitive.
//!
//! `TermNode::UseTool { tool, args }` (see term.rs) lets a tool call
//! COMPOSE inside an engine-evaluated Term-tree: the evaluator evaluates
//! each `args` term to a `Value`, then dispatches to a registered Python
//! handler under the GIL and converts the returned Python value back to a
//! `Value`. This makes the tool boundary a first-class Term the engine
//! evaluates, rather than a Python-side world-adapter call.
//!
//! The registry is a process-global `Mutex<HashMap<String, Py<PyAny>>>` of
//! tool-name → Python callable. `register_tool_handler` / `clear_tool_handlers`
//! are PyO3 functions the world adapter (`domains/tool_use.py`) calls once at
//! startup so the NATIVE `UseTool` dispatches to the same handlers the
//! Python `use_tool` world-adapter path uses.
//!
//! Re-entrancy: `call_tool` is invoked from `term::evaluate`, which already
//! runs under the GIL when called from `PySubstrate.evaluate`. `with_gil`
//! re-acquires the GIL safely (PyO3 supports nested acquisition), so a tool
//! handler that itself calls back into the substrate composes correctly.
//!
//! Safety: a missing handler or any handler error degrades to a safe default
//! `Value` (Int(0)) — the evaluator NEVER panics on a tool boundary.

use std::collections::HashMap;
use std::sync::Mutex;
use std::sync::OnceLock;

use pyo3::prelude::*;
use pyo3::types::PyTuple;

use crate::sym::Interner;
use crate::value::{SurfaceKind, Value};

/// Process-global tool-name → Python callable registry. `OnceLock` lazily
/// initialises the `Mutex<HashMap>` on first touch so registration order
/// across import sites doesn't matter.
fn registry() -> &'static Mutex<HashMap<String, Py<PyAny>>> {
    static REG: OnceLock<Mutex<HashMap<String, Py<PyAny>>>> = OnceLock::new();
    REG.get_or_init(|| Mutex::new(HashMap::new()))
}

/// Process-global counter of how many times a NATIVE `UseTool` actually
/// fired a handler from inside `evaluate`. The demo reads this to prove the
/// tool ran natively (not at the world-adapter boundary).
fn fire_count() -> &'static std::sync::atomic::AtomicU64 {
    static N: OnceLock<std::sync::atomic::AtomicU64> = OnceLock::new();
    N.get_or_init(|| std::sync::atomic::AtomicU64::new(0))
}

/// Register `handler` (any Python callable) under `name`. The native
/// `UseTool` dispatch looks the handler up by this name. Idempotent —
/// re-registering a name replaces the handler.
#[pyfunction]
fn register_tool_handler(name: String, handler: PyObject) -> PyResult<()> {
    if let Ok(mut reg) = registry().lock() {
        reg.insert(name, handler);
    }
    Ok(())
}

/// Drop every registered handler. Used by tests / re-init.
#[pyfunction]
fn clear_tool_handlers() -> PyResult<()> {
    if let Ok(mut reg) = registry().lock() {
        reg.clear();
    }
    Ok(())
}

/// How many handler names are registered. Diagnostic.
#[pyfunction]
fn tool_handler_count() -> usize {
    registry().lock().map(|r| r.len()).unwrap_or(0)
}

/// How many times a native `UseTool` has fired a handler from inside
/// `evaluate`, process-wide. Proves the tool ran natively.
#[pyfunction]
fn tool_fire_count() -> u64 {
    fire_count().load(std::sync::atomic::Ordering::Relaxed)
}

/// Convert a runtime `Value` to a Python object for handing to a tool
/// handler. Self-contained (doesn't borrow py.rs's private `value_to_py`):
/// covers the scalar + text-surface cases a tool boundary deals in; richer
/// collection types map to None (a tool that needs them takes a different
/// adapter path). `interner` resolves `Str` Syms to Python `str`.
fn value_to_pyobj<'py>(py: Python<'py>, v: &Value, interner: &Interner) -> PyObject {
    match v {
        Value::None => py.None(),
        Value::Bool(b) => b.into_py(py),
        Value::Int(n) => n.into_py(py),
        Value::Float(f) => f.into_py(py),
        Value::Str(s) => interner.resolve(*s).to_string().into_py(py),
        Value::Surface(SurfaceKind::Text, bytes) => std::str::from_utf8(bytes)
            .unwrap_or("")
            .to_string()
            .into_py(py),
        Value::Surface(SurfaceKind::Bytes, bytes) => {
            pyo3::types::PyBytes::new_bound(py, bytes).into_py(py)
        }
        // Collections / nodes aren't part of the scalar tool boundary; a
        // handler that needs them should be called via the world adapter.
        _ => py.None(),
    }
}

/// Convert a Python value returned by a tool handler back to a `Value`.
/// bool→Bool, int→Int, float→Float, str→Surface(Text) (no interner
/// mutation needed — string primitives in the engine already return text
/// surfaces), None/unknown→Int(0) (the safe default the evaluator returns).
fn pyobj_to_value(obj: &Bound<'_, PyAny>) -> Value {
    // Order matters: bool is a subclass of int in Python, so test bool first.
    if obj.is_none() {
        return Value::Int(0);
    }
    if obj.is_instance_of::<pyo3::types::PyBool>() {
        if let Ok(b) = obj.extract::<bool>() {
            return Value::Bool(b);
        }
    }
    if let Ok(n) = obj.extract::<i64>() {
        return Value::Int(n);
    }
    if let Ok(f) = obj.extract::<f64>() {
        return Value::Float(f);
    }
    if let Ok(s) = obj.extract::<String>() {
        return Value::Surface(SurfaceKind::Text, std::sync::Arc::from(s.into_bytes()));
    }
    // Unknown Python type → safe default.
    Value::Int(0)
}

/// Dispatch a native `UseTool`: look the handler up by `name`, convert the
/// already-evaluated `args` Values to a Python tuple, call the handler, and
/// convert the result back to a `Value`. Missing handler or any Python
/// error degrades to `Value::Int(0)` — never panics. `interner` resolves
/// `Str` args to Python strings.
pub fn call_tool(name: &str, args: &[Value], interner: &Interner) -> Value {
    Python::with_gil(|py| {
        // Clone the Py<PyAny> out under the lock, then drop the lock before
        // calling so a re-entrant handler (which may register/clear) can't
        // deadlock on the registry mutex.
        let handler: Py<PyAny> = match registry().lock() {
            Ok(reg) => match reg.get(name) {
                Some(h) => h.clone_ref(py),
                None => return Value::Int(0),
            },
            Err(_) => return Value::Int(0),
        };

        let py_args: Vec<PyObject> = args
            .iter()
            .map(|v| value_to_pyobj(py, v, interner))
            .collect();
        let tuple = PyTuple::new_bound(py, &py_args);

        match handler.bind(py).call1(tuple) {
            Ok(result) => {
                fire_count().fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                pyobj_to_value(&result)
            }
            // Handler raised — degrade to the safe default rather than
            // propagating a Python exception through the evaluator.
            Err(_) => Value::Int(0),
        }
    })
}

/// Register the tool-dispatch PyO3 functions on the module. Called from
/// `lib.rs::_native` alongside `py::register` so this lives outside the
/// (concurrently-edited) py.rs.
pub fn register_tools(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(register_tool_handler, m)?)?;
    m.add_function(wrap_pyfunction!(clear_tool_handlers, m)?)?;
    m.add_function(wrap_pyfunction!(tool_handler_count, m)?)?;
    m.add_function(wrap_pyfunction!(tool_fire_count, m)?)?;
    Ok(())
}
