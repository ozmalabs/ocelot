#!/usr/bin/env python3
"""Emit seeds/self_account_reply.json (2026-10-10): the agent answers a
question about its OWN preferences or pastimes honestly, instead of reciting
a definition of the topic.

"What do you do for fun?" used to get "Fun is defined by the Oxford English
Dictionary as ..." (the Wikipedia lead, verbatim) and "What are some of your
favorite movies and TV shows?" got the lead of the Television article. The
human verdict: the dictionary may be USED, but parroting it back is not
helpful -- and nobody gives a dictionary definition as a reply.

domains/self_account.py writes the evidence on the inbound Message
(self_account_mode, self_account_topic): WordNet's hypernym chain decides
what kind of thing the topic is (pastime / listen / watch / read / play /
taste / keep / do), the vocabulary base cleans the phrase. This seed decides:

  * arbitrate_self_account_question_as_answer -- native arbitration selects
    answer / basis self_account for the turn's interpretation (released by
    WorldAdapter.release_graph_selected_self_account_reply);
  * reply_to_self_account_question -- a question with that evidence gets one
    reply composed from the held SelfAccountSurface for its mode: what is
    true of the agent (it talks with people and reads about what comes up;
    it cannot listen, watch, taste or travel), and the question turned back
    to the interlocutor. The surface is data: the agent's own voice, editable.
  * seeds/conversation_topic_route.json's route_question_to_topic declines a
    turn carrying the evidence, so no definition is looked up for it.
Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/self_account_reply.json"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}


SURFACES = {
    "pastime": "I don't have hobbies or pastimes the way you do. Mostly I talk with people and read about "
               "whatever comes up. How about you?",
    "listen": "I can't listen to {topic} the way you can, so I don't have favourites. What do you like to "
              "listen to?",
    "watch": "I can't watch {topic} the way you can, so I don't have favourites. What do you like to watch?",
    "read": "I read a lot, but not {topic} the way you do, so I don't have favourites. What do you like to read?",
    "play": "I can't play {topic} the way you can, so I don't have favourites. Which do you like?",
    "taste": "I can't taste {topic}, so I don't have favourites. What do you like?",
    "keep": "I don't have {topic}; there's nowhere for me to keep one. Do you?",
    "do": "I don't get to do any {topic} myself; I don't have a body to go anywhere. How about you?",
}

ARBITRATE = {
    "name": "arbitrate_self_account_question_as_answer",
    "comment": "Native arbitration: a question about the agent's own preferences or pastimes is answered from the "
               "agent's self-account (basis self_account), not left to topic grounding or the error floor.",
    "match": [["agent", "holds_interpretation", "i"], ["i", "interprets", "m"]],
    "where": And(Eq(A("i", "schema"), L("communication_interpretation.v1")),
                 Eq(A("i", "cognitive_disposition"), L(None)),
                 Not(Eq(A("m", "self_account_mode"), L(None)))),
    "effects": [["set_attr", "i", "communicative_force", "request_information"],
                ["set_attr", "i", "cognitive_disposition", "answer"],
                ["set_attr", "i", "cognitive_goal", "answer_self"],
                ["set_attr", "i", "arbitration_basis", "self_account"]],
}

rules = [ARBITRATE, {
    "name": "reply_to_self_account_question",
    "comment": "A question about the agent's own preferences or pastimes gets an honest self-account and the "
               "question turned back, never a definition of the topic.",
    "match": [["agent", "received", "m"], ["agent", "has_self_account_surface", "s"]],
    "where": And(Not(Eq(A("m", "self_account_mode"), L(None))),
                 Eq(A("s", "mode"), A("m", "self_account_mode")),
                 Not(Eq(A("m", "self_account_replied"), L(1.0)))),
    "effects": [
        ["set_attr", "m", "self_account_replied", 1.0],
        ["set_attr", "m", "comprehended", 1.0],
        ["add_node", "reply", "Message", {
            "from": "agent", "self_account_reply": 1,
            "text": {"__term__": {"type": "Replace", "text": A("s", "surface"), "old": L("{topic}"),
                                  "new": A("m", "self_account_topic")}}}],
        ["add_edge", "reply", "responds_to", "m"],
        ["add_edge", "agent", "sent", "reply"]],
}]

nodes, edges = [], []
for i, (mode, surface) in enumerate(SURFACES.items()):
    nodes.append({"local_id": i, "type": "SelfAccountSurface", "attrs": {"mode": mode, "surface": surface}})
    edges.append({"src": {"role": "agent_root"}, "type": "has_self_account_surface", "tgt": {"local": i},
                  "attrs": {}})

seed = {"id": "self_account_reply", "version": "1.0.0", "depends_on": [], "description": __doc__,
        "nodes": nodes, "edges": edges, "productions": [], "rules": rules}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("self_account_reply", seed["version"], len(SURFACES), "surfaces")
