# Extraction Form — one row per accepted paper

Copy the template below into `references/literature_table.csv`
(or a spreadsheet that exports to CSV) and fill it in per paper.

| field              | type    | notes |
|--------------------|---------|-------|
| paper_id           | text    | short slug, e.g. `bernard2004` |
| authors            | text    | first author et al. |
| year               | int     | publication year |
| title              | text    | full title |
| venue              | text    | journal or conference |
| doi                | text    | DOI, verified via Crossref |
| data_source        | text    | Olympics edition, years covered, NOC count |
| dependent_var      | text    | e.g. `total medals`, `gold only`, `per-capita` |
| unit_of_analysis   | text    | country / country-sport / athlete / event |
| predictors         | text    | list, semicolon-separated |
| method             | text    | e.g. `Poisson`, `XGBoost`, `OLS` |
| validation         | text    | random split / time split / cross-val / none |
| key_result         | text    | one sentence |
| limitation         | text    | one sentence |
| gap_notes          | text    | what this paper does NOT do (relevant to our project) |

## Quick copy-paste header

