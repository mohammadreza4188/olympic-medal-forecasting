# Sensitivity: zero-inflated models for aggregation

```
=== Sensitivity: zero-inflated models for aggregation ===

============================================================
=== TEST YEAR 2012 (PRIMARY) ===
============================================================
  sports: XGB=31, Hurdle=31, total=31
  calibration factor (train_actual_mean / test_agg_mean) = 1.117

  model                    RMSE   log_RMSE    vs M0
  M0 naive                2.758      0.420
  M1 XGB direct           2.618      0.364    +5.1%
  M1 Hurdle direct        3.231      0.456   -17.1%
  AGG XGB                 3.823      0.348   -38.6%
  AGG Hurdle              2.779      0.383    -0.8%
  AGG XGB calibrated      3.219      0.355   -16.7%

============================================================
=== TEST YEAR 2016 (PRIMARY) ===
============================================================
  sports: XGB=31, Hurdle=31, total=31
  calibration factor (train_actual_mean / test_agg_mean) = 1.045

  model                    RMSE   log_RMSE    vs M0
  M0 naive                2.906      0.359
  M1 XGB direct           3.559      0.353   -22.5%
  M1 Hurdle direct        3.879      0.452   -33.5%
  AGG XGB                 3.662      0.343   -26.0%
  AGG Hurdle              3.214      0.371   -10.6%
  AGG XGB calibrated      3.516      0.347   -21.0%

============================================================
=== TEST YEAR 2020 (SENSITIVITY) ===
============================================================
  sports: XGB=31, Hurdle=31, total=31
  calibration factor (train_actual_mean / test_agg_mean) = 1.482

  model                    RMSE   log_RMSE    vs M0
  M0 naive                3.514      0.457
  M1 XGB direct           3.726      0.380    -6.0%
  M1 Hurdle direct        5.372      0.446   -52.9%
  AGG XGB                 5.518      0.439   -57.0%
  AGG Hurdle              5.182      0.429   -47.5%
  AGG XGB calibrated      3.610      0.386    -2.7%

============================================================
=== TEST YEAR 2024 (SENSITIVITY) ===
============================================================
  sports: XGB=31, Hurdle=31, total=31
  calibration factor (train_actual_mean / test_agg_mean) = 1.418

  model                    RMSE   log_RMSE    vs M0
  M0 naive                3.310      0.458
  M1 XGB direct           3.651      0.387   -10.3%
  M1 Hurdle direct        5.031      0.465   -52.0%
  AGG XGB                 6.477      0.426   -95.7%
  AGG Hurdle              6.450      0.443   -94.8%
  AGG XGB calibrated      3.483      0.402    -5.2%

============================================================
=== SUMMARY (all test years) ===
============================================================
 edition         tag  M0_rmse  M1_xgb_rmse  M1_hurdle_rmse  AGG_xgb_rmse  AGG_hurdle_rmse  AGG_calib_rmse
    2012     PRIMARY    2.758        2.618           3.231         3.823            2.779           3.219
    2016     PRIMARY    2.906        3.559           3.879         3.662            3.214           3.516
    2020 SENSITIVITY    3.514        3.726           5.372         5.518            5.182           3.610
    2024 SENSITIVITY    3.310        3.651           5.031         6.477            6.450           3.483

=== PRIMARY (2012, 2016) — mean relative to naive ===
  M1_xgb         mean_vs_M0 = -8.7%
  M1_hurdle      mean_vs_M0 = -25.3%
  AGG_xgb        mean_vs_M0 = -32.3%
  AGG_hurdle     mean_vs_M0 = -5.7%
  AGG_calib      mean_vs_M0 = -18.9%

=== VERDICT ===
  Best aggregation variant: AGG_hurdle (mean RMSE = 2.996)
  Naive mean RMSE: 2.832
  => Aggregation still fails; null result is robust
```
