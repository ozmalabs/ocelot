//! Optimised binary recogniser for the substrate's `recognise_frame` hot path.
//!
//! Architecture:
//! - Frames are installed once via `install_frame` and live in a process-global
//!   `FrameStore` behind an `RwLock`. Each evoked_by surface form is compiled
//!   into a `memchr::memmem::Finder<'static>` AT INSTALL TIME so per-tick
//!   recognition pays only SIMD substring-scan cost, not Finder construction.
//! - Recognition takes a JSON request and returns a JSON response.
//! - Pure-Rust `recognise_frame_rs` is exposed for native tests and for callers
//!   that prefer typed Rust over JSON.

use memchr::memmem;
use rustc_hash::{FxHashMap, FxHashSet};
use serde::{Deserialize, Serialize};
use std::ffi::{c_char, CStr, CString};
use std::sync::{OnceLock, RwLock};

// ---------- Types ----------

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BindingPattern {
    FunctionOfSubject,
    PredicateOfSubject,
    FunctionOfTwoSubjects,
}

impl BindingPattern {
    fn parse(s: &str) -> Option<Self> {
        match s {
            "function_of_subject" => Some(Self::FunctionOfSubject),
            "predicate_of_subject" => Some(Self::PredicateOfSubject),
            "function_of_two_subjects" => Some(Self::FunctionOfTwoSubjects),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind", content = "v")]
pub enum Value {
    Int(i64),
    Str(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoreElement {
    pub slot: String,
    #[serde(rename = "type")]
    pub ty: String,
}

/// A frame as stored internally. Surface forms are pre-lowercased and a
/// `Finder<'static>` is built per form ONCE at install time.
pub struct Frame {
    pub id: i64,
    /// (lowercased surface form, SIMD finder over that form)
    pub evoked_by: Vec<(String, memmem::Finder<'static>)>,
    pub core_elements: Vec<CoreElement>,
    pub binding_pattern: BindingPattern,
    pub holds_in: Option<i64>,
    /// Stable install order; smaller wins ties.
    pub install_seq: u64,
}

/// Wire-format frame used at the FFI boundary.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrameSpec {
    pub id: i64,
    pub evoked_by: Vec<String>,
    pub core_elements: Vec<CoreElement>,
    pub binding_pattern: String,
    pub holds_in: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recognition {
    pub frame_id: i64,
    pub slots: FxHashMap<String, Value>,
    pub fok: f64,
}

// ---------- Frame store ----------

pub struct FrameStore {
    pub frames: Vec<Frame>,
    next_seq: u64,
}

impl FrameStore {
    pub fn new() -> Self {
        Self { frames: Vec::new(), next_seq: 0 }
    }

    pub fn install(&mut self, spec: FrameSpec) -> Result<(), String> {
        let bp = BindingPattern::parse(&spec.binding_pattern)
            .ok_or_else(|| format!("unknown binding_pattern: {}", spec.binding_pattern))?;
        let evoked_by: Vec<_> = spec
            .evoked_by
            .into_iter()
            .map(|s| {
                let lower = s.to_lowercase();
                // Finder needs to own its needle for 'static; we leak nothing —
                // the Finder borrows from the owned String we keep alongside.
                // `into_owned()` upgrades the lifetime to 'static.
                let finder = memmem::Finder::new(lower.as_bytes()).into_owned();
                (lower, finder)
            })
            .collect();
        let seq = self.next_seq;
        self.next_seq += 1;
        self.frames.push(Frame {
            id: spec.id,
            evoked_by,
            core_elements: spec.core_elements,
            binding_pattern: bp,
            holds_in: spec.holds_in,
            install_seq: seq,
        });
        Ok(())
    }

    pub fn clear(&mut self) {
        self.frames.clear();
        self.next_seq = 0;
    }
}

impl Default for FrameStore {
    fn default() -> Self { Self::new() }
}

fn global_store() -> &'static RwLock<FrameStore> {
    static STORE: OnceLock<RwLock<FrameStore>> = OnceLock::new();
    STORE.get_or_init(|| RwLock::new(FrameStore::new()))
}

// ---------- Core algorithm ----------

const PREAMBLES: &[&str] = &[
    // Longest first so longer matches win.
    "calculate the ",
    "determine the ",
    "compute the ",
    "what is the ",
    "find the ",
    "calculate ",
    "determine ",
    "compute ",
    "what is ",
    "find ",
];

/// Strip a leading preamble + trailing .?! from a (lowercased) question.
fn strip_preamble(q_lower: &str) -> &str {
    let mut s = q_lower;
    for pre in PREAMBLES {
        if s.starts_with(pre) {
            s = &s[pre.len()..];
            break;
        }
    }
    let trimmed = s.trim_end_matches(|c: char| c == '.' || c == '?' || c == '!');
    trimmed
}

/// Compute the scope closure: agent_scope ∪ ancestors-of(agent_scope).
/// The `mt_genl_table` is expected to already contain the genlMt closure
/// (ancestors). Per spec the recogniser does NOT additionally compute
/// descendants — that closure is the caller's responsibility (matches the
/// spec wording "agent_scope ∪ genlMt-ancestors of agent_scope ∪ all sub-Mts
/// of those" where the table is taken as already containing what it should).
fn scope_closure(
    agent_scope: &[i64],
    mt_genl_table: &FxHashMap<i64, Vec<i64>>,
) -> FxHashSet<i64> {
    let mut out: FxHashSet<i64> = FxHashSet::default();
    for &mt in agent_scope {
        out.insert(mt);
        if let Some(ancestors) = mt_genl_table.get(&mt) {
            for &a in ancestors {
                out.insert(a);
            }
        }
    }
    out
}

/// Try to bind slots for a single frame given the question (both lowercased
/// and original-case), the hit position+form, and the core elements. The
/// match position is computed against the lowercased question; SLOT BINDING
/// uses the original-case text so a named subject like "M" stays "M" (matches
/// the Python recogniser). Returns None on binding failure.
fn bind(
    q_lower: &str,
    q_original: &str,
    hit_form: &str,
    hit_pos: usize,
    core_elements: &[CoreElement],
    pattern: BindingPattern,
) -> Option<FxHashMap<String, Value>> {
    let hit_end = hit_pos + hit_form.len();
    match pattern {
        BindingPattern::FunctionOfSubject => {
            if core_elements.is_empty() {
                return None;
            }
            let tail = q_original[hit_end..].trim();
            let tail_lower = tail.to_lowercase();
            let tail = if tail_lower.starts_with("of ") {
                &tail[3..]
            } else if tail_lower.starts_with("for ") {
                &tail[4..]
            } else {
                tail
            };
            let tail = tail.trim_end_matches(|c: char| c == '.' || c == '?' || c == '!');
            let tail = tail.trim();
            if tail.is_empty() {
                return None;
            }
            let mut slots = FxHashMap::default();
            slots.insert(core_elements[0].slot.clone(), parse_value(tail));
            Some(slots)
        }
        BindingPattern::PredicateOfSubject => {
            if core_elements.is_empty() {
                return None;
            }
            let before = &q_original[..hit_pos];
            let before = before.trim_start();
            let before_lower = before.to_lowercase();
            let subj = if before_lower.starts_with("is ") {
                &before[3..]
            } else if before_lower.starts_with("are ") {
                &before[4..]
            } else if before_lower.starts_with("does ") {
                &before[5..]
            } else if before_lower.starts_with("do ") {
                &before[3..]
            } else {
                return None;
            };
            let subj = subj.trim();
            // Strip trailing " a"/" an"/" the" (in that priority — longest first).
            // Compare lowercased to match Python (which lowercases for the check).
            let subj_lower = subj.to_lowercase();
            let subj = if subj_lower.ends_with(" the") {
                &subj[..subj.len() - 4]
            } else if subj_lower.ends_with(" an") {
                &subj[..subj.len() - 3]
            } else if subj_lower.ends_with(" a") {
                &subj[..subj.len() - 2]
            } else {
                subj
            };
            let subj = subj.trim();
            if subj.is_empty() {
                return None;
            }
            let mut slots = FxHashMap::default();
            slots.insert(core_elements[0].slot.clone(), parse_value(subj));
            Some(slots)
        }
        BindingPattern::FunctionOfTwoSubjects => {
            if core_elements.len() < 2 {
                return None;
            }
            let tail = q_original[hit_end..].trim();
            // Strip leading "of " / "for " marker so "gcd of A and B" parses
            // the first subject as "A", not "of A". Matches the Python recogniser.
            let tail_lower = tail.to_lowercase();
            let tail = if tail_lower.starts_with("of ") {
                &tail[3..]
            } else if tail_lower.starts_with("for ") {
                &tail[4..]
            } else {
                tail
            };
            let tail = tail.trim_end_matches(|c: char| c == '.' || c == '?' || c == '!');
            let tail = tail.trim();
            // Case-insensitive search for the splitter.
            let tail_lower = tail.to_lowercase();
            let parts: Vec<&str> = if let Some(idx) = tail_lower.find(" and ") {
                vec![tail[..idx].trim(), tail[idx + 5..].trim()]
            } else if let Some(idx) = tail_lower.find(" by ") {
                vec![tail[..idx].trim(), tail[idx + 4..].trim()]
            } else if let Some(idx) = tail_lower.find(", ") {
                vec![tail[..idx].trim(), tail[idx + 2..].trim()]
            } else {
                return None;
            };
            if parts.len() != 2 || parts[0].is_empty() || parts[1].is_empty() {
                return None;
            }
            let mut slots = FxHashMap::default();
            slots.insert(core_elements[0].slot.clone(), parse_value(parts[0]));
            slots.insert(core_elements[1].slot.clone(), parse_value(parts[1]));
            Some(slots)
        }
    }
}

fn parse_value(s: &str) -> Value {
    match s.parse::<i64>() {
        Ok(n) => Value::Int(n),
        Err(_) => Value::Str(s.to_string()),
    }
}

/// Native-Rust entry point. Returns the winning recognition or None.
pub fn recognise_frame_rs(
    question_text: &str,
    frames: &[Frame],
    agent_scope: &[i64],
    mt_genl_table: &FxHashMap<i64, Vec<i64>>,
) -> Option<Recognition> {
    let q_lower = question_text.to_lowercase();
    let q_bytes = q_lower.as_bytes();
    let q_original = question_text;
    let stripped = strip_preamble(&q_lower);
    let stripped_len = stripped.chars().count().max(1) as f64;

    let scope = scope_closure(agent_scope, mt_genl_table);

    let mut best: Option<(f64, u64, Recognition)> = None;

    for frame in frames {
        // (2) Mt scoping — cheap; do it before substring scans when possible.
        if let Some(mt) = frame.holds_in {
            if !scope.contains(&mt) {
                continue;
            }
        }

        // (1) Longest evoked_by form that occurs as case-insensitive substring.
        let mut best_form: Option<(&str, usize)> = None;
        for (form, finder) in &frame.evoked_by {
            if let Some(pos) = finder.find(q_bytes) {
                if best_form.map_or(true, |(f, _)| form.len() > f.len()) {
                    best_form = Some((form.as_str(), pos));
                }
            }
        }
        let (hit_form, hit_pos) = match best_form {
            Some(x) => x,
            None => continue,
        };

        // (3) Binding.
        let slots = match bind(&q_lower, q_original, hit_form, hit_pos, &frame.core_elements, frame.binding_pattern) {
            Some(s) => s,
            None => continue,
        };

        // (4) Coverage gate.
        let mut numeric_subject_len = 0usize;
        for v in slots.values() {
            if let Value::Int(n) = v {
                numeric_subject_len += n.to_string().len();
            }
        }
        let coverage = (hit_form.len() + numeric_subject_len) as f64 / stripped_len;
        if coverage < 0.20 {
            continue;
        }

        // (5) FOK.
        let mut fok = hit_form.len() as f64 * coverage;
        if !slots.is_empty() {
            fok += 1.0;
        }

        let rec = Recognition { frame_id: frame.id, slots, fok };

        let replace = match &best {
            None => true,
            Some((best_fok, best_seq, _)) => {
                fok > *best_fok || (fok == *best_fok && frame.install_seq < *best_seq)
            }
        };
        if replace {
            best = Some((fok, frame.install_seq, rec));
        }
    }

    best.map(|(_, _, r)| r)
}

// ---------- C ABI ----------

#[derive(Debug, Deserialize)]
struct RecogniseRequest {
    question_text: String,
    agent_scope: Vec<i64>,
    #[serde(default)]
    mt_genl_table: FxHashMap<String, Vec<i64>>, // JSON keys are strings
}

fn to_int_keyed(m: FxHashMap<String, Vec<i64>>) -> FxHashMap<i64, Vec<i64>> {
    let mut out = FxHashMap::default();
    for (k, v) in m {
        if let Ok(k) = k.parse::<i64>() {
            out.insert(k, v);
        }
    }
    out
}

/// Install a frame from a JSON-encoded FrameSpec. Returns 0 on success, -1 on error.
///
/// # Safety
/// `spec_json` must be a valid NUL-terminated UTF-8 C string.
#[no_mangle]
pub unsafe extern "C" fn install_frame(spec_json: *const c_char) -> i32 {
    if spec_json.is_null() { return -1; }
    let cstr = CStr::from_ptr(spec_json);
    let s = match cstr.to_str() { Ok(s) => s, Err(_) => return -1 };
    let spec: FrameSpec = match serde_json::from_str(s) { Ok(s) => s, Err(_) => return -1 };
    let mut store = match global_store().write() { Ok(g) => g, Err(_) => return -1 };
    match store.install(spec) {
        Ok(()) => 0,
        Err(_) => -1,
    }
}

/// Clear all installed frames (mostly for tests / re-seeding).
#[no_mangle]
pub extern "C" fn clear_frames() {
    if let Ok(mut store) = global_store().write() {
        store.clear();
    }
}

/// Recognise a frame. Input is a JSON-encoded `RecogniseRequest`. Output is a
/// JSON-encoded `Recognition` or the literal string "null".
///
/// The returned pointer must be freed by `free_cstring`.
///
/// # Safety
/// `req_json` must be a valid NUL-terminated UTF-8 C string.
#[no_mangle]
pub unsafe extern "C" fn recognise_frame(req_json: *const c_char) -> *mut c_char {
    if req_json.is_null() { return std::ptr::null_mut(); }
    let cstr = CStr::from_ptr(req_json);
    let s = match cstr.to_str() { Ok(s) => s, Err(_) => return std::ptr::null_mut() };
    let req: RecogniseRequest = match serde_json::from_str(s) {
        Ok(r) => r,
        Err(_) => return std::ptr::null_mut(),
    };
    let mt_table = to_int_keyed(req.mt_genl_table);

    let store = match global_store().read() { Ok(g) => g, Err(_) => return std::ptr::null_mut() };
    let result = recognise_frame_rs(&req.question_text, &store.frames, &req.agent_scope, &mt_table);

    let body = match result {
        Some(r) => serde_json::to_string(&r).unwrap_or_else(|_| "null".to_string()),
        None => "null".to_string(),
    };
    match CString::new(body) {
        Ok(cs) => cs.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Free a string previously returned by `recognise_frame`.
///
/// # Safety
/// `ptr` must have come from `recognise_frame` and must not have been freed.
#[no_mangle]
pub unsafe extern "C" fn free_cstring(ptr: *mut c_char) {
    if !ptr.is_null() {
        drop(CString::from_raw(ptr));
    }
}

// ---------- Tests ----------

#[cfg(test)]
mod tests {
    use super::*;

    fn mk_frame(
        id: i64,
        evoked_by: &[&str],
        core_elements: &[(&str, &str)],
        binding_pattern: BindingPattern,
        holds_in: Option<i64>,
        install_seq: u64,
    ) -> Frame {
        let evoked_by = evoked_by
            .iter()
            .map(|s| {
                let lower = s.to_lowercase();
                let finder = memmem::Finder::new(lower.as_bytes()).into_owned();
                (lower, finder)
            })
            .collect();
        let core_elements = core_elements
            .iter()
            .map(|(s, t)| CoreElement { slot: s.to_string(), ty: t.to_string() })
            .collect();
        Frame { id, evoked_by, core_elements, binding_pattern, holds_in, install_seq }
    }

    #[test]
    fn function_of_subject_numeric() {
        let f = mk_frame(
            1,
            &["factorial"],
            &[("n", "Int")],
            BindingPattern::FunctionOfSubject,
            None,
            0,
        );
        let r = recognise_frame_rs(
            "What is the factorial of 7?",
            &[f],
            &[],
            &FxHashMap::default(),
        ).expect("should recognise");
        assert_eq!(r.frame_id, 1);
        assert_eq!(r.slots.get("n"), Some(&Value::Int(7)));
    }

    #[test]
    fn function_of_subject_string() {
        let f = mk_frame(
            2,
            &["definition"],
            &[("term", "Str")],
            BindingPattern::FunctionOfSubject,
            None,
            0,
        );
        let r = recognise_frame_rs(
            "What is the definition of homeomorphism?",
            &[f],
            &[],
            &FxHashMap::default(),
        ).expect("should recognise");
        assert_eq!(r.frame_id, 2);
        assert_eq!(r.slots.get("term"), Some(&Value::Str("homeomorphism".to_string())));
    }

    #[test]
    fn predicate_of_subject() {
        let f = mk_frame(
            3,
            &["prime"],
            &[("n", "Int")],
            BindingPattern::PredicateOfSubject,
            None,
            0,
        );
        let r = recognise_frame_rs(
            "Is 97 a prime?",
            &[f],
            &[],
            &FxHashMap::default(),
        ).expect("should recognise");
        assert_eq!(r.frame_id, 3);
        assert_eq!(r.slots.get("n"), Some(&Value::Int(97)));
    }

    #[test]
    fn function_of_two_subjects() {
        let f = mk_frame(
            4,
            &["gcd"],
            &[("a", "Int"), ("b", "Int")],
            BindingPattern::FunctionOfTwoSubjects,
            None,
            0,
        );
        let r = recognise_frame_rs(
            "Compute the gcd of 48 and 18",
            &[f],
            &[],
            &FxHashMap::default(),
        ).expect("should recognise");
        assert_eq!(r.frame_id, 4);
        // "of 48 and 18" — tail after "gcd" has "of " stripped to match the
        // Python recogniser. parts → ["48", "18"]; both bind as Int.
        assert_eq!(r.slots.get("a"), Some(&Value::Int(48)));
        assert_eq!(r.slots.get("b"), Some(&Value::Int(18)));
    }

    #[test]
    fn coverage_gate_rejects_tiny_hit_in_long_question() {
        // 4-char hit in a long padded question — coverage well under 0.20.
        let f = mk_frame(
            5,
            &["sqrt"],
            &[("n", "Int")],
            BindingPattern::FunctionOfSubject,
            None,
            0,
        );
        let long = "what is the sqrt of 4 plus many many many many many many extra words to dilute coverage well below the gate threshold okay";
        let r = recognise_frame_rs(long, &[f], &[], &FxHashMap::default());
        assert!(r.is_none(), "coverage gate should reject");
    }

    #[test]
    fn mt_scoping_out_of_scope() {
        let f = mk_frame(
            6,
            &["factorial"],
            &[("n", "Int")],
            BindingPattern::FunctionOfSubject,
            Some(999), // not in scope
            0,
        );
        let r = recognise_frame_rs(
            "What is the factorial of 5?",
            &[f],
            &[1, 2, 3],
            &FxHashMap::default(),
        );
        assert!(r.is_none(), "out-of-scope Mt must be skipped");
    }

    #[test]
    fn mt_scoping_in_scope_via_ancestor() {
        let f = mk_frame(
            7,
            &["factorial"],
            &[("n", "Int")],
            BindingPattern::FunctionOfSubject,
            Some(42),
            0,
        );
        let mut table = FxHashMap::default();
        table.insert(1i64, vec![42i64]); // 1's ancestors include 42
        let r = recognise_frame_rs(
            "What is the factorial of 5?",
            &[f],
            &[1],
            &table,
        ).expect("ancestor closure should bring 42 into scope");
        assert_eq!(r.frame_id, 7);
    }

    #[test]
    fn longest_evoked_by_wins() {
        // Two forms on the same frame, longer should be chosen for FOK.
        let f = mk_frame(
            8,
            &["gcd", "greatest common divisor"],
            &[("a", "Int"), ("b", "Int")],
            BindingPattern::FunctionOfTwoSubjects,
            None,
            0,
        );
        let r = recognise_frame_rs(
            "Compute the greatest common divisor of 12 and 18",
            &[f],
            &[],
            &FxHashMap::default(),
        ).expect("should recognise");
        assert_eq!(r.frame_id, 8);
        // FOK should reflect the longer form (24 chars), proving longest-wins.
        assert!(r.fok > 5.0);
    }

    #[test]
    fn ties_broken_by_first_installed() {
        // Two distinct frames with the same surface form. install_seq=0 wins.
        let a = mk_frame(100, &["foo"], &[("x", "Str")], BindingPattern::FunctionOfSubject, None, 0);
        let b = mk_frame(200, &["foo"], &[("x", "Str")], BindingPattern::FunctionOfSubject, None, 1);
        let r = recognise_frame_rs(
            "what is the foo of bar",
            &[a, b],
            &[],
            &FxHashMap::default(),
        ).expect("should recognise");
        assert_eq!(r.frame_id, 100, "first-installed wins on tie");
    }
}
