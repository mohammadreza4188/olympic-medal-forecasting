# Chapter 2: Women's Participation and Olympic Medal Prediction

**Status:** Working draft
**Date:** 2026-10-18
**Protocol:** references/ch03_women_protocol.md (pre-registered)
**Scripts:** src/build/build_women_features.py, src/models/train_eval_women.py
**Results:** reports/phase7a_women_results.csv

## 2.1 Introduction

Female participation in the Summer Olympic Games has risen from 2.2% of
athletes in Paris 1900 to approximately 49% in Paris 2024, where the
International Olympic Committee (IOC) achieved full gender parity in athlete
quotas for the first time. This rise is not purely symbolic: in most sports,
women now contest roughly half of the available medal events, so women's
athletic production is numerically comparable to men's in a way it was not
three decades ago.

Yet the predictive value of gender information in Olympic medal forecasting
remains under-examined. Standard macro-level models (Bernard and Busse 2004;
Schlembach et al. 2022) aggregate medal counts across sexes. Where gender is
examined (Leeds and Leeds 2012; Noland and Stahler 2016), it tends to be
treated as a descriptive covariate or within a single-edition analysis rather
than as a candidate feature whose incremental predictive value is tested
out-of-sample across multiple editions. Recent athlete-level work (Choi 2026)
is informative but operates on a different unit of analysis and a single
national system.

This chapter tests whether gender-disaggregated features—beyond the simple
share of female athletes (`female_share`) already present in the baseline
macro block—improve out-of-sample prediction of a country's total medal count.
The hypothesis structure is pre-registered (Section 2.2). The answer turns out
to be: **on RMSE, no; on log_rmse, only for linear count models.**

## 2.2 Pre-registered hypotheses

- **H2a (parsimony):** `female_share` in the macro block is sufficient;
  granular gender features do not improve prediction.
- **H2b (RCA-gender):** gender-disaggregated RCA features (revealed
  specialization among female athletes) add predictive value beyond both
  `female_share` and aggregate RCA.
- **H2c (time trend):** the association between gender-specific features and
  medal count strengthens in post-2000 editions. *(Not formally tested in
  this draft; see Section 2.7.)*

Three nested variants:

| Variant | Features |
|---|---|
| M1 (baseline) | 10 macro features including `female_share` |
| M1_women | M1 + `log_female_athletes` + `lag_female_medal_share` + `female_athletes_to_pop_ratio` + `lag_female_medal_share_missing` |
| M1_women_rca | M1_women + `rca_mean_weighted_female` + `n_sports_rca_gt1_female` + `medal_hhi_female` |

## 2.3 Data and features

### 2.3.1 Sample

Primary sample: 1,543 country-edition observations across eight Summer
editions (1996–2024) and 201 NOCs, restricted to rows with complete macro
features. The count outcome `mt_total` is 57.6% zero-valued.

### 2.3.2 Gender feature construction

Same-edition medal counts by sex are derived from
`athlete_events_through_2026.csv` using the team-medal de-duplication rule
from Chapter 1 (one medal per NOC–Year–Sport–Event–Medal tuple). These
variables are stored in `model_dataset_women.csv` for descriptive reporting
only. They are **not** used as model inputs, because they are direct functions
of the target.

Four features are candidates:

1. **`log_female_athletes`** — log1p of female athletes sent (participation
   intensity). Available pre-Games.
2. **`lag_female_medal_share`** — female medal share in the previous edition.
   Lagged, therefore leakage-free.
3. **`female_athletes_to_pop_ratio`** — female athletes divided by
   four-year-average population. A depth-of-talent-pool proxy.
4. **`lag_female_medal_share_missing`** — binary flag, 1 when the previous
   edition had no medal (0/0 undefined). Per protocol v1.1, NaN fills with 0
   and is flagged.

Additionally, three gender-disaggregated RCA features from
`discipline_features.csv` (variant=female, window=last4) are used in
`M1_women_rca`: `rca_mean_weighted_female`, `n_sports_rca_gt1_female`,
`medal_hhi_female`.

### 2.3.3 Descriptive trends

| Edition | Mean female_share | Mean female medals |
|---|---|---|
| 1996 | 0.255 | 1.66 |
| 2004 | 0.364 | 2.02 |
| 2012 | 0.403 | 2.14 |
| 2020 | 0.423 | 1.88 |
| 2024 | 0.439 | 1.92 |

This secular rise is why H2c was worth pre-registering. It also raises the
concern that any observed effect of gender features could be confounded with
time trends in participation.

## 2.4 Methods

Identical to Chapter 1 (Section 1.4):

- Forward-chaining validation on test years 2012, 2016, 2020, 2024.
- Four model families: Poisson GLM, Hurdle (logistic × Poisson), Random
  Forest, XGBoost (`count:poisson`).
- Fixed hyperparameters, seed 42.
- Primary metric: RMSE. Secondary: log_rmse, Spearman rank correlation.
- Pre-registered H2a decision rule: M1_women must beat M1 on RMSE by ≥3%
  averaged across editions, with positive direction in ≥3 of 4 editions, in
  ≥3 of 4 families.

## 2.5 Results

### 2.5.1 RMSE: H2a confirmed

Aggregate RMSE across the four held-out editions:

| Variant | Poisson | Hurdle | RF | XGB |
|---|---|---|---|---|
| M1 | 4.506 | 4.378 | 3.208 | 3.383 |
| M1_women | 4.247 | 4.446 | 3.193 | 3.419 |
| M1_women_rca | 4.076 | 4.297 | 3.207 | 3.451 |

Per-family mean improvement of M1_women over M1:

| Family | mean | min | max | positive / 4 |
|---|---|---|---|---|
| Poisson | +4.9% | −29.4% | +30.6% | 3 |
| Hurdle | +0.1% | −14.9% | +8.8% | 2 |
| RF | +1.0% | −5.2% | +7.6% | 2 |
| XGB | −1.1% | −6.3% | +2.6% | 2 |

The Poisson family shows a positive mean (+4.9%) but is unstable: +30.6% in
2016, −29.4% in 2020. RF and Hurdle are effectively zero. XGB is slightly
negative.

**H2a is confirmed.** No family meets the pre-registered threshold of ≥3%
mean improvement with ≥3 of 4 editions positive. `female_share` alone carries
the gender signal that matters for RMSE.

### 2.5.2 log_rmse: linear models improve, tree models do not

Aggregate log_rmse across editions:

| Variant | Poisson | Hurdle | RF | XGB |
|---|---|---|---|---|
| M1 | 0.597 | 0.455 | 0.379 | 0.369 |
| M1_women | **0.447** | **0.424** | 0.380 | 0.371 |
| M1_women_rca | 0.443 | 0.423 | 0.381 | 0.370 |

Relative change M1 → M1_women:

- Poisson: **−25.1%**
- Hurdle: **−6.8%**
- RF: +0.3%
- XGB: +0.5%

**The metric inversion is stark.** The same feature set that is
neutral-to-harmful on RMSE cuts Poisson's log-scale error by a quarter. Two
explanations are plausible:

1. Tree models already exploit `female_share` as a sufficient split;
   correlated features add noise without new signal. Linear count models,
   which add effects linearly, gain from the additional predictors.
2. Metric selection determines conclusions. RMSE is dominated by the largest
   countries (US, China, Russia, Germany) because it penalizes error in
   absolute medal units. log_rmse weights countries more equally.

### 2.5.3 RCA-gender add-on: partial value

M1_women_rca beats M1_women on RMSE for Poisson (+8.3% vs +4.9%) and Hurdle
(+2.6% vs +0.1%), is neutral for RF (+0.2%), and harmful for XGB (−3.3%).
On log_rmse, the RCA block adds almost nothing: Poisson 0.447→0.443,
Hurdle 0.424→0.423, RF/XGB unchanged.

Interpretation: `M1_women_rca` is a weak positive for linear count models on
RMSE, but does not meet the pre-registered threshold. **H2b is not
supported on RMSE.**

## 2.6 Discussion

**Finding 2.1: H2a is confirmed on RMSE.** `female_share` carries the
meaningful gender signal for count prediction. Additional granularity does
not produce a pre-registered improvement on RMSE in any model family. This
matches the parsimony argument: gender is a coarse structural feature, and
disaggregating it does not extract additional predictive signal from the
count target.

**Finding 2.2: The metric inversion from Chapter 1 persists.** Chapter 1
showed that M2 (macro + discipline RCA) was neutral on RMSE but positive on
log_rmse. Chapter 2 replicates this pattern with a different feature block.
This is not a coincidence. Absolute error metrics are dominated by ~15 large
countries; log-scale metrics reflect the ~200 small countries that
constitute most of the sample. Any claim about "improving medal prediction"
must specify which population is being improved.

**Finding 2.3: Model family interacts with feature usefulness.** Linear count
models benefit from gender features on log_rmse; tree ensembles do not. The
mechanism is plausibly that trees discover `female_share` as a sufficient
split and treat correlated features as noise; linear models must estimate a
coefficient for each feature and can benefit from additional signal. This
has a practical implication: when testing a new feature block,
model-family heterogeneity is not noise—it is informative.

**Practical implication for sports managers.** The finding does not argue for
abandoning disaggregated gender data. It argues that the marginal predictive
return to granular gender features is small for count prediction. Female
athlete participation share alone—publicly available and easily
measured—provides most of the predictive signal available for medal-count
forecasting.

## 2.7 Limitations

1. **H2c not formally tested.** The pre-registered time-trend hypothesis is
   descriptive only. Formal tests would require interaction terms between
   gender features and edition year, or split-sample coefficient comparison.
   Recommended as future work.
2. **`lag_female_medal_share` for 2024 inherits the athlete_events 2020
   attribution gap.** Phase 0b documented 74 missing medal events in 2020,
   which affects 2024's lag. Zero-fill + flag strategy mitigates but does not
   eliminate this.
3. **Single national system variation.** The sample includes all NOCs, but
   many have never sent female athletes; the `_missing` flag handles this
   structurally but the model has few examples to learn from.
4. **Same-edition female medal share excluded as leakage.** Correct for
   forecasting, but means we cannot test whether in-edition gender
   composition adds value.

## 2.8 Conclusion

Pre-registered forward-chaining evaluation across 1996–2024 shows that
disaggregated gender features do not improve RMSE-based count prediction of
Olympic medals beyond `female_share`. On log_rmse, linear count models
benefit substantially (Poisson −25%), while tree ensembles do not. The
finding replicates Chapter 1's metric-sensitivity pattern and reinforces that
predictive claims about Olympic medals must be evaluated with explicit
attention to both metric and model family.

**Status of hypotheses:**

| Hypothesis | Verdict |
|---|---|
| H2a (parsimony holds) | **Confirmed** on RMSE |
| H2b (RCA-gender adds) | **Not supported** on RMSE |
| H2c (time trend) | **Not tested** — future work |
