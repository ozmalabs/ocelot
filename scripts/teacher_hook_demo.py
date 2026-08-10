import os, sys; sys.path.insert(0, os.getcwd())
import scripts.ask_agent as aa
from domains.teacher_hook import needs_teacher, ask_if_needed
sub, pipe, test_set, vc, rec = aa._develop(cycles=10)
needs = needs_teacher(sub)
print(f"\n==== The agent's NEEDS (confusions it could not crack on its own):  ====\n")
if not needs:
    print("  (none — it resolved its confusions itself)")
for X,Y,n,f in needs[:6]:
    print(f"  '{X}' heard as '{Y}'  x{n}   (best self-found separation: Fisher {f:.2f})")
# the agent asks — stub teacher just marks the channel works; the real answer is mine
qa = ask_if_needed(sub, lambda q: "<pending teacher reply>", max_asks=3)
print(f"\n==== It reached for the teacher and asked (its own words, its own need):  ====\n")
for q,a in qa:
    print(f"  Q: {q}")
hints = [sub.node(h)['attrs'] for h in sub.nodes('TaughtHint')]
print(f"\n  recorded {len(hints)} TaughtHint node(s) for it to ground.")
