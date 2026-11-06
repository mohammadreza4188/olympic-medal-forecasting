# Chapter 3.4 — Team vs individual evaluation

```
=== Chapter 3.4: team vs individual evaluation ===
seed=42
primary: rows=1543 editions=[1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]

########## TARGET = team_medals ##########
test years for this target: [2012, 2016]

--- 2012: train=756 test=197  zero_share=0.792
  M0/naive    rmse=  1.276  log_rmse=0.269  rho=0.831
  M1       /poisson  rmse=  1.229  log_rmse=0.343  rho=0.613
  M1       /hurdle   rmse=  1.045  log_rmse=0.295  rho=0.658
  M1       /rf       rmse=  0.802  log_rmse=0.240  rho=0.743
  M1       /xgb      rmse=  1.132  log_rmse=0.240  rho=0.665
  M1_noLag /poisson  rmse=  1.206  log_rmse=0.342  rho=0.622
  M1_noLag /hurdle   rmse=  1.049  log_rmse=0.321  rho=0.647
  M1_noLag /rf       rmse=  0.929  log_rmse=0.282  rho=0.709
  M1_noLag /xgb      rmse=  1.450  log_rmse=0.289  rho=0.652

--- 2016: train=953 test=198  zero_share=0.783
  M0/naive    rmse=  0.967  log_rmse=0.320  rho=0.766
  M1       /poisson  rmse=  1.844  log_rmse=0.392  rho=0.633
  M1       /hurdle   rmse=  1.258  log_rmse=0.331  rho=0.667
  M1       /rf       rmse=  1.064  log_rmse=0.296  rho=0.719
  M1       /xgb      rmse=  1.254  log_rmse=0.300  rho=0.684
  M1_noLag /poisson  rmse=  2.052  log_rmse=0.391  rho=0.634
  M1_noLag /hurdle   rmse=  1.414  log_rmse=0.359  rho=0.661
  M1_noLag /rf       rmse=  1.442  log_rmse=0.307  rho=0.735
  M1_noLag /xgb      rmse=  1.478  log_rmse=0.301  rho=0.686

########## TARGET = individual_medals ##########
test years for this target: [2012, 2016, 2020, 2024]

--- 2012: train=756 test=197  zero_share=0.599
  M0/naive    rmse=  2.422  log_rmse=0.421  rho=0.841
  M1       /poisson  rmse=  2.575  log_rmse=0.555  rho=0.750
  M1       /hurdle   rmse=  2.303  log_rmse=0.433  rho=0.787
  M1       /rf       rmse=  2.005  log_rmse=0.369  rho=0.820
  M1       /xgb      rmse=  2.840  log_rmse=0.351  rho=0.819
  M1_noLag /poisson  rmse=  2.999  log_rmse=0.562  rho=0.743
  M1_noLag /hurdle   rmse=  3.120  log_rmse=0.472  rho=0.773
  M1_noLag /rf       rmse=  2.677  log_rmse=0.409  rho=0.811
  M1_noLag /xgb      rmse=  2.681  log_rmse=0.401  rho=0.808

--- 2016: train=953 test=198  zero_share=0.601
  M0/naive    rmse=  3.173  log_rmse=0.380  rho=0.877
  M1       /poisson  rmse=  4.555  log_rmse=0.568  rho=0.768
  M1       /hurdle   rmse=  3.338  log_rmse=0.434  rho=0.819
  M1       /rf       rmse=  2.896  log_rmse=0.361  rho=0.826
  M1       /xgb      rmse=  3.124  log_rmse=0.378  rho=0.820
  M1_noLag /poisson  rmse=  4.540  log_rmse=0.578  rho=0.760
  M1_noLag /hurdle   rmse=  4.115  log_rmse=0.477  rho=0.799
  M1_noLag /rf       rmse=  4.525  log_rmse=0.429  rho=0.812
  M1_noLag /xgb      rmse=  4.240  log_rmse=0.428  rho=0.811

--- 2020: train=1151 test=197  zero_share=0.553
  M0/naive    rmse=  3.032  log_rmse=0.476  rho=0.834
  M1       /poisson  rmse=  3.577  log_rmse=0.576  rho=0.765
  M1       /hurdle   rmse=  4.075  log_rmse=0.435  rho=0.814
  M1       /rf       rmse=  2.942  log_rmse=0.404  rho=0.823
  M1       /xgb      rmse=  2.858  log_rmse=0.397  rho=0.834
  M1_noLag /poisson  rmse=  4.305  log_rmse=0.591  rho=0.747
  M1_noLag /hurdle   rmse=  5.423  log_rmse=0.480  rho=0.784
  M1_noLag /rf       rmse=  4.274  log_rmse=0.443  rho=0.807
  M1_noLag /xgb      rmse=  4.776  log_rmse=0.416  rho=0.829

--- 2024: train=1348 test=195  zero_share=0.554
  M0/naive    rmse=  3.288  log_rmse=0.461  rho=0.830
  M1       /poisson  rmse=  3.626  log_rmse=0.565  rho=0.759
  M1       /hurdle   rmse=  3.570  log_rmse=0.439  rho=0.807
  M1       /rf       rmse=  2.989  log_rmse=0.398  rho=0.823
  M1       /xgb      rmse=  2.571  log_rmse=0.393  rho=0.824
  M1_noLag /poisson  rmse=  4.310  log_rmse=0.582  rho=0.746
  M1_noLag /hurdle   rmse=  4.976  log_rmse=0.494  rho=0.784
  M1_noLag /rf       rmse=  3.372  log_rmse=0.425  rho=0.817
  M1_noLag /xgb      rmse=  3.185  log_rmse=0.434  rho=0.811

=== Aggregate by (target, variant, family) ===
           target  variant  family  rmse_mean  log_rmse_mean  rho_mean  n_editions
individual_medals       M0   naive      2.979          0.434     0.846           4
individual_medals       M1  hurdle      3.322          0.435     0.807           4
individual_medals       M1 poisson      3.583          0.566     0.760           4
individual_medals       M1      rf      2.708          0.383     0.823           4
individual_medals       M1     xgb      2.848          0.380     0.824           4
individual_medals M1_noLag  hurdle      4.408          0.481     0.785           4
individual_medals M1_noLag poisson      4.038          0.578     0.749           4
individual_medals M1_noLag      rf      3.712          0.427     0.812           4
individual_medals M1_noLag     xgb      3.721          0.420     0.815           4
      team_medals       M0   naive      1.122          0.294     0.798           2
      team_medals       M1  hurdle      1.152          0.313     0.662           2
      team_medals       M1 poisson      1.536          0.367     0.623           2
      team_medals       M1      rf      0.933          0.268     0.731           2
      team_medals       M1     xgb      1.193          0.270     0.675           2
      team_medals M1_noLag  hurdle      1.232          0.340     0.654           2
      team_medals M1_noLag poisson      1.629          0.367     0.628           2
      team_medals M1_noLag      rf      1.186          0.295     0.722           2
      team_medals M1_noLag     xgb      1.464          0.295     0.669           2

=== H3b: relative RMSE improvement over naive, per target ===

--- team_medals ---
  poisson  M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
  hurdle   M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
  rf       M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
  xgb      M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%

--- individual_medals ---
  poisson  M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
  hurdle   M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
  rf       M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
  xgb      M1_gap_mean=  +nan%   M1_noLag_gap_mean=  +nan%
```
