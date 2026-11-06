# Chapter 3.4 — Team vs Individual targets

```
=== Chapter 3.4: team vs individual target build ===
model_dataset_women: shape=(3142, 80)
athlete_events: shape=(315094, 15)
targets built: shape=(1459, 9)

Sanity check: |mt_total - (team+individual)|
  mean diff = 0.26   max = 28
  rows with diff > 5: 38  (expected: 2020/2024 attribution gap)

model_dataset_team.csv saved: shape=(3142, 89)

=== H3a: concentration of team vs individual medals ===

team_medals:
  mean = 0.97   max = 30
  zero_share = 0.815
  gini = 0.916
  top_10_share_of_all_medals = 0.181

individual_medals:
  mean = 3.62   max = 93
  zero_share = 0.591
  gini = 0.843
  top_10_share_of_all_medals = 0.141

=== per-edition means (primary sample) ===
  1996: team=1.18  ind=3.38  team_share_of_medals=0.259
  2004: team=1.23  ind=3.53  team_share_of_medals=0.259
  2012: team=1.19  ind=3.65  team_share_of_medals=0.245
  2020: team=0.23  ind=3.73  team_share_of_medals=0.059
  2024: team=0.22  ind=3.82  team_share_of_medals=0.053

=== descriptive: sports by event-level team share ===

Top 8 most team-oriented sports:
               n_medals  team_share
Sport                              
Alpinism              2         1.0
Baseball             18         1.0
Cricket               3         1.0
Basque Pelota         1         1.0
Basketball          102         1.0
Handball             84         1.0
Lacrosse              5         1.0
Volleyball          132         1.0

Top 8 most individual-oriented sports:
                n_medals  team_share
Sport                               
Roque                  3         0.0
Karate                32         0.0
Skateboarding         24         0.0
Sport Climbing        18         0.0
Surfing               12         0.0
Taekwondo            208         0.0
Triathlon             42         0.0
Wrestling           1440         0.0
```
