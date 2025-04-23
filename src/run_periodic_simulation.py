import os
import json
import datetime
import pandas as pd

from generate_users import load_watch_catalog, generate_users_for_period
from loop_matching import run_loop_matching
from simulate_trades import simulate_trade_loops
from loop_visuals import analyze_watch_frequencies

def run_multi_period_simulation(config_path="configs/config_run_periodic.json"):
    with open(config_path, "r") as f:
        config = json.load(f)

    initial_users = config["initial_users"]
    growth_rate = config["growth_rate"]
    num_periods = config["num_periods"]
    catalog_path = config["catalog_path"]

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join("simulations", f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    catalog = load_watch_catalog(catalog_path)

    carried_users_df = pd.DataFrame()
    user_trade_log = []
    user_history_tracker = {}
    executed_loops_all = []
    rejected_loops_all = []
    total_users = 0
    total_2way = 0
    total_3way = 0
    total_users_matched = set()

    trade_counter = [0]  # Ensures trade_id is globally unique across periods

    for period in range(num_periods):
        print(f"\n📆 Starting Period {period + 1}...")

        period_dir = os.path.join(run_dir, f"period_{period+1}")
        os.makedirs(period_dir, exist_ok=True)

        new_user_count = int(initial_users * ((1 + growth_rate) ** period))
        new_users_df = generate_users_for_period(
            num_users=new_user_count,
            catalog=catalog,
            period=period + 1
        )
        total_users += len(new_users_df)

        period_users_df = pd.concat([carried_users_df, new_users_df], ignore_index=True)
        period_users_path = os.path.join(period_dir, f"period_{period+1}_users.csv")
        period_users_df.to_csv(period_users_path, index=False)

        match_results_path = os.path.join(period_dir, f"period_{period+1}_matching.csv")
        run_loop_matching(period_users_path, match_results_path)

        sim_result = simulate_trade_loops(
            user_csv_path=period_users_path,
            loop_csv_path=match_results_path,
            output_dir=period_dir,
            return_status=True,
            user_trade_log=user_trade_log,
            user_history_tracker=user_history_tracker,
            catalog=catalog,
            period=period + 1,
            timestamp=timestamp,
            trade_counter=trade_counter
        )

        exec_path = os.path.join(period_dir, "executed_loops.csv")
        rejected_path = os.path.join(period_dir, "rejected_loops.csv")
        all_path = os.path.join(period_dir, "all_matched_loops.csv")
        plot_dir = os.path.join(period_dir, "plots")

        if os.path.exists(exec_path):
            try:
                exec_df = pd.read_csv(exec_path)
                if not exec_df.empty:
                    executed_loops_all.append(exec_df)
                    if "relative_fairness_score" in exec_df.columns:
                        analyze_watch_frequencies(exec_df, "Executed Trade", "executed_trades", plot_dir)
            except pd.errors.EmptyDataError:
                print(f"⚠️ Skipped visualization — {exec_path} is empty.")

        if os.path.exists(rejected_path):
            try:
                rejected_df = pd.read_csv(rejected_path)
                if not rejected_df.empty:
                    rejected_loops_all.append(rejected_df)
            except pd.errors.EmptyDataError:
                print(f"⚠️ Skipped rejected loop aggregation — {rejected_path} is empty.")

        if os.path.exists(all_path):
            try:
                all_df = pd.read_csv(all_path)
                if not all_df.empty and "relative_fairness_score" in all_df.columns:
                    analyze_watch_frequencies(all_df, "Matched Loop", "matched_loops", plot_dir)
            except pd.errors.EmptyDataError:
                print(f"⚠️ Skipped visualization — {all_path} is empty.")

        user_status = sim_result["user_status"]
        status_df = pd.DataFrame([
            row for row in period_users_df.to_dict(orient="records")
            if user_status.get(row["user_id"], "") in ["available", "declined"]
        ])
        carried_users_df = status_df

        exec_loops_path = os.path.join(period_dir, "executed_loops.csv")
        if os.path.exists(exec_loops_path):
            try:
                exec_loops_df = pd.read_csv(exec_loops_path)
                if not exec_loops_df.empty:
                    count_2way = (exec_loops_df["loop_type"] == "2-way").sum()
                    count_3way = (exec_loops_df["loop_type"] == "3-way").sum()
                    queue_size = len(status_df)

                    total_2way += count_2way
                    total_3way += count_3way

                    for user_list in exec_loops_df.get("users", []):
                        try:
                            user_ids = json.loads(user_list.replace("'", '"'))
                            total_users_matched.update(user_ids)
                        except:
                            continue

                    print(f"📊 Period {period + 1} Summary:")
                    print(f"  - Executed 2-way trades: {count_2way}")
                    print(f"  - Executed 3-way trades: {count_3way}")
                    print(f"  - Users carried to next period: {queue_size}")
            except pd.errors.EmptyDataError:
                print(f"⚠️ Skipped summary — {exec_loops_path} is empty.")

    pd.DataFrame([{
        "total_users_generated": total_users,
        "users_accepted_trade": len(total_users_matched),
        "total_2way_trades": total_2way,
        "total_3way_trades": total_3way,
        "total_trades_executed": total_2way + total_3way,
        "percent_users_traded": round(100 * len(total_users_matched) / total_users, 2) if total_users else 0,
        "avg_users_per_trade": round((2 * total_2way + 3 * total_3way) / (total_2way + total_3way), 2) if (total_2way + total_3way) else 0,
        "num_periods": num_periods,
        "initial_users": initial_users,
        "growth_rate": growth_rate
    }]).to_csv(os.path.join(run_dir, "aggregate_summary.csv"), index=False)

    if executed_loops_all:
        full_executed_df = pd.concat(executed_loops_all)
        full_executed_df.to_csv(os.path.join(run_dir, "all_executed_loops.csv"), index=False)

    if rejected_loops_all:
        full_rejected_df = pd.concat(rejected_loops_all)
        full_rejected_df.to_csv(os.path.join(run_dir, "all_rejected_loops.csv"), index=False)

    user_summary_df = pd.DataFrame.from_dict(user_history_tracker, orient="index")
    user_summary_df.index.name = "user_id"
    user_summary_df.reset_index(inplace=True)
    user_summary_df.to_csv(os.path.join(run_dir, "user_tracking_summary.csv"), index=False)
    pd.DataFrame(user_trade_log).to_csv(os.path.join(run_dir, "user_trade_log.csv"), index=False)

    print(f"\n🏁 Simulation complete across {num_periods} periods")
    print(f"📁 All outputs saved to: {run_dir}")
    print(f"\n📈 Aggregate Summary:")
    print(f"  - Total users generated: {total_users}")
    print(f"  - Users who accepted a trade: {len(total_users_matched)}")
    print(f"  - Total 2-way trades executed: {total_2way}")
    print(f"  - Total 3-way trades executed: {total_3way}")

if __name__ == "__main__":
    run_multi_period_simulation()