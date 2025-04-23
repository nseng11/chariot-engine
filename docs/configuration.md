# Configuration Management

This document describes the configuration system used in the Chariot Engine trading system.

## Overview

The system uses a hierarchical configuration system with multiple configuration files:
- Base configuration (`config.json`)
- Trade parameters (`trade_config.json`)
- Simulation parameters (`simulation_config.json`)

## Configuration Files

### Base Configuration (config.json)
```json
{
    "input_directory": "data/input",
    "output_directory": "data/output",
    "log_level": "INFO",
    "random_seed": 42
}
```

### Trade Configuration (trade_config.json)
```json
{
    "min_acceptable_value": 100.0,
    "max_cash_top_up": 500.0,
    "min_efficiency": 0.3,
    "max_value_disparity": 0.5,
    "fairness_threshold": 0.7
}
```

### Simulation Configuration (simulation_config.json)
```json
{
    "max_rounds": 100,
    "min_trades_per_round": 5,
    "generate_reports": true,
    "save_visualizations": true
}
```

## Usage

1. Copy the example configuration files from `configs/examples/`
2. Modify parameters as needed
3. Place in the `configs/` directory
4. Configuration is automatically loaded when running simulations

## Parameters

### Trade Parameters
- `min_acceptable_value`: Minimum value a user will accept in trade
- `max_cash_top_up`: Maximum cash a user will add to balance a trade
- `min_efficiency`: Minimum acceptable trade efficiency
- `max_value_disparity`: Maximum allowed difference in watch values
- `fairness_threshold`: Minimum fairness score for trade acceptance

### Simulation Parameters
- `max_rounds`: Maximum number of trading rounds
- `min_trades_per_round`: Minimum trades required per round
- `generate_reports`: Whether to generate analysis reports
- `save_visualizations`: Whether to save visualization plots

## Best Practices

1. Always use configuration files instead of hardcoding values
2. Keep sensitive information in separate configuration files
3. Version control example configurations, not actual configurations
4. Document any changes to configuration parameters 