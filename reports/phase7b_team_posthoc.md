# Chapter 3.4 post-hoc analysis

```
=== Chapter 3.4 post-hoc analysis ===
loaded results: shape=(54, 7)

=== H3b: relative RMSE improvement over naive (corrected) ===

--- team_medals (2 test editions) ---
  family        M1_gap   M1_noLag_gap
  poisson       -43.5%         -53.4%
  hurdle         -6.0%         -14.3%
  rf            +13.6%         -11.0%
  xgb            -9.2%         -33.2%

--- individual_medals (4 test editions) ---
  family        M1_gap   M1_noLag_gap
  poisson       -19.5%         -35.0%
  hurdle        -10.8%         -47.2%
  rf             +9.5%         -24.2%
  xgb            +3.0%         -24.7%

=== H3c: female_share marginal association ===
(Pearson r on primary sample + XGB feature importance)

  team_medals:
    Pearson r = +0.110  (p = 1.55e-05, n = 1543)
    2012: female_share rank = 6/10, importance = 0.011
    2016: female_share rank = 7/10, importance = 0.012

  individual_medals:
    Pearson r = +0.137  (p = 6.15e-08, n = 1543)
    2012: female_share rank = 8/10, importance = 0.005
    2016: female_share rank = 8/10, importance = 0.004
    2020: female_share rank = 9/10, importance = 0.004
    2024: female_share rank = 9/10, importance = 0.004

=== Bonus: aggregation test (team + individual vs naive) ===
Fit RF on team and individual, sum predictions, compare to naive total.
Only 2012 and 2016 are valid (2020/2024 team data contaminated).

  2012:
    actual team+individual coverage of total = 1.003
    RMSE (team+ind sum vs total)  = 2.745
    RMSE (naive vs total)          = 2.758
    naive gap of aggregation       = +0.5%

  2016:
    actual team+individual coverage of total = 1.001
    RMSE (team+ind sum vs total)  = 3.250
    RMSE (naive vs total)          = 2.906
    naive gap of aggregation       = -11.8%
```
