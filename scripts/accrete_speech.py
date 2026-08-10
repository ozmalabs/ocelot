"""Iterate over speech, accreting runtime PRIMITIVES the agent designs.

For each candidate primitive the agent reasons it needs, this drives the FULL
self-extension automatically (no hand-patching): emit Rust (mechanical compiler) ->
patch every TermNode home (mirror Max) -> cargo check -> maturin build -> install
-> re-measure speech on held-out speakers. Keep the primitive if it helps; revert
(git checkout) if it breaks the build. The accretion trajectory is the answer to
"add primitives until it can understand".
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)

from domains.runtime_design import emit_primitive_rust

DSL = "runners/dsl"
SRC = f"{DSL}/src"


def _ins(fn, anchor, addition, name):
    s = open(fn).read()
    if addition in s:                    # THIS specific site already patched
        return
    assert s.count(anchor) >= 1, f"anchor missing in {fn}: {anchor[:48]!r}"
    open(fn, "w").write(s.replace(anchor, anchor + addition, 1))


def patch_source(spec):
    name, lname = spec["name"], spec["name"].lower()
    helper = emit_primitive_rust(spec)["term.rs (helper)"]
    t = f"{SRC}/term.rs"
    _ins(t, "    Max { items: Vec<TermIdx> },\n",
         f"    {name} {{ items: Vec<TermIdx> }},\n", name)
    _ins(t, "        TermNode::Max { items } => numeric_minmax(arena, items, env, ctx, false),\n",
         f"        TermNode::{name} {{ items }} => numeric_{lname}(arena, items, env, ctx),\n", name)
    _ins(t, "    best.unwrap_or(Value::Int(0))\n}\n",
         "\n" + helper + "\n", name)
    _ins(t, "        TermNode::Max { items } =>\n            TermNode::Max { items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect() },\n",
         f"        TermNode::{name} {{ items }} =>\n            TermNode::{name} {{ items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect() }},\n", name)
    _ins(t, "        | TermNode::Min { items } | TermNode::Max { items }",
         f" | TermNode::{name} {{ items }}", name)
    j = f"{SRC}/jsonio.rs"
    _ins(j, '        TermNode::Max { .. } => "Max",\n',
         f'        TermNode::{name} {{ .. }} => "{name}",\n', name)
    _ins(j, '        "Max" => TermNode::Max { items: children_of("items", obj, arena, interner)? },\n',
         f'        "{name}" => TermNode::{name} {{ items: children_of("items", obj, arena, interner)? }},\n', name)
    _ins(j, "        | TermNode::Min { items } | TermNode::Max { items }",
         f" | TermNode::{name} {{ items }}", name)
    r = f"{SRC}/reflect.rs"
    _ins(r, '        TermNode::Max { items } => ("Max", vec![Children { name: "items", items }]),\n',
         f'        TermNode::{name} {{ items }} => ("{name}", vec![Children {{ name: "items", items }}]),\n', name)
    _ins(r, '        "Max" => TermNode::Max { items: take_children!("items") },\n',
         f'        "{name}" => TermNode::{name} {{ items: take_children!("items") }},\n', name)


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def install_so():
    dst = run([sys.executable, "-c",
               "import substrate_rs,os;print(os.path.dirname(substrate_rs.__file__))"]
              ).stdout.strip()
    src = f"{DSL}/python/substrate_rs/_native.abi3.so"
    if os.path.exists(src) and dst:
        subprocess.run(["cp", src, f"{dst}/_native.abi3.so"])


def measure():
    return run([sys.executable, "scripts/_measure_formant.py"]).stdout.strip()


def main():
    # genuine non-composable index primitives the agent reasons it needs
    toolset = [
        {"name": "ArgMin", "items_field": "items",
         "semantic_kind": "index_of_reduction", "reduce_op": "min"},
    ]
    def acc(line):
        try:
            return int(line.split("ACC")[1].split()[0])
        except Exception:
            return -1

    base = measure()
    best = acc(base)
    print(f"baseline (ArgMax only): {base}")
    for spec in toolset:
        print(f"\n>> agent designs + integrates {spec['name']} ...")
        patch_source(spec)
        chk = run(["cargo", "check"], cwd=DSL)
        if chk.returncode != 0:
            run(["git", "checkout", "--", "runners/dsl/src"])
            print(f"   {spec['name']}: cargo check FAILED -> reverted")
            continue
        if run(["maturin", "develop", "--release"], cwd=DSL).returncode != 0:
            run(["git", "checkout", "--", "runners/dsl/src"])
            print(f"   {spec['name']}: build FAILED -> reverted")
            continue
        install_so()
        m = measure()
        a = acc(m)
        if a > best:                          # KEEP only if it understands better
            best = a
            print(f"   {spec['name']} KEPT (improved): {m}")
        else:                                  # reject: revert source (rebuild clean)
            run(["git", "checkout", "--", "runners/dsl/src"])
            run(["maturin", "develop", "--release"], cwd=DSL)
            install_so()
            print(f"   {spec['name']} REJECTED (no gain: {m}) -> reverted to "
                  f"best {best}%")
    print(f"\ndone. kept runtime understands at {best}% (held-out speakers)")


if __name__ == "__main__":
    main()
