# Chariot Engine

A peer-to-peer watch trading platform simulation engine that matches users for potential trades based on their watch preferences and value constraints.

## Features

- User generation with realistic watch preferences
- Trade loop matching algorithm
- Multi-period simulation
- Interactive web interface
- Detailed analytics and visualizations

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chariot-engine.git
   cd chariot-engine
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit app locally:
   ```bash
   streamlit run src/web/streamlit_app.py
   ```

## Project Structure

```
chariot-engine/
├── src/
│   ├── web/
│   │   └── streamlit_app.py
│   ├── generate_users.py
│   ├── loop_matching.py
│   ├── simulate_trades.py
│   └── run_periodic_simulation.py
├── seed_catalogs_w/
│   └── watch_catalog.csv
├── configs/
│   ├── temp_config.json
│   ├── watch_catalog.json
│   └── config_test.json
├── docs/
│   └── configuration.md
├── requirements.txt
└── README.md
```

## Configuration

See [configuration.md](docs/configuration.md) for detailed configuration options.

## License

MIT License