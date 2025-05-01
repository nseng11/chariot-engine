# Configuration Guide

## Simulation Parameters

### User Generation
- `num_users`: Number of users to generate per period
- `min_acceptable_item_value`: Minimum value a user will accept in a trade
- `max_cash_top_up`: Maximum cash a user is willing to add to a trade
- `value_efficiency_threshold`: Minimum efficiency required for a trade to be valid

### Trade Matching
- `max_loop_size`: Maximum number of participants in a trade loop
- `min_loop_size`: Minimum number of participants in a trade loop
- `value_efficiency_threshold`: Minimum efficiency required for a trade to be valid

## Deployment Configuration

### Streamlit Cloud
- No additional configuration needed
- App runs on Streamlit's infrastructure
- Automatic HTTPS and domain management

### DigitalOcean
- Server Requirements:
  - Ubuntu 22.04 LTS
  - 1GB RAM minimum
  - 25GB SSD storage
  - Python 3.8+

- Network Configuration:
  - Open ports: 80 (HTTP), 443 (HTTPS)
  - Domain DNS pointing to droplet IP
  - SSL certificate via Let's Encrypt

- Service Configuration:
  - Streamlit runs on port 8501
  - Nginx reverse proxy
  - Systemd service management

## Environment Variables

The following environment variables can be set for additional configuration:

- `STREAMLIT_SERVER_PORT`: Port for Streamlit server (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)
- `PYTHONPATH`: Add project root to Python path

## File Structure

- `src/`: Source code directory
- `seed_catalogs_w/`: Watch catalog data
- `configs/`: Configuration files
- `requirements.txt`: Python dependencies
- `deploy.sh`: Deployment script

## Security Considerations

1. Always use HTTPS in production
2. Keep system packages updated
3. Use strong passwords for server access
4. Regularly backup simulation data
5. Monitor server logs for suspicious activity 