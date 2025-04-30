# Chariot Engine

A peer-to-peer watch trading platform simulation engine that matches users for potential trades based on their watch preferences and value constraints.

## Features

- User generation with realistic watch preferences
- Trade loop matching algorithm
- Multi-period simulation
- Interactive web interface
- Detailed analytics and visualizations

## Deployment Options

### Option 1: Streamlit Cloud (Recommended for Development)
The app is currently hosted on Streamlit Cloud at [chariotengine.streamlit.app](https://chariotengine.streamlit.app).

### Option 2: DigitalOcean (Production)
For production deployment, the app can be hosted on a DigitalOcean droplet:

1. Set up a DigitalOcean droplet (Ubuntu 22.04 recommended)
2. Configure your domain's DNS to point to the droplet
3. Copy the application files to the server
4. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
5. Set up SSL with Let's Encrypt:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

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
│   └── config.md
├── requirements.txt
├── deploy.sh
└── README.md
```

## Configuration

See [config.md](configs/config.md) for detailed configuration options.

## License

MIT License