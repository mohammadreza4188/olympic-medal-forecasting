# World Bank Data Protocol — Phase 3

## Purpose
Attach country-level socioeconomic indicators to the macro panel
(`data/processed/panel_summer_macro_v1.csv`) with a defensible, reproducible rule.

## Indicators (frozen for this project)

| alias         | World Bank code       | unit                        | rationale |
|---------------|------------------------|-----------------------------|-----------|
| gdp_const     | NY.GDP.MKTP.KD         | constant 2015 US$           | Level of economic capacity, comparable over time |
| gdp_pcap_const| NY.GDP.PCAP.KD         | constant 2015 US$ per person| Economic development controlling for size |
| population    | SP.POP.TOTL            | total persons               | Talent pool size |

**Why constant 2015 US$:** cross-edition comparison must not be contaminated by inflation or exchange-rate movement. Current-price indicators are recorded but not used as the primary spec.

## Reference year rule
For an Olympic edition with official year Y, compute both:
- `*_avg4y` — arithmetic mean of indicator values for years Y-4, Y-3, Y-2, Y-1
- `*_prev1y` — indicator value at year Y-1

`*_avg4y` is the primary specification (smooths cyclical shocks, matches Schlembach et al. 2022). `*_prev1y` is included as an alternative specification for sensitivity.

**Missing-year handling:** if a year within the 4-year window is missing, the average uses the available years, requiring at least 2 of 4 to be present. If fewer than 2 are present, the average is NaN.

**COVID-era editions:** the 2020 Tokyo Games were held in 2021 but retain the official label "2020". All reference years use the official year: for 2020, window = 2016–2019; for 2024, window = 2020–2023.

## NOC to ISO3 mapping
The World Bank publishes data under ISO 3166-1 alpha-3 codes. Olympic NOCs use IOC codes.
For most NOCs the code is identical to ISO3 (USA, GBR, FRA, JPN, …).
For a fixed list of mismatches an explicit mapping is applied (see `NOC_ISO3_MAP` in `fetch_worldbank.py`).

## Historical NOC policy
The following NOCs are **excluded from the World Bank merge** (their panel rows are retained with NaN WB features):Reason: these entities have no separate World Bank series. Mapping them to a successor state would create false attribution. They remain usable as historical observations for non-economic features (athletes, sports, events, medals).

Two historical NOCs are mapped to Germany, because the World Bank "DEU" series before 1990 is West Germany:
- `FRG` → `DEU`
- `EUA` (Unified Germany 1956–1964) → `DEU`

## Output
- `data/raw/worldbank/{indicator}.csv` — raw per-indicator extract (iso3, year, value)
- `data/processed/panel_summer_macro_v2.csv` — v1 panel plus six new columns:
  `gdp_const_avg4y`, `gdp_pcap_const_avg4y`, `population_avg4y`,
  `gdp_const_prev1y`, `gdp_pcap_const_prev1y`, `population_prev1y`

## Constraints
- No imputation of missing economic values. NaN is preserved.
- No retroactive edits to the protocol. Any change is a new version of this document.
- Full missing-rate summary is written to `reports/phase3_worldbank_merge.md`.

## Known limitations
- World Bank data for 2024 may be incomplete for some countries at the time of extraction; the `*_avg4y` column is robust to this because the window ends at 2023.
- Countries with missing WB data in the 1960s–1970s will have NaN economic features for early editions. This is expected and is handled at model time (drop or impute-with-flag).
