# Chapter 3.5 — per-sport evaluation

```
=== Chapter 3.5: per-sport evaluation ===
per_sport dataset: shape=(49848, 21)  sports=31
macro dataset: shape=(3142, 89)

============================================================
=== TEST YEAR 2012 (PRIMARY) ===
============================================================
  sports trained: 31, fallback (predict 0): 0

  metric        M0       M1       AGG
  RMSE         2.758    2.618    3.823
  log_RMSE     0.420    0.364    0.348
  Spearman     0.855    0.838    0.855

  AGG vs M0: -38.6%
  AGG vs M1: -46.0%
  M1  vs M0: +5.1%

============================================================
=== TEST YEAR 2016 (PRIMARY) ===
============================================================
  sports trained: 31, fallback (predict 0): 0

  metric        M0       M1       AGG
  RMSE         2.906    3.559    3.662
  log_RMSE     0.359    0.353    0.343
  Spearman     0.889    0.846    0.841

  AGG vs M0: -26.0%
  AGG vs M1: -2.9%
  M1  vs M0: -22.5%

============================================================
=== TEST YEAR 2020 (SENSITIVITY) ===
============================================================
  sports trained: 31, fallback (predict 0): 0

  metric        M0       M1       AGG
  RMSE         3.514    3.726    5.518
  log_RMSE     0.457    0.380    0.439
  Spearman     0.869    0.848    0.852

  AGG vs M0: -57.0%
  AGG vs M1: -48.1%
  M1  vs M0: -6.0%

============================================================
=== TEST YEAR 2024 (SENSITIVITY) ===
============================================================
  sports trained: 31, fallback (predict 0): 0

  metric        M0       M1       AGG
  RMSE         3.310    3.651    6.477
  log_RMSE     0.458    0.387    0.426
  Spearman     0.849    0.844    0.840

  AGG vs M0: -95.7%
  AGG vs M1: -77.4%
  M1  vs M0: -10.3%

============================================================
=== AGGREGATE SUMMARY ===
============================================================
 edition         tag  M0_rmse  M1_rmse  AGG_rmse  AGG_vs_M0_pct  AGG_vs_M1_pct  M1_vs_M0_pct
    2012     PRIMARY    2.758    2.618     3.823        -38.594        -46.046         5.103
    2016     PRIMARY    2.906    3.559     3.662        -26.027         -2.903       -22.471
    2020 SENSITIVITY    3.514    3.726     5.518        -57.038        -48.082        -6.048
    2024 SENSITIVITY    3.310    3.651     6.477        -95.654        -77.387       -10.298

=== PRIMARY TEST YEARS (2012, 2016) ===
  mean M1_vs_M0:  -8.7%
  mean AGG_vs_M0: -32.3%
  mean AGG_vs_M1: -24.5%
  AGG beats M0 in 0/2 editions
  AGG beats M1 in 0/2 editions

=== H4a verdict (pre-registered) ===
  VERDICT: H4a NOT SUPPORTED

=== H4c: per-sport error correlation diagnostic ===
If H4a fails, we test whether errors of per-sport predictions are correlated.
  2012  USA: n_sports=31, mean_err=-0.758
  2012  CHN: n_sports=31, mean_err=-0.735
  2012  GBR: n_sports=31, mean_err=-0.696
  2012  RUS: n_sports=31, mean_err=-0.828
  2012  GER: n_sports=31, mean_err=+0.044
  2016  USA: n_sports=31, mean_err=-0.863
  2016  CHN: n_sports=31, mean_err=+0.265
  2016  GBR: n_sports=31, mean_err=-0.832
  2016  RUS: n_sports=31, mean_err=-0.273
  2016  FRA: n_sports=31, mean_err=-0.055

=== H4b: specialization subgroup (preliminary) ===
Split countries by rca_max in any sport; compare aggregation gains.
  2012  specialized=0: n=92, AGG_vs_M0_RMSE_gain=+0.047
  2012  specialized=1: n=105, AGG_vs_M0_RMSE_gain=-1.463
  2016  specialized=0: n=93, AGG_vs_M0_RMSE_gain=+0.026
  2016  specialized=1: n=105, AGG_vs_M0_RMSE_gain=-1.043
```
