# Challenger selector to receipt and adoption v1 — preregistration

## Question

Can the new target-blind challenger selector choose a fresh probe, bind it into the existing provenance-bound adequacy request, and carry the resulting accepted/rejected receipt through the real write-code-shape `teach()` boundary?

## Frozen cases

Each fresh process boots the complete seed set and runs one case, repeated three times:

| Case | Candidate source | Challenger | Probe domain | Expected receipt/adoption |
|---|---|---|---|---|
| Correct candidate | `square(x)=x*x` | identity | `x=1..4` | accepted and adopted |
| Wrong, broad domain | `identity(x)=x` | square | `x=1..4` | distinguishing probe, rejected, no codebook growth |
| Wrong, alias domain | `identity(x)=x` | square | `x=1` | accepted on alias, adopted; held-outs expose failure |

All use the single acquisition example `x=0 -> 0`, separate square-oracle labels, one selected fresh probe, and strict receipt-required adoption. The selector receives candidate/challenger Terms and the finite input domain but no labels. The request API receives only the selected point as its admissible domain, so its request ID binds that exact descriptor. Record selector commitment, request/receipt integrity, codebook/epoch before and after, generated held-out behavior, full-seed boot, and teach time.

## Gates and limits

- All workers must preserve source/native/seed hashes; selected inputs must be fresh and match the request descriptor.
- Broad wrong candidates must produce a rejected receipt and no shape/epoch growth.
- The correct candidate must produce an accepted receipt, exactly one adoption, and exact held-out behavior.
- The alias-domain control is expected to accept and adopt the false identity candidate, demonstrating that selection cannot improve a domain containing no distinguishing input.

This is a three-case, one-oracle integration probe with harness-authored alternatives and labels. It establishes API composition on this write-shape boundary, not general candidate discovery, provider authentication, automatic domain construction, or production policy quality.
