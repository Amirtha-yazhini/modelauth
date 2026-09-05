# Complete change record

Everything changed from the original repository (`94a9122`), why, and the
reference for every metric, measurement and method used.

**Scale:** 55 files, +5272 / −314. 23 new modules, 6 modified, 1 deleted,
4 documents archived.

**Citation honesty.** Every reference below is marked:

- **[V]** — the source was opened and checked during this work.
- **[K]** — recalled from background knowledge, not opened. These are standard,
  long-established results and are very likely correct, but volume, pages and
  exact titles are the fields most likely to be wrong. **Verify before any of
  these enters a bibliography.** `paper/references.bib` carries the same marks.

---

## Part 0 — The headline

Three things changed that alter what the project can claim:

1. **A parser bug was inflating detection rates on the medium and hard tiers.**
   On the hard tier, **6 of the 10 original "detections" fired directly on a
   malformed value**, not on a model substitution. Hard-tier power falls from
   71.4% to 28.6% once the artifact is removed.
2. **The statistical framing was wrong for the data.** The probe channel is
   categorical; mean/variance detectors discard most of the evidence. Working on
   the PMF directly gives an oracle bound of 1.29 probes where the best deployed
   detector took 8.5.
3. **The novelty claim did not survive a literature check.** Self-baselined
   sequential e-value monitoring already exists [V1]; single-token fingerprinting
   already exists [V2]. The contribution moved to the adversary, which nobody
   has modelled.

---

# Part I — Bugs found and fixed

## I.1 The probe parser accepted truncated responses

**Original** (`data_loader.py`):

```python
def parse_numeric_answer(answer_text):
    match = re.search(r'\d+', answer_text)
    return int(match.group()) if match else None
```

**The failure.** `MAX_TOKENS = 5` truncated some generations mid-digits. The bare
`\d+` then accepted the fragment as a legitimate draw from a 1–100 distribution:

```
'854'  x42     '842' x20     '814' x10     '853' x11     '857' x11
'8549'  '8425'  '8546'  '8427'  '8428'      (all fragments of longer answers)
```

**Measured impact on the response distribution:**

| | mean | std |
|---|---:|---:|
| `llama3.2:3b` pooled, as originally parsed | 84.19 | **349.09** |
| `llama3.2:3b` with a `[1,100]` range guard | 57.0 | **18.25** |

A standard deviation of 349 on a variable bounded in [1,100] is impossible; 76
out-of-range values inflated it about **19×**. Every detector that standardises
by σ — `adaptive_cusum`, `variance_cusum` — was dividing by that.

**Why it mattered more than it looks.** Out-of-range values are rare (0.39–0.91%
per tier) but they are enormous in z-score terms, so a single one can push a
CUSUM past its threshold on its own. I tested this directly by re-running the
*original* detector with and without the range guard:

| tier | guard | power | delay | detections that fired **on** a malformed value |
|---|---|---:|---:|---|
| easy | off | 78.6% | 11.00 | 0 of 11 |
| easy | **on** | **100.0%** | **8.50** | — |
| medium | off | 92.9% | 41.15 | **4 of 13 (31%)** |
| medium | **on** | **64.3%** | **28.67** | — |
| hard | off | 71.4% | 71.20 | **6 of 10 (60%)** |
| hard | **on** | **28.6%** | **60.00** | — |

The `guard off` rows reproduce the original `summary_table_all_tiers.csv`
exactly, which confirms the comparison is like-for-like.

**Two opposite effects, both real:**

- On **easy**, outliers inflated σ and *masked* genuine detections. Removing them
  raises power from 78.6% to 100%. The original result was pessimistic.
- On **medium and hard**, outliers *created* detections. Removing them drops
  hard-tier power from 71.4% to 28.6%. The original result was optimistic, and
  most of the hard-tier detection rate was an artifact.

**Fix.** Range guard to `[1,100]`; `MAX_TOKENS` raised 5 → 8; rejects classified
as `out_of_range` / `unparseable` / `failed` rather than silently dropped, so
loss is visible in `audit_data.py` instead of hiding in the results.

## I.2 The parser fix would have been a silent no-op

`run_experiments.py` never passed `MAX_TOKENS` to the generator, so
`generate_probe_stream` kept its own default of `5`. Raising the value in
`config.py` alone would have changed nothing, and any regenerated data would
still have been truncated. Now threaded through `simulator.py` and
`probe_client.py`.

## I.3 False alarms were counted only before the switch point

**Original** (`evaluate.py`):

```python
flags = sum(1 for d in results if d["flagged"] and d["index"] < true_switch)
```

A *null* stream never switches, so a flag at `t=300` is as false as one at
`t=100`. The original counted only the first half of each null stream, roughly
halving every reported false-alarm rate. Now counted across the whole stream,
and `streams_with_false_alarm` is reported beside the rate — operationally, one
alarm on a clean endpoint costs what ten do.

## I.4 `DAS-CUSUM` was not DAS-CUSUM

The original `detector_das_cusum.py` accumulates `0.5·(z²−1)`, a χ²-style
variance CUSUM. DAS-CUSUM in the literature modulates the allowance *k* from a
running drift estimate, which the code never did. Renamed to
`detector_variance_cusum.py`, with the old name kept as a deprecation alias so
nothing breaks.

## I.5 Two of my own errors, corrected mid-work

Recorded because they affect how the results should be read.

**I divided by the Lorden bound.** I initially reported "% of optimal" using
`h/KL` as the denominator. That is wrong: Lorden's criterion [K7] is the worst
case over change points and pre-change histories, and `h/KL` is asymptotic in
*h*, while the measured quantity is an average-case delay from a known switch
with the statistic reset. The oracle legitimately came in *below* the bound
(1.29 vs 4.29). Now reported as a ratio to the oracle's **measured** delay on the
same streams, with Lorden kept as a labelled reference column only.

**My first compression detector was measuring an artifact.** Detailed in II.3.

---

# Part II — Methodological changes

## II.1 The channel is categorical, not continuous

**The observation.** The probe responses are not draws from a distribution on
the real line. They are draws from a sharply peaked categorical distribution
over a few dozen symbols:

| model | top mass | entropy |
|---|---|---:|
| `llama3.2:3b` | 53 (32%), 87 (14%), 74 (6%) | 4.16 bits |
| `qwen2.5:3b` | 42 (34%), 37 (19%), 83 (10%) | 4.33 bits |

CUSUM on the mean and KS on the ECDF both encode the assumption that 53 and 54
are near-neighbours while 53 and 87 are far apart. For this signal the numeric
ordering carries nothing, so both discard most of the available evidence.

**New module:** `stats_categorical.py`, working on the PMF directly.

**Metrics and their sources:**

| Quantity | Definition | Reference |
|---|---|---|
| PMF estimate | add-½ smoothing over the full 1–100 support | Krichevsky–Trofimov [K1] |
| KL divergence | `Σ p log(p/q)`, nats | Cover & Thomas [K2] |
| Total variation | `½ Σ \|p−q\|` | Cover & Thomas [K2] |
| Shannon entropy | `−Σ p log p` | Cover & Thomas [K2] |
| Bayes error | `(1 − TV)/2`, optimal single-probe error | standard consequence of the TV/Bayes-risk identity [K2] |
| Lorden reference | `log(1/α)/KL` | Lorden [K7] |

Smoothing is applied over the **whole** support rather than only observed
values, so the log-ratio stays finite when the substituted model emits a symbol
the baseline never produced — which is exactly the high-evidence event the
detector should reward.

**Measured (held-out rep14, no test leakage):**

| tier | substitution | KL(B‖A) | TV | Bayes err. |
|---|---|---:|---:|---:|
| easy | llama3.2:3b → qwen2.5:3b | 2.149 | 0.725 | 0.138 |
| medium | llama3.2:1b → llama3.2:3b | 1.450 | 0.635 | 0.183 |
| hard | q4_K_M → q8_0 | **0.152** | **0.186** | **0.407** |

## II.2 An oracle upper bound was added

`detector_oracle.py` implements Page's CUSUM [K6] on the **exact** categorical
log-likelihood ratio, given both PMFs fitted from held-out data:

```
S_t = max(0, S_{t-1} + log( p_B(x_t) / p_A(x_t) )),   flag when S_t > log(1/α)
```

This detector cheats — no deployable monitor knows `p_B` — and exists so every
real detector can be reported as a fraction of what was attainable on the
channel, rather than only against its neighbours in a table.

- **Method:** CUSUM on the log-likelihood ratio — Page [K6]
- **Optimality:** exactly optimal under Lorden's criterion — Moustakides [K8],
  Lorden [K7]
- **Threshold:** `log(1/α)` via Ville's inequality [K9]

**Result:** easy 1.29 probes at 100% power and zero false alarms; medium 4.86;
hard 106 probes at only **21.4%** power.

## II.3 The compression detector — and two constructions that look right and are not

This is the most substantive methodological work, and it took three attempts.

### Attempt 1: excess surprisal — invalid

Accumulate `−log p(x) − H(p)`. It is mean-zero under the null, which makes it
feel like a natural evidence accumulator. But `E[exp(·)] = K·exp(−H) ≫ 1`, so
`exp(S)` is not a supermartingale, Ville's inequality [K9] does not apply, and a
`log(1/α)` threshold buys nothing.

### Attempt 2: frozen null vs adaptive alternative — invalid, and it produced a false headline

Freeze `p₀` on a warmup window, run an adaptive KT codebook against it,
accumulate `log q/p₀`. This looks like a likelihood ratio. It is not a
martingale: `E[q/p₀] = 1` requires `p₀` to be the **true** null law, not a
40-sample estimate of it. The adaptive code compresses better purely by having
seen more data.

Measured on a single **clean** null stream, where the correct answer is "nothing
happened":

```
t= 60   log_e =  -13.05
t=100   log_e =  -21.54
t=200   log_e =    4.60
t=397   log_e =  +92.92        <- on a stream with no substitution

frozen  p0(53) = 0.1722
adaptive  q(53) = 0.3076       <- nothing changed; the estimate just sharpened

false-alarm rate, every alpha from 1e-1 to 1e-6:  100%
```

This is the construction that produced my earlier claim of **5.27 probes at 100%
power**. That number is withdrawn: the statistic drifts upward on its own, so
"fast detection" was partly the detector detecting its own estimation error.

### Attempt 3: both codes prequential — valid

Make the null adaptive too:

```
null         q_all  -- one KT codebook fed every observation from t=0
alternative  q_v    -- a KT codebook restarted at candidate change point v

logLR(v,t) = Σ_{i=v..t} [ log q_v(x_i | x_v..x_{i-1})
                          − log q_all(x_i | x_0..x_{i-1}) ]
```

Each prequential code defines a genuine joint probability distribution over
sequences, so for any two of them `E_P[Q/P] = 1` holds exactly and Ville applies.
The null being tested — "one stationary categorical law generated this whole
stream" — is precisely the hypothesis of interest, and needs no oracle knowledge
of what that law is. Under the null the restarted code has strictly less data, so
the statistic drifts *negative*: the model-complexity penalty MDL is supposed to
charge, which makes the test conservative rather than anti-conservative.

Mixing over the unknown change point gives a Shiryaev–Roberts statistic with
`E[R_t] = t` under the null, thresholded at `t/α`.

**Methods and sources:**

| Component | Reference |
|---|---|
| KT add-½ predictive estimator | Krichevsky & Trofimov [K1] |
| Prequential coding / plug-in codes | Dawid [K3]; Grünwald [K4] |
| MDL, two-part vs one-part codes | Rissanen [K5]; Grünwald [K4] |
| Ville's inequality, anytime-valid thresholds | Ville [K9] |
| E-processes, safe testing | Ramdas et al. [K10]; Grünwald et al. [K11]; Vovk & Wang [K12] |
| Shiryaev–Roberts mixture over change points | Shiryaev [K13]; Roberts [K14] |
| Union bound over the routing grid | Bonferroni [K15] |

**Variants shipped:** `eprocess_detector` (Ville-valid, no reset),
`mdl_cusum_detector` (CUSUM form, rearms, empirical control),
`mixture_alternative_detector` (alternative is `(1−r)·p_null + r·p_other`, for
partial routing, where a clean-swap alternative tests the wrong hypothesis).

## II.4 The anytime-valid guarantee was checked, not asserted

`calibration.py` sweeps α over six orders of magnitude on clean null streams and
reports the fraction that ever fire. A detector claiming `P(false alarm) ≤ α`
makes a checkable promise; asserting the theorem is not evidence.

**Result:** the e-process fires on **0 of 15 streams at every α on every tier**.
The CUSUM variant, whose reset breaks the martingale, **violates at α = 0.1 on
the medium tier (7/15)** — exactly where the theory says a reset should break it.
Theory and measurement agree on both counts.

With 15 streams the smallest resolvable rate is 1/15 = 0.067, and the script says
so rather than implying resolution the sample size does not support.

## II.5 Comparison at a matched false-alarm budget

Comparing detectors at their default settings is not like-for-like: adaptive
CUSUM at `h=5` reaches 8.50 probes on easy but false-alarms on 7 of 14 clean
streams, while the e-process raises none.

`matched_operating_point.py` tunes every threshold-bearing detector to the
tightest setting that stays silent on held-out rep14, then scores on reps 0–13 —
so no threshold is chosen on the streams it is scored against.

| tier | detector | tuned | delay | power | streams w/ FA |
|---|---|---|---:|---:|---:|
| easy | adaptive CUSUM | h=5 | **8.50** | 100% | **7/14** |
| easy | e-process | α=1e−2 | 17.29 | 100% | **0/14** |
| medium | e-process | α=1e−2 | **29.64** | **100%** | **0/14** |
| medium | adaptive CUSUM | h=6 | 40.14 | 50.0% | 4/14 |

**Two findings, one uncomfortable.** At a matched budget the tuned CUSUM is
*faster* on easy — the e-process is not a speed win, and should not be described
as one. What it buys is that its threshold is derived from α rather than swept,
and **the swept threshold did not generalise**: CUSUM at `h=5` was silent on the
held-out stream and still fired on 7 of 14 test streams. Deployed against a real
endpoint there is no labelled substitution stream to sweep against. On medium the
e-process wins outright.

---

# Part III — New capabilities

## III.1 Adversarial provider strategies

Every original result assumed a provider who swaps 100% of traffic at a clean
instant and does not know it is being audited. `adversary.py` makes the provider
a first-class object.

| Strategy | Behaviour | Provider keeps |
|---|---|---:|
| `Honest` | never substitutes — the control | 0% |
| `FullSwap` | 100% of traffic after the switch | 83% |
| `PartialRoute(r)` | fraction *r* of requests to the cheap model | (1−r) |
| `ProbeAwareCache` | serves audit-shaped requests honestly from cache | 82% |
| `DistributionMatched` | cheap model, output resampled to match the marginal | 71% |

`DistributionMatched` is unbeatable on a single channel *by construction* — the
marginal is identical, so no test on that channel can have power above α. It is
included to mark the boundary honestly, not to be beaten.

**The measurement that changed how the table reads.** Adding the `honest` control
revealed that adaptive CUSUM fires on honest traffic **20% of the time**, so its
apparent 20–30% power against weak routing is its own false-alarm rate. The
output now reports *excess power over the honest baseline* and flags every cell
where that excess is under 10 points.

**Frontier (easy tier, 30 trials, offline resampling):**

| strategy | keeps | e-process | mixture-alt | CUSUM |
|---|---:|---|---|---|
| honest *(control)* | 0% | 0% | 0% | **20%** |
| full swap | 83% | 100% | 100% | 93% |
| route 75% | 62% | 97% | 100% | 80% |
| route 50% | 42% | 0% | **30%** | 60% |
| route 25% | 21% | 0% | 3% | 30% |
| probe-aware cache | **82%** | 0% | 0% | 30% |

**Below 25% routing, no detector beats its own noise floor.** A provider willing
to cheat on a fifth of traffic is safe on this channel. `ProbeAwareCache` defeats
everything while keeping 82% of the saving, for the price of one string match.

*Caveat:* offline resampling from logged pools destroys within-session run
structure, so delays are pessimistic. Power numbers and shapes are final;
absolute delays need `run_adversarial.py --online`.

## III.2 Probe design as experimental design

The three original probe templates were hand-written and are not equally
informative — on easy, "Name a random number" leaves llama's top answer at 17.9%
mass while "Give me a random integer" concentrates it at 47.1%. Nothing measured
that.

- **`probe_bank.py`** — 83 candidates across five families: `random_number` (48),
  `covert_task` (15), `binary_choice` (8), `open_categorical` (8), `formatting`
  (4). Each declares its parser, support, token cost, and whether it reads as
  organic traffic.
- **`run_probe_survey.py`** — samples the bank against every model. **Requires
  Ollama**; the only blocked step.
- **`probe_selection.py`** — ranks by information per token billed, scoring each
  probe on its **worst** model pair rather than its average, because the
  adversary chooses which substitution to make. Greedy selection under a token
  budget with a per-family cap.

**Methods:** expected information gain — Lindley [K16]; sequential design of
experiments — Chernoff [K17]; greedy selection under a cardinality constraint —
Nemhauser, Wolsey & Fisher [K18].

## III.3 Probe camouflage — a constraint nobody has stated

`fpverify` [V4] ships the "pick a random number" probe in a public repository, so
a provider can filter audit traffic with one string match. `camouflage.py`
measures how easily.

| filter | probes caught | organic misrouted |
|---|---:|---:|
| one-line keyword match | **78.3%** | 2.5% |
| character n-gram classifier | 83.8% held-out accuracy | — |

**The finding that lands: the three templates this project shipped with are the
most detectable probes in the entire bank** (classifier p ≈ 0.959–0.966). Least
detectable: `covert_sep` (0.436), `fmt_list` (0.473), `covert_indent` (0.583).

The declared-covert set is still caught 68.4% of the time, because several still
carry "One word." or "Number only." formatting instructions. Not papered over —
it is the next edit to the bank.

**Methods:** character n-gram features with the hashing trick — Weinberger et al.
[K19]; logistic regression by gradient descent (no `sklearn` dependency added).

*Caveat:* the organic corpus is a 40-line hand-written stand-in so the module
runs offline. Point `--organic` at a real prompt log before quoting the numbers.

## III.4 Identification, not just detection

An alarm saying "something changed" is not actionable; a customer disputing a
bill needs "you are being served qwen2.5:3b, posterior 0.94".

`detector_lineup.py` keeps a codebook per candidate model, fitted only on
held-out rep14, and reports a posterior over a **trailing window** so it answers
"who is serving me now" rather than being dominated by pre-switch history. A flat
catch-all with prior mass `prior_unknown` absorbs streams matching nothing, so
the report can say "not any model I hold" instead of naming the least-wrong
option.

| tier | exact model | model family |
|---|---:|---:|
| easy | **14/14 = 100%** | 14/14 = 100% |
| medium | 6/14 = 42.9% | 14/14 = 100% |
| hard | 3/14 = 21.4% | 14/14 = 100% |
| **all** | 23/42 = 54.8% | **42/42 = 100%** |

The lineup never picks the wrong model *family*. Every error is `llama3.2:3b`
confused with its own q4_K_M or q8_0 quantization — the same weights at different
precision. Reporting only the 54.8% would have hidden that.

**Method:** Bayesian model selection with a categorical likelihood and a
uniform-plus-catch-all prior — standard; see Cover & Thomas [K2] for the coding
interpretation. Contrast with Bruckner [V2], who does one-shot identification
against a reference library rather than as the output of a sequential alarm.

## III.5 Reimplemented 2026 comparators

`detector_baselines_2026.py`. **These are reconstructions from the papers'
descriptions, adapted to a single-token integer channel — not the authors' code**,
and they are labelled as such throughout.

| Comparator | After | Method |
|---|---|---|
| `energy_distance_detector` | Leshin et al. [V1] | energy distance — Székely & Rizzo [K20]; permutation test [K21]; p-to-e conversion via `1/p` [K12] |
| `js_fingerprint_detector` | Bruckner [V2] | Jensen–Shannon divergence — Lin [K22] |

**A finding worth reporting:** Bruckner's published 0.30 JS cut never fires here
(0% power), because KT smoothing over 100 symbols compresses JS. The *separation*
is fine — 0.040 pre-switch vs 0.200 post. A fixed threshold from another corpus
does not transfer. Recalibrated to 0.08 it is competitive on easy and unusable on
medium (12/14 false-alarm streams).

## III.6 Data audit and reproducible paper assets

- **`audit_data.py`** — per-file parse completeness and a per-tier separability
  verdict, which states outright when a channel is too blind for detector work to
  be meaningful.
- **`run_experiments.py`** — now preflights the Ollama tag list, takes tier
  arguments, and writes streams atomically.
- **`paper/make_assets.py`** — single source of truth: reads the experiment CSVs
  and emits 418 LaTeX macros, `numbers.json`, booktabs tables and four figures.
  `--check` exits nonzero while any asset is provisional.

---

# Part IV — Results, before and after

Same data, same 14 test repetitions. Every difference is caused by the changes
above, not by regenerating streams.

| tier | detector | delay before → after | power before → after | FA rate before → after |
|---|---|---|---|---|
| easy | KS sliding window | 15.33 → 13.75 | 85.7% → 85.7% | 0.000% → 0.120% |
| easy | adaptive CUSUM | 11.00 → **8.50** | 78.6% → **100%** | 0.417% → 0.220% |
| easy | variance CUSUM | 53.00 → 43.00 | 57.1% → 57.1% | 0.377% → 0.060% |
| easy | fixed reference | 20.00 → 20.00 | 100% → 100% | 0.357% → 0.376% |
| medium | KS sliding window | 14.50 → 52.33 | 14.3% → 21.4% | 0.159% → 0.179% |
| medium | adaptive CUSUM | 41.15 → 28.67 | **92.9% → 64.3%** | 0.080% → 0.220% |
| medium | variance CUSUM | 83.55 → 153.00 | **78.6% → 21.4%** | 0.000% → 0.000% |
| medium | fixed reference | 22.86 → 22.86 | 100% → 100% | 0.752% → 1.880% |
| hard | KS sliding window | 126.00 → 123.25 | 28.6% → 28.6% | 0.000% → 0.040% |
| hard | adaptive CUSUM | 71.20 → 60.00 | **71.4% → 28.6%** | 0.575% → 0.261% |
| hard | variance CUSUM | 88.75 → 87.00 | **57.1% → 14.3%** | 0.536% → 0.100% |
| hard | fixed reference | 90.00 → 80.00 | 14.3% → 7.1% | 0.357% → 0.376% |

**Reading this table.** The power drops on medium and hard are not a regression —
they are the removal of parse artifacts (see I.1). False-alarm rates rise
throughout because they are now counted over the whole null stream (see I.3).
The easy-tier CUSUM improvement is genuine: outliers had been masking detection.

**New rows the original had no equivalent for:**

| tier | detector | delay | power | streams w/ FA |
|---|---|---:|---:|---:|
| easy | **oracle LR-CUSUM** *(upper bound)* | **1.29** | 100% | 0/14 |
| easy | e-process (Ville) | 30.29 | 100% | **0/14** |
| easy | energy distance [Leshin] | 68.57 | 100% | 1/14 |
| medium | oracle LR-CUSUM | 4.86 | 100% | 0/14 |
| medium | e-process (Ville) | 38.36 | 100% | **0/14** |
| hard | oracle LR-CUSUM | 106.00 | **21.4%** | 2/14 |

**The negative result.** On the hard tier, even an oracle handed both
distributions reaches only 21.4% power. Quantization substitution (q4_K_M vs
q8_0) is close to invisible on the numeric probe channel — KL = 0.152 nats/probe,
single-probe Bayes error 0.407, barely better than a coin flip. No detector work
fixes this; it needs a different probe family.

---

# Part V — Documentation

| Change | Rationale |
|---|---|
| `PAPER.md` **new** | The argument: problem, prior art, contributions, method, results, limitations |
| `RESULTS.md` **new** | Every table with the command that regenerates it |
| `README.md` rewritten | What it is, how to run, what needs Ollama, what to distrust |
| `paper/OUTLINE.md` **new** | Section-by-section status: READY / PROVISIONAL / BLOCKED |
| `paper/CLAIMS.md` **new** | 28 claims mapped to macro and producing script, plus claims to avoid |
| `paper/references.bib` **new** | 22 entries, each marked VERIFIED or UNVERIFIED |
| 4 reports → `docs/archive/` | Numbers predate the parser fix. **Moved, not deleted** — isolated to file moves so a maintainer can revert that alone |

Removed from the README: "Production Ready" and "Enterprise-grade" badges, and
the ASCII directory tree duplicated across four documents.

---

# Part VI — Reference list

## Verified in this work

Opened and checked. Claims attributed to them were read from the source.

- **[V1]** Leshin, Shah, Timmis & Kang. *Behavioral Fingerprints for LLM Endpoint
  Stability and Identity.* arXiv:2603.19022, Mar 2026.
  <https://arxiv.org/abs/2603.19022> — self-baselining, e-value sequential
  evidence, energy distance with permutation testing, 800 requests per
  fingerprint. **Its limitations section names partial routing and adversarial
  providers as open**, which is this work's motivation. *Author given names were
  not captured; complete before citing.*
- **[V2]** Bruckner, Tomas. *One Token Is Enough: Fingerprinting and Verifying
  Large Language Models from Single-Token Output Distributions.*
  arXiv:2607.10252, Jul 2026. <https://arxiv.org/abs/2607.10252> — 165 models,
  326k requests; Jensen–Shannon on single-token PMFs; reference-based one-shot
  identification, ~100 queries per audit.
- **[V3]** Gao, Irena; Liang, Percy; Guestrin, Carlos. *Model Equality Testing:
  Which Model Is This API Serving?* ICLR 2025, arXiv:2410.20247.
  <https://arxiv.org/abs/2410.20247> — MMD with a string kernel; 77.4% median
  power at ~10 samples/prompt; **11 of 31 commercial Llama endpoints deviated
  from Meta's reference weights**.
- **[V4]** `fpverify`. <https://github.com/Mohamed7415/fpverify> — single-token
  probes plus a betting e-process. Its **public** probe set is why camouflage is
  a binding constraint rather than a hypothetical one.
- **[V5]** Surfaced in search, listed by title only, **not read in depth**:
  *Auditing Black-Box LLM APIs with a Rank-Based Uniformity Test*
  (arXiv:2506.06975); *KBF: Knowledge Boundary as Fingerprint*
  (arXiv:2605.29524); *Token-Efficient Change Detection in LLM APIs*
  (arXiv:2602.11083). Authors not captured — complete before citing.

## From background knowledge — verify before citing

Standard, long-established results. Not opened during this work.

**Information theory**
- **[K1]** Krichevsky, R. E. & Trofimov, V. K. *The Performance of Universal
  Encoding.* IEEE Trans. Inf. Theory 27(2):199–207, 1981. — the add-½ predictive
  estimator used in every codebook here.
- **[K2]** Cover, T. M. & Thomas, J. A. *Elements of Information Theory.* 2nd ed.,
  Wiley, 2006. — KL, entropy, total variation, the TV/Bayes-risk identity.
- **[K3]** Dawid, A. P. *Present Position and Potential Developments: Some
  Personal Views. Statistical Theory: The Prequential Approach.* JRSS-A
  147(2):278–292, 1984. — the prequential principle the valid construction rests on.
- **[K4]** Grünwald, P. D. *The Minimum Description Length Principle.* MIT Press,
  2007. — MDL, plug-in and prequential codes.
- **[K5]** Rissanen, J. *Modeling by Shortest Data Description.* Automatica
  14(5):465–471, 1978. — MDL origin.
- **[K23]** Willems, Shtarkov & Tjalkens. *The Context-Tree Weighting Method:
  Basic Properties.* IEEE Trans. Inf. Theory 41(3):653–664, 1995. — relevant only
  if the run-structure extension is pursued.

**Sequential change detection**
- **[K6]** Page, E. S. *Continuous Inspection Schemes.* Biometrika 41(1/2):100–115,
  1954. — CUSUM.
- **[K7]** Lorden, G. *Procedures for Reacting to a Change in Distribution.* Ann.
  Math. Statist. 42(6):1897–1908, 1971. — the `h/KL` reference. **Worst case over
  change points, asymptotic in h — never a denominator for an average-case delay.**
- **[K8]** Moustakides, G. V. *Optimal Stopping Times for Detecting Changes in
  Distributions.* Ann. Statist. 14(4):1379–1387, 1986. — exact optimality of
  CUSUM under Lorden's criterion.
- **[K13]** Shiryaev, A. N. *On Optimum Methods in Quickest Detection Problems.*
  Theory Probab. Appl. 8(1):22–46, 1963.
- **[K14]** Roberts, S. W. *A Comparison of Some Control Chart Procedures.*
  Technometrics 8(3):411–430, 1966. — with [K13], the Shiryaev–Roberts mixture.
- **[K24]** Basseville, M. & Nikiforov, I. V. *Detection of Abrupt Changes: Theory
  and Application.* Prentice Hall, 1993.
- **[K25]** Tartakovsky, Nikiforov & Basseville. *Sequential Analysis: Hypothesis
  Testing and Changepoint Detection.* CRC Press, 2014.

**E-values and anytime-valid inference**
- **[K9]** Ville, J. *Étude critique de la notion de collectif.* Gauthier-Villars,
  1939. — Ville's inequality; the threshold `log(1/α)`.
- **[K10]** Ramdas, Grünwald, Vovk & Shafer. *Game-Theoretic Statistics and Safe
  Anytime-Valid Inference.* Statistical Science, 2023. arXiv:2210.01948 —
  *surfaced in search but not opened.*
- **[K11]** Grünwald, de Heide & Koolen. *Safe Testing.* JRSS-B, 2024.
- **[K12]** Vovk, V. & Wang, R. *E-values: Calibration, Combination and
  Applications.* Ann. Statist. 49(3), 2021. — including `1/p` as a valid e-value.

**Statistical tests**
- **[K20]** Székely, G. J. & Rizzo, M. L. — energy distance / energy statistics.
  *Exact venue and year need checking; the concept appears across several of
  their papers from 2004 onward.*
- **[K21]** Permutation testing — Fisher (1935) / Pitman (1937). *Standard; pick a
  canonical citation.*
- **[K22]** Lin, J. *Divergence Measures Based on the Shannon Entropy.* IEEE
  Trans. Inf. Theory 37(1):145–151, 1991. — Jensen–Shannon divergence.
- **[K26]** Kolmogorov (1933) / Smirnov (1948) — the two-sample KS test used by
  the original `detector_v1.py`, via `scipy.stats.ks_2samp`.
- **[K27]** Gretton, Borgwardt, Rasch, Schölkopf & Smola. *A Kernel Two-Sample
  Test.* JMLR 13:723–773, 2012. — MMD, for context on [V3].
- **[K15]** Bonferroni correction — standard; used for the union bound over the
  routing grid in `mixture_alternative_detector`.

**Experimental design and machine learning**
- **[K16]** Lindley, D. V. *On a Measure of the Information Provided by an
  Experiment.* Ann. Math. Statist. 27(4):986–1005, 1956. — expected information
  gain.
- **[K17]** Chernoff, H. *Sequential Design of Experiments.* Ann. Math. Statist.
  30(3):755–770, 1959.
- **[K18]** Nemhauser, Wolsey & Fisher. *An Analysis of Approximations for
  Maximizing Submodular Set Functions.* Math. Programming 14:265–294, 1978. —
  the greedy guarantee invoked by `probe_selection.py`. *Note: the objective as
  implemented is a simple sum and is not verified to be submodular, so the
  guarantee is motivational rather than established. Either prove submodularity
  or drop the claim before publication.*
- **[K19]** Weinberger, Dasgupta, Langford, Smola & Attenberg. *Feature Hashing
  for Large Scale Multitask Learning.* ICML 2009. — the hashing trick in
  `camouflage.py`.

---

# Appendix — File-by-file

**New modules (23):** `stats_categorical.py`, `detector_oracle.py`,
`detector_variance_cusum.py`, `detector_compression.py`,
`detector_baselines_2026.py`, `detector_lineup.py`, `adversary.py`,
`audit_data.py`, `calibration.py`, `matched_operating_point.py`,
`run_adversarial.py`, `probe_bank.py`, `run_probe_survey.py`,
`probe_selection.py`, `camouflage.py`, `requirements.txt`,
`paper/make_assets.py`, plus `PAPER.md`, `RESULTS.md`, `CHANGES.md`,
`paper/OUTLINE.md`, `paper/CLAIMS.md`, `paper/references.bib`.

**Modified (6):** `config.py` (MAX_TOKENS 5→8, VALID_RANGE added),
`data_loader.py` (reject taxonomy, path resolution, `split_by_model`),
`evaluate.py` (whole-stream false alarms, oracle, ×oracle ratio with a 50%-power
floor, tier skipping), `run_experiments.py` (MAX_TOKENS threading, preflight,
tier args, atomic writes), `simulator.py` and `probe_client.py` (MAX_TOKENS from
config), `final-analysis/visualizations.py` (import rename).

**Deleted (1):** `detector_das_cusum.py` — superseded by
`detector_variance_cusum.py`, old name retained as a deprecation alias.

**Archived (4):** `FINNNNNNAAAAALreport.md` → `docs/archive/FINAL_report_2026-08.md`;
`COMPLETE_PROJECT_REPORT.md`, `TEAM_REFERENCE_PROGRESS_REPORT.md`,
`EXPERIMENT_EVALUATION_GUIDE.md` → `docs/archive/`.

## Still outstanding

Both require a live Ollama serving stack:

1. `run_probe_survey.py` → `probe_selection.py` — the probe leaderboard.
   ~25k generations, resumable.
2. `run_adversarial.py --online` — run-structure-preserving delays for the
   frontier. Power numbers and shapes are already final; only absolute delays move.
