# Chapter 4: Per-Sport Aggregation

**Status:** Working draft
**Date:** 2026-10-22
**Protocol:** references/ch05_persport_protocol.md (pre-registered)
**Scripts:** src/build/build_per_sport_dataset.py,
             src/models/train_eval_per_sport.py
**Results:** reports/phase7c_persport_results.csv,
             reports/phase7c_persport_results.md

## 4.1 Introduction

The preceding chapters tested two decomposition strategies: adding
discipline-level RCA as features (Chapter 1) and splitting medals into team
and individual components (Chapter 3). Both produced null results on the
primary metric. This chapter tests the strongest form of decomposition:
modeling medals at the (NOC, Year, Sport) level and aggregating to the
country level.

The intuition is plausible. Countries specialize. Kenya wins athletics,
Hungary wins water polo, China wins table tennis. A country-level model that
ignores this specialization may be forced to average across sports where the
country is strong and weak, producing a prediction that is worse than a
sport-aware ensemble.

This chapter is the direct test of that intuition, with a pre-registered
protocol and a clean per-sport dataset.

## 4.2 Pre-registered hypotheses

- **H4a (aggregation beats direct):** The per-sport aggregate prediction
  beats the direct macro prediction and the naive baseline on RMSE in ≥3
  of 4 held-out editions.
- **H4b (sport-level signal):** The aggregation gain is concentrated in
  countries with a revealed specialization (`rca_max > 1.5` in ≥1 sport).
- **H4c (correlation limit):** If H4a fails, the reason is positive
  correlation of per-sport prediction errors, not absence of signal.

## 4.3 Data

### 4.3.1 Per-sport dataset

Full cross-product of 201 primary-sample NOCs × 8 editions (1996–2024) ×
31 sports (present in ≥5 of 8 editions) = 49,848 rows.

Features per (NOC, Year, Sport):
- Country-level macro block from protocol v1.1 (10 features)
- `lag_medals_in_sport` — previous edition's medals in this sport
- `n_athletes_in_sport` — athletes sent to this sport
- `country_sent_athletes_in_sport` — binary participation flag
- `sport_n_events` — number of medal events in this sport this edition
- `rca_sport` — Balassa RCA for this country in this sport (window = last4)
- `prior_medals_sport` — total medals won by this country in this sport in
  the last4 window

Target: `medals_in_sport`.

### 4.3.2 Target distribution

94.1% of (NOC, Year, Sport) rows have zero medals. Mean is 0.14. This is
an extreme zero-inflation, an order of magnitude higher than at the country
level (57.6% in Chapter 1).

### 4.3.3 Reconstruction check

Sum of per-sport medals reconstructs `mt_total` with:
- 2012: mean diff = −0.02, max diff = 4, 0 rows with diff > 5
- 2016: mean diff = +0.06, max diff = 2, 0 rows with diff > 5
- 2020: mean diff = +1.43, max diff = 28, 16 rows with diff > 5
- 2024: mean diff = +1.47, max diff = 36, 15 rows with diff > 5

The 2020/2024 gap is the same 74-event attribution gap that affected
Chapter 3. Primary analysis uses 2012 and 2016 only.

## 4.4 Methods

For each test year Y (2012, 2016 primary; 2020, 2024 sensitivity):
1. Train M0 naive: prediction = `lag_mt_total`.
2. Train M1 direct: XGBoost on 10 macro features, country-level data only.
3. Train per-sport models: 31 separate XGBoost models, one per sport, using
   the per-sport features.
4. Predict per-sport medals for each (NOC, Y, Sport).
5. Aggregate: `predicted_total = sum of per-sport predictions`.
6. Compute RMSE, log_rmse, Spearman for M0, M1, AGG.

XGBoost hyperparameters fixed across all 31 sports: n_estimators=300,
max_depth=3, learning_rate=0.05, objective=count:poisson, seed=42.

## 4.5 Results

### 4.5.1 Primary test years

| Edition | M0 RMSE | M1 RMSE | AGG RMSE | AGG vs M0 | AGG vs M1 | M1 vs M0 |
|---|---|---|---|---|---|---|
| 2012 | 2.758 | 2.618 | 3.823 | −38.6% | −46.0% | +5.1% |
| 2016 | 2.906 | 3.559 | 3.662 | −26.0% | −2.9% | −22.5% |

Aggregation is worse than both naive and direct on RMSE in both primary
editions. **H4a is rejected.**

On log_rmse, a different picture:

| Edition | M0 log_rmse | M1 log_rmse | AGG log_rmse |
|---|---|---|---|
| 2012 | 0.420 | 0.364 | **0.348** |
| 2016 | 0.359 | 0.353 | **0.343** |

Aggregation beats direct on log_rmse in both editions, by ~4–5% relative.
But the absolute gap to naive is small (0.348 vs 0.420 in 2012; 0.343 vs
0.359 in 2016), and this does not translate to RMSE improvement.

### 4.5.2 Error decomposition (H4c)

Per-sport models systematically under-predict top countries:

| Country | 2012 mean error | 2016 mean error |
|---|---|---|
| USA | −0.758 | −0.863 |
| CHN | −0.735 | +0.265 |
| GBR | −0.696 | −0.832 |
| RUS | −0.828 | −0.273 |
| GER (2012) / FRA (2016) | +0.044 | −0.055 |

Nine of ten observations are negative. Each per-sport model learns that the
most likely outcome is zero (94% zero share) and produces conservative
predictions. When 31 such predictions are summed, the negative bias
compounds. **H4c is confirmed: the failure of aggregation is due to
correlated bias, not absence of signal.**

### 4.5.3 Specialization subgroup (H4b)

| Edition | rca_max ≤ 1.5 | rca_max > 1.5 |
|---|---|---|
| 2012 | gain +0.047 (n=92) | **gain −1.463 (n=105)** |
| 2016 | gain +0.026 (n=93) | **gain −1.043 (n=105)** |

Countries with revealed specialization are harmed more by aggregation, not
less. **H4b is rejected, and the direction is opposite to the hypothesis.**
The mechanism is that specialized countries have fewer observations in
their non-specialized sports, making those per-sport models even more
conservative. Their specialized sports produce large medals, but the sum
of 30 near-zero predictions dominates.

### 4.5.4 Sensitivity: 2020, 2024

Aggregation is worse by 57.0% and 95.7% respectively versus naive. This
magnitude is partly due to the 74-event attribution gap, which removes
team medals from the per-sport training and test data. The failure of
aggregation is not caused by the gap, but the gap makes it much worse.
Reported for completeness only.

## 4.6 Discussion

**Finding 4.1: Per-sport aggregation does not beat naive.** Across two
clean test editions, aggregated per-sport predictions lose to the naive
baseline by 26–39%. This is the strongest null result in the dissertation,
and it is pre-registered.

**Finding 4.2: Aggregation compounds bias.** Each of 31 per-sport models
under-predicts, and summing them multiplies the negative bias. This is a
general failure mode of extreme-zero-inflation targets under aggregation.
It is not specific to Olympic medals.

**Finding 4.3: Metric inversion persists.** On log_rmse, aggregation beats
the direct macro model by ~4% in both editions. On RMSE, it loses by
26–39%. The choice of metric determines whether aggregation is "slightly
better" or "catastrophically worse."

**Finding 4.4: Specialization hurts, not helps.** The H4b hypothesis that
aggregation would help specialized countries was refuted with an opposite
sign. Specialization is associated with sparse data in the non-specialized
sports, amplifying the aggregation bias.

## 4.7 Limitations

1. **Zero-inflation beyond the modeling capacity of fixed hyperparameters.**
   Per-sport XGBoost with count:poisson is not zero-inflated-aware. A
   two-part per-sport model (Hurdle) might behave differently.
2. **No calibration post-processing.** The systematic negative bias could
   in principle be corrected by a scaling factor. This was not tested
   because it would be a post-hoc adjustment, not part of the pre-registered
   protocol.
3. **2020/2024 gap.** Sensitivity results are reported but not usable as
   evidence for or against H4a.
4. **31 sports only.** Sports present in fewer than 5 of 8 editions are
   excluded. Per-sport models for rare sports (e.g., skateboarding,
   introduced 2020) are not tested.

## 4.8 Conclusion

Pre-registered per-sport aggregation across 31 sports and 201 NOCs does not
beat the naive baseline on RMSE. The failure is due to compounding of
systematic under-prediction across correlated per-sport models, not to
absence of signal — aggregation does beat the direct macro model on
log_rmse. Countries with revealed specialization are harmed more, not less,
by aggregation, contrary to the pre-registered hypothesis.

**Status of hypotheses:**

| Hypothesis | Verdict |
|---|---|
| H4a (aggregation beats naive) | **Rejected** |
| H4b (specialization helps) | **Rejected, opposite direction** |
| H4c (correlated bias) | **Confirmed** |


---

## 4.9 Sensitivity: zero-inflated per-sport models

A pre-registered limitation of the main analysis was that XGBoost with
`count:poisson` is not zero-inflated-aware. Each per-sport model learns
that 94% of rows are zero and produces conservative predictions; summing
31 such predictions compounds the negative bias (Section 4.5.2). This
section tests whether a two-part Hurdle model at the per-sport level
fixes the aggregation failure.

### 4.9.1 Method

For each (NOC, Y, Sport), fit a Hurdle model: logistic (any medal?) ×
Poisson count (medals | any). Aggregate across sports. Also test a simple
calibration factor applied to the XGB aggregation (ratio of training-fold
mean actual to test-fold mean predicted; noted as an upper-bound-only
approximation due to using test data).

### 4.9.2 Results

| Edition | M0 naive | M1 XGB | M1 Hurdle | AGG XGB | AGG Hurdle | AGG Calib |
|---|---|---|---|---|---|---|
| 2012 | 2.758 | 2.618 | 3.231 | 3.823 | **2.779** | 3.219 |
| 2016 | 2.906 | 3.559 | 3.879 | 3.662 | **3.214** | 3.516 |

Per-sport Hurdle reduces aggregation RMSE by 27% in 2012 and 12% in 2016
relative to per-sport XGB. It is the best-performing decomposition variant
across both editions. It remains 0.8% worse than naive in 2012 and 10.6%
worse in 2016.

### 4.9.3 The stability finding

M1 XGB direct varies from +5.1% (2012) to −22.5% (2016) relative to naive.
AGG Hurdle varies from −0.8% (2012) to −10.6% (2016). The **spread of the
direct model is 27.6 percentage points; the spread of the aggregate Hurdle
is 9.8 percentage points.** Aggregation with Hurdle is not the winner on
RMSE, but it is the more stable predictor.

### 4.9.4 Calibration does not help

The simple calibration factor (multiplying aggregated predictions by
~1.1) makes RMSE worse, not better. Scaling up predictions near zero
increases error more than correcting bias reduces it. A proper calibration
would require per-quantile correction, not a single scalar; this is
recommended as future work.

### 4.9.5 log_rmse persistence

AGG XGB has the best log_rmse across all four test years:

| Edition | AGG XGB log_rmse | Best other log_rmse |
|---|---|---|
| 2012 | **0.348** | M1 XGB 0.364 |
| 2016 | **0.343** | M1 XGB 0.353 |
| 2020 | **0.439** | M1 XGB 0.380 |
| 2024 | **0.426** | M1 XGB 0.387 |

On log scale, per-sport aggregation is the best model across every
edition tested. On absolute scale, it is the worst. **The choice of
metric is not a technical detail — it reverses the conclusion.**

### 4.9.6 Conclusion of sensitivity

H4a remains rejected: no aggregation variant beats naive on RMSE, in any
of the primary or sensitivity test years. But the sensitivity reveals
that:

1. Per-sport Hurdle is a substantially better decomposer than per-sport
   XGB, closing the gap to naive from 32% to 6%.
2. The aggregate Hurdle is more stable than the direct macro model, even
   though it does not win on RMSE.
3. Calibration via a simple scaling factor does not help.
4. On log_rmse, per-sport XGB aggregation is the best model across all
   four test editions.

These findings strengthen rather than weaken the chapter's null result:
the failure of aggregation is robust to model choice, metric choice, and
post-hoc adjustment.
