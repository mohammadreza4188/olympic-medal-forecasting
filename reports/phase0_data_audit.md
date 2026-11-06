# Phase 0 Data Audit

**date:** 2026-10-18 13:06

**root:** C:\Users\Mohammad Reza\Desktop\sport\olympic-sport-mgmt


### file: athlete_events_through_2026.csv

- size: 40.00 MB
- encoding: utf-8

### file: medal_table_summary.csv

- size: 0.11 MB
- encoding: utf-8

### file: edition_metadata.csv

- size: 0.01 MB
- encoding: utf-8

## A.1. athlete_events_through_2026.csv

- shape: (315094, 15)
- columns: ['ID', 'Name', 'Sex', 'Age', 'Height', 'Weight', 'Team', 'NOC', 'Games', 'Year', 'Season', 'City', 'Sport', 'Event', 'Medal']

**dtypes:**
```
ID          int64
Name       object
Sex        object
Age       float64
Height    float64
Weight    float64
Team       object
NOC        object
Games      object
Year        int64
Season     object
City       object
Sport      object
Event      object
Medal      object
```
- Year=Year Season=Season NOC=NOC Sport=Sport Event=Event Medal=Medal Sex=Sex
- years: min=1896 max=2026 n=40
- noc_unique: 235
- special_nocs_present: ['AIN', 'ANZ', 'BOH', 'EOR', 'EUN', 'FRG', 'GDR', 'IOA', 'ROC', 'SCG', 'TCH', 'UAR', 'URS', 'YUG']
- sports_unique: 69
- events_unique: 1270

**missing rate (top):**
```
Medal     0.860
Weight    0.276
Height    0.258
NOC       0.032
Team      0.032
Age       0.030
```
- full_duplicates: 1385

**critical years coverage:**

| year | rows | noc | sports | medal_rows |
|---|---|---|---|---|
| 2008 | 13602 | 204 | 31 | 2048 |
| 2012 | 12920 | 205 | 29 | 1941 |
| 2016 | 13688 | 207 | 31 | 2023 |
| 2020 | 14535 | 206 | 37 | 1589 |
| 2024 | 13660 | 206 | 35 | 1433 |

**team medal check:**

- 2020: groups=839 mean_athletes_per_medal=1.89 max=25
- 2024: groups=802 mean_athletes_per_medal=1.79 max=23

**rows per year (last 15):**
```
Year
1998     3605
2000    13821
2002     4109
2004    13443
2006     4382
2008    13602
2010     4402
2012    12920
2014     4891
2016    13688
2018     5119
2020    14535
2022     5249
2024    13660
2026     5415
```

## A.2. medal_table_summary.csv

- shape: (1929, 11)
- columns: ['edition_id', 'games', 'year', 'season', 'noc', 'country', 'gold', 'silver', 'bronze', 'total', 'notes']

**dtypes:**
```
edition_id     int64
games         object
year           int64
season        object
noc           object
country       object
gold           int64
silver         int64
bronze         int64
total          int64
notes         object
```

**head(5) first 15 cols:**
```
   edition_id        games  year  season  noc        country  gold  silver  bronze  total notes
0           1  1896 Summer  1896  Summer  USA  United States    11       7       2     20   NaN
1           1  1896 Summer  1896  Summer  GRE         Greece    10      18      19     47   NaN
2           1  1896 Summer  1896  Summer  GER        Germany     6       5       2     13   NaN
3           1  1896 Summer  1896  Summer  FRA         France     5       4       2     11   NaN
4           1  1896 Summer  1896  Summer  GBR  Great Britain     2       3       2      7   NaN
```
- years: min=1896 max=2026 n=40

**missing:**
```
notes    0.934
```
- duplicates: 0

## A.3. edition_metadata.csv

- shape: (62, 14)
- columns: ['edition_id', 'games', 'year', 'season', 'city', 'country', 'opening_ceremony', 'closing_ceremony', 'participants', 'nocs', 'medal_events', 'disciplines', 'notes', 'source']

**dtypes:**
```
edition_id            int64
games                object
year                  int64
season               object
city                 object
country              object
opening_ceremony     object
closing_ceremony     object
participants        float64
nocs                float64
medal_events        float64
disciplines         float64
notes                object
source               object
```

**head(10):**
```
   edition_id        games  year  season       city        country opening_ceremony closing_ceremony  participants  nocs  medal_events  disciplines                                                                                                                 notes                                 source
0           1  1896 Summer  1896  Summer     Athina         Greece       1896-04-06       1896-04-15         176.0  13.0          43.0         10.0                                                                                                                   NaN   https://www.olympedia.org/editions/1
1           2  1900 Summer  1900  Summer      Paris         France              NaN              NaN        1241.0  26.0          95.0         22.0                                                                                                                   NaN   https://www.olympedia.org/editions/2
2           3  1904 Summer  1904  Summer  St. Louis  United States       1904-05-14              NaN         650.0  10.0          95.0         18.0                                                                                                                   NaN   https://www.olympedia.org/editions/3
3           4  1906 Summer  1906  Summer     Athina         Greece       1906-04-22       1906-05-02         841.0  21.0          74.0         14.0  Intercalated Games; not officially recognised by the IOC, but included here to match the original athlete_events.csv   https://www.olympedia.org/editions/4
4           5  1908 Summer  1908  Summer     London  Great Britain       1908-07-13       1908-07-25        2024.0  23.0         110.0         24.0                                                                                                                   NaN   https://www.olympedia.org/editions/5
5           6  1912 Summer  1912  Summer  Stockholm         Sweden       1912-07-06       1912-07-15        2409.0  28.0         107.0         23.0                                                                                                                   NaN   https://www.olympedia.org/editions/6
6          50  1916 Summer  1916  Summer     Berlin        Germany              NaN              NaN           NaN   NaN           NaN          NaN                                                                                          Cancelled due to World War I  https://www.olympedia.org/editions/50
7           7  1920 Summer  1920  Summer  Antwerpen        Belgium       1920-08-14       1920-08-30        2680.0  29.0         162.0         33.0                                                                                                                   NaN   https://www.olympedia.org/editions/7
8           8  1924 Summer  1924  Summer      Paris         France       1924-07-05       1924-07-27        3255.0  45.0         131.0         27.0                                                                                                                   NaN   https://www.olympedia.org/editions/8
9          29  1924 Winter  1924  Winter   Chamonix         France       1924-01-24       1924-02-05         312.0  19.0          17.0         10.0                                                                                                                   NaN  https://www.olympedia.org/editions/29
```
- duplicates: 0

## B. cross-file checks

- (NOC, Year) medal pairs: 1710

**head(5):**
```
   NOC  Year  medals_from_events
0  AFG  2008                   1
1  AFG  2012                   1
2  AHO  1988                   1
3  AIN  2024                   4
4  AIN  2026                   1
```

## Gate 1

_to be filled after joint interpretation._
