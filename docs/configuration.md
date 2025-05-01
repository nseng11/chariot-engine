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

## Metric Calculations

### Value Efficiency Example
Value efficiency measures how much of the total value movement is watch value versus cash movement.

```python
value_efficiency = total_watch_value / (total_watch_value + total_cash_flow)
```

Example for a 3-way trade:
```python
# Watch Values
user1_watch = $10,000
user2_watch = $12,000
user3_watch = $11,000

# Trade Flow
user1 -> user2  (needs to add $2,000)
user2 -> user3  (receives $1,000)
user3 -> user1  (receives $1,000)

# Calculation
total_watch_value = $10,000 + $12,000 + $11,000 = $33,000
total_cash_flow = |$2,000| + |$1,000| + |$1,000| = $4,000

value_efficiency = $33,000 / ($33,000 + $4,000)
                = $33,000 / $37,000
                ≈ 0.892 (89.2% efficient)
```

### Interpretation

Value Efficiency (0.892):
- Above Q2 (0.86) but below Q3 (0.898)
- Gets a +0.25 efficiency modifier
- Indicates a good trade with relatively low cash movement

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

## Best Practices

1. Use the Streamlit interface for parameter adjustments
2. Monitor trade efficiency distributions
3. Analyze both executed and rejected trades
4. Track match rates across different trade types
5. Consider the trade efficiency scores 