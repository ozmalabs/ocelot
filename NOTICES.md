# Third-party notices

This project incorporates source code from the following projects.
Each entry lists the upstream source, the file(s) we vendored, and the
upstream licence (reproduced verbatim).

---

## OxideAV/oxideav-h264

Upstream: https://github.com/OxideAV/oxideav-h264
Commit:   `f55142b9707b461b92cd39118da9d34ba2c960c9` (2026-06-01)
Vendored as:
  - `runners/dsl/src/h264_inter_pred.rs` ← original `src/inter_pred.rs`

Local modifications (documented in the file header):
  - Removed the `thiserror` dependency. `InterPredError` re-derived
    with a manual `std::fmt::Display` + `std::error::Error` impl;
    functionally identical to the upstream `#[derive(thiserror::Error)]`.

### Upstream licence

```
MIT License

Copyright (c) 2026 Karpelès Lab Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
