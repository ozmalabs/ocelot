//! Unified clock abstraction for native and WebAssembly targets.

#[cfg(not(target_arch = "wasm32"))]
pub use std::time::{Duration, Instant, SystemTime};

#[cfg(target_arch = "wasm32")]
pub use web_time::{Duration, Instant, SystemTime};
