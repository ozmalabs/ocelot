"""CONVERSE DEMO — the on-device conversational loop: the agent talks, registers what it
DOESN'T know, ASKS the human (the in-band teacher, no network), grounds the answer, and carries
on — then can answer about what it just learned.

A world adapter (host I/O only, per CLAUDE.md). It makes NO decisions — every cognitive step is
a graph-native faculty already on the seed-booted WorldAdapter:

  comprehend + reply -> adapter.converse(text)                 [intent + reply rules]
  see what it missed -> adapter.discover_unknown_words(text)   [lexicon gap = the trigger to ask]
  ASK + GROUND       -> adapter.ground_unknowns(text, teacher) [per unknown word: teacher(word) ->
                        learn_from_teacher grounds the sign + memoises the answer]
  recall the learned -> adapter.answer_about(word)             [taught lookup / known fact]

The teacher is the PERSON in the conversation: `teacher(word)` asks them and returns the
definition. No network. Speech is under active development, so I/O is a pluggable Channel —
TextChannel works today; SpeechChannel is the seam where the graph-native ear + voice plug in
unchanged.

This also shows the deployment shape: LEARN TETHERED (a base vocabulary, here from a canned
dictionary standing in for prior learning), then CONVERSE UNTETHERED (the human is the only
teacher).

Run:
  PYTHONPATH=.:runners/dsl/python python -m scripts.converse_demo        # scripted self-test
  PYTHONPATH=.:runners/dsl/python python -m scripts.converse_demo -i     # interactive (stdin)
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries   # on-disk teacher chain: grammar->dict->wiki->tropes

SEP = "=" * 84
CHAT_SEEDS = ["relations", "intent", "conversation", "discourse", "conversation_reply",
              "reference_resolution", "language_foundation", "lang_production",
              "communication_concepts", "grounding"]

# A base vocabulary standing in for prior (tethered) learning, so genuinely-novel words are the
# exception. word -> plain-text gloss; grounded at boot via the same teacher path the human uses.
BASE_VOCAB = {
    "hello": "a greeting", "cat": "a small furry animal", "dog": "a four-legged animal",
    "sat": "rested on a surface", "mat": "a flat piece of floor covering",
    "bird": "a small creature that flies", "small": "little in size",
    "shabby": "worn and untidy", "ran": "moved quickly on foot", "big": "large in size",
    "animal": "a living creature", "hey": "a casual greeting", "yeah": "yes",
}


def _payload(word, gloss):
    """The teacher payload learn_from_teacher grounds a word from."""
    return {"learn": [{"phrase": word, "answer": gloss}], "answer": gloss}


# --------------------------------------------------------------------------- channels (the seam)
class Channel:
    def listen(self) -> str | None: raise NotImplementedError
    def say(self, who: str, text: str) -> None: raise NotImplementedError


class TextChannel(Channel):
    """Placeholder I/O: scripted turns (self-test) or stdin (interactive). Shared by the main
    loop AND the human-teacher callable, so an agent question consumes the human's next turn."""
    def __init__(self, scripted=None):
        self._scripted = list(scripted) if scripted is not None else None
    def listen(self):
        if self._scripted is not None:
            if not self._scripted:
                return None
            line = self._scripted.pop(0); print(f"  HUMAN : {line}"); return line
        try:
            return input("  HUMAN : ").strip()
        except EOFError:
            return None
    def say(self, who, text):
        print(f"  {who:<6}: {text}")


class SpeechChannel(Channel):
    """SEAM for live speech (under development): input = the graph-native ear's recognised turn,
    output = the agent's own voice synth. Plug SpeechWorld here; the loop is unchanged."""
    def __init__(self, speech_world): self.sw = speech_world
    def listen(self): raise NotImplementedError("wire SpeechWorld recognise->text")
    def say(self, who, text): raise NotImplementedError("wire the voice synth")


# --------------------------------------------------------------------------- boot + base vocab
def boot(seeds=CHAT_SEEDS):
    adapter = WorldAdapter()
    for sid in seeds:
        try:
            adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
        except Exception as e:
            print(f"  (seed '{sid}' skipped: {e})")
    adapter.install_register_lexicon()
    return adapter


def learn_tethered(adapter, vocab=BASE_VOCAB):
    """Ground a base vocabulary (prior learning). Same grounding path as the human teacher."""
    n = 0
    for word, gloss in vocab.items():
        try:
            adapter.learn_from_teacher(word, _payload(word, gloss)); n += 1
        except Exception as e:
            print(f"  (base '{word}' skipped: {e})")
    return n


def human_teacher(channel, adapter, human_taught):
    """The in-band human teacher — the LAST resort, after the on-disk libraries miss. When the
    agent meets a word even Wikipedia/TVTropes/the dictionary don't have, it asks the human (in
    the interlocutor's REGISTER — a polite hedge for the face-threat of asking). The human
    answering means THEY know it -> record on the interlocutor model. No network."""
    def ask(word):
        q = adapter.surface_for("inquire_unknown", word=word) or f"what is '{word}'?"
        channel.say("AGENT", q)
        ans = channel.listen()
        if not ans:
            return None
        adapter.note_interlocutor_knows(word)
        human_taught.add(word)
        return _payload(word, ans)
    return ask


def on_disk_then_human(adapter, human_ask):
    """Teacher CHAIN: try the on-disk libraries (grammar -> dictionary -> wikipedia -> tvtropes)
    first; only ask the human when they all miss. Returns a teacher(word)->payload callable."""
    head = getattr(adapter, "_self_teacher", None)        # set by attach_libraries

    def teach(word):
        if head is not None:
            try:
                p = head(word)
            except Exception:
                p = None
            if p:
                return p
        return human_ask(word)
    return teach


# --------------------------------------------------------------------------- the loop
def turn(adapter, channel, text, teacher, learned):
    sa = adapter.classify_speech_act(text)         # greeting/question/statement -> right reply rule
    adapter.note_register(text)                    # match the interlocutor's register
    try:
        reply = adapter.converse(text, speech_act=sa)
    except Exception as e:
        reply = None; print(f"  (converse error: {e})")
    if reply:
        channel.say("AGENT", adapter.surface_for(reply) or reply)   # render in matched register
    # MODEL THE INTERLOCUTOR: if they asserted a definition, they know it (given) -> record it.
    if sa == "statement":
        adapter.note_stated_knowledge(text)
    # INITIATIVE: volunteer something relevant it KNOWS about the topic — but only what's NEW to
    # the interlocutor (given/new); never tell them what they already know.
    if sa == "statement":
        contrib = adapter.compose_contribution(text)
        if contrib:
            form, fact = contrib
            channel.say("AGENT", f"{form} — {fact}.")
    # SEE WHAT IT DOESN'T KNOW -> consult the on-disk libraries (silent), else ASK the human.
    try:
        got = adapter.ground_unknowns(text, teacher=teacher)
    except Exception as e:
        got = []; print(f"  (ground error: {e})")
    learned.extend(got)
    return got


def main():
    interactive = "-i" in sys.argv or "--interactive" in sys.argv
    print(SEP)
    print("CONVERSE DEMO — converse, ask what it doesn't know, learn from the human (no network)")
    print(SEP)
    adapter = boot()
    nbase = learn_tethered(adapter)
    rep = attach_libraries(adapter, log=lambda *a: None)   # on-disk teacher chain
    print(f"  learned-tethered base vocabulary: {nbase} words; on-disk libraries: "
          f"{rep['teachers']}; now conversing untethered\n")
    human_taught = set()

    if interactive:
        channel = TextChannel(scripted=None)
        learned = []
        t = on_disk_then_human(adapter, human_teacher(channel, adapter, human_taught))
        print("  (type a turn; Ctrl-D to end)\n")
        while True:
            line = channel.listen()
            if line is None:
                break
            if line:
                turn(adapter, channel, line, t, learned)
        _report(adapter, learned, human_taught)
        return

    # SCRIPTED self-test: a real word the agent doesn't know but the LIBRARIES do (looked up on
    # disk, silently), then a NONSENSE word only the human can supply (asked).
    script = [
        "hey",                     # CASUAL register -> the agent matches it
        "the aardvark sat",        # 'aardvark' unknown to agent but ON DISK -> grounded silently
        "what is an aardvark",     # answers from what it looked up (never asked the human!)
        "a dog is a big animal",   # human DEFINES dog -> agent records the interlocutor KNOWS dog
        "the dog sat",             # dog is GIVEN -> suppressed; 'sat' is NEW -> offered
        "the borogove sat",        # 'borogove' nonsense -> libraries miss -> asks the HUMAN...
        "a borogove is a small bird",  # ...human answers (consumed by the teacher)
        "what is a borogove",      # now known -> answers from what the human taught
    ]
    channel = TextChannel(scripted=script)
    t = on_disk_then_human(adapter, human_teacher(channel, adapter, human_taught))
    learned = []
    while True:
        line = channel.listen()
        if line is None:
            break
        if line:
            turn(adapter, channel, line, t, learned)
    _report(adapter, learned, human_taught)


def _report(adapter, learned, human_taught=frozenset()):
    print("\n" + SEP)
    from_disk = [w for w in learned if w not in human_taught]
    print(f"  grounded from ON-DISK libraries (wikipedia/tvtropes/dictionary), no asking: "
          f"{from_disk}")
    print(f"  asked the human only for what's NOT on disk: {sorted(human_taught)}")
    known_forms = {s.get("form") for s in adapter.taught_signs()}
    caps = adapter.taught_capabilities()
    for w in sorted(set(learned)):
        known = w in known_forms                              # the path ground_unknowns checks
        concept = "taught_" + w
        try:
            meaning = caps[concept](None) if concept in caps else None
        except Exception:
            meaning = None
        # PROOF it learned: it no longer asks about the word (refusing teacher -> empty if known).
        reasked = adapter.ground_unknowns(f"the {w} flew", teacher=lambda _w: None)
        src = "human" if w in human_taught else "on-disk library"
        print(f"  '{w}' (via {src}): known now={known}  no longer asks={w not in reasked}  "
              f"meaning={meaning!r}")
    print(f"  the agent's MODEL of what the interlocutor knows: {adapter.interlocutor_knowledge()}")
    print("  (it offers only what's NEW to them, and never tells them what they already know.)")
    detected = adapter.register()
    print(f"\n  register matched to the interlocutor: {detected!r}  "
          "(its turns shaped to it; the ask politely hedged)")
    print("  the SAME acts rendered per register (greeting / acknowledgment / ask):")
    for reg in ("casual", "neutral", "formal"):
        adapter.inner.set_attr(adapter._interlocutor(), "register", reg)
        print(f"    {reg:<7}: {adapter.surface_for('greeting')} / "
              f"{adapter.surface_for('acknowledgment')} / "
              f"{adapter.surface_for('inquire_unknown', word='borogove')}")
    adapter.inner.set_attr(adapter._interlocutor(), "register", detected)
    print("\n  the human was the teacher — no network. (speech: TextChannel -> SpeechChannel)")
    print(SEP)


if __name__ == "__main__":
    main()
