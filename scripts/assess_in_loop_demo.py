import os, sys; sys.path.insert(0, os.getcwd())
import scripts.ask_agent as aa
from domains.acoustic_resolution import get_resolution
from domains.cue_assessment import agent_assess_cues
sub, pipe, test_set, vc, rec = aa._develop(cycles=10)
# the agent, in its loop, assesses its full feature menu on its own confusions
grounded = agent_assess_cues(sub, pipe, test_set, res=12)
print("\n== The agent autonomously assessed its feature menu on its own confusions ==\n")
for X,Y,cue,f,base in sorted(grounded, key=lambda r:-r[3]):
    print(f"  '{X}' vs '{Y}': grounded {cue:<13} (Fisher {f:.2f}, beat its whole-word {base:.2f})")
print(f"\n  grounded {len(grounded)} new discriminating features, by itself, "
      f"from {len(list(sub.nodes('Confusion')))} confusions — keeping only cues that "
      f"beat its plain average.")
