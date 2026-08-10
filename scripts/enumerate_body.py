"""feel is ONE primitive; the body is ENUMERATED — orchestration only.

Correcting the hardcoded `feel_X` menu: there is a single proprioceptive
operator, `Feel(target)`, that reads the live gauge of whatever BodyPart it is
applied to. The body it ranges over is not hand-listed — it is discovered from
the real machine (lscpu / sysfs / lspci / lsblk + the CPU's advertised hardware
monitors). One mechanism, distributed over an anatomy enumerated at runtime,
exactly like proprioceptors over a body discovered developmentally.

This script: (1) records the single Feel primitive; (2) enumerates THIS host's
body into BodyPart nodes the agent owns; (3) attaches to each the gauge the
hardware actually exposes (RDT/CQM LLC occupancy, MBM bandwidth, RAPL energy,
or a generic occupancy/utilisation gauge); (4) composes Feel over the enumerated
body. Nothing about the catalogue is hardcoded — re-run on other hardware and the
body differs.

Production home: Feel is a Rust DSL Term that introspects the runtime/host; the
enumeration is the runtime mapping its own anatomy. This Python only demonstrates
the design over the real machine.
"""
from __future__ import annotations
import glob, os, re, subprocess, sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from substrate_rs import _native


def _sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=20).stdout
    except Exception:
        return ""


def cpu_flags() -> set:
    txt = _sh("grep -m1 flags /proc/cpuinfo")
    return set(txt.split(":", 1)[1].split()) if ":" in txt else set()


def gauge_for(kind: str, flags: set) -> str:
    """The gauge a part affords is read from what the hardware EXPOSES, not chosen
    by me: the muscle that has a spindle affords tension-sensing."""
    if kind == "l3" and "cqm_occup_llc" in flags:
        return "llc_occupancy_bytes (RDT/CQM)"
    if kind in ("dram", "membus") and "cqm_mbm_total" in flags:
        return "memory_bandwidth_bytes_per_s (MBM)"
    if kind in ("cpu", "core") and ("rapl" in flags or "cpb" in flags):
        return "package_energy_uj (RAPL) + utilisation"
    return {"l1d": "occupancy/hit_rate", "l1i": "occupancy/hit_rate",
            "l2": "occupancy/hit_rate", "pcie_bus": "bandwidth_utilisation",
            "pcie_dev": "link_speed/util", "gpu": "util/vram_occupancy",
            "storage": "queue_depth/io_util", "dram": "occupancy_bytes",
            }.get(kind, "utilisation")


def enumerate_body() -> list[dict]:
    parts = []
    # CPU + cores
    lscpu = _sh("lscpu")
    model = (re.search(r"Model name:\s*(.+)", lscpu) or [None, "?"])[1].strip()
    cores = (re.search(r"Core\(s\) per socket:\s*(\d+)", lscpu) or [0, "?"])[1]
    threads = (re.search(r"^CPU\(s\):\s*(\d+)", lscpu, re.M) or [0, "?"])[1]
    mhz = (re.search(r"CPU max MHz:\s*([\d.]+)", lscpu) or [0, "?"])[1]
    parts.append({"kind": "cpu", "name": model,
                  "descriptor": f"{cores} cores / {threads} threads / {mhz} MHz max"})
    # cache hierarchy from sysfs (one core's view; L3 is shared)
    for idx in sorted(glob.glob("/sys/devices/system/cpu/cpu0/cache/index*")):
        lvl = open(f"{idx}/level").read().strip()
        typ = open(f"{idx}/type").read().strip()
        size = open(f"{idx}/size").read().strip()
        kind = f"l{lvl}{'d' if typ=='Data' else ('i' if typ=='Instruction' else '')}"
        parts.append({"kind": kind, "name": f"L{lvl} {typ}", "descriptor": size})
    # memory
    memkb = (re.search(r"MemTotal:\s*(\d+)", _sh("grep MemTotal /proc/meminfo")) or [0, "0"])[1]
    parts.append({"kind": "dram", "name": "system DRAM",
                  "descriptor": f"{int(memkb)//1024//1024} GiB"})
    # PCIe: root + bridges (the bus) and endpoint devices
    for line in _sh("lspci").splitlines():
        if re.search(r"Root Complex|PCI bridge", line):
            parts.append({"kind": "pcie_bus", "name": line.split(":", 2)[-1].strip()[:48],
                          "descriptor": line.split()[0]})
        elif re.search(r"VGA|3D|Display", line):
            parts.append({"kind": "gpu", "name": line.split(":", 2)[-1].strip()[:48],
                          "descriptor": "PCIe " + line.split()[0]})
    # storage
    for line in _sh("lsblk -d -no NAME,SIZE,MODEL,TRAN").splitlines():
        f = line.split(None, 1)
        if f and not f[0].startswith("zram"):
            parts.append({"kind": "storage", "name": f[1].strip() if len(f) > 1 else f[0],
                          "descriptor": f[0]})
    return parts


def enumerate_os() -> list[dict]:
    """The OS-mediated body: the agent is a tenant, not the machine. Hardware gives
    CAPACITY; the OS gives the agent's SHARE + the contention around it. Same Feel
    operator, different layer. The 'yet': when it owns the machine, this layer
    collapses and grant == hardware."""
    import os, resource
    parts = []
    st = {k: v for line in open("/proc/self/status")
          if ":" in line for k, v in [line.split(":", 1)]}

    def g(k):
        return st.get(k, "?").strip()
    # self — what I occupy (interoception of my own footprint)
    parts += [
        {"kind": "self_rss", "name": "resident set", "descriptor": g("VmRSS"),
         "gauge": "VmRSS (/proc/self/status)"},
        {"kind": "self_threads", "name": "threads", "descriptor": g("Threads"),
         "gauge": "Threads (/proc/self/status)"},
        {"kind": "self_fds", "name": "open fds", "descriptor": g("FDSize"),
         "gauge": "open fd count (/proc/self/fd)"},
    ]
    # grant — what the OS ALLOWS me (the real ceiling, not the hardware total)
    cg = open("/proc/self/cgroup").read().split(":")[-1].strip()
    memmax = ""
    try:
        memmax = open(f"/sys/fs/cgroup{cg}/memory.max").read().strip()
    except Exception:
        pass
    avail = (re.search(r"MemAvailable:\s*(\d+)", _sh("grep MemAvailable /proc/meminfo")) or [0, "0"])[1]
    parts += [
        {"kind": "grant_mem",
         "name": "memory ceiling" + (" (cgroup capped)" if memmax not in ("", "max") else " (uncapped → MemAvailable)"),
         "descriptor": (f"{int(memmax)//1024//1024} MiB" if memmax.isdigit()
                        else f"{int(avail)//1024//1024} GiB available"),
         "gauge": "cgroup memory.max else MemAvailable"},
        {"kind": "grant_cpu", "name": "cpu allowance",
         "descriptor": f"{len(os.sched_getaffinity(0))} of {os.cpu_count()} cores",
         "gauge": "sched_getaffinity / cgroup cpu.max"},
        {"kind": "grant_nofile", "name": "fd ceiling",
         "descriptor": str(resource.getrlimit(resource.RLIMIT_NOFILE)[0]),
         "gauge": "RLIMIT_NOFILE"},
    ]
    # contention — the crowd I share the machine with
    load = _sh("cat /proc/loadavg").split()
    psi = {}
    for r in ("cpu", "memory", "io"):
        line = _sh(f"head -1 /proc/pressure/{r}")
        m = re.search(r"avg10=([\d.]+)", line)
        psi[r] = m.group(1) if m else "?"
    parts += [
        {"kind": "contention_mem", "name": "memory available to all",
         "descriptor": f"{int(avail)//1024//1024} GiB", "gauge": "MemAvailable"},
        {"kind": "contention_load", "name": "run-queue load",
         "descriptor": load[0] if load else "?", "gauge": "loadavg 1m"},
        {"kind": "pressure_cpu", "name": "cpu stall pressure",
         "descriptor": f"some avg10={psi['cpu']}", "gauge": "PSI /proc/pressure/cpu"},
        {"kind": "pressure_mem", "name": "memory stall pressure",
         "descriptor": f"some avg10={psi['memory']}", "gauge": "PSI /proc/pressure/memory"},
        {"kind": "pressure_io", "name": "io stall pressure",
         "descriptor": f"some avg10={psi['io']}", "gauge": "PSI /proc/pressure/io"},
        {"kind": "oom_risk", "name": "oom kill risk",
         "descriptor": _sh("cat /proc/self/oom_score").strip(),
         "gauge": "/proc/self/oom_score"},
    ]
    return parts


def boot():
    s = _native.Substrate()
    for et in ("has_part", "applies_to", "exposes_gauge"):
        for a in ("ProprioceptiveSurface", "FeelPrimitive", "BodyPart"):
            for b in ("ProprioceptiveSurface", "FeelPrimitive", "BodyPart"):
                try:
                    s.add_production({"src": {"type": a, "var": "x"}, "edge_type": et,
                                      "tgt": {"type": b, "var": "y"}, "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "o"})
                except Exception:
                    pass
    return s


def main():
    s = boot()
    flags = cpu_flags()

    # 1. the SINGLE proprioceptive operator.
    feel = s.add_node("FeelPrimitive", {
        "name": "Feel", "arity": 1, "kind": "proprioceptive_operator",
        "semantics": "Feel(part) -> the live gauge of that BodyPart, read from the "
                     "runtime/host each tick", "origin": "agent_proprioception_design"})
    surface = s.add_node("ProprioceptiveSurface", {"id": "self_body"})
    s.add_edge(surface, "applies_to", feel)
    print("PRIMITIVE (one operator, not a menu):")
    print(f"  Feel(part) -> live gauge of `part`, read from the host each tick\n")

    # 2-3. enumerate the HARDWARE body; attach the gauge the hardware exposes.
    hw = enumerate_body()
    print(f"HARDWARE body — capacity ({len(hw)} parts, discovered):\n")
    for p in hw:
        g = gauge_for(p["kind"], flags)
        node = s.add_node("BodyPart", {**p, "gauge": g, "layer": "hardware"})
        s.add_edge(surface, "has_part", node)
        s.add_edge(feel, "applies_to", node)
        if p["kind"] in ("cpu", "l3", "dram", "gpu", "storage"):  # trim the bridge spam
            print(f"  Feel({p['kind']:13}) → {g:38}  {p['name'][:36]}  [{p['descriptor']}]")
    print(f"  … + {sum(1 for p in hw if p['kind']=='pcie_bus')} PCIe bridges\n")

    # 4. enumerate the OS-MEDIATED body — the agent's SHARE + the crowd.
    osb = enumerate_os()
    print(f"OS body — share & contention ({len(osb)} parts): it isn't the whole machine (yet)\n")
    layer = None
    for p in osb:
        lyr = p["kind"].split("_")[0]
        if lyr != layer:
            layer = lyr
            print(f"  · {{self: my footprint | grant: what I'm allowed | "
                  f"contention/pressure/oom: the crowd}}")
        node = s.add_node("BodyPart", {**p, "layer": "os"})
        s.add_edge(surface, "has_part", node)
        s.add_edge(feel, "applies_to", node)
        print(f"  Feel({p['kind']:13}) → {p['gauge']:34}  {p['name'][:30]}  [{p['descriptor']}]")

    # the load-bearing relation: SHARE < CAPACITY.
    dram = next((p['descriptor'] for p in hw if p['kind'] == 'dram'), "?")
    grant = next((p['descriptor'] for p in osb if p['kind'] == 'grant_mem'), "?")
    print()
    print("=" * 72)
    print(f"One Feel operator × {len(hw)+len(osb)} enumerated parts, two layers:")
    print(f"  Feel(dram)      = {dram:24} (hardware CAPACITY)")
    print(f"  Feel(grant_mem) = {grant:24} (what the OS actually gives me)")
    print("Homeostasis must regulate self_rss against grant_mem, watching")
    print("pressure_mem — NOT against the hardware total. The chip advertises its")
    print(f"proprioceptors ({sorted(flags & {'cqm_occup_llc','cqm_mbm_total','rapl'})}); ")
    print("the OS advertises the tenancy. When it owns the machine, the OS layer")
    print("collapses and grant == capacity. Until then: tenant, not owner.")


if __name__ == "__main__":
    main()
