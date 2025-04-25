# Configuration Management

This document describes the configuration system used in the Chariot Engine trading system.

## Overview

The system uses a modular configuration system with several key components:
- Simulation parameters (`temp_config.json`)
- Watch catalog (`seed_catalogs_w/watch_catalog.csv`)
- Trade acceptance thresholds (built into the code)

## Configuration Files

### Simulation Configuration (temp_config.json)
```json
{
    "initial_users": 15,
    "growth_rate": 0.15,
    "num_periods": 12,
    "catalog_path": "seed_catalogs_w/watch_catalog.csv"
}
```

### Watch Catalog (watch_catalog.csv)
A CSV file containing watch models and their values, ranging from $500 to $25,000.

## Trade Acceptance Parameters

### Value Efficiency Thresholds
```python
efficiency_thresholds = {
    "penalty": 0.8,      # Strong penalty below this
    "Q1": 0.8338,       # Baseline
    "Q2": 0.86,         # Good
    "Q3": 0.898         # Excellent
}

efficiency_modifiers = {
    "below_min": -0.4,  # Below 0.8
    "Q1_to_Q2": 0.15,   # 0.8338 to 0.86
    "Q2_to_Q3": 0.25,   # 0.86 to 0.898
    "above_Q3": 0.35    # Above 0.898
}
```

### Fairness Score Thresholds
```python
fairness_thresholds = {
    "Q1": 0.7469,      # Baseline
    "Q2": 0.7888,      # Minimal boost
    "Q3": 0.8509,      # Moderate boost
    "excellent": 0.9    # Maximum boost
}

fairness_modifiers = {
    "below_Q1": 0.0,   # Below 0.7469
    "Q1_to_Q2": 0.03,  # 0.7469 to 0.7888
    "Q2_to_Q3": 0.08,  # 0.7888 to 0.8509
    "Q3_to_0.9": 0.12, # 0.8509 to 0.9
    "above_0.9": 0.15  # Above 0.9
}
```

## Usage

1. Configure simulation parameters in the Streamlit interface:
   - Initial Users (5-50)
   - Growth Rate (0-100%)
   - Number of Periods (1-20)

2. The system will:
   - Create a temporary config file
   - Run the simulation
   - Generate visualizations and analytics
   - Save results in `simulations/run_TIMESTAMP/`

## Output Structure

### Simulation Output Directory
```
simulations/run_TIMESTAMP/
├── period_summary.csv       # Period-by-period metrics
├── executed_loops.csv       # Successfully executed trades
└── rejected_loops.csv       # Rejected trade opportunities
```

### Key Metrics Tracked
- Trade counts (2-way and 3-way)
- User pool statistics
- Match success rates
- Value efficiency metrics
- Fairness scores

## Best Practices

1. Use the Streamlit interface for parameter adjustments
2. Monitor trade efficiency and fairness distributions
3. Analyze both executed and rejected trades
4. Track match rates across different trade types
5. Consider the balance between efficiency and fairness scores 