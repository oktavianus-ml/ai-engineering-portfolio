# Forecasting Decision Assistant (V1)

An AI-powered Inventory Decision Intelligence System that transforms multi-horizon demand forecasts into actionable inventory recommendations with scenario simulation and explainable reasoning.

---

## 🎯 Project Vision

Most forecasting systems stop at predicting future demand.

Forecasting Decision Assistant (V1) goes further by translating predictions into operational decisions such as:

- Reorder or Delay
- Urgency level classification
- Stock coverage evaluation
- Scenario-based robustness analysis
- Confidence scoring
- Natural language explanations

This system bridges the gap between predictive modeling and real-world inventory decision-making.

---

## 🧠 Core Capabilities

### 1. Multi-Horizon Forecasting
- Weekly → Operational control (reorder & stock monitoring)
- Monthly → Planning & allocation
- Yearly → Budgeting & strategic direction

Models are trained using XGBoost and evaluated with:
- MAE (Mean Absolute Error)
- Bias (BAE)
- Zero-demand ratio
- Trend classification

---

### 2. Decision Intelligence Engine

The system converts forecasts into structured decisions using:

- Reorder point calculation
- Safety stock estimation
- Stock coverage days
- Urgency classification (Low / Medium / High)
- Confidence scoring

Output example:
- Action: DELAY
- Urgency: LOW
- Confidence: 0.6

---

### 3. Scenario & What-If Analysis

The system evaluates decision robustness under demand volatility:

- Worst-case demand simulation
- Best-case demand simulation
- Sensitivity analysis
- Decision stability validation

This ensures recommendations remain consistent even when demand fluctuates.

---

### 4. Explainability Layer

Each decision includes natural language reasoning, for example:

Despite demand fluctuations in best and worst-case scenarios, the recommendation remains DELAY. Current stock coverage exceeds safety thresholds, indicating low urgency.

This improves transparency and stakeholder trust.

---

### 5. User Interfaces

- 📱 Telegram Bot (Conversational interface)
- 📊 Forecast visualizations (Weekly / Monthly / Yearly)
- Scenario summary reports

The interface allows non-technical users to consume decision intelligence easily.

---

## 🏗 System Architecture

The system follows a modular architecture:

Sales Data  
→ Forecast Engine  
→ Scenario Simulation  
→ Decision Engine  
→ Explanation Layer  
→ User Interface  

The architecture separates:

- Domain logic
- Forecasting models
- Decision services
- Infrastructure integrations

This ensures maintainability and extensibility.

---

## 📂 Repository Structure

This repository contains two layers:

### 🧠 Production Code
Located in:
- `/app`
- `/planning`
- `/scripts`
- `/streamlit_app`
- `/telegram_bot`

These folders contain the full engineering implementation.

### 🎯 Portfolio Documentation
Located in:
- `/showcase`

If you are reviewing system design and business framing, start there.  
If you are reviewing implementation quality, explore `/app`.

---

## 🚀 Business Value

- Reduces reactive inventory decisions
- Improves reorder timing
- Enhances planning confidence
- Evaluates decision robustness under uncertainty
- Bridges forecasting and operational execution

---

## ⚠️ Current Limitations (V1)

- Assumes stable supplier lead times
- Does not yet integrate real-time ERP inventory feeds
- Does not model supplier reliability uncertainty

---

## 🔮 Future Improvements

- Lead-time variability modeling
- Reinforcement learning-based inventory policy optimization
- ERP Odoo integration
- Automated threshold calibration
- Multi-product portfolio optimization

---

## 🏁 Why This Project Matters

Accurate forecasts do not automatically produce good decisions.

Actionable, explainable, and robust decision intelligence does.

Forecasting Decision Assistant (V1) demonstrates how predictive modeling can evolve into a structured decision-support system.
