import os
import json
import pandas as pd
import random
from collections import deque

def get_trade_weights(fairness_score, value_efficiency, max_value_diff, avg_watch_value):
    """Calculate acceptance weights based on multiple factors"""
    base_weight = 0.5

    # Adjust for fairness (existing logic)
    fairness_modifier = 0.3 if fairness_score <= 0.25 else \
                       0.2 if fairness_score <= 0.5 else \
                       0.1 if fairness_score <= 0.75 else \
                       0.0

    # Adjust for value efficiency
    efficiency_modifier = 0.2 if value_efficiency < 0.5 else \
                         0.1 if value_efficiency < 0.7 else \
                         0.0

    # Adjust for value disparity relative to average value
    disparity_modifier = 0.2 if max_value_diff > avg_watch_value else \
                        0.1 if max_value_diff > avg_watch_value * 0.5 else \
                        0.0

    accept_weight = base_weight + fairness_modifier + efficiency_modifier + disparity_modifier
    return [1 - accept_weight, accept_weight]  # [accept, decline]

def simulate_trade_loops(user_csv_path, loop_csv_path, output_dir, return_status=False,
                          user_trade_log=None, user_history_tracker=None, catalog=None,
                          period=None, timestamp=None, trade_counter=[0]):

    users_df = pd.read_csv(user_csv_path)
    loops_df = pd.read_csv(loop_csv_path)

    user_status = {uid: 'available' for uid in users_df['user_id']}
    user_queue = deque(users_df['user_id'].tolist())

    executed_loops = []
    rejected_loops = []
    matched_loops = []
    round_counter = 1

    while True:
        available = [u for u in user_status if user_status[u] == 'available']
        if not available:
            print("\n🚩 No users available for further matching.")
            break

        current_loops = loops_df.copy()
        current_loops['valid'] = current_loops.apply(
            lambda row: all(user_status.get(row.get(f"user_{i+1}"), 'matched') == 'available'
                            for i in range(3) if pd.notna(row.get(f"user_{i+1}"))),
            axis=1
        )

        filtered_loops = current_loops[current_loops['valid']].drop(columns='valid')
        if filtered_loops.empty:
            print("\n🚩 No valid loops left to simulate.")
            break

        fairness_values = filtered_loops['relative_fairness_score'].dropna()
        if not fairness_values.empty:
            q1, q2, q3 = fairness_values.quantile([0.25, 0.5, 0.75])
        else:
            q1 = q2 = q3 = 0.0

        round_exec, round_reject = 0, 0

        for _, row in filtered_loops.iterrows():
            loop_users = [row.get(f"user_{i+1}") for i in range(3) if pd.notna(row.get(f"user_{i+1}"))]
            if not all(user_status[u] == 'available' for u in loop_users):
                continue

            fairness = row.get('relative_fairness_score', None)

            if fairness is None or pd.isna(fairness):
                weights = [0.5, 0.5]
            elif fairness <= q1:
                weights = [0.8, 0.2]
            elif fairness <= q2:
                weights = [0.6, 0.4]
            elif fairness <= q3:
                weights = [0.4, 0.6]
            else:
                weights = [0.2, 0.8]

            decisions = {
                u: random.choices(['accept', 'decline'], weights=weights)[0]
                for u in loop_users
            }

            trade_id = f"T{trade_counter[0]+1:05d}"
            loop_record = row.to_dict()
            loop_record['users'] = json.dumps(loop_users)
            loop_record['trade_id'] = trade_id
            loop_record['period_executed'] = period
            loop_record.pop('loop_id', None)

            for idx, u in enumerate(loop_users):
                if user_history_tracker is not None:
                    user_history_tracker.setdefault(u, {
                        "offered": 0, "accepted": False,
                        "first_seen_period": period, "exit_period": None
                    })
                    user_history_tracker[u]["offered"] += 1

                if user_trade_log is not None:
                    have_watch = row.get(f"watch_{idx+1}")
                    received_watch = row.get(f"received_watch_{idx+1}")
                    base_val = catalog.get(have_watch, 1) if catalog else 1
                    recv_val = catalog.get(received_watch, 0) if catalog else 0
                    weight_factor = 1 / (0.5 * base_val) if base_val else None

                    user_trade_log.append({
                        "user_id": u,
                        "trade_id": trade_id,
                        "user_sub_id": f"{trade_id}_{idx+1}",
                        "period_number": period,
                        "timestamp": timestamp,
                        "decision": decisions[u],
                        "cash_delta": row.get(f"cash_flow_{idx+1}"),
                        "have_watch": have_watch,
                        "received_watch": received_watch,
                        "relative_fairness_score": row.get("relative_fairness_score"),
                        "asset_value_per_user": round(float(row.get("total_value_moved", 0)) / len(loop_users), 2),
                        "watch_value_gain_pct": round(weight_factor * (recv_val - base_val), 2) if weight_factor is not None else None,
                        "loop_type": row.get("loop_type"),
                        "entry_period": user_history_tracker[u]["first_seen_period"],
                        "exit_period": period if decisions[u] == 'accept' else None,
                        "num_trades_seen": user_history_tracker[u]["offered"]
                    })

            if all(d == 'accept' for d in decisions.values()):
                for u in loop_users:
                    user_status[u] = 'matched'
                    if u in user_queue:
                        user_queue.remove(u)
                    if user_history_tracker is not None:
                        user_history_tracker[u]["accepted"] = True
                        user_history_tracker[u]["exit_period"] = period
                executed_loops.append(loop_record)
                round_exec += 1
            else:
                for u, decision in decisions.items():
                    if decision == 'decline':
                        user_status[u] = 'declined'
                        if u in user_queue:
                            user_queue.remove(u)
                            user_queue.append(u)
                rejected_loops.append(loop_record)
                round_reject += 1

            trade_counter[0] += 1

        print(f"\n🌀 Round {round_counter} Summary:")
        print(f"  ✅ Executed loops: {round_exec}")
        print(f"  ❌ Rejected loops: {round_reject}")

        matched_loops.extend(executed_loops + rejected_loops)
        round_counter += 1

    os.makedirs(output_dir, exist_ok=True)
    pd.DataFrame(executed_loops).to_csv(os.path.join(output_dir, "executed_loops.csv"), index=False)
    pd.DataFrame(rejected_loops).to_csv(os.path.join(output_dir, "rejected_loops.csv"), index=False)
    pd.DataFrame(matched_loops).to_csv(os.path.join(output_dir, "all_matched_loops.csv"), index=False)

    available = [u for u, s in user_status.items() if s == 'available']
    declined = [u for u, s in user_status.items() if s == 'declined']
    print("\n✅ Trade Simulation Complete")
    print(f"  🔁 Total executed: {len(executed_loops)}")
    print(f"  ❌ Total rejected: {len(rejected_loops)}")
    print(f"  ⏳ Remaining in queue: {len(available) + len(declined)}")
    print(f"  - Available: {len(available)}")
    print(f"  - Declined: {len(declined)}")

    if return_status:
        return {
            "executed_loops": executed_loops,
            "rejected_loops": rejected_loops,
            "user_status": user_status
        }


if __name__ == "__main__":
    with open("configs/config_simulate_trades.json", "r") as f:
        cfg = json.load(f)

    simulate_trade_loops(
        user_csv_path=cfg["input_users_path"],
        loop_csv_path=cfg["input_matching_path"],
        output_dir=cfg["output_dir"]
    )