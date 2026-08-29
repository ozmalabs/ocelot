# The Palimpsests check: what was settled, what was not, and why the retrieval failed

Flagged by the implied-author prior-art agent as the one unresolved risk to 01b's novelty
claim: does Genette's *Palimpsestes* (1982) already state the forward-running author-model?

## Settled — enough to force a narrowing, and it did

Genette defines the hypertext as derived from an earlier text **"par transformation simple …
ou par transformation *indirecte* : nous dirons imitation"**, and separates the two practices
by what each holds fixed:

| practice | changes | keeps |
|---|---|---|
| transformation (→ parody) | style | subject |
| **imitation (→ pastiche)** | **subject** | **style** |

So pastiche, by his own definition, **produces new subject matter in the imitated manner**, and
does it *indirectly* — not by operating on the text but by way of something abstracted from it.
That is a model of a producer, run forward on material the producer never treated. The risk was
real.

01b r12 narrows the claim accordingly: **the generativity is prior art; the personification is
not.** Genette's object is a *style*, and his standing objection to the implied author is
precisely against personifying it — a manner extends to new subjects without committing anyone
to what its owner would have thought. What survives as this paper's own is running a model of a
*person* forward on questions whose answers can be right or wrong, which is Schwitzgebel's
design and is not what pastiche is assessed for. That is the reverse of how the passage
previously divided prior art from contribution.

## NOT settled — do not quote these until verified

The stronger phrasing the agent recalled, and which would make the anticipation tighter still:

- **"model of competence" / "modèle de compétence"** — Genette borrowing the Chomskyan
  competence/performance distinction for imitation.
- **"matrix of imitation"** — the abstracted generator itself.
- the claim that such a matrix generates an **indefinite number** of new texts.

None of these were verified against Genette's text or a citable secondary source. **They are not
used in the paper and must not be until someone reads the chapter.** If they check out, the
anticipation is not merely definitional but explicit, and the narrowing above should tighten
again.

## Why retrieval failed — recorded so it is not repeated blind

Twelve routes attempted. Two classes of failure, neither of them "the source does not exist":

| route | outcome |
|---|---|
| DuckDuckGo (html + lite), Mojeek, searx.be, Startpage-likes | **bot challenge / captcha** |
| Marginalia | 302 to nothing |
| Bing | 200, but results not rendered without JS |
| Google Books API | **429 — daily quota exhausted** |
| OpenAlex | **429**, three attempts spread over minutes |
| Semantic Scholar | **429** |
| archive.org (advancedsearch, scrape, ia-pub-fts) | 0 results / 404 / no route |
| HAL, Erudit | **Anubis bot protection** |
| OpenEdition | JS-only app shell |
| Persée | reachable, but result blocks not in fetched HTML |
| Springer PDF (BF00054025) | HTML paywall served as `.pdf` |
| Monoskop | indexes the book, links to a login-walled host |
| fr.wikipedia API | **worked** — and is what settled the definitional core |

The scholarly APIs were rate-limited because three prior-art subagents had exhausted them
earlier in the same session; the search engines were blocked independently of that. **Wikipedia's
API was the only open channel**, which is why a reliable-but-not-citable summary is what the
narrowing rests on. The narrowing is safe because the transformation/imitation definition is
uncontroversial and appears in every narratology handbook; the unverified phrasings above are
not, which is why they are quarantined here instead.

**What would settle it:** twenty minutes with the chapter, in either language.
