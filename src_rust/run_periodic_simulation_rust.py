import os
import json
import datetime
import pandas as pd
from typing import Dict, Any

from chariot_engine_core import (  # Our Rust components
    TradeGraph,
    TradeSimulator,
    UserGenerator
)

def run_multi_period_simulation_rust(
    config_path: str = "configs/config_run_periodic.json"
) -> None:
    """
    Rust-powered version of periodic simulation.
    Uses Rust components for performance-critical operations.
    """
    # Load configuration
    with open(config_path, "r") as f:
        config = json.load(f)

    initial_users = config["initial_users"]
    growth_rate = config["growth_rate"]
    num_periods = config["num_periods"]
    catalog_path = config["catalog_path"]

    # Create output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join("simulations", f"run_rust_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    # Initialize Rust components
    trade_graph = TradeGraph()
    simulator = TradeSimulator()
    user_generator = UserGenerator(catalog_path)

    # Initialize tracking
    user_trade_log = []
    user_history_tracker = {}
    executed_loops_all = []
    rejected_loops_all = []
    total_users = 0
    total_2way = 0
    total_3way = 0
    total_users_matched = set()
    trade_counter = [0]

    for period in range(num_periods):
        print(f"\n📆 Starting Period {period + 1}...")

        period_dir = os.path.join(run_dir, f"period_{period+1}")
        os.makedirs(period_dir, exist_ok=True)

        # Generate new users using Rust
        new_user_count = int(initial_users * ((1 + growth_rate) ** period))
        new_users = user_generator.generate_users(
            count=new_user_count,
            period=period + 1
        )
        total_users += new_user_count

        # Combine with carried users
        period_users = pd.concat([
            pd.DataFrame(new_users),
            pd.DataFrame(user_history_tracker.get('carried_users', []))
        ])

        # Save period users
        period_users_path = os.path.join(period_dir, f"period_{period+1}_users.csv")
        period_users.to_csv(period_users_path, index=False)

        # Find trading loops using Rust
        trade_graph.build_from_users(period_users.to_dict('records'))
        loops = trade_graph.find_loops(max_loops=1000)

        # Simulate trades using Rust
        simulation_result = simulator.simulate_trades(
            users=period_users.to_dict('records'),
            loops=loops,
            period=period + 1,
            trade_counter=trade_counter[0]
        )

        # Update counters and tracking
        trade_counter[0] = simulation_result['next_trade_counter']
        user_trade_log.extend(simulation_result['trade_log'])
        user_history_tracker.update(simulation_result['user_history'])

        # Process results
        executed = pd.DataFrame(simulation_result['executed_loops'])
        rejected = pd.DataFrame(simulation_result['rejected_loops'])

        if not executed.empty:
            executed_loops_all.append(executed)
            executed.to_csv(os.path.join(period_dir, "executed_loops.csv"), index=False)
            
            # Update statistics
            total_2way += (executed['loop_type'] == '2-way').sum()
            total_3way += (executed['loop_type'] == '3-way').sum()
            
            for users in executed['users']:
                total_users_matched.update(json.loads(users))

        if not rejected.empty:
            rejected_loops_all.append(rejected)
            rejected.to_csv(os.path.join(period_dir, "rejected_loops.csv"), index=False)

        # Update carried users for next period
        user_history_tracker['carried_users'] = simulation_result['carried_users']

        # Print period summary
        print(f"📊 Period {period + 1} Summary:")
        print(f"  - Executed 2-way trades: {(executed['loop_type'] == '2-way').sum()}")
        print(f"  - Executed 3-way trades: {(executed['loop_type'] == '3-way').sum()}")
        print(f"  - Users carried to next period: {len(simulation_result['carried_users'])}")

    # Save final results
    save_final_results(
        run_dir=run_dir,
        executed_loops_all=executed_loops_all,
        rejected_loops_all=rejected_loops_all,
        user_trade_log=user_trade_log,
        user_history_tracker=user_history_tracker,
        total_users=total_users,
        total_users_matched=total_users_matched,
        total_2way=total_2way,
        total_3way=total_3way,
        num_periods=num_periods,
        initial_users=initial_users,
        growth_rate=growth_rate
    )

def save_final_results(**kwargs) -> None:
    """Save final simulation results."""
    run_dir = kwargs['run_dir']
    
    # Save aggregate summary
    pd.DataFrame([{
        "total_users_generated": kwargs['total_users'],
        "users_accepted_trade": len(kwargs['total_users_matched']),
        "total_2way_trades": kwargs['total_2way'],
        "total_3way_trades": kwargs['total_3way'],
        "total_trades_executed": kwargs['total_2way'] + kwargs['total_3way'],
        "percent_users_traded": round(100 * len(kwargs['total_users_matched']) / kwargs['total_users'], 2),
        "avg_users_per_trade": round(
            (2 * kwargs['total_2way'] + 3 * kwargs['total_3way']) / 
            (kwargs['total_2way'] + kwargs['total_3way']), 2
        ),
        "num_periods": kwargs['num_periods'],
        "initial_users": kwargs['initial_users'],
        "growth_rate": kwargs['growth_rate']
    }]).to_csv(os.path.join(run_dir, "aggregate_summary.csv"), index=False)

    # Save all executed loops
    if kwargs['executed_loops_all']:
        pd.concat(kwargs['executed_loops_all']).to_csv(
            os.path.join(run_dir, "all_executed_loops.csv"), 
            index=False
        )

    # Save all rejected loops
    if kwargs['rejected_loops_all']:
        pd.concat(kwargs['rejected_loops_all']).to_csv(
            os.path.join(run_dir, "all_rejected_loops.csv"), 
            index=False
        )

    # Save user tracking summary
    user_summary_df = pd.DataFrame.from_dict(
        kwargs['user_history_tracker'], 
        orient="index"
    )
    user_summary_df.index.name = "user_id"
    user_summary_df.reset_index(inplace=True)
    user_summary_df.to_csv(
        os.path.join(run_dir, "user_tracking_summary.csv"), 
        index=False
    )

    # Save trade log
    pd.DataFrame(kwargs['user_trade_log']).to_csv(
        os.path.join(run_dir, "user_trade_log.csv"), 
        index=False
    )

if __name__ == "__main__":
    run_multi_period_simulation_rust() 