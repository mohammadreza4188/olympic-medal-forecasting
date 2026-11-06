# Chapter 3.2 — Women's feature evaluation

```
=== Chapter 3.2: Women's feature evaluation ===
seed=42
primary: rows=1543 editions=[1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
variants: ['M1', 'M1_women', 'M1_women_rca']

--- test 2012: train=756 test=197
  M0        /naive    rmse=  2.758  log_rmse=0.420  rho=0.855
  M1          /poisson rmse=  3.321  log_rmse=0.591  rho=0.763
  M1          /hurdle  rmse=  3.231  log_rmse=0.456  rho=0.810
  M1          /rf      rmse=  2.560  log_rmse=0.380  rho=0.841
  M1          /xgb     rmse=  2.675  log_rmse=0.370  rho=0.834
  M1_women    /poisson rmse=  2.807  log_rmse=0.449  rho=0.823
  M1_women    /hurdle  rmse=  2.946  log_rmse=0.419  rho=0.834
  M1_women    /rf      rmse=  2.366  log_rmse=0.380  rho=0.840
  M1_women    /xgb     rmse=  2.660  log_rmse=0.367  rho=0.845
  M1_women_rca/poisson rmse=  2.927  log_rmse=0.449  rho=0.821
  M1_women_rca/hurdle  rmse=  3.075  log_rmse=0.431  rho=0.827
  M1_women_rca/rf      rmse=  2.489  log_rmse=0.382  rho=0.840
  M1_women_rca/xgb     rmse=  3.130  log_rmse=0.375  rho=0.840

--- test 2016: train=953 test=198
  M0        /naive    rmse=  2.906  log_rmse=0.359  rho=0.889
  M1          /poisson rmse=  5.385  log_rmse=0.608  rho=0.790
  M1          /hurdle  rmse=  3.879  log_rmse=0.452  rho=0.835
  M1          /rf      rmse=  3.386  log_rmse=0.336  rho=0.849
  M1          /xgb     rmse=  3.921  log_rmse=0.342  rho=0.847
  M1_women    /poisson rmse=  3.737  log_rmse=0.436  rho=0.845
  M1_women    /hurdle  rmse=  3.612  log_rmse=0.411  rho=0.845
  M1_women    /rf      rmse=  3.562  log_rmse=0.339  rho=0.851
  M1_women    /xgb     rmse=  3.969  log_rmse=0.346  rho=0.848
  M1_women_rca/poisson rmse=  3.670  log_rmse=0.426  rho=0.844
  M1_women_rca/hurdle  rmse=  3.640  log_rmse=0.410  rho=0.843
  M1_women_rca/rf      rmse=  3.461  log_rmse=0.340  rho=0.851
  M1_women_rca/xgb     rmse=  3.666  log_rmse=0.336  rho=0.847

--- test 2020: train=1151 test=197
  M0        /naive    rmse=  3.514  log_rmse=0.457  rho=0.869
  M1          /poisson rmse=  4.361  log_rmse=0.594  rho=0.782
  M1          /hurdle  rmse=  5.372  log_rmse=0.446  rho=0.831
  M1          /rf      rmse=  3.290  log_rmse=0.389  rho=0.841
  M1          /xgb     rmse=  3.261  log_rmse=0.384  rho=0.845
  M1_women    /poisson rmse=  5.641  log_rmse=0.445  rho=0.843
  M1_women    /hurdle  rmse=  6.172  log_rmse=0.422  rho=0.847
  M1_women    /rf      rmse=  3.157  log_rmse=0.390  rho=0.838
  M1_women    /xgb     rmse=  3.468  log_rmse=0.395  rho=0.844
  M1_women_rca/poisson rmse=  5.299  log_rmse=0.444  rho=0.841
  M1_women_rca/hurdle  rmse=  5.906  log_rmse=0.416  rho=0.847
  M1_women_rca/rf      rmse=  3.240  log_rmse=0.390  rho=0.837
  M1_women_rca/xgb     rmse=  3.449  log_rmse=0.395  rho=0.844

--- test 2024: train=1348 test=195
  M0        /naive    rmse=  3.310  log_rmse=0.458  rho=0.849
  M1          /poisson rmse=  4.955  log_rmse=0.596  rho=0.774
  M1          /hurdle  rmse=  5.031  log_rmse=0.465  rho=0.818
  M1          /rf      rmse=  3.595  log_rmse=0.411  rho=0.836
  M1          /xgb     rmse=  3.674  log_rmse=0.377  rho=0.844
  M1_women    /poisson rmse=  4.805  log_rmse=0.460  rho=0.822
  M1_women    /hurdle  rmse=  5.054  log_rmse=0.443  rho=0.832
  M1_women    /rf      rmse=  3.686  log_rmse=0.412  rho=0.834
  M1_women    /xgb     rmse=  3.579  log_rmse=0.375  rho=0.840
  M1_women_rca/poisson rmse=  4.409  log_rmse=0.451  rho=0.822
  M1_women_rca/hurdle  rmse=  4.567  log_rmse=0.437  rho=0.830
  M1_women_rca/rf      rmse=  3.638  log_rmse=0.411  rho=0.836
  M1_women_rca/xgb     rmse=  3.558  log_rmse=0.373  rho=0.841

=== Aggregate ===
     variant  family  rmse_mean  log_rmse_mean  rho_mean
          M0   naive      3.122          0.424     0.866
          M1  hurdle      4.378          0.455     0.824
          M1 poisson      4.506          0.597     0.777
          M1      rf      3.208          0.379     0.842
          M1     xgb      3.383          0.369     0.843
    M1_women  hurdle      4.446          0.424     0.840
    M1_women poisson      4.247          0.447     0.833
    M1_women      rf      3.193          0.380     0.841
    M1_women     xgb      3.419          0.371     0.844
M1_women_rca  hurdle      4.297          0.423     0.837
M1_women_rca poisson      4.076          0.443     0.832
M1_women_rca      rf      3.207          0.381     0.841
M1_women_rca     xgb      3.451          0.370     0.843

=== M1_women vs M1 ===
 edition  family    M0    M1  M1_women  M1_women_rca  women_vs_M1_pct  women_rca_vs_M1_pct
    2012  hurdle   NaN 3.231     2.946         3.075            8.808                4.806
    2012   naive 2.758   NaN       NaN           NaN              NaN                  NaN
    2012 poisson   NaN 3.321     2.807         2.927           15.492               11.860
    2012      rf   NaN 2.560     2.366         2.489            7.564                2.784
    2012     xgb   NaN 2.675     2.660         3.130            0.572              -17.007
    2016  hurdle   NaN 3.879     3.612         3.640            6.896                6.173
    2016   naive 2.906   NaN       NaN           NaN              NaN                  NaN
    2016 poisson   NaN 5.385     3.737         3.670           30.613               31.849
    2016      rf   NaN 3.386     3.562         3.461           -5.177               -2.186
    2016     xgb   NaN 3.921     3.969         3.666           -1.224                6.484
    2020  hurdle   NaN 5.372     6.172         5.906          -14.905               -9.939
    2020   naive 3.514   NaN       NaN           NaN              NaN                  NaN
    2020 poisson   NaN 4.361     5.641         5.299          -29.359              -21.506
    2020      rf   NaN 3.290     3.157         3.240            4.042                1.532
    2020     xgb   NaN 3.261     3.468         3.449           -6.331               -5.743
    2024  hurdle   NaN 5.031     5.054         4.567           -0.464                9.228
    2024   naive 3.310   NaN       NaN           NaN              NaN                  NaN
    2024 poisson   NaN 4.955     4.805         4.409            3.035               11.028
    2024      rf   NaN 3.595     3.686         3.638           -2.516               -1.185
    2024     xgb   NaN 3.674     3.579         3.558            2.606                3.181

=== Per-family summary ===
 family  women_mean  women_min  women_max  n_pos  women_rca_mean
 hurdle       0.084    -14.905      8.808      2           2.567
  naive         NaN        NaN        NaN      0             NaN
poisson       4.945    -29.359     30.613      3           8.308
     rf       0.978     -5.177      7.564      2           0.236
    xgb      -1.094     -6.331      2.606      2          -3.271
```
