import os
import pandas as pd
import json

def run_simulation():
    # Allow environment override from Flask app
    executed_path = os.environ.get("EXECUTED_LOOPS_PATH")
    rejected_path = os.environ.get("REJECTED_LOOPS_PATH")
    stats_path = os.environ.get("SIM_STATS_PATH")

    executed_df = pd.read_csv(executed_path) if executed_path and os.path.exists(executed_path) else pd.DataFrame()
    rejected_df = pd.read_csv(rejected_path) if rejected_path and os.path.exists(rejected_path) else pd.DataFrame()

    # Load additional stats if available
    stats = {}
    if stats_path and os.path.exists(stats_path):
        with open(stats_path, 'r') as f:
            stats = json.load(f)

    summary = {
        'executed': len(executed_df),
        'rejected': len(rejected_df),
        'queue': stats.get('users_still_in_queue', 0),
        'available': stats.get('available_but_unmatched', 0),
        'declined': stats.get('declined_in_queue', 0),
        'initial_loops': stats.get('initial_loops', 0),
        'percent_2way': stats.get('percent_2way', 0),
        'percent_3way': stats.get('percent_3way', 0),
        'avg_users_per_loop': stats.get('avg_users_per_loop', 0)
    }

    return executed_df, rejected_df, summary