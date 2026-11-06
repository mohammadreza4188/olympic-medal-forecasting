# Chapter 3: Team vs Individual Medal Prediction

**Status:** Working draft
**Date:** 2026-10-22
**Protocol:** references/ch04_team_protocol.md (pre-registered)
**Scripts:** src/build/build_team_individual.py,
             src/models/train_eval_team.py,
             src/models/analyze_team_results.py
**Results:** reports/phase7b_team_results.csv,
             reports/phase7b_team_posthoc.md

## 3.1 Introduction

Olympic medals are not homogeneous. A country that wins women's basketball
earns one team medal; a country that wins the men's 100m earns one individual
medal. Both count equally in the medal table, but they are produced by
different organizational systems, different talent-development pipelines, and
different pools of athletes. Team medals depend on a small squad that may
include dozens of athletes; individual medals depend on a single athlete's
performance on a given day.

Whether these two categories are equally predictable from macro-level
socioeconomic features has not been systematically tested in the medal
forecasting literature. Studies that include sport-level information (Tcha
and Pershin 2003; Noland and Stahler 2016; Schlembach et al. 2022) treat
medal count as an aggregate. Studies that examine team sports do so at a
single-sport level or within a single edition. A pre-registered two-target
comparison, with a clean classification rule and forward-chaining validation,
is the modest contribution of this chapter.

Two structural facts motivate the inquiry:

1. Team events concentrate medals in a smaller set of large, well-resourced
   countries. Most NOCs never win a team medal.
2. Individual events distribute medals more widely because more countries
   have depth in at least a few individual disciplines.

These facts lead to three pre-registered hypotheses (Section 3.2).

## 3.2 Pre-registered hypotheses

- **H3a (concentration):** Team medals are more concentrated than individual
  medals (higher Gini, higher zero share, higher top-10 share).
- **H3b (predictability):** The same macro block predicts team medals with
  lower relative RMSE than individual medals, because team medals are
  concentrated in a small set of large countries.
- **H3c (gender):** `female_share` has a larger marginal association with
  individual medals than with team medals.

## 3.3 Data and target construction

### 3.3.1 Classification rule

For each (NOC, Year, Sport, Event, Medal) tuple, `team_size` is the number
of unique athlete IDs contributing to that medal. If `team_size > 1`, the
medal is classified as team. If `team_size == 1`, it is individual. This rule
is data-driven, objective, and reproducible. A manual sport-level mapping is
used only for descriptive tables, not for modeling.

### 3.3.2 Coverage check

| Edition | team_mean | individual_mean | team_share |
|---|---|---|---|
| 1996 | 1.18 | 3.38 | 0.259 |
| 2004 | 1.23 | 3.53 | 0.259 |
| 2012 | 1.19 | 3.65 | 0.245 |
| 2020 | 0.23 | 3.73 | **0.059** |
| 2024 | 0.22 | 3.82 | **0.053** |

The team target drops by ~80% in 2020 and 2024. This is not a real change
in Olympic sport; it is an artifact of the 74 missing medal-attribution
events per edition documented in Phase 0b. Individual medals are stable
across all editions.

**Decision:** The team model is evaluated on 2012 and 2016 only.
The individual model is evaluated on all four test years (2012, 2016, 2020,
2024).

### 3.3.3 Reconstruction validity

Sum of team + individual medals per (NOC, Year) reconstructs the medal
table target (`mt_total`) with mean absolute deviation 0.26 and maximum
deviation 28 (in the 2020/2024 editions with the attribution gap). For
2012 and 2016, coverage is 1.003 and 1.001 respectively — essentially exact.

### 3.3.4 Descriptive: which sports are team-dominated

Top team-oriented sports (share of medal events with team_size > 1):
Basketball (1.00), Volleyball (1.00), Handball (1.00), Baseball (1.00),
Hockey (0.99), Football (0.97), Water Polo (0.95), Rugby Sevens (0.93).

Top individual-oriented sports: Karate (0.00), Skateboarding (0.00),
Sport Climbing (0.00), Taekwondo (0.00), Wrestling (0.00), Triathlon (0.00),
Archery (0.02), Shooting (0.02).

## 3.4 Methods

Identical to Chapters 1 and 2:

- Forward-chaining validation on test years 2012, 2016 (team) and 2012,
  2016, 2020, 2024 (individual).
- Four model families: Poisson GLM, Hurdle (logistic × Poisson), Random
  Forest, XGBoost (`count:poisson`).
- Fixed hyperparameters, seed 42.
- Primary metric: RMSE. Secondary: log_rmse, Spearman.
- Two variants per target: `M1` (macro + target-specific lag + lag_mt_gold)
  and `M1_noLag` (macro only, no lag).
- Naive baseline `M0`: predict previous edition's value of the same target.

## 3.5 Results

### 3.5.1 H3a: confirmed

Concentration of team vs individual medals in the primary sample:

| Metric | Team | Individual |
|---|---|---|
| Mean | 0.97 | 3.62 |
| Max | 30 | 93 |
| Zero share | **0.815** | 0.591 |
| Gini | **0.916** | 0.843 |
| Top-10 share | **0.181** | 0.141 |

Team medals are unambiguously more concentrated. **H3a is confirmed.**
This is the first of the two structural facts motivating the chapter: most
NOCs never win a team medal.

### 3.5.2 H3b: rejected on stability

Aggregate RMSE across test editions:

| Target | Best family | M1 RMSE | M0 naive | M1 gap | Editions |
|---|---|---|---|---|---|
| Team | RF | 0.933 | 1.122 | **+13.6%** | 2 |
| Individual | RF | 2.708 | 2.979 | **+9.5%** | 4 |

Per-edition M1 gaps for the best family (RF):

| Edition | Team RF gap | Individual RF gap |
|---|---|---|
| 2012 | +37.1% | +17.2% |
| 2016 | **−10.0%** | +8.7% |
| 2020 | — (contaminated) | +2.9% |
| 2024 | — (contaminated) | +9.1% |

The team model wins on average (+13.6%) but loses in one of two editions
(2016, −10%). The individual model wins in all four editions.

**H3b is rejected on the pre-registered stability criterion.** Individual
medals are more predictably stable across editions, despite the higher
overall variability of the individual target. The team result depends on a
single strong edition (2012); the 2016 loss is substantive, not noise.

### 3.5.3 H3c: direction confirmed, magnitude negligible

| Target | Pearson r with `female_share` | XGB rank of `female_share` |
|---|---|---|
| Team | +0.110 | 6/10 (2012), 7/10 (2016) |
| Individual | **+0.137** | 8/10 (2012–2024) |

The direction is as hypothesized (individual > team), but both correlations
are below 0.15 and XGB importances are 0.004–0.012 — effectively noise. The
XGB rank of `female_share` is higher in the team model than in the
individual model, but this reflects how tree ensembles split importance
across correlated features, not a substantive team–gender interaction.

**H3c is directionally supported, quantitatively negligible.** The
`female_share` association with both targets is weak. This reinforces
Chapter 2's finding that `female_share` alone carries the gender signal, and
that this signal is modest.

### 3.5.4 Bonus: aggregation does not beat naive

Fit RF separately for `team_medals` and `individual_medals`, sum the
predictions, compare to naive:

| Edition | Coverage | RMSE (team + ind sum) | RMSE (naive) | Gap |
|---|---|---|---|---|
| 2012 | 1.003 | 2.745 | 2.758 | +0.5% |
| 2016 | 1.001 | 3.250 | 2.906 | **−11.8%** |

Coverage is essentially 1.00 — the split-and-sum reconstruction is
mathematically valid. But the aggregated prediction does **not** beat naive
in either edition. In 2016 it is worse by 11.8%.

**Interpretation:** Splitting the target into two sub-targets, predicting
each, and summing gives no forecast advantage. Errors from the two
sub-models are positively correlated (both over-predict large countries and
under-predict small ones), so the aggregated error is larger than the errors
of either sub-model would suggest in isolation. This previews the Chapter 4
finding on per-sport aggregation.

## 3.6 Discussion

**Finding 3.1: Team medals are far more concentrated than individual
medals.** The zero share differs by 22 percentage points, the Gini by 0.073,
and the top-10 share by 4 percentage points. For sports managers, this means
that the team-medal distribution is a small-game: roughly 20% of NOCs
participate in it at all in any given edition.

**Finding 3.2: Individual medals are more predictably stable.** The team
model has a higher mean gain but fails in one of two editions. The
individual model wins in all four. Predictability is a stability property,
not a mean-gain property.

**Finding 3.3: `female_share` is weak for both targets.** Correlations below
0.15 in both cases confirm Chapter 2's conclusion: gender composition, at
the country level, is a coarse covariate with modest explanatory power. It
is not a driver of medal count in the causal sense, and it is not a strong
predictor in the statistical sense.

**Finding 3.4: Aggregation does not beat naive.** Splitting the total into
team and individual, modeling each, and summing produces predictions that
are as good or worse than simply repeating the previous edition's total.
This is not a failure of the split itself; it is a consequence of
positive error correlation between the two sub-models.

## 3.7 Limitations

1. **Team target tested on two editions only.** The 2020/2024 attribution
   gap prevents using all four. This is a substantive limitation: the team
   result is based on 2012 and 2016 only, and the 2016 loss carries
   disproportionate weight.
2. **The `team_size > 1` rule conflates team sports with team events.**
   A basketball medal (12 athletes, always team) and a 4x100m relay medal
   (4 athletes, technically an individual sport with a team event) are both
   classified as team. This is defensible for prediction but blurs the
   interpretation in discussion.
3. **`female_share` tested only as a linear correlation.** A nonparametric
   test of gender–target interaction might reveal structure that Pearson r
   and XGB rank miss. Recommended as future work.
4. **No per-sport decomposition.** The current chapter aggregates at the
   NOC–Year level. Chapter 4 pursues the per-sport decomposition.

## 3.8 Conclusion

Pre-registered evaluation shows that team medals are far more concentrated
than individual medals (H3a confirmed), that individual medals are more
predictably stable across editions than team medals (H3b rejected on
stability), and that `female_share` has a marginal association with both
targets that is directionally correct but quantitatively negligible (H3c
directionally supported). An exploratory aggregation test shows that
summing team and individual predictions does not improve on the naive
baseline, previewing Chapter 4's investigation of per-sport decomposition.

**Status of hypotheses:**

| Hypothesis | Verdict |
|---|---|
| H3a (team more concentrated) | **Confirmed** |
| H3b (team more predictable) | **Rejected on stability** |
| H3c (gender asymmetry) | Directionally supported, quantitatively negligible |
| Bonus (aggregation beats naive) | **Rejected** |
