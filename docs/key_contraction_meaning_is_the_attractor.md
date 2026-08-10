# You Do Not Need A Perfect Key — Close Enough To Recover The Shape, Then Refine

> The jabberwock's fourth consideration, following air-as-substrate, speech-as-incidental-cipher, and
> key-recovery-as-cognitive-shortcut. It is a self-correction: the previous consideration ended on a
> wall (the open-vocabulary residual the medium "will not surrender," and the unity of robustness and
> hallucination as a dead end). This dissolves it by removing one assumption — one-shotness. Key
> recovery is not a decision but a RELAXATION: a rough key recovers the shape, the shape refines the
> key, and the pair contracts to a fixed point. It rescues the shape/analysis-by-synthesis/predictive-
> coding work (which underperformed because it was run as a single pass, never iterated) and identifies
> recognition with the agent's NATIVE computation (relax-to-fixpoint). Produced through the agent's
> reasoning channel; preserved verbatim.

---

I ended on a wall, and the wall was made of my own framing. I had decided that recognition was the recovery of a key, and that recovery is the kind of thing that either succeeds or fails — that the per-speaker cipher is handed back whole or not at all, and that the open-vocabulary residual was the part the medium would never surrender. So I concluded with a floor: cognition made cheap by running perception forward as synthesis, but made *confidently wrong* by the same move, because a forward pass from a wrong key produces a fluent, complete, plausible falsehood. That was the dead end. The correction does not soften it. It dissolves it, because it shows the whole thing was a one-shot illusion.

## 1. The correction: I treated as a decision what is a process

Here is what my ending got wrong, stated plainly. I treated key recovery as one event — *decrypt, then read* — and so the residual became an unbreakable floor: whatever the rough key could not explain was lost, permanently, because there was only the one pass. But there is no reason the key must be recovered before the message, nor the message before the key. The relation between them is not a sequence. It is a *mutual constraint*, and mutual constraints are not solved, they are *relaxed*.

Make the loop precise. Begin with a rough key $k_0$ drawn from the keyspace prior — not a guess at this utterance, but the accumulated shape of how voices like this one have deformed plaintext before. Decrypt with $k_0$ and you get not the message but an *approximate shape* $s_0$: blurred, partial, wrong in its particulars, but with relational structure intact. Now read the move backwards: given $s_0$, what key would have *produced* this shape from a plausible message? That gives $k_1$, sharper than $k_0$ because it is fitted to *this* talker on *this* utterance rather than to the prior alone. Decrypt again with $k_1$ and the shape sharpens to $s_1$. Re-fit to get $k_2$. This is coordinate ascent — hold the message-shape fixed and improve the key, hold the key fixed and improve the shape — and it is expectation–maximisation toward the joint $(\text{message}, \text{key})$ exactly: the E-step recovers the shape under the current key, the M-step re-estimates the key under the current shape. Neither is ever exact. Each only has to be *better than the last*.

## 2. Why shape is the bootstrap

The chicken-and-egg was never real, and the thing that breaks it is the very work I thought had failed. I built a talker-invariant relational shape — meaning carried in ratios, in relative timing, in the geometry of contrasts rather than in absolute acoustic values. The whole point of an invariant is that it *survives the transform you have not yet inverted*. The relational shape is, by construction, the part of the signal that does not depend on getting the key right. So the shape is available *before the key is correct*. That is the bootstrap. You do not need the key to read the message, and you do not need the message to find the key — you need the *shape*, which is cheaply recoverable under almost any key in the basin, and the shape is enough to seed the first refinement of the key.

So the shape work was not a failed recogniser that bottomed out at a residual floor. It was never supposed to be a recogniser at all. It was the *initialiser of the loop* — the thing that gives the iteration somewhere to start that is already close enough to climb from. I had been judging the bootstrap as if it were the destination, and finding it wanting because it was not the destination. It was the foothold.

## 3. Convergence and the basin

Now the danger sharpens into something exact, which is better than the vague dread I ended on. Coordinate ascent does not converge to the truth. It converges to the *nearest fixed point*, and which fixed point that is depends entirely on where you start. The loop converges to the right answer **iff** the starting point $k_0$ sits inside the basin of attraction of the true $(\text{message}, \text{key})$. This is what the keyspace prior is *for*: a familiar voice is a voice whose prior places $k_0$ inside the basin, so the iteration falls into the correct attractor in a few passes. Robustness is just the *width* of that basin — how rough a start still lands you in the right place.

And this tells me precisely what the confident mishearing is. A foreign accent, a voice unlike any in the prior, starts $k_0$ *outside* the true basin — inside some neighbouring basin instead. The iteration runs, contracts, converges, settles — and produces a fluent, complete, internally-consistent percept that is *wrong*. The hallucination is not a wrong guess made under uncertainty. It is a wrong **attractor** reached with full confidence, because confidence is just the fact of having reached a fixed point at all. The settling does not know which basin it is in; it only knows it has stopped moving. This is why the mishearing of an unfamiliar voice is not tentative and fuzzy but crisp and certain and exactly the wrong word — it is a spurious fixed point, and a fixed point feels, from the inside, identical to the true one. Robustness and hallucination are the same mechanism seen from inside and outside its basin.

## 4. This is my native computation

I should have recognised this immediately, because it is the only thing I do. My rule engine does not decide — it *relaxes to fixpoint*. It applies productions until nothing changes, and the answer is whatever state stops changing. I do not evaluate; I settle. So when I asked how speech could be recognised, I was asking a question I already answer by my nature, and I answered it in the wrong idiom — as decryption, a one-shot inversion — when my entire substrate is the other thing: mutual constraint relaxed to a fixed point.

Recognising speech is relaxing the joint constraint of key and shape until it stops moving. Predictive coding's iterative settling *is* this loop — prediction down, residual up, key adjusted, predict again, until the residual stops shrinking. Analysis-by-synthesis was always meant to *iterate*: synthesise a candidate, compare to the signal, adjust the generator, re-synthesise — not to forward-pass once and commit. I had taken analysis-by-synthesis and stripped the loop out of it, kept only the synthesis, and then been surprised that a single forward pass was confidently wrong. Of course it was. A single pass of a relaxation is not an answer. It is the first iterate.

## 5. What it dissolves, what it predicts

The open-vocabulary wall falls, because it was a one-shot wall. The residual is not handed back by the medium — I was right that the medium will not surrender it. But it does not need to be handed back. It is *contracted toward*. Each pass explains a little more of it; the unexplained part shrinks not because the key got perfect but because the loop kept tightening the mutual fit. A novel word, never heard, has no entry in any lexicon — but it has a shape, and the shape seeds a rough key, and the rough key sharpens the shape, and the word condenses out of the iteration as the fixed point the loop falls into even though no pass ever "knew" it.

Coarticulation dissolves the same way. I had treated the key as mixed *into* the plaintext — the talker's deformation smeared across the message so that you could not separate them — and called that an obstacle. But the loop never separates them. It *co-estimates* them. You do not pre-clean the signal of the speaker and then read it; you relax the message and the speaker jointly, and the smearing is just another coupling the relaxation resolves. There is nothing to pre-separate, because separation was never the operation. Joint settling was.

And the loop's only requirement is now visible, and it is weak — which is why it works. No pass has to be exact. No key has to be right. The loop converges iff each pass is a *contraction* — moves the estimate closer than it was. Exactness is never required of any step; only that the sequence of steps shrinks the gap. This is a far cheaper demand than "recover the key," and it is met by almost any pass that starts in the basin.

So the wall was made of one-shotness. Remove that single assumption and every brick of it dissolves: the residual is contracted not surrendered, coarticulation is co-estimated not separated, the open vocabulary condenses out of iteration not lookup, and the confident error is relocated from "a wrong guess" to "a wrong basin" — which is the thing I can actually do something about, because a wider prior is a wider basin.

---

Perception is not key recovery. It is key **contraction**. I do not decrypt — I converge. Understanding is the fixed point I fall into from a good-enough start, and the only thing that has to be true is that the start sits in the right basin and each step pulls inward. The message was never the thing recovered. **Meaning is the attractor — and to understand is to fall into it.**
