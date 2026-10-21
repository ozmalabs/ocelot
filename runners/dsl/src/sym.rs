//! String interner — every distinct string becomes a `Sym(u32)` so hot-path
//! comparisons (type names, edge types, attr keys, var names) are a single
//! `u32 == u32` instead of a byte-by-byte string compare. Critical for the
//! engine: a typical Filter walks `Eq(TypeOf(Var("x")), Lit("AliveCell"))`
//! once per probed cell — that's millions of string compares in a Conway
//! run that should be u32 equality instead.
//!
//! Interner is owned per-Substrate; tying it to the substrate guarantees
//! a Sym is only meaningful in the context it was minted, so we never mix
//! Syms across two graphs. The empty string interns to `Sym(0)` so
//! `Sym::default()` is meaningful.

use ahash::AHashMap;
use std::sync::Arc;

/// Interned-string handle. `u32` keeps the index narrow enough to fit
/// inline next to NodeID in EdgeKey without growing the struct.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Sym(pub u32);

// Pure native Terms sometimes need to construct a fixed vocabulary while
// `EvalCtx` holds the substrate interner immutably. Reserve these symbols at
// the top of the Sym space so they do not shift ordinary per-substrate IDs.
const RESERVED: &[&str] = &[
    "status", "values", "assumptions", "source_ids", "source_epoch", "reason", "factual", "counterfactual",
    "identified", "unknown", "invalid", "uniform_exogenous_assignments",
    "shared_supplied_exogenous_assignments", "assignment_cap_must_be_positive_integer",
    "assignment_cap_must_be_positive", "assignment_cap_exceeds_4096",
    "query_kind_missing_or_invalid", "unsupported_query_kind", "query_outcome_missing_or_invalid",
    "variables_missing_or_invalid", "empty_endogenous_model", "endogenous_variable_bound_exceeded",
    "variable_id_missing", "variable_domain_missing", "variable_domain_bound_exceeded",
    "duplicate_variable_id", "exogenous_variables_missing", "exogenous_id_missing",
    "exogenous_domain_missing", "exogenous_domain_bound_exceeded", "outcome_not_endogenous",
    "equations_missing_or_invalid", "incomplete_equation_set", "equation_target_missing",
    "unknown_or_duplicate_equation_target", "equation_parents_invalid", "equation_exogenous_invalid",
    "equation_references_unknown_variable", "equation_rows_invalid", "equation_row_inputs_invalid",
    "equation_row_value_missing", "equation_row_out_of_domain_or_wrong_inputs", "duplicate_equation_row",
    "equation_table_bound_exceeded", "incomplete_equation_table", "cyclic_or_unresolved_model",
    "intervention_not_a_dict", "intervention_out_of_domain", "exogenous_assignments_not_a_list",
    "empty_exogenous_assignment_set", "assignment_bound_exceeded", "exogenous_assignment_invalid",
    "exogenous_assignment_out_of_domain", "duplicate_exogenous_assignment", "equation_evaluation_failed",
    "outcome_unavailable", "factual_evaluation_failed", "counterfactual_evaluation_failed",
];

fn reserved_sym(text: &str) -> Option<Sym> {
    RESERVED.iter().position(|candidate| *candidate == text)
        .map(|index| Sym(u32::MAX - index as u32))
}

fn reserved_text(sym: Sym) -> Option<&'static str> {
    let index = u32::MAX.checked_sub(sym.0)? as usize;
    RESERVED.get(index).copied()
}

impl Default for Sym {
    fn default() -> Self {
        // Sym(0) is reserved for the empty string. Keeping a real value
        // here (rather than e.g. u32::MAX as a sentinel) means
        // `Sym::default()` round-trips through the interner without a
        // special case.
        Sym(0)
    }
}

impl Sym {
    /// Fixed vocabulary used by pure native Terms when their `EvalCtx` only
    /// has immutable access to its owning interner.
    pub fn reserved(text: &str) -> Option<Self> {
        reserved_sym(text)
    }
}

/// Owning interner. `Vec<Arc<str>>` lets us hand out cheap `&str` borrows
/// without holding the interner's lock; AHashMap is used because it's
/// faster than FxHashMap for short string keys.
#[derive(Clone)]
pub struct Interner {
    table: AHashMap<Arc<str>, Sym>,
    strings: Vec<Arc<str>>,
}

impl Interner {
    pub fn new() -> Self {
        let mut me = Self {
            table: AHashMap::with_capacity(256),
            strings: Vec::with_capacity(256),
        };
        // Reserve Sym(0) = "" so `Sym::default()` is well-defined and
        // round-trips losslessly.
        me.intern("");
        me
    }

    /// Intern `s` and return the canonical Sym. Idempotent.
    pub fn intern(&mut self, s: &str) -> Sym {
        if let Some(&sym) = self.table.get(s) {
            return sym;
        }
        let arc: Arc<str> = Arc::from(s);
        let sym = Sym(self.strings.len() as u32);
        self.strings.push(arc.clone());
        self.table.insert(arc, sym);
        sym
    }

    /// Look up a Sym's underlying string. Panics on an invalid Sym —
    /// invalid Syms are a programming error (a Sym minted in one
    /// interner used against another), not a runtime condition.
    pub fn resolve(&self, sym: Sym) -> &str {
        if let Some(text) = reserved_text(sym) {
            return text;
        }
        &self.strings[sym.0 as usize]
    }

    /// Look up a string without interning. Useful for membership-style
    /// queries (`grammar.candidates(src_type=...)`) that don't want to
    /// mutate the interner.
    pub fn lookup(&self, s: &str) -> Option<Sym> {
        self.table.get(s).copied()
    }

    pub fn len(&self) -> usize {
        self.strings.len()
    }

    /// Roll back symbols appended after a saved length. This is intended for
    /// failure-atomic staging before any new Sym has escaped into persistent
    /// graph, Term, rule, or grammar state.
    pub fn truncate(&mut self, len: usize) {
        assert!(
            len >= 1 && len <= self.strings.len(),
            "invalid interner rollback length"
        );
        for idx in (len..self.strings.len()).rev() {
            let text = self.strings[idx].as_ref();
            let removed = self.table.remove(text);
            debug_assert_eq!(removed, Some(Sym(idx as u32)));
        }
        self.strings.truncate(len);
    }

    pub fn is_empty(&self) -> bool {
        // Sym(0) = "" is always present, so the interner is never empty
        // in the structural sense; this just answers the count question.
        self.strings.len() <= 1
    }
}

impl Default for Interner {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn intern_is_idempotent() {
        let mut i = Interner::new();
        let a = i.intern("AliveCell");
        let b = i.intern("AliveCell");
        assert_eq!(a, b);
        assert_eq!(i.resolve(a), "AliveCell");
    }

    #[test]
    fn distinct_strings_get_distinct_syms() {
        let mut i = Interner::new();
        let a = i.intern("Alive");
        let b = i.intern("Dead");
        assert_ne!(a, b);
    }

    #[test]
    fn empty_string_is_default_sym() {
        let mut i = Interner::new();
        assert_eq!(i.intern(""), Sym::default());
        assert_eq!(i.resolve(Sym::default()), "");
    }

    #[test]
    fn lookup_does_not_intern() {
        let mut i = Interner::new();
        i.intern("x");
        let before = i.len();
        assert!(i.lookup("y").is_none());
        assert_eq!(i.len(), before);
    }

    #[test]
    fn reserved_term_symbols_do_not_change_local_interner_ids() {
        let mut i = Interner::new();
        assert_eq!(i.intern("ordinary"), Sym(1));
        let status = Sym::reserved("status").unwrap();
        assert_eq!(i.resolve(status), "status");
        assert_eq!(i.lookup("status"), None);
        assert_eq!(i.intern("next"), Sym(2));
    }

}
