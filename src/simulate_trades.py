"""
Trade Simulation Module
======================

This module implements the core trade simulation logic for the Chariot Engine.
It simulates trading rounds where users can accept or decline trades based on
various factors including fairness, efficiency, and personal preferences.

Key Features:
------------
- Multi-round trade simulation
- Probabilistic trade acceptance
- User state management
- Trade execution tracking
- Performance metrics calculation

Components:
----------
- Trade simulation engine
- User state management
- Trade decision logic
- Performance tracking
- Result logging

Example:
--------
>>> result = simulate_trade_loops(
...     user_csv_path="data/users.csv",
...     loop_csv_path="data/loops.csv",
...     output_dir="output/simulation"
... )
>>> print(f"Executed trades: {len(result['executed_loops'])}")
"""

import os
import json
import pandas as pd
import random
from collections import deque
from typing import Dict, List, Optional, Union, Any

def get_trade_weights(fairness_score, value_efficiency, max_value_diff=None, avg_watch_value=None):
    """Calculate acceptance weights based on value efficiency (primary) and fairness (secondary)"""
    base_weight = 0.5
    
    # Value Efficiency - Primary factor with data-driven thresholds
    if value_efficiency < 0.8:         # Strong penalty below 0.8
        efficiency_modifier = -0.4
    elif value_efficiency < 0.8338:    # Q1: baseline
        efficiency_modifier = 0.0
    elif value_efficiency < 0.86:      # Q1-Q2: good
        efficiency_modifier = 0.15
    elif value_efficiency < 0.898:     # Q2-Q3: very good
        efficiency_modifier = 0.25
    else:                             # Above Q3: excellent
        efficiency_modifier = 0.35
    
    # Relative Fairness - Secondary factor with right-skewed thresholds
    if fairness_score < 0.7469:       # Below Q1: no boost
        fairness_modifier = 0.0
    elif fairness_score < 0.7888:     # Q1-Q2: minimal boost
        fairness_modifier = 0.03
    elif fairness_score < 0.8509:     # Q2-Q3: moderate boost
        fairness_modifier = 0.08
    elif fairness_score < 0.9:        # Q3-0.9: good boost
        fairness_modifier = 0.12
    else:                            # >0.9: excellent boost
        fairness_modifier = 0.15
    
    accept_weight = base_weight + efficiency_modifier + fairness_modifier
    return [1 - accept_weight, accept_weight]  # [decline, accept]

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

    # Get all valid loops for this round
    current_loops = loops_df.copy()
    current_loops['valid'] = current_loops.apply(
        lambda row: all(user_status.get(row.get(f"user_{i+1}"), 'matched') == 'available'
                        for i in range(3) if pd.notna(row.get(f"user_{i+1}"))),
        axis=1
    )

    filtered_loops = current_loops[current_loops['valid']].drop(columns='valid')
    
    print(f"\nSimulating trades:")
    print(f"Total possible loops: {len(filtered_loops)}")
    
    if not filtered_loops.empty:
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

    os.makedirs(output_dir, exist_ok=True)
    pd.DataFrame(executed_loops).to_csv(os.path.join(output_dir, "executed_loops.csv"), index=False)
    pd.DataFrame(rejected_loops).to_csv(os.path.join(output_dir, "rejected_loops.csv"), index=False)
    pd.DataFrame(matched_loops).to_csv(os.path.join(output_dir, "all_matched_loops.csv"), index=False)

    available = [u for u, s in user_status.items() if s == 'available']
    declined = [u for u, s in user_status.items() if s == 'declined']

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