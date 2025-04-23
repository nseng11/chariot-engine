# Chariot Engine

Chariot Engine is a sophisticated watch trading simulation system that implements multi-party trading loops with fairness calculations and trade validation.

## Project Structure

```
chariot_engine/
├── src/                      # Main Python implementation
│   ├── loop_matching.py      # Core trade matching algorithms
│   ├── simulate_trades.py    # Trade simulation engine
│   ├── trade_analytics.py    # Analytics and reporting
│   ├── trade_validation.py   # Trade validation rules
│   ├── config.py            # Configuration management
│   ├── loop_visuals.py      # Visualization utilities
│   └── generate_users.py    # User data generation
├── rust_components/         # High-performance Rust implementations
├── configs/                 # Configuration files
├── simulations/            # Simulation outputs
├── templates/              # Template files
└── static/                 # Static resources
```

## Features

- Multi-party trade matching (2-way and 3-way trades)
- Fairness-based trade validation
- Configurable simulation parameters
- Trade analytics and visualization
- High-performance Rust components (optional)

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your environment:
- Copy `configs/config.example.json` to `configs/config.json`
- Adjust parameters as needed

3. Run a simulation:
```bash
python src/run_periodic_simulation.py
```

## Documentation

- See `docs/` for detailed documentation
- Each module has inline documentation
- Example configurations in `configs/examples/`

## Development

- Python 3.8+ required
- Rust 1.54+ (optional, for rust_components)
- See CONTRIBUTING.md for development guidelines