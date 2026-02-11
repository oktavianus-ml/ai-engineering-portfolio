# System Architecture

The system follows a modular decision-intelligence architecture:

1. Data Layer
   - Sales history
   - Aggregated multi-horizon data

2. Forecasting Engine
   - Weekly model (operational)
   - Monthly model (planning)
   - Yearly model (strategic)

3. Scenario Simulation
   - Best-case demand
   - Worst-case demand
   - Sensitivity adjustments

4. Decision Engine
   - Reorder point calculation
   - Safety stock logic
   - Stock coverage analysis
   - Urgency classification

5. Explainability Layer
   - Natural language reasoning
   - Confidence scoring
   - Scenario interpretation

6. Interface Layer
   - Telegram bot
   - Forecast visualization charts
