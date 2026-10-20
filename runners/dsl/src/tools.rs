//! Tool-dispatch boundary as a first-class engine primitive.
//!
//! `TermNode::UseTool { tool, args }` (see term.rs) lets a tool call
//! COMPOSE inside an engine-evaluated Term-tree: the evaluator evaluates
//! each `args` term to a `Value`, then dispatches to a registered host
//! handler and converts the returned value back to a `Value`.
//!
//! Safety: a missing handler or any handler error degrades to a safe default
//! `Value` (Int(0)) — the evaluator NEVER panics on a tool boundary.

use std::collections::HashMap;
use std::sync::{Arc, Mutex, OnceLock};

use crate::sym::Interner;
use crate::value::Value;

#[cfg(feature = "python")]
use crate::value::SurfaceKind;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyTuple;

/// Process-global counter of how many times a NATIVE `UseTool` actually
/// fired a handler from inside `evaluate`. The demo reads this to prove the
/// tool ran natively (not at the world-adapter boundary).
pub fn fire_count() -> &'static std::sync::atomic::AtomicU64 {
    static N: OnceLock<std::sync::atomic::AtomicU64> = OnceLock::new();
    N.get_or_init(|| std::sync::atomic::AtomicU64::new(0))
}

pub type NativeToolFn = Arc<dyn Fn(&[Value], &Interner) -> Value + Send + Sync>;

fn generic_registry() -> &'static Mutex<HashMap<String, NativeToolFn>> {
    static REG: OnceLock<Mutex<HashMap<String, NativeToolFn>>> = OnceLock::new();
    REG.get_or_init(|| Mutex::new(HashMap::new()))
}

/// Register a generic Rust/WASM tool handler function.
pub fn register_native_tool(name: String, handler: NativeToolFn) {
    if let Ok(mut reg) = generic_registry().lock() {
        reg.insert(name, handler);
    }
}

/// Clear generic native tool handlers.
pub fn clear_native_tools() {
    if let Ok(mut reg) = generic_registry().lock() {
        reg.clear();
    }
}

#[cfg(feature = "python")]
fn registry() -> &'static Mutex<HashMap<String, Py<PyAny>>> {
    static REG: OnceLock<Mutex<HashMap<String, Py<PyAny>>>> = OnceLock::new();
    REG.get_or_init(|| Mutex::new(HashMap::new()))
}

#[cfg(feature = "python")]
#[pyfunction]
fn register_tool_handler(name: String, handler: PyObject) -> PyResult<()> {
    if let Ok(mut reg) = registry().lock() {
        reg.insert(name, handler);
    }
    Ok(())
}

#[cfg(feature = "python")]
#[pyfunction]
fn clear_tool_handlers() -> PyResult<()> {
    if let Ok(mut reg) = registry().lock() {
        reg.clear();
    }
    Ok(())
}

#[cfg(feature = "python")]
#[pyfunction]
fn tool_handler_count() -> usize {
    registry().lock().map(|r| r.len()).unwrap_or(0)
}

#[cfg(feature = "python")]
#[pyfunction]
fn tool_fire_count() -> u64 {
    fire_count().load(std::sync::atomic::Ordering::Relaxed)
}

#[cfg(feature = "python")]
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
        _ => py.None(),
    }
}

#[cfg(feature = "python")]
fn pyobj_to_value(obj: &Bound<'_, PyAny>) -> Value {
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
    Value::Int(0)
}

#[cfg(feature = "python")]
pub fn call_tool(name: &str, args: &[Value], interner: &Interner) -> Value {
    // Check generic registry first
    if let Ok(reg) = generic_registry().lock() {
        if let Some(h) = reg.get(name) {
            fire_count().fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            return h(args, interner);
        }
    }

    Python::with_gil(|py| {
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
            Err(_) => Value::Int(0),
        }
    })
}

#[cfg(not(feature = "python"))]
pub fn call_tool(name: &str, args: &[Value], interner: &Interner) -> Value {
    if let Ok(reg) = generic_registry().lock() {
        if let Some(h) = reg.get(name) {
            fire_count().fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            return h(args, interner);
        }
    }
    Value::Int(0)
}

#[cfg(feature = "python")]
pub fn register_tools(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(register_tool_handler, m)?)?;
    m.add_function(wrap_pyfunction!(clear_tool_handlers, m)?)?;
    m.add_function(wrap_pyfunction!(tool_handler_count, m)?)?;
    m.add_function(wrap_pyfunction!(tool_fire_count, m)?)?;
    Ok(())
}
