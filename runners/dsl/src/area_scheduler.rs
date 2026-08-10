//! Semantic cognitive areas and dependency-derived execution components.
//!
//! Areas describe cognition.  Read/write SCCs describe what may safely execute
//! independently.  The distinction is load-bearing: two rules called "vision"
//! are not automatically race-free, and two differently-named areas may still
//! form one execution component through a boundary dependency.

use crate::rewrite::RewriteRule;
use crate::sym::Sym;
use rustc_hash::FxHashMap;

#[derive(Clone, Debug)]
pub struct AreaInfo {
    pub area: Sym,
    pub rule_indices: Vec<usize>,
}

#[derive(Clone, Debug, Default)]
pub struct AreaSchedule {
    pub areas: Vec<AreaInfo>,
    /// Directed area dependencies: writer area -> reader area.
    pub dependencies: Vec<(usize, usize)>,
    /// Strongly connected area groups. Members and groups are stable by first
    /// global RuleIdx, never hash iteration order.
    pub components: Vec<Vec<usize>>,
}

fn intersects(a: &RewriteRule, b: &RewriteRule) -> bool {
    a.writes_any
        || b.reads_any
        || a.write_set.iter().any(|key| b.read_set.contains(key))
}

pub fn derive(rules: &[RewriteRule]) -> AreaSchedule {
    let mut area_pos: FxHashMap<Sym, usize> = FxHashMap::default();
    let mut areas: Vec<AreaInfo> = Vec::new();
    for (idx, rule) in rules.iter().enumerate().filter(|(_, r)| r.active) {
        let pos = *area_pos.entry(rule.area).or_insert_with(|| {
            areas.push(AreaInfo { area: rule.area, rule_indices: Vec::new() });
            areas.len() - 1
        });
        areas[pos].rule_indices.push(idx);
    }

    let mut deps = rustc_hash::FxHashSet::default();
    for (ai, a) in areas.iter().enumerate() {
        for (bi, b) in areas.iter().enumerate() {
            if ai == bi {
                continue;
            }
            if a.rule_indices.iter().any(|&ri| {
                b.rule_indices.iter().any(|&rj| intersects(&rules[ri], &rules[rj]))
            }) {
                deps.insert((ai, bi));
            }
        }
    }
    let mut dependencies: Vec<_> = deps.into_iter().collect();
    dependencies.sort_unstable();
    let components = tarjan(areas.len(), &dependencies);
    AreaSchedule { areas, dependencies, components }
}

fn tarjan(n: usize, edges: &[(usize, usize)]) -> Vec<Vec<usize>> {
    let mut adj = vec![Vec::new(); n];
    for &(a, b) in edges {
        adj[a].push(b);
    }
    for xs in &mut adj {
        xs.sort_unstable();
        xs.dedup();
    }
    struct State {
        index: usize,
        indices: Vec<Option<usize>>,
        low: Vec<usize>,
        stack: Vec<usize>,
        on_stack: Vec<bool>,
        out: Vec<Vec<usize>>,
    }
    fn visit(v: usize, adj: &[Vec<usize>], s: &mut State) {
        let idx = s.index;
        s.index += 1;
        s.indices[v] = Some(idx);
        s.low[v] = idx;
        s.stack.push(v);
        s.on_stack[v] = true;
        for &w in &adj[v] {
            if s.indices[w].is_none() {
                visit(w, adj, s);
                s.low[v] = s.low[v].min(s.low[w]);
            } else if s.on_stack[w] {
                s.low[v] = s.low[v].min(s.indices[w].unwrap());
            }
        }
        if s.low[v] == s.indices[v].unwrap() {
            let mut component = Vec::new();
            loop {
                let w = s.stack.pop().unwrap();
                s.on_stack[w] = false;
                component.push(w);
                if w == v {
                    break;
                }
            }
            component.sort_unstable();
            s.out.push(component);
        }
    }
    let mut state = State {
        index: 0,
        indices: vec![None; n],
        low: vec![0; n],
        stack: Vec::new(),
        on_stack: vec![false; n],
        out: Vec::new(),
    };
    for v in 0..n {
        if state.indices[v].is_none() {
            visit(v, &adj, &mut state);
        }
    }
    state.out.sort_by_key(|c| c.iter().copied().min().unwrap_or(usize::MAX));
    state.out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rewrite::RuleKey;

    #[test]
    fn dependency_scc_not_area_name_governs_components() {
        let a = Sym(10);
        let b = Sym(11);
        let x = Sym(20);
        let y = Sym(21);
        let mut r0 = RewriteRule { area: a, active: true, ..Default::default() };
        r0.write_set.insert(RuleKey::Attr(x));
        let mut r1 = RewriteRule { area: b, active: true, ..Default::default() };
        r1.read_set.insert(RuleKey::Attr(x));
        r1.write_set.insert(RuleKey::Attr(y));
        let mut r2 = RewriteRule { area: a, active: true, ..Default::default() };
        r2.read_set.insert(RuleKey::Attr(y));
        let schedule = derive(&[r0, r1, r2]);
        assert_eq!(schedule.areas.len(), 2);
        assert_eq!(schedule.components, vec![vec![0, 1]]);
    }
}
