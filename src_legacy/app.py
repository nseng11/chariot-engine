from flask import Flask, render_template
from run_simulation import run_simulation
import os
import pandas as pd

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)

@app.route('/')
def index():
    # Determine latest simulation folder
    base_dir = os.path.dirname(__file__)
    simulations_dir = os.path.join(base_dir, '..', 'simulations')
    latest_txt_path = os.path.join(simulations_dir, 'latest.txt')

    if not os.path.exists(latest_txt_path):
        return "No simulation results found. Please run a full simulation first."

    with open(latest_txt_path, 'r') as f:
        latest_run_dir = f.read().strip()

    # Inject file path override into run_simulation
    os.environ['MATCHING_RESULTS_PATH'] = os.path.join(latest_run_dir, 'matching_results.csv')
    os.environ['EXECUTED_LOOPS_PATH'] = os.path.join(latest_run_dir, 'executed_loops.csv')
    os.environ['REJECTED_LOOPS_PATH'] = os.path.join(latest_run_dir, 'rejected_loops.csv')

    executed_df, rejected_df, stats = run_simulation()

    # Override stats if executed_df was already loaded
    if not executed_df.empty:
        matched_users = set()
        for col in ['user_1', 'user_2', 'user_3']:
            if col in executed_df:
                matched_users.update(executed_df[col].dropna().astype(str))

        declined_users = set()
        if not rejected_df.empty:
            for col in ['user_1', 'user_2', 'user_3']:
                if col in rejected_df:
                    declined_users.update(rejected_df[col].dropna().astype(str))

        queue = matched_users.union(declined_users)

        stats['executed'] = len(executed_df)
        stats['rejected'] = len(rejected_df)
        stats['queue'] = len(queue)
        stats['available'] = len(queue - declined_users)
        stats['declined'] = len(declined_users)

    return render_template('index.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True)