# 60-second screencast script

A shot-by-shot guide for recording the live-Γ-swap demo. Designed to land the headline — **rule change in milliseconds, no retraining** — to an AI-researcher audience in under a minute.

## Pre-flight (do not record)

1. Close other browser tabs; close noisy apps.
2. Open a terminal. From this directory:
   ```bash
   python -m viz.server
   ```
3. Wait for `Uvicorn running on http://127.0.0.1:8000`.
4. Open <http://127.0.0.1:8000> in a fresh browser window. Resize to ~1280×800.
5. Click **Run** to confirm Conway runs at ~30 fps. Click **Stop**.
6. Click **Reset (random)** until you get an interesting initial pattern (mixed density, not all-dead by gen 50).
7. Press F11 for full-screen (browser, not OS).
8. Hide the OS clock / notifications.
9. Start the screen recorder. Record at 1080p, 30 fps.

## Take 1 — narration with timing

| Time | What's on screen | Narration (one breath each line) |
|---|---|---|
| 0:00 | Full UI, Conway label visible, board static | "This is the (G, Γ) substrate from Paper I — a typed graph with an admissibility grammar — running on a laptop CPU." |
| 0:05 | Click **Run**, board begins evolving | "Conway's Game of Life: four production rules. No neural net. No training." |
| 0:12 | Hover the **Custom Γ (JSON editor)** summary briefly, don't open | "The grammar is a small list of typed rules — fully introspectable, editable at runtime." |
| 0:18 | Click **HighLife** preset | "Watch the headline number. I'm swapping the grammar — not the substrate, not the board." |
| 0:20 | Wall-clock-ms number flashes — point at it | "Rule changed in ~50 milliseconds. Same board, new rule. No retraining." |
| 0:26 | Click **Day&Night** | "Day and Night. Self-complementary rule. Behaviour visibly different — same substrate, same board." |
| 0:33 | Click **Seeds** | "Seeds. Every alive cell dies. Explosive growth. One Γ-swap." |
| 0:40 | Click **Replicator** | "Replicator. Pattern propagates indefinitely. Four rules, same shape, completely different dynamics." |
| 0:47 | Open the **Custom Γ (JSON editor)** | "And the grammar is plain JSON. I can write any rule by hand." |
| 0:52 | Click **Sync from active Γ**, point at the JSON | "Sync from the running grammar — then edit any production." |
| 0:58 | (Cut to "thanks") | "Same substrate. Any rule. Milliseconds. Repo link below." |

## Take 2 — alt opening (skip narration if recording silent)

If recording silent for B-roll:

- 0:00–0:05: Run Conway for 5 seconds (let viewer recognise the pattern).
- 0:05–0:07: Hover, then click HighLife.
- 0:07–0:09: Pause on the **wall-clock-ms** indicator (this is the money shot).
- 0:09–0:20: Cycle Day&Night → Seeds → Replicator, ~3 seconds each.
- 0:20–0:30: Open JSON editor, Sync, edit one Lit value, Apply.
- 0:30–0:40: Show running under custom rule.

## Don't

- Don't show the terminal. The story is the substrate, not the server.
- Don't say "AI" or "intelligence" — say "substrate" and "grammar".
- Don't mention `python-chess` or "we're going to do chess next" — that's a separate video.
- Don't open the SPEC. Researchers will find it.

## Post

Title suggestion: **"(G, Γ) — rule change in milliseconds, no retraining"**
Description first line: **A working substrate from Paper I. Pure Python. Laptop CPU.**
Link to: this repo path + `SPEC.md` + Paper I.
