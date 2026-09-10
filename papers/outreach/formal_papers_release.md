# The rest is science: how a routing problem became nineteen papers

**A plain-language release note.** Matthew Parslow, 6 September 2026 — current formal draft: `draft-2026-09-06.1`.

**Status: 19 cleared preprints, circulated for comment; not finished or peer-reviewed results.** This is the story of why the papers exist. It is not evidence that their claims are true. The papers themselves carry the arguments, assumptions, evidence, and points of failure.

---

This did not begin as a plan to write about physics, consciousness, or ontology. It began with a routing problem.

I was building Ozma, a software-defined networked system for routing keyboard, video, mouse, and audio between machines. At first that sounds like plumbing: a keyboard here, a screen there, an audio stream somewhere else. But the problem becomes interesting as soon as it has to scale. The things being routed have types. Their connections have types. Some connections are allowed, some are not. A route that makes sense for audio can be nonsense for a keyboard. The system needs a map of what is connected to what, and rules for what those connections mean.

That map was the first graph.

Then building Ozma with language models exposed another problem. It was not simply that the models needed to be better. The expensive part was often the context around them: repeatedly passing large, loose bodies of information through a chain of tools and models, then writing bespoke glue for every hand-off. The work needed more efficient LLM inference, but it also needed a way to make the work itself legible enough to move.

So I built a second graph system. It represented tasks, state, capabilities, and specialist hand-offs as structured, typed relations rather than as an ever-growing conversation. Compact context and scoped delegation were not decoration around the model. They were an attempt to give each part of a job only the information and authority it needed.

That did not solve inference in general. It did make one engineering question much sharper: what has to be true for a system of relations to remain inspectable, composable, and cheap enough to use?

## The same shape, twice

The routing graph and the model-coordination graph came from different practical problems. One moved signals between machines. The other organised work around language models. But both required labelled things, labelled relationships, and constraints on what could connect or change.

The comparison did not prove that all systems are one graph. It was a prompt to ask a more fundamental question.

The thread I kept pulling was the same one I use on an engineering problem: what is the unstated assumption here? Then remove it and see what the removal costs. If nothing breaks, the description was carrying dead weight. If something does break, the break names a condition the system actually needs. That is not a rhetorical trick. It is a way of making a vague discomfort into a concrete question.

The question changed scale without changing form. A routing design assumes some connections are meaningful and others are not. A model workflow assumes that a conversation, a hand-off, or a body of context is the natural unit of work. Pulling at those assumptions exposed relations, constraints, and histories that had been treated as background. The thread eventually reached the word *is*: what has to be present before anything can count as a determinate thing at all?

What does a graph need before it can do explanatory work? A list of nodes and edges is not enough. It also needs a way to say which relations are admissible, which changes preserve the structure at issue, and which apparent moves are not really part of the system at all.

That is where the work stopped being only a software project. The question was no longer how to route a keyboard or divide work among models. It was whether relation, distinction, compression, accessibility, persistence, and consequence could be treated as one family of problems without quietly adding a privileged observer, an unexplained category, or a rule that only applies where it is convenient.

The formal papers are the attempt to make that question answerable.

## From an engineering pattern to scientific claims

The papers begin with a small claim: to be is to stand in relation and cohere in it. They ask what follows if that claim is made explicit and then held to the same standard as an engineering design.

That does not mean a routing system proves a theory of reality. It means the engineering work made a structural question hard to ignore. Once a design keeps encountering the same distinction—between a connection and an allowed connection, between an available possibility and a realised state, between a useful compression and lost information—the right next step is not to declare victory. It is to state the distinction clearly, look for prior work, and test where it stops carrying.

That is why the papers are formal preprints rather than a product announcement. They try to say exactly what is being claimed, which parts are inherited from existing work, which parts are contingent, and what would count against the arrangement.

Some arguments concern physical grounding and cosmology. Others concern mind, self, communication, qualia, social and psychological application, narrative, and audit. They are not all the same claim in different language. Each paper names what it takes from the shared framework, what it adds, and the boundary at which its conclusion no longer follows.

The release is therefore not a request to accept a large story whole. It is a request to inspect particular joints in it.

## Where to start

You do not need to read nineteen papers in order.

- Start with [`00_is`](../formal/00_is.pdf) for the single premise and the method before any application.
- Start with [`01`, the longer theory paper](../formal/01_law_of_graphic_equalisation_theory_referenced.pdf) for the proposed structure and its dependencies.
- Start with [`01a`, the physics grounding](../formal/01a_graphic_equalisation_physics_grounding.pdf) for the claims concerning constants, relativity, thermodynamics, and measurement.
- Start with [`01c`, the cosmology grounding](../formal/01c_graphic_equalisation_cosmology_grounding.pdf) for the measure problem, anthropic reasoning, and the cosmological principle.
- Start with [`01f`, the qualia and consciousness grounding](../formal/01f_graphic_equalisation_qualia_and_consciousness_grounding.pdf) for the argument that consciousness should not receive exceptional ontological treatment merely because it is familiar to humans.
- Start with [`07`, causal attitude networks](../formal/07_causal_attitude_networks_on_the_substrate.pdf) for a smaller engineering record: a native graph-rule system, the limits it retains, and findings that changed when the implementation was tested.

The formal record is deliberately citable and inspectable. It contains theorem-style statements where they help, references, scope conditions, and falsifiability sections. The shared draft identity is generated from one checked source, so a title page, a footer, a build, and a release gate do not silently disagree about which version a reader has.

## What this release is not

This is a deliberately bounded release. It is not the repository, the complete project, or a release of implementation material.

Nineteen documents are cleared from a 22-document formal record. Three remain unreleased because they concern adaptive autonomous-control capability or executable realisation. The boundary is an allowlist, not a vague assurance: only the nineteen cleared preprints belong to this release.

The papers are also not peer-reviewed results. They are drafts made available for criticism. The origin story explains why the questions were asked; it does not answer them. The fact that a graph pattern appeared in two engineering settings is a reason to investigate a structural claim, not a reason to treat that claim as established.

## The question that remained

A routing system has to distinguish a possible connection from a permitted one.
A model-coordination system has to distinguish a possible answer from one that
fits the task, the available state, and the hand-off it is making. In both cases,
the useful object was not merely a graph. It was a graph together with the rules
that made some relations available and excluded others.

That may be an engineering rhyme and no more. But it leaves a question that does
not go away by naming it: if relation is doing this much work in systems built
for entirely different purposes, what exactly is relation required to be before
it can carry distinction, persistence, consequence, and explanation?

The papers begin at that question. They make the proposed answer explicit enough
to keep, change, or break. The rest is science: measurement, comparison,
correction, and the ordinary slow work of finding out which structures earn
their consequences.