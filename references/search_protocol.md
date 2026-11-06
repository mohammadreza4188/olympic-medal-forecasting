# Literature Search Protocol — Phase 2

## Goal
Find a documented research gap for the project: comparing macro-level and
discipline-level predictors of Summer Olympic medal counts.

## Databases (priority order)
1. Google Scholar
2. Scopus
3. Web of Science
4. Crossref (for DOI verification)
5. PubMed (only if health/gender becomes relevant)

## Time window
- Primary search: 2015–2026
- Supplementary (classic papers): 2000–2015

## Keywords — three concept blocks
Each query must AND across blocks and OR within each block.

### Block 1 — Topic
- "Olympic medal*"
- "Olympic performance"
- "Olympic success"
- "medal table"
- "medal count"

### Block 2 — Method
- "machine learning"
- "random forest"
- "XGBoost"
- "neural network"
- "gradient boosting"
- "forecasting"
- "prediction"
- "panel data"

### Block 3 — Level of analysis
- "country-level"
- "national"
- "discipline-level"
- "sport-specific"
- "comparative advantage"
- "specialization"
- "sport specialization"
- "event-level"

## Example queries
1. ("Olympic medal*" OR "medal count") AND ("machine learning" OR "random forest" OR "XGBoost") AND ("country-level" OR "national")
2. ("Olympic performance") AND ("forecasting" OR "prediction") AND ("discipline-level" OR "sport-specific")
3. ("medal table") AND ("panel data" OR "gradient boosting") AND ("comparative advantage" OR "specialization")

## Inclusion criteria
- Peer-reviewed journal article, conference paper, or working paper with a DOI
- Uses Olympic medal outcomes as dependent variable
- Published 2015–2026 (or classic methodological reference if older)
- English language

## Exclusion criteria
- Opinion pieces without data
- Studies that only predict host-country performance
- Studies with no clear validation protocol

## Screening workflow
1. Title/abstract screen → record decision in extraction_form.md
2. Full-text screen → confirm method and validation approach
3. Data extraction → one row per accepted paper

## Deliverable
- `references/literature_table.csv` (built from extraction_form.md)
- A short note `reports/phase2_gap_note.md` listing the 3 candidate novelty claims and whether each is already covered.
