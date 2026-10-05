# Colour reference data — provenance

All files retrieved 2026-10-04 (UTC, machine clock) by plain HTTP(S) GET; raw
files in `raw/` are byte-unmodified. Loader: `domains/spectral_forward.py`.
Grid used by the model: 390–780 nm (1 nm; 5 nm ablation = exact subsample of
the 1 nm tables, or the CIE 5 nm table where stated). No interpolation is
applied to any CIE/CVRL function on the 1 or 5 nm grid (all are tabulated on
those nodes).

| File (`raw/`) | Content | URL | Units / interval | sha256 |
|---|---|---|---|---|
| `linss2_10e_1_8dp.csv` | CIE 2006 LMS cone fundamentals, 2°, **default 2-deg source** | http://www.cvrl.org/database/data/cones/linss2_10e_1_8dp.csv | energy, linear, peak = 1; 390–830 nm, 1 nm; 8 decimals; S blank > 615 nm | `9f1b5c200ef9081c2e011bd565415ecb347426ccad6c863422ab8331bcf79297` |
| `linss10e_1_8dp.csv` | CIE 2006 LMS cone fundamentals, 10° (wrong-observer condition) | http://www.cvrl.org/database/data/cones/linss10e_1_8dp.csv | energy, linear, peak = 1; 390–830, 1 nm; S blank > 615 nm | `591481951b562489d7becb511e5d459c2e818f7728740d73b0b1371effaa65fc` |
| `CIE_lms_cf_2deg.csv` (+ `_metadata.json`) | CIE 170-1:2006 Table 6.7, 2° LMS (official CIE datatable, DOI 10.25039/CIE.DS.tijidesg) — **the file that matches the pilot values exactly** | https://files.cie.co.at/Publications-datasets/CIE_lms_cf_2deg.csv | energy, linear; 390–830, **5 nm**; 7 sig. fig.; S NaN ≥ 620 | `f48160edf11c1a121aaaf41d4c3b7513385bfc9c60d726b88e735519f6d37b1f` (meta `c488310e9f07…ab`) |
| `CIE_lms_cf_10deg.csv` (+ meta) | CIE 170-1:2006 Table 6.2, 10° LMS | https://files.cie.co.at/Publications-datasets/CIE_lms_cf_10deg.csv | energy; 390–830, 5 nm | `bd64f1f688a4b319c6d3fa6b31770a32eaaaaea0eed532befd0424f96304db18` |
| `CIE_cfb_stv_2deg.csv` (+ meta) | CIE 170-2:2015 Table 10.7a cone-fundamental-based XYZ, 2° (“CIE 2012 2-deg XYZ”; identical to CVRL `lin2012xyz2e_1_7sf.csv`) | https://files.cie.co.at/Publications-datasets/CIE_cfb_stv_2deg.csv | energy; 390–830, 1 nm | `a10751ec8aecdb023f16ba079557e7fb794806884fe3da982dd63da285f872a9` |
| `CIE_cfb_sle_2deg.csv` (+ meta) | CIE 170-2:2015 Table 10.2 V_F(λ) 2° = CIE 2008 physiologically-relevant V*(λ) (identical to CVRL `linCIE2008v2e_1.csv`) | https://files.cie.co.at/Publications-datasets/CIE_cfb_sle_2deg.csv | energy, peak 1; 390–830, 1 nm | `e2a07b2bbab0dc800b35d2b070e79b87674740bd8c4ceb53ae78c6053c0e2316` |
| `CIE_std_illum_D65.csv` (+ meta) | CIE D65, ISO/CIE 11664-2:2022 Table B.1 | https://files.cie.co.at/Publications-datasets/CIE_std_illum_D65.csv | relative, 100 at 560; 300–830, 1 nm | `e76f210bffff3d552ef7113025da5f325d5dfec200dd4b878b1a2f3a507032cb` |
| `CIE_std_illum_A_1nm.csv` (+ meta) | CIE illuminant A, ISO/CIE 11664-2:2022 Table A.1 — **cross-check only** (A is computed, see below) | https://files.cie.co.at/Publications-datasets/CIE_std_illum_A_1nm.csv | relative; 300–830, 1 nm | `61ef23fe146b8b665c74706717ab28cec7db6c9022993490bdc71991f43cb59b` |
| `ColorChecker_RGB_and_spectra.zip` | BabelColor ColorChecker data (D. Pascale), contains `ColorChecker_RGB_and_spectra.xls` | https://babelcolor.com/index_htm_files/ColorChecker_RGB_and_spectra.zip | reflectance factor 0–1; 380–730, 10 nm; average of 30 charts | `6ec58d7b72b5d0a7372928a552982cf9b613d459de3d0f1214a188ef31d1211f` |

Metadata JSON sha256: D65 `71994379b81c65db111f652e747a00b599b5456c2a8242e9a0d6f379f560a14e`,
A `35b735803ef7f64b61a0df3839fdb90efde47fd491562223c4a228bb2e0384d0`,
10° LMS `c71ce42dd0a320f79d66b1d69e76d506bb59ce6e0128e930cd0f66844ea29372`,
XYZ `24eb42e00e0b6dc3f6b60fcaae1bd5ea2d9195e6da28ff69b801cf475c80cb7a`,
V_F `84968a44130512386276b22a522c2e9f5ffe06821cb518d301fc97bd29072e56`,
2° LMS `c488310e9f076a9e00bff69d206eae8821bd17137e6a3ba260570eae4ff91fab`.
CIE datatables are CC BY-SA 4.0 (per metadata).

## Derived file

`colorchecker24_babelcolor_avg_10nm.csv` (sha256
`b9cba659c76f4a2672a90422af435d720d04be6bb74493eb800144f7e4ed654f`): rows 3–26
(“BabelColor Avg.”, 24 patches) of sheet `spectral_data` of the xls, exported
with LibreOffice headless (`soffice --convert-to csv`) — values unchanged,
columns `patch,name,380..730`. The model interpolates linearly to the grid
(`np.interp`) and **holds the 730 nm value for 731–780 nm** (no extrapolation
slope). 390 nm lies inside the measured range.

## Verification of the pilot's 2° values (task requirement)

Pilot (`scripts/marys_room_red_green.py`): 610 nm = (0.7057161, 0.2052721,
8.034895e-06); 530 nm = (0.7706373, 0.9356857, 0.01260114).

- `CIE_lms_cf_2deg.csv` (CIE 170-1 Table 6.7, 5 nm) matches **exactly**.
- No 1 nm file matching to 7 digits was found. The CVRL 1 nm tabulations give
  610 nm = (0.705713103, 0.205273346, 8.03487566e-06) and 530 nm =
  (0.770629906, 0.935687022, 0.0126012838): |Δ| ≤ 3.1e-6 here, and ≤ 1.006e-5
  absolute / 1.25e-5 relative at every 5 nm node 390–780 (10°: ≤ 4.9e-7 abs).
  The 6-decimal CVRL `linss2_10e_1.csv` has the same values rounded.
- Decision: the **1 nm default is CVRL 8dp** (`load_lms(source='cvrl')`); the
  official CIE 5 nm table is available as `load_lms(..., step=5,
  source='cie_table')` and reproduces the pilot to 1e-12.

## Other checks

- V_F(λ) = 0.68990272·L̄ + 0.34832189·M̄ (CVRL-published coefficients; Stockman
  & Sharpe) — least-squares refit on the 1 nm tables gives the same
  coefficients, max residual 5.0e-8.
- K_m,F (2°) = 683 / V_F(555.016 nm) = **683.36265 lm/W** (SI candela
  definition at 540 THz, linear interpolation of the 1 nm table). Derived, not
  copied from CIE 170-2.
- Illuminant A is **computed** with the CIE formula
  S_A(λ) = 100·(560/λ)^5·(e^{c2/(2848·560)} − 1)/(e^{c2/(2848·λ)} − 1),
  c2 = 1.435e7 nm·K (≡ 2856 K Planckian with c2 = 1.4388e7); agreement with the
  CIE 1 nm table over 390–780: max relative difference 4.8e-6 (table rounding).
- Illuminant E: constant 100.
- Blank/NaN S-cone entries (> 615 nm) are read as 0.

## Added in Phase 3 (Amendment A1, wrong-optics condition) — retrieved 2026-10-04 11:24 UTC

| File (`raw/`) | Content | URL | Units / interval | sha256 |
|---|---|---|---|---|
| `lensss_1.csv` | Stockman, Sharpe & Fach (1999) lens optical density (adjusted van Norren & Vos 1974); CVRL page `database/text/maclens/lensss.htm` | http://www.cvrl.org/database/data/maclens/lensss_1.csv | optical density; 390–830 nm, 1 nm; 1.7649 at 400 nm | `2a4c20a190556dfa8b89496e47f9105a687bc91f8f142e8b1fa41675714ddc65` |
| `macss_1.csv` | Stockman, Sharpe & Fach (1999) macular pigment optical density; CVRL page `database/text/maclens/macss.htm` | http://www.cvrl.org/database/data/maclens/macss_1.csv | optical density; 390–830 nm, 1 nm; peak 0.35211 at 458 nm | `6b735bf52418d29cefdbee048e1417e9c91dc2570f0740fd7571f62f30c923b5` |

Both byte-unmodified (CRLF line endings). Loaded by
`scripts/marys_room_broad_theory.py::prereceptoral_density` (blank values → 0;
no interpolation; 1 nm grid). Used only as `T = 10^−D` pre-receptoral filters
applied to the eye input in the `wrong_optics` family. (First attempts at
`database/data/lens/…` and `database/data/maculars/…` returned 404 HTML and
were deleted.)

## Literature verification (not a data file)

Unique-hue loci for the ground-truth labels: Kuehni R.G. (2004) *Variability in
unique hue selection: a surprising phenomenon*, Color Res. Appl. 29(2):158–162,
doi 10.1002/col.10237, Table I — read from
https://sites.socsci.uci.edu/~kjameson/KuehniCRA.pdf on 2026-10-04 (PDF not
stored in the repo). Declared values and their derivation: prereg Amendment A1-1.
