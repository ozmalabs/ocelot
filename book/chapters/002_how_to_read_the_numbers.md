# How to Read the Numbers in This Book

*Front matter. Read before Part I. Long-form treatment in chapter 16.*

---

There is a small involuntary motion the eye makes during fixation — a drift
that keeps the image sliding across the retina even when you are staring at
something. It has a measurable signature: persistent at short timescales,
anti-persistent at long ones, with published scaling exponents around 1.38 and
0.79.

The eye in chapter 1 reproduces that signature to two decimal places.

It also, for a considerable time, **drove nothing**. The drift ran. The numbers
matched. And the only thing in the entire system that consumed the drift's
output was the ruler that measured it. Nothing downstream moved when it moved.

No test went red. Nothing was broken, in the sense that software is broken.
Every gate was green, and the number in the results table was correct, and the
whole thing was worthless — until somebody looked at it and thought: *that is
suspiciously clean.*

It was one of sixteen. Sixteen instruments in that one line of work turned out
to be inert: a measure that passed pure noise, a dead cell scoring a flawless
floor, a stocked library reading empty because of a mistyped dictionary key, a
benchmark containing ten tests that had never once executed. **Not one of the
sixteen was caught by a test failing.** Every one was caught by a person finding
a result too tidy and going to look.

That is the situation this book's numbers come from, and it is why this page
exists before any of them.

---

## What the numbers here are

Almost every quantitative claim in this book comes from a pair of documents: a
**preregistration** written and committed *before* the measurement, and a
**results** document written after. The preregistration fixes the prediction,
the sample size, the analysis, and — this is the part that does the work — what
outcome would count as a failure. There are roughly 1,700 such pairs behind the
chapters that follow.

The discipline is unusual for engineering and ordinary for experimental science,
and it is not decoration. Its whole function is to make it impossible to decide
after the fact which analysis was the one you meant.

So when a chapter reports a number, three things are normally true of it: the
prediction was fixed first, the sample size was declared first, and the result
is reported whether or not it went the desired way.

---

## How to read them

**Read the interval, not the point.** A number in this book normally arrives
with a range attached. The range is not a decoration on the estimate; in most
cases it *is* the claim. Two arms whose intervals overlap have not been shown to
differ, no matter how far apart their midpoints sit. Chapter 5 contains the
book's most expensive lesson on this exact point.

**Read what each number does and does not establish.** Every reported figure in
this book should be followed by a sentence bounding it, and if one is missing,
that is an error rather than a style choice. A mechanism demonstrated on
synthetic data is a demonstration that the mechanism works; it is not a claim
about performance on real data, and the two are reported separately throughout.

**Treat a null as a result.** When a measurement came out flat, or negative, or
the opposite of what was expected, it appears in the chapter at the same weight
as a success. Chapter 1's largest section by consequence is a null — five
pre-registered attempts at a capability, an interval on the wrong side of zero,
and an arithmetic explanation of why no amount of retrying would have helped.

**A number quoted without its condition is not a number.** This is the rule this
project learned most painfully, and chapter 16 tells that story properly. The
short version: a status line about the state of the test suite was true under
the conditions it was measured in, was quoted for ten days without those
conditions, and was wrong by a factor of 3.4 under the conditions someone else
was working in. Where a figure here depends on a condition, the condition is
stated with it.

---

## What you should expect to find

**Retractions, in the body.** Where a claim in this work was published and later
withdrawn, the withdrawal appears in the chapter where the claim would have
been, with the measurement that forced it. They are not collected in an
appendix and they are not quietly edited out. Five of them are in chapter 1
alone.

There is a self-interested reason for that, beyond honesty. A body of work with
no visible retractions is not a body of work that was never wrong; it is one
where you cannot tell. The retractions are the evidence that the rest was
checked.

**Falsifiers, at the end of each chapter.** Every chapter closes by stating what
would have to be true for its central claims to be wrong. Some of those are
things a reader could plausibly go and test.

**Numbers that are smaller than you might expect.** This is a research prototype
at small scale, built by one person. Where a chapter reports a capability, the
scale is stated. Where a result would be more convincing at ten times the sample
size, the chapter says so.

---

## What this book does not do

It does not report a number without saying where it came from. Every figure
traces to a committed results file and, in almost every case, a committed script
that produced it. This too was learned rather than assumed: one early result in
this work turned out to have been produced by a runner that was never committed,
which made the number unattributable to any code that exists. It was retracted
on those grounds alone, before anyone knew whether it was correct.

**An uncommitted runner means the result is not a result.** That rule applies to
the figures in this book as much as to the experiments behind it.

---

*One page, one request: when a number in the following chapters seems too clean,
do what the sixteen inert instruments needed somebody to do — assume the
instrument, not the result. Chapter 16 is where that habit is made into a
method.*
