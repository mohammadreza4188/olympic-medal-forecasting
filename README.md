# Olympic Medal Forecasting: Data Pipeline & Decomposition Strategies

## Overview
This repository contains the data processing pipelines, engineered features, and machine learning evaluation scripts for predicting Summer Olympic medal counts. 

The project evaluates **four decomposition strategies** to determine if increasing model complexity improves predictive accuracy over a simple naive baseline (predicting a country's previous medal count).

## Repository Structure
*   `src/audit/`: Scripts for initial data quality assessment and gap detection (e.g., missing 2020/2024 team events).
*   `src/build/`: Scripts for building the country-level panel, World Bank integration, Balassa RCA calculation, and per-sport datasets.
*   `src/models/`: Machine learning evaluation scripts (Forward-chaining validation).
*   `data/processed/`: Final, model-ready datasets (CSV).
*   `references/`: Pre-registered protocols and methodology notes.

## Data Sources
*   **Olympic Data:** Athlete and event-level data (1896-2024) sourced from the `ismayc/olympic-moderndive-data` repository.
*   **Socioeconomic Data:** GDP and Population data from the World Bank API.

## Engineered Features
*   **Balassa Revealed Comparative Advantage (RCA):** Calculated at the country-sport level to quantify specialization.
*   **Gender-Disaggregated Metrics:** Female participation shares and lagged female medal shares.
*   **Per-Sport Aggregation:** Dataset split into 31 distinct sports to test bottom-up forecasting.

## Key Findings (Null Results)
1.  **The Naive Baseline is unbeatable:** No machine learning model (XGBoost, Random Forest, Poisson, Hurdle) outperformed the simple benchmark of repeating the previous edition's medal count on RMSE.
2.  **Metric Inversion:** Complex models frequently beat the baseline on log-RMSE (which weights small countries equally) while losing on standard RMSE (dominated by large countries).
3.  **Aggregation Bias:** In extreme zero-inflated targets (like per-sport medals), summing sub-model predictions compounds under-prediction errors.

## Reproducibility
The pipeline is fully reproducible. To recreate the processed datasets:
1. Install requirements: `pip install -r requirements.txt`
2. Place raw data in `data/raw/` (see Data Sources).
3. Run build scripts in order: `python src/build/build_macro.py` ... etc.

## Author
**Mohammad Reza Gholami**  
MSc Student in Computer Science (AI & Soft Computing)  
Shahid Bahonar University of Kerman  
[LinkedIn](https://www.linkedin.com/in/mohammadrezagholami4188)
