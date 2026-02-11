# Forecasting Engine

The forecasting module uses XGBoost models for multi-horizon demand prediction.

## Why XGBoost?
- Handles non-linear patterns
- Robust to irregular sales behavior
- Performs well on structured tabular time-series data

## Evaluation Metrics
- MAE (Mean Absolute Error)
- BAE (Bias Absolute Error)
- Zero Ratio
- Trend classification

Each horizon serves a different purpose:
- Weekly → operational control
- Monthly → planning & allocation
- Yearly → budgeting & strategic direction
