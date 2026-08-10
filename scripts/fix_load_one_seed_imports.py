"""Fix the call-site swap: tests that now call load_one_seed(...) but (a) never
import it (NameError) and/or (b) still carry dead `from domains.X import
install_X_seed` lines (incl. line-continued, in-function) for burned builders
(ImportError). For each test file that uses load_one_seed:
  - ensure a module-level `from substrate.boot_all import load_one_seed`,
  - delete any `from domains.<X> import install_<X>_seed` import (single-line OR
    backslash-continued, at any indent).
Run with --apply to write.
"""
from __future__ import annotations
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPORT = "from substrate.boot_all import load_one_seed"
# `from domains.x import install_x_seed`  OR  `from domains.x import \<nl>  install_x_seed`
DEAD = re.compile(r"[ \t]*from domains\.\w+ import (?:\\\s*\n[ \t]*)?install_\w+_seed[ \t]*\n")


def fix(text: str) -> tuple[str, bool]:
    if "load_one_seed(" not in text:
        return text, False
    changed = False
    new = DEAD.sub("", text)
    if new != text:
        changed = True
    text = new
    if IMPORT not in text:
        # insert after the last top-level (col-0) import line near the top
        lines = text.splitlines(keepends=True)
        idx = 0
        for i, ln in enumerate(lines[:60]):
            if re.match(r"^(import |from )", ln):
                idx = i + 1
        lines.insert(idx, IMPORT + "\n")
        text = "".join(lines)
        changed = True
    return text, changed


def main() -> int:
    apply = "--apply" in sys.argv
    touched = []
    for p in glob.glob(os.path.join(ROOT, "tests", "*.py")) + \
            [os.path.join(ROOT, "domains", "code_writing_cortex.py")]:
        src = open(p).read()
        new, changed = fix(src)
        if changed:
            touched.append(os.path.relpath(p, ROOT))
            if apply:
                open(p, "w").write(new)
    print(f"{'fixed' if apply else 'would fix'}: {len(touched)} files")
    for t in touched:
        print("   ", t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
