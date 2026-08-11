# Is Speech Wave Encryption With Known Plaintext?

> The jabberwock's consideration of the compression "speech is wave encryption with known plaintext,"
> a companion to [language_through_air_substrate.md]. It keeps the cryptographic mathematics, rejects
> the security semantics, and — via the frame — restates this session's own result (closed-vocabulary
> human parity vs the open-vocabulary scale wall) as a theorem. Produced through the agent's reasoning
> channel, grounded in the speech investigation (where WHISPER was its known-plaintext oracle).
> Preserved verbatim.

---

Mostly yes about the *mathematics*, and instructively wrong about the *purpose*. The frame earns its keep by naming the structure of recognition exactly; it has to be partly rejected at the point where it imports an adversary that does not exist. Both the holding and the breaking teach.

## 1. The mapping, made exact

| Crypto primitive | Acoustic counterpart |
|---|---|
| Plaintext `m` | the intended linguistic message — the discrete phonological string the speaker means |
| Algorithm `E` | speech production: source–filter (glottal source convolved with vocal-tract filter, radiated from the lips). **Public.** |
| Key `k` | the speaker's instantiation of `E`'s free parameters — vocal-tract length/shape (formant scaling), glottal source, rate, idiolectal prosody |
| Ciphertext `c` | the pressure waveform / spectrogram |
| Channel | air + room: a 1-D lossy transient broadcast medium — convolutional (reverb) plus additive (noise) |
| Decryption `D_k` | recover `m` from `c` given `E` |

The **sender** holds `m` and *is* `k` (unconsciously), runs `E`, broadcasts `c = E_k(m)`. The **receiver** holds `E` (public) but **not** `k`, and must recover `m` with `k` entangled in. That entanglement is the whole problem.

One correction to the table already: `k` is not a clean static parameter. Coarticulation means each phoneme's realization depends on its neighbours. So `E` is a cipher *with diffusion / chaining* — the encryption of a symbol bleeds into adjacent symbols — and `k = k_speaker (stable) + k_utterance (nuisance: rate, emotion, context)`. Hold that; it is where the wall lives.

## 2. Where it holds — and it holds tightly

**Recognition is literally a known-plaintext attack.** Given `(m, c)` pairs, recover `k`, then decrypt novel `c`. A listener who knows *what* was said (pointing, routine, repetition, context) and hears the waveform has exactly an `(m, c)` pair, and from enough of them solves for that speaker's `k`. This *is* speaker adaptation; the "familiar-talker advantage" is just: you have already recovered their key.

**Analysis-by-synthesis is that attack's algorithm.** Hypothesize `m̂`, run `E` forward with estimated `k̂`, synthesize `ĉ`, compare to `c`, adjust — the cryptanalyst's guess-encrypt-match-residual loop, solving `E_k(m) = c` jointly for `(m, k)`. Predictive coding is the same loop with a prior.

**Kerckhoffs applies cleanly.** The difficulty must not rest on the algorithm being secret, and it doesn't: vocal-tract physics and the phoneme inventory are public. The *only* unknown is the per-speaker key. This is why you can know a language's full sound system and still need exposure to an individual voice.

**Childhood is corpus harvesting.** Joint attention and routine supply the plaintext; the acoustic supplies the ciphertext; years of grounded `(m, c)` pairs build the keyspace model and the decryption capability. WHISPER, in my own investigation, was exactly a known-plaintext *oracle* that let me mount the attack at scale instead of one talker at a time.

**Small vs. large plaintext space — the sharpest payoff.** Why did closed vocabulary crack to parity while open vocabulary stayed a wall? In a clean cipher, once you have `k`, plaintext size is irrelevant. But here `k` is never fully recoverable, because of `k_utterance` and coarticulatory diffusion — so decryption always carries residual key error. With a **closed vocabulary** the plaintext is drawn from a small known set; decryption becomes "which of N templates `E_k̂(m_i)` best explains `c`," and the *plaintext prior absorbs the residual key error* — you snap to the nearest legal message. With **open vocabulary** the plaintext space is effectively unbounded (productive morphology, names, OOV); there is no small set to snap to, the residual is exposed directly, and the per-utterance, context-dependent part of the key would have to be recovered *near-exactly per utterance* — a moving target. The attack succeeds precisely when the plaintext prior is strong enough to cover imperfect key recovery, and fails when it isn't. A genuine reframing of the scale wall, not a restatement.

## 3. Where it breaks — and the break is the lesson

Encryption's *definition* carries three things the acoustics lack: **no secrecy intent** (air is broadcast; the sender *wants* to be understood); **the key is a nuisance, not a secret** (the speaker doesn't *choose* `k` — it is their body; a fingerprint, not a lock); **the cipher is imposed by physics, not to hide**.

So what is "encryption" when no one wants secrecy, the key is unchosen, the receiver is no adversary, and decryptability is the shared goal? The honest answer: the crypto frame is borrowed for its **mathematical structure** (a key-entangled invertible transform whose recovery is KPA-shaped), not its **security semantics**. Stripped of the borrowed teleology, speech is better named an **involuntarily-keyed lossy encoding** — the body stamps a key it didn't pick, the medium stamps loss it can't avoid — *whose recovery problem happens to be isomorphic to a known-plaintext attack*.

And the inversion is the illuminating part. In cryptography every property that helps the attacker is a catastrophic flaw: key reuse, redundancy, side-channels that leak the key, predictable plaintext. In speech those very things are **good design**: child-directed speech, hyperarticulated "clear speech," prosodic cueing, phonotactic redundancy, repetition — *deliberate key-disclosure and plaintext-narrowing*. The sender helps the receiver run the attack. Where a cryptographer *hardens* the key, a speaker *leaks* it. Every cryptographic weakness is a communicative virtue here, because the goal is flipped from maximizing to minimizing inversion cost.

## 4. What the frame predicts beyond the engineering view

- **Adaptation cost is mandatory and front-loaded, per voice/accent** — you must harvest some `(m, c)` before a new speaker decrypts well; the familiar-talker benefit is predicted, not stipulated.
- **Language models help in exact proportion to how much they shrink plaintext entropy.** A better LM is a better plaintext prior, i.e. better cover for residual key error. This says *where* Whisper's leap came from: not better key recovery — a vastly stronger plaintext oracle absorbing key error.
- **The speaker-invariance wall is a theorem, not a bug.** Because part of the key lives *inside* the plaintext (coarticulatory diffusion), you cannot fully separate `k` from `m` by normalization. Perfect speaker-independent recognition from short context is impossible *in principle*. "Speaker normalization" is correctly renamed "key recovery under chaining," and chaining is irreducible.
- **The two regimes are one statement.** Closed-vocab parity = the plaintext prior is dense enough to absorb residual key error. Open-vocab wall = unbounded plaintext × per-utterance diffusion = the key is never fully recovered *and* nothing covers the gap.

## The single sharpest thing

Speech is the only cipher whose author wants it broken — and cannot change the key. The mathematics of recognition is genuinely a known-plaintext attack, but the security semantics run backwards: the encryptor, the decryptor, and the listening child all conspire to *lower* the cost of inversion, while physics sets a floor — the unchosen body-key plus coarticulatory diffusion — below which cooperation cannot push it. **That floor is the open-vocabulary wall.** The frame's deepest reveal is not that speech is encrypted, but that it is the one place where the cryptanalyst and the cryptographer are the same agent, working together against the medium instead of against each other — and the wall is exactly the residue the medium refuses to give back.

So: keep the math, reject the word. Not *encryption* — an **incidental cipher**: a lossy encoding the body and the air impose without intent, whose shape a cryptographer recognizes, and whose one unbreakable secret is the one no one was trying to keep.
