# Chapter 3.5 — per-sport dataset build

```
=== Chapter 3.5: per-sport dataset build ===
athlete_events: shape=(315094, 15)
primary NOCs: 201
medal grid: shape=(3084, 4) sports=38
participation grid: shape=(13566, 4)
sport-level features: shape=(254, 3)
sports kept (>= 5 of 8 editions): 31
  Archery, Athletics, Badminton, Baseball, Basketball, Boxing, Canoeing, Cycling, Diving, Equestrianism, Fencing, Football, Gymnastics, Handball, Hockey, Judo, Modern Pentathlon, Rowing, Sailing, Shooting, Softball, Swimming, Synchronized Swimming, Table Tennis, Taekwondo, Tennis, Triathlon, Volleyball, Water Polo, Weightlifting, Wrestling
full grid: shape=(49848, 3)
after medal merge: medals mean=0.140 zero_share=0.941
after participation merge: participation_rate=0.258
after sport-level merge: sport_n_events mean=9.7
after macro merge: shape=(49848, 18)
after RCA merge: rca non-zero rate=0.094
after lag: shape=(49848, 21)

per_sport_dataset.csv saved: shape=(49848, 21)
columns: ['NOC', 'Year', 'Sport', 'medals_in_sport', 'lag_medals_in_sport', 'n_athletes_in_sport', 'country_sent_athletes_in_sport', 'sport_n_events', 'rca_sport', 'prior_medals_sport', 'log_gdp_const_avg4y', 'log_gdp_pcap_const_avg4y', 'log_population_avg4y', 'athletes', 'sports', 'events', 'female_share', 'host', 'lag_mt_total', 'lag_mt_gold', 'sample_primary']

=== zero share by year ===
  1996: n=  6231  zero_share=0.948  mean=0.133
  2000: n=  6231  zero_share=0.939  mean=0.147
  2004: n=  6231  zero_share=0.939  mean=0.147
  2008: n=  6231  zero_share=0.938  mean=0.152
  2012: n=  6231  zero_share=0.939  mean=0.153
  2016: n=  6231  zero_share=0.939  mean=0.152
  2020: n=  6231  zero_share=0.945  mean=0.115
  2024: n=  6231  zero_share=0.944  mean=0.119

=== diagnostics per sport (top 8 by mean medals) ===
            mean_medals  total_medals  n_events  participation_rate
Sport                                                              
Athletics         0.675          1085    46.625               0.947
Swimming          0.481           774    34.000               0.783
Wrestling         0.315           507    18.000               0.311
Judo              0.272           437    14.250               0.534
Cycling           0.254           408    18.500               0.335
Gymnastics        0.248           399    17.750               0.254
Boxing            0.234           377    12.250               0.378
Canoeing          0.217           349    15.000               0.264

=== diagnostics per sport (bottom 8 by mean medals) ===
                       mean_medals  total_medals  n_events  participation_rate
Sport                                                                         
Baseball                     0.009            15     0.625               0.022
Softball                     0.009            15     0.625               0.022
Synchronized Swimming        0.021            33     1.875               0.078
Triathlon                    0.026            42     2.000               0.164
Water Polo                   0.027            43     1.875               0.067
Modern Pentathlon            0.028            45     1.875               0.133
Handball                     0.029            47     2.000               0.087
Basketball                   0.029            47     2.000               0.086

=== Sanity check: sum of per-sport medals vs mt_total ===
  1996: mean_diff=+0.01  max_diff=1  rows_with_diff_gt5=0
  2000: mean_diff=+0.01  max_diff=2  rows_with_diff_gt5=0
  2004: mean_diff=-0.01  max_diff=0  rows_with_diff_gt5=0
  2008: mean_diff=+0.01  max_diff=6  rows_with_diff_gt5=1
  2012: mean_diff=-0.02  max_diff=4  rows_with_diff_gt5=0
  2016: mean_diff=+0.06  max_diff=2  rows_with_diff_gt5=0
  2020: mean_diff=+1.43  max_diff=28  rows_with_diff_gt5=16
  2024: mean_diff=+1.47  max_diff=36  rows_with_diff_gt5=15
```
