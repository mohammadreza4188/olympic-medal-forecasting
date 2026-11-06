# Research Protocol — Phase 5 (v1.1)

**Supersedes:** v1.0 (2026-10-18)
**Status:** Frozen. Any further change is v1.2.

## Change log vs v1.0
- D_base expanded from 8 to 9 features (added `has_discipline_data`).
- `host` feature now built in `build_model_dataset.py` (was inline in train).
- M0/M1/M2/M3 hierarchy clarified. Because M1 and M2 both include
  `lag_mt_total` and `lag_mt_gold`, two sensitivity variants are added:
  `M1_noLag` (macro without lag) and `M2_noLag` (macro+discipline without lag).
  M0 remains "predict previous edition's medal count".
- Hyperparameter tuning is **removed**. All model families use fixed,
  documented hyperparameters for reproducibility. Justification is in each
  model card. No inner CV search is performed.
- H1 verdict logic updated to three sub-conditions (mean improvement, direction
  stability across editions, breadth across model families). All three must pass.
- Winsorize at 99th percentile remains the primary spec. A 95th-percentile
  sensitivity is documented as future work in the model card.
- Discipline NaN handling: primary spec zero-fills (justified: no medals in
  window = no revealed specialization). A `has_discipline_data` flag is
  included so models can down-weight filled rows. A dropna sensitivity is
  documented as future work.

## Unchanged from v1.0
- Research question, hypotheses H1–H4 (H4 remains exploratory, not tested in
  Phase 6), sample definitions, dependent variable, macro block, primary
  validation scheme (forward-chaining on 2012, 2016, 2020, 2024), metrics,
  and reporting rules are identical to v1.0. See
  `references/phase5_research_protocol.md` for those sections.

## Seeds and reproducibility
- Global seed 42 (`random`, `numpy`).
- Per-model `random_state=42` (RF, XGB, logistic).
- Every Phase 6 run produces identical metrics on identical input.

## Sensitivity analyses deferred to a follow-up report
- Winsorize at 95th percentile.
- Drop-NaN discipline features.
- Secondary sample (1960–2024).
- Alternate window (cum instead of last4).
- Alternate reference year (prev1y instead of avg4y).

These will be run only if the primary analysis produces a non-trivial
M2-vs-M1 gap worth defending.
