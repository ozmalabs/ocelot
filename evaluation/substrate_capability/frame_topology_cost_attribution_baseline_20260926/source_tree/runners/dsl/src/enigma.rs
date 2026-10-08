//! Native hard admissibility kernel for graph-resident Enigma hypotheses.
//!
//! This is deliberately a predicate, not a solver hidden in Rust.  The
//! candidate's settings and the problem's crib data live in graph attrs; the
//! Γ term asks only whether the hypothesis survives an exact machine check.
//! Ranking, language models, and final presentation remain ordinary graph
//! composition above this kernel.

use crate::graph::{NodeID, TypedGraph};
use crate::sym::Interner;
use crate::value::{SurfaceKind, Value};

const ROTOR_WIRINGS: &[(&str, &str, Option<u8>)] = &[
    ("I", "EKMFLGDQVZNTOWYHXUSPAIBRCJ", Some(16)),
    ("II", "AJDKSIRUXBLHWTMCQGZNPYFVOE", Some(4)),
    ("III", "BDFHJLCPRTXVZNYEIWGAKMUSQO", Some(21)),
    ("IV", "ESOVPZJAYQUIRHXLNFTGKDCMWB", Some(9)),
    ("V", "VZBRGITYUPSDNHLXAWMJQOFECK", Some(25)),
    ("VI", "JPGVOUMFYQBENHZRDKASXLICT", Some(25)),
    ("VII", "NZJHGRCXMYSWBOUFAIVLPEKQDT", Some(25)),
    ("VIII", "FKQHTLXOCBJSPDZRAMEWNIUYGV", Some(25)),
    ("BETA", "LEYJVCNIXWPBQMDRTAKZGFUHOS", None),
    ("GAMMA", "FSOKANUERHMBTIYCWLQPZXVGJD", None),
];

const REFLECTORS: &[(&str, &str)] = &[
    ("A", "EJMZALYXVBWFCRQUONTSPIKHGD"),
    ("B", "YRUHQSLDPXNGOKMIEBFZCWVJAT"),
    ("C", "FVPJIAOYEDRZXWGCTKUQSBNMHL"),
    ("THIN-B", "ENKQAUYWJICOPBLMDXZVFTHRGS"),
    ("THIN-C", "RDOBJNTKVEHMLFCWZAXGYIPSUQ"),
];

#[derive(Clone)]
struct Rotor {
    forward: [u8; 26],
    inverse: [u8; 26],
    notch: Option<u8>,
    ring: u8,
    position: u8,
}

impl Rotor {
    fn at_notch(&self) -> bool {
        self.notch
            .map(|n| self.position == (n + 26 - self.ring) % 26)
            .unwrap_or(false)
    }

    fn step(&mut self) {
        self.position = (self.position + 1) % 26;
    }

    fn forward(&self, x: u8) -> u8 {
        (self.forward[((x + self.position + 26 - self.ring) % 26) as usize] + 26 - self.position
            + self.ring)
            % 26
    }

    fn backward(&self, x: u8) -> u8 {
        (self.inverse[((x + self.position + 26 - self.ring) % 26) as usize] + 26 - self.position
            + self.ring)
            % 26
    }
}

struct Machine {
    rotors: Vec<Rotor>,
    reflector: [u8; 26],
    plugboard: [u8; 26],
    stationary: usize,
}

impl Machine {
    fn step_rotors(&mut self) {
        let moving = self.rotors.len().saturating_sub(self.stationary);
        if moving == 0 {
            return;
        }
        let right = self.rotors.len() - 1;
        let middle = right.saturating_sub(1);
        let left = right.saturating_sub(2);
        let middle_notch = self.rotors[middle].at_notch();
        let left_notch = self.rotors[left].at_notch();
        if middle_notch {
            self.rotors[left].step();
        }
        if middle_notch || left_notch {
            self.rotors[middle].step();
        }
        self.rotors[right].step();
    }

    fn scramble(&self, x: u8) -> u8 {
        let mut y = x;
        for rotor in self.rotors.iter().rev() {
            y = rotor.forward(y);
        }
        y = self.reflector[y as usize];
        for rotor in self.rotors.iter() {
            y = rotor.backward(y);
        }
        y
    }

    fn encipher(&mut self, x: u8) -> u8 {
        self.step_rotors();
        let mut y = self.plugboard[x as usize];
        y = self.scramble(y);
        self.plugboard[y as usize]
    }
}

fn wiring(name: &str) -> Option<(&'static str, Option<u8>)> {
    ROTOR_WIRINGS
        .iter()
        .find(|(n, _, _)| *n == name)
        .map(|(_, w, notch)| (*w, *notch))
}

fn permutation(text: &str) -> Option<[u8; 26]> {
    let bytes = text.as_bytes();
    if bytes.len() != 26 || !bytes.iter().all(|b| b.is_ascii_uppercase()) {
        return None;
    }
    let mut out = [0u8; 26];
    for (i, b) in bytes.iter().enumerate() {
        out[i] = b - b'A';
    }
    Some(out)
}

fn rotor(name: &str, ring: u8, position: u8) -> Option<Rotor> {
    let (text, notch) = wiring(name)?;
    let forward = permutation(text)?;
    let mut inverse = [0u8; 26];
    for (i, &v) in forward.iter().enumerate() {
        inverse[v as usize] = i as u8;
    }
    Some(Rotor {
        forward,
        inverse,
        notch,
        ring,
        position,
    })
}

fn clean_letters(s: &str) -> Vec<u8> {
    s.bytes()
        .filter(|b| b.is_ascii_alphabetic())
        .map(|b| b.to_ascii_uppercase() - b'A')
        .collect()
}

fn value_text<'a>(value: &'a Value, interner: &'a Interner) -> Option<String> {
    match value {
        Value::Str(sym) => Some(interner.resolve(*sym).to_string()),
        Value::Surface(SurfaceKind::Text, bytes) => String::from_utf8(bytes.to_vec()).ok(),
        _ => None,
    }
}

fn attr<'a>(
    graph: &'a TypedGraph,
    node: NodeID,
    key: &str,
    interner: &'a Interner,
) -> Option<&'a Value> {
    let sym = interner.lookup(key)?;
    crate::access_trace::note(2, node.0, sym.0, crate::access_trace::NO_ID);
    graph.node(node).attrs.get(&sym)
}

fn attr_text(graph: &TypedGraph, node: NodeID, key: &str, interner: &Interner) -> Option<String> {
    attr(graph, node, key, interner).and_then(|v| value_text(v, interner))
}

fn attr_int(graph: &TypedGraph, node: NodeID, key: &str, interner: &Interner) -> Option<i64> {
    match attr(graph, node, key, interner)? {
        Value::Int(v) => Some(*v),
        Value::Rational(n, d) if *d != 0 && n % d == 0 => Some(n / d),
        Value::Float(v) if v.is_finite() && v.fract() == 0.0 => Some(*v as i64),
        Value::Bool(v) => Some(i64::from(*v)),
        _ => None,
    }
}

fn parse_numbers(value: &Value, interner: &Interner) -> Option<Vec<u8>> {
    if let Some(text) = value_text(value, interner) {
        let values: Vec<u8> = text
            .split(|c: char| c == ',' || c.is_ascii_whitespace() || c == '/')
            .filter(|s| !s.is_empty())
            .map(|s| s.parse::<u8>().ok())
            .collect::<Option<Vec<_>>>()?;
        return Some(values);
    }
    match value {
        Value::Tuple(items) | Value::List(items) => items
            .iter()
            .map(|v| match v {
                Value::Int(n) if (0..=25).contains(n) => Some(*n as u8),
                Value::Float(n) if n.fract() == 0.0 && (0.0..=25.0).contains(n) => Some(*n as u8),
                _ => None,
            })
            .collect(),
        _ => None,
    }
}

fn reflector(name: &str) -> Option<[u8; 26]> {
    let name = name.to_ascii_uppercase().replace('_', "-");
    if name.len() == 26 {
        return permutation(&name);
    }
    REFLECTORS
        .iter()
        .find(|(n, _)| *n == name)
        .and_then(|(_, wiring)| permutation(wiring))
}

fn plugboard(text: &str) -> Option<[u8; 26]> {
    let mut out = [0u8; 26];
    for (i, slot) in out.iter_mut().enumerate() {
        *slot = i as u8;
    }
    let mut used = [false; 26];
    for token in text
        .split(|c: char| c == ',' || c.is_ascii_whitespace() || c == '/')
        .filter(|s| !s.is_empty())
    {
        let bytes = token.as_bytes();
        if bytes.len() != 2 || !bytes.iter().all(|b| b.is_ascii_alphabetic()) {
            return None;
        }
        let a = (bytes[0].to_ascii_uppercase() - b'A') as usize;
        let b = (bytes[1].to_ascii_uppercase() - b'A') as usize;
        if a == b || used[a] || used[b] {
            return None;
        }
        used[a] = true;
        used[b] = true;
        out[a] = b as u8;
        out[b] = a as u8;
    }
    Some(out)
}

fn build_machine(graph: &TypedGraph, node: NodeID, interner: &Interner) -> Option<Machine> {
    let names: Vec<String> = attr_text(graph, node, "rotor_order", interner)?
        .split(|c: char| c == ',' || c.is_ascii_whitespace() || c == '/')
        .filter(|s| !s.is_empty())
        .map(|s| s.to_ascii_uppercase())
        .collect();
    if !(3..=4).contains(&names.len()) {
        return None;
    }
    let rings = parse_numbers(attr(graph, node, "ring", interner)?, interner)?;
    let positions = parse_numbers(attr(graph, node, "start", interner)?, interner)?;
    if rings.len() != names.len() || positions.len() != names.len() {
        return None;
    }
    let stationary = attr_int(graph, node, "stationary_rotors", interner).unwrap_or_else(|| {
        if names.len() == 4 && matches!(names[0].as_str(), "BETA" | "GAMMA") {
            1
        } else {
            0
        }
    }) as usize;
    if stationary > names.len().saturating_sub(3) {
        return None;
    }
    let mut rotors = Vec::with_capacity(names.len());
    for ((name, ring), position) in names.iter().zip(rings).zip(positions) {
        rotors.push(rotor(name, ring, position)?);
    }
    let reflector = reflector(&attr_text(graph, node, "reflector", interner)?)?;
    let plugboard = plugboard(&attr_text(graph, node, "plugboard", interner).unwrap_or_default())?;
    Some(Machine {
        rotors,
        reflector,
        plugboard,
        stationary,
    })
}

/// Return true iff the candidate node's machine decrypts the crib at its
/// offset. Invalid/incomplete candidates are inadmissible, never panics.
pub fn crib_admissible(graph: &TypedGraph, node: NodeID, interner: &Interner) -> bool {
    let Some(mut machine) = build_machine(graph, node, interner) else {
        return false;
    };
    let Some(ciphertext) =
        attr_text(graph, node, "ciphertext", interner).map(|s| clean_letters(&s))
    else {
        return false;
    };
    let Some(crib) = attr_text(graph, node, "crib", interner).map(|s| clean_letters(&s)) else {
        return false;
    };
    let offset = attr_int(graph, node, "crib_offset", interner).unwrap_or(0);
    if offset < 0 || (offset as usize).saturating_add(crib.len()) > ciphertext.len() {
        return false;
    }
    let offset = offset as usize;
    // Positions after the crib cannot affect this hard predicate. The
    // machine must advance through the prefix, but there is no reason to
    // decrypt the remainder of a long message just to check a short crib.
    for (i, &cipher) in ciphertext.iter().take(offset + crib.len()).enumerate() {
        let decoded = machine.encipher(cipher);
        if i >= offset && i < offset + crib.len() && decoded != crib[i - offset] {
            return false;
        }
    }
    true
}

fn set_pair(mapping: &mut [i8; 26], a: u8, b: u8) -> bool {
    let a = a as usize;
    let b = b as usize;
    if (mapping[a] >= 0 && mapping[a] as usize != b)
        || (mapping[b] >= 0 && mapping[b] as usize != a)
    {
        return false;
    }
    mapping[a] = b as i8;
    mapping[b] = a as i8;
    true
}

/// Return true iff at least one involutive plugboard can satisfy the crib.
/// This is the Bombe cut: a false result rejects the complete plugboard
/// space for the rotor/start hypothesis without materialising any plugboard.
pub fn bombe_admissible(graph: &TypedGraph, node: NodeID, interner: &Interner) -> bool {
    bombe_witness(graph, node, interner).is_some()
}

/// Return one crib-forced partial steckering, or `None` if every Bombe branch
/// contradicts. The witness is intentionally only the forced pairs; the
/// later completion stage owns soft language scoring.
pub fn bombe_witness(graph: &TypedGraph, node: NodeID, interner: &Interner) -> Option<String> {
    let Some(mut machine) = build_machine(graph, node, interner) else {
        return None;
    };
    let Some(ciphertext) =
        attr_text(graph, node, "ciphertext", interner).map(|s| clean_letters(&s))
    else {
        return None;
    };
    let Some(crib) = attr_text(graph, node, "crib", interner).map(|s| clean_letters(&s)) else {
        return None;
    };
    let offset = attr_int(graph, node, "crib_offset", interner).unwrap_or(0);
    if crib.is_empty()
        || offset < 0
        || (offset as usize).saturating_add(crib.len()) > ciphertext.len()
    {
        return None;
    }
    let offset = offset as usize;

    // Advance the odometer over the whole stream and retain the raw rotor
    // permutation only at crib positions. This is the expensive mechanical
    // part, but it stays inside the native term evaluation loop.
    let mut perms: Vec<[u8; 26]> = Vec::with_capacity(crib.len());
    for i in 0..offset + crib.len() {
        machine.step_rotors();
        if i >= offset && i < offset + crib.len() {
            let mut row = [0u8; 26];
            for x in 0..26 {
                row[x] = machine.scramble(x as u8);
            }
            perms.push(row);
        }
    }

    let mut freq = [0usize; 26];
    for &p in &crib {
        freq[p as usize] += 1;
    }
    let test_letter = freq
        .iter()
        .enumerate()
        .max_by_key(|(_, count)| **count)
        .map(|(letter, _)| letter as u8)
        .unwrap_or(0);

    // Keep the menu's ciphertext side separate from the full stream.
    let cipher_window = &ciphertext[offset..offset + crib.len()];
    for partner in 0..26u8 {
        let mut mapping = [-1i8; 26];
        if !set_pair(&mut mapping, test_letter, partner) {
            continue;
        }
        let mut ok = true;
        let mut changed = true;
        while ok && changed {
            changed = false;
            for i in 0..crib.len() {
                let plain = crib[i];
                let cipher = cipher_window[i];
                if mapping[plain as usize] >= 0 {
                    let middle = perms[i][mapping[plain as usize] as usize];
                    if mapping[cipher as usize] >= 0 {
                        if mapping[cipher as usize] as u8 != middle {
                            ok = false;
                            break;
                        }
                    } else if !set_pair(&mut mapping, cipher, middle) {
                        ok = false;
                        break;
                    } else {
                        changed = true;
                    }
                }
                if mapping[cipher as usize] >= 0 {
                    let wanted = mapping[cipher as usize] as u8;
                    let inverse = perms[i].iter().position(|&v| v == wanted).map(|v| v as u8);
                    let Some(inverse) = inverse else {
                        ok = false;
                        break;
                    };
                    if mapping[plain as usize] >= 0 {
                        if mapping[plain as usize] as u8 != inverse {
                            ok = false;
                            break;
                        }
                    } else if !set_pair(&mut mapping, plain, inverse) {
                        ok = false;
                        break;
                    } else {
                        changed = true;
                    }
                }
            }
        }
        if ok {
            let mut pairs = Vec::new();
            let mut seen = [false; 26];
            for (letter, &partner) in mapping.iter().enumerate() {
                if partner >= 0 && partner as usize != letter && !seen[letter] {
                    let a = letter.min(partner as usize);
                    let b = letter.max(partner as usize);
                    pairs.push(format!(
                        "{}{}",
                        (b'A' + a as u8) as char,
                        (b'A' + b as u8) as char
                    ));
                    seen[letter] = true;
                    seen[partner as usize] = true;
                }
            }
            pairs.sort();
            return Some(pairs.join(" "));
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn plugboard_rejects_reused_letter() {
        assert!(plugboard("AB CD").is_some());
        assert!(plugboard("AB AC").is_none());
    }

    #[test]
    fn rotor_notch_respects_ring_setting() {
        let base = rotor("I", 0, 16).unwrap();
        let shifted = rotor("I", 1, 15).unwrap();
        assert!(base.at_notch());
        assert!(shifted.at_notch());
    }
}
