# phase0b - medal gap audit

## medal_table head
```
   edition_id        games  year  season  noc        country  gold  silver  bronze  total notes
0           1  1896 Summer  1896  Summer  USA  United States    11       7       2     20   NaN
1           1  1896 Summer  1896  Summer  GRE         Greece    10      18      19     47   NaN
2           1  1896 Summer  1896  Summer  GER        Germany     6       5       2     13   NaN
3           1  1896 Summer  1896  Summer  FRA         France     5       4       2     11   NaN
4           1  1896 Summer  1896  Summer  GBR  Great Britain     2       3       2      7   NaN
```
cols: ['edition_id', 'games', 'year', 'season', 'noc', 'country', 'gold', 'silver', 'bronze', 'total', 'notes']

## medal_rows by year
```
   year    season   rows  events  events_medal  nocs  nocs_medal  medal_rows
0  2008  [Summer]  13602     302           302   204          86        2048
1  2012  [Summer]  12920     302           302   205          85        1941
2  2016  [Summer]  13688     306           306   207          86        2023
3  2020  [Summer]  14535     333           259   206          92        1589
4  2024  [Summer]  13660     323           249   206          92        1433
5  2026  [Winter]   5415     116            86    93          28         439
```

## events in 2020/2024 without ANY medal
- 2016: 0 events with zero medals
  []
- 2020: 74 events with zero medals
- 2024: 74 events with zero medals

## NOC cross-check for 2020/2024

## year 2026

## duplicate sample
sample cols: ['Year', 'Season', 'NOC', 'Name', 'Sex', 'Sport', 'Event', 'Medal', 'Team']
```
      Year  Season  NOC                          Name Sex    Sport                    Event Medal            Team
1614  1900  Summer  FRA         Albert Ernest Glandaz   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN      Colette-12
1615  1900  Summer  FRA         Albert Ernest Glandaz   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN      Colette-12
1621  1900  Summer  FRA          Albert Eugne Laverne   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN  Sidi-Fekkar-14
1622  1900  Summer  FRA          Albert Eugne Laverne   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN  Sidi-Fekkar-14
1675  1900  Summer  FRA          Albert Eugne Laverne   M  Sailing    Sailing Mixed 1-2 Ton   NaN        Amulet-3
1676  1900  Summer  FRA          Albert Eugne Laverne   M  Sailing    Sailing Mixed 1-2 Ton   NaN        Amulet-3
1751  1900  Summer  FRA  Camille mile Gaston Michelet   M  Sailing   Sailing Mixed 3-10 Ton   NaN     Turquoise-3
1752  1900  Summer  FRA  Camille mile Gaston Michelet   M  Sailing   Sailing Mixed 3-10 Ton   NaN     Turquoise-3
1749  1900  Summer  FRA        Charles William Martin   M  Sailing   Sailing Mixed 3-10 Ton   NaN     Pirouette-5
1750  1900  Summer  FRA        Charles William Martin   M  Sailing   Sailing Mixed 3-10 Ton   NaN     Pirouette-5
1611  1900  Summer  FRA                       Dupland   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN       Galopin-9
1612  1900  Summer  FRA                       Dupland   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN       Galopin-9
1624  1900  Summer  FRA  Gabriel Charles Jean Le Bret   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN    Crocodile-11
1626  1900  Summer  FRA  Gabriel Charles Jean Le Bret   M  Sailing  Sailing Mixed 0.5-1 Ton   NaN    Crocodile-11
1703  1900  Summer  FRA         Gaston Frdric Blanchy   M  Sailing    Sailing Mixed 2-3 Ton  Gold            Olle
1704  1900  Summer  FRA         Gaston Frdric Blanchy   M  Sailing    Sailing Mixed 2-3 Ton  Gold            Olle
1693  1900  Summer  FRA    Georges Camille Warenhorst   M  Sailing    Sailing Mixed 1-2 Ton   NaN         Freia-5
1694  1900  Summer  FRA    Georges Camille Warenhorst   M  Sailing    Sailing Mixed 1-2 Ton   NaN         Freia-5
1588  1900  Summer  FRA    Georges Louis Paul Smichon   M  Sailing  Sailing Mixed 0-0.5 Ton   NaN       Giselle-6
1589  1900  Summer  FRA    Georges Louis Paul Smichon   M  Sailing  Sailing Mixed 0-0.5 Ton   NaN       Giselle-6
```