# Representation Learning in Cognition: Local Plasticity, Not Backpropagation

## Abstract

The real-speech ceiling demands a *learned* discriminative representation, but end-to-end
backpropagation is **forbidden as a model of cognition**: the cortex has no global backward pass and
no mechanism to transport a layer's weights backward to carry error (the "weight-transport problem"),
so a learning rule that requires a global chain-rule sweep is biologically implausible. This note
establishes the alternative that *does* happen in cognition — **local, error-driven, Hebbian
plasticity** — and the key result that such local rules can learn the *same* representations as
backpropagation *without* a backward pass. Representation learning is therefore not synonymous with
gradient descent; it is an emergent property of local plasticity, which is what biological cognition
uses. The agent already embodies two of these mechanisms (prediction-error minimisation and
competitive clustering); the missing piece is the *discriminative* (label-driven) local rule.

## 1. What is forbidden, and why

**Axiom 1 (No global backward pass).** A biologically faithful learning rule updates each synapse
from signals locally available at that synapse — pre-synaptic activity, post-synaptic activity, and a
locally delivered error or modulatory signal. It may NOT require (i) a separate backward network that
transports transposed weights, nor (ii) a global, two-phase forward-then-backward chain-rule sweep.
Backpropagation violates both. Gradient descent on a global loss is, in this sense, the forbidden
operation: not because gradients are wrong, but because the *global backward computation* of them is
not something cortex can do.

## 2. What does happen: Hebbian and competitive plasticity

**Axiom 2 (Hebbian plasticity).** Synapses change from local co-activity: dw_ij ∝ f(x_i, y_j) (Hebb
1949; long-term potentiation/depression). Normalised Hebbian learning (Oja's rule,
dw ∝ y(x - y w)) converges to the principal subspace of the input — an *unsupervised* representation,
learned locally, no backprop.

**Axiom 3 (Competitive learning).** Winner-take-all activation plus Hebbian update on the winner
yields clustering and topographic feature maps (Rumelhart & Zipser 1985; Kohonen self-organising
maps) — a local model of cortical map formation. (*The agent already does this*: its categorical-
perception layer learns phoneme categories by leader-follower online clustering — competitive
learning, not gradient descent.)

## 3. The key result: local rules compute the backprop signal

**Theorem CHL (contrastive Hebbian learning equals the error gradient).** In a symmetric network run
to equilibrium, the **contrastive Hebbian** update — the difference between local Hebbian
co-activities in a *clamped* phase (outputs pinned to the target) and a *free* phase (outputs
relaxed), dw ∝ <x_i y_j>_clamped − <x_i y_j>_free — equals, to first order, the gradient of the
output error with respect to that weight (Movellan 1991; Xie & Seung 2003). **Equilibrium
Propagation** (Scellier & Bengio 2017) generalises this to energy-based networks: a single nudged
relaxation yields the exact loss gradient from *purely local* updates. **Predictive coding** networks
likewise approximate backprop with local prediction-error units (Whittington & Bogacz 2017).

The consequence is decisive for the forbidden-operation question: *the learning signal backprop
computes globally can be obtained by local plasticity acting on the difference between two neural
states.* Representation learning thus **happens in cognition** — as the settling difference between a
predicted (free) and an observed/target (clamped) state — without any backward pass. This is the
sense in which the forbidden operation is *permitted*: not as a backward sweep, but as the local
consequence of relaxing toward, versus being driven by, the target.

## 4. Predictive coding: the agent already has the substrate

**Axiom 4 (Prediction-error learning).** Hierarchical cortex continuously predicts its own input and
updates to reduce the *local* prediction error (Rao & Ballard 1999; Friston's free-energy
principle). Learning is error-driven but the error is *local* to each level — exactly the
free-vs-clamped difference of Theorem CHL. The agent's standing `understand` drive is already a
prediction-error minimiser (prediction vs observation, surprise). A discriminative representation is
learned by treating the *word label* as the clamped top-level state and letting the local
free-vs-clamped plasticity shape the layers below.

## 5. The empirical claim to test

**Hypothesis cog-embedding (local plasticity learns the discriminative representation).** A
discriminative embedding trained by a LOCAL rule — contrastive Hebbian / predictive-coding
(free-phase = predict the word from the utterance; clamped-phase = pin the true word; update each
layer by its local pre·post co-activity difference) — lifts real-speech recognition above the
write-not-train (un-trained featuriser) ceiling, WITHOUT any global backpropagation, because local
error-driven plasticity learns the representation and this is the mechanism cognition uses. If it
matches a backprop-trained embedding, it demonstrates that the representation learning the ceiling
required was never *backprop* — it was *local plasticity*, which the agent may faithfully do.

## 6. Falsifiability

If a local contrastive-Hebbian / predictive-coding rule does **not** lift recognition while a
backprop-trained embedding does, then — within this architecture and data — the gap between local
plasticity and global backprop is operative, and the honest report is that the agent's cognitively
faithful learning underperforms the forbidden operation here (a real, publishable negative about
local learning at this scale), not that backprop should be adopted. If neither lifts it, the limit is
data, not the learning rule.
