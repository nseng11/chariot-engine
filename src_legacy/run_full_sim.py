import os
import pandas as pd
import json
import datetime
import subprocess
from flask import Flask, render_template, redirect, url_for, request, send_from_directory

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'simulations')
)

def run_script(script_name):
    print(f"\n[RUN] {script_name}...")
    result = subprocess.run(["python", script_name], capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0:
        print(f"[OK] {script_name} executed successfully")
    else:
        print(f"[ERROR] Failed to run {script_name}:")
        print(result.stderr)

def run_full_simulation():
    base_dir = os.path.dirname(__file__)
    simulations_dir = os.path.join(base_dir, "..", "simulations")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(simulations_dir, f"run_{timestamp}")
    os.makedirs(run_folder, exist_ok=True)

    # Step 1: Run matching scripts first
    run_script("generate_sample_users.py")
    run_script("loop_export.py")
    run_script("simulate_round.py")

    # Step 2: Move intermediate files to run folder
    for fname in ["sample_users.csv", "matching_results.csv", "executed_loops.csv", "rejected_loops.csv", "all_matched_loops.csv"]:
        src = os.path.join(simulations_dir, fname)
        dst = os.path.join(run_folder, fname)
        if os.path.exists(src):
            try:
                os.replace(src, dst)
            except Exception as e:
                print(f"[WARN] Could not move {fname}: {e}")

    # Step 3: Run loop_visuals.py — it will auto-detect the latest run folder
    run_script("loop_visuals.py")

    # Step 4: Load CSVs from the run folder
    executed_path = os.path.join(run_folder, "executed_loops.csv")
    rejected_path = os.path.join(run_folder, "rejected_loops.csv")
    matched_path = os.path.join(run_folder, "all_matched_loops.csv")
    user_path = os.path.join(run_folder, "sample_users.csv")
    matching_path = os.path.join(run_folder, "matching_results.csv")

    executed_df = pd.read_csv(executed_path) if os.path.exists(executed_path) else pd.DataFrame()
    rejected_df = pd.read_csv(rejected_path) if os.path.exists(rejected_path) else pd.DataFrame()
    matched_df = pd.read_csv(matched_path) if os.path.exists(matched_path) else pd.DataFrame()
    user_df = pd.read_csv(user_path)
    matching_df = pd.read_csv(matching_path)

    # Step 5: Compute stats
    user_status = {uid: 'available' for uid in user_df['user_id']}
    def extract_users(row):
        try:
            return json.loads(row['users'].replace("'", '"'))
        except:
            return []

    for _, row in executed_df.iterrows():
        for u in extract_users(row):
            user_status[u] = 'matched'

    for _, row in rejected_df.iterrows():
        for u in extract_users(row):
            if user_status.get(u) != 'matched':
                user_status[u] = 'declined'

    available = sum(1 for v in user_status.values() if v == 'available')
    declined = sum(1 for v in user_status.values() if v == 'declined')

    summary = {
        'executed': len(executed_df),
        'rejected': len(rejected_df),
        'matched_loops': len(matched_df),
        'queue': available + declined,
        'available': available,
        'declined': declined,
        'total_loops': len(matching_df),
        'percent_2way': round(100 * len(matching_df[matching_df['loop_type'] == '2-way']) / len(matching_df), 2) if len(matching_df) else 0,
        'percent_3way': round(100 * len(matching_df[matching_df['loop_type'] == '3-way']) / len(matching_df), 2) if len(matching_df) else 0,
        'avg_users_per_loop': round(matching_df[['user_1', 'user_2', 'user_3']].notnull().sum(axis=1).mean(), 2) if len(matching_df) else 0,
        'plots': []
    }

    # Step 6: Check for plots in this run folder
    run_plot_dir = os.path.join(run_folder, "plots")
    if os.path.exists(run_plot_dir):
        summary['plots'] = sorted(os.listdir(run_plot_dir))

    # Step 7: Write sim_stats.json with updated plots
    with open(os.path.join(run_folder, "sim_stats.json"), "w", encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Outputs saved in: {run_folder}")
    return run_folder

def get_all_run_folders():
    base_dir = os.path.dirname(__file__)
    simulations_dir = os.path.join(base_dir, "..", "simulations")
    return sorted([f for f in os.listdir(simulations_dir) if f.startswith("run_")], reverse=True)

@app.route('/')
def index():
    run_folders = get_all_run_folders()
    selected_run = run_folders[0] if run_folders else None
    stats, plots = {}, []

    if selected_run:
        run_dir = os.path.join(os.path.dirname(__file__), "..", "simulations", selected_run)
        stats_path = os.path.join(run_dir, "sim_stats.json")
        if os.path.exists(stats_path):
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        plots = stats.get("plots", [])

    return render_template("index.html", stats=stats, runs=run_folders, selected=selected_run, plots=plots)

@app.route('/run-again')
def run_again():
    run_full_simulation()
    return redirect(url_for('index'))

@app.route('/run/<run_id>')
def view_run(run_id):
    run_dir = os.path.join(os.path.dirname(__file__), "..", "simulations", run_id)
    stats_path = os.path.join(run_dir, "sim_stats.json")
    stats, plots = {}, []
    if os.path.exists(stats_path):
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        plots = stats.get("plots", [])
    run_folders = get_all_run_folders()
    return render_template("index.html", stats=stats, runs=run_folders, selected=run_id, plots=plots)

@app.route('/plots/<run_id>/<filename>')
def get_plot(run_id, filename):
    plot_dir = os.path.join(os.path.dirname(__file__), "..", "simulations", run_id, "plots")
    return send_from_directory(plot_dir, filename)

if __name__ == "__main__":
    app.run(debug=True)