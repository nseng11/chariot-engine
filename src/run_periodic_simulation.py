import os
import json
import datetime
import pandas as pd
from tabulate import tabulate

from generate_users import load_watch_catalog, generate_users_for_period
from loop_matching import run_loop_matching
from simulate_trades import simulate_trade_loops

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
    print(f"✅ Loaded watch catalog with {len(catalog)} watches\n")

    carried_users_df = pd.DataFrame()
    user_trade_log = []
    user_history_tracker = {}
    period_summaries = []

    for period in range(num_periods):
        print(f"============= Period {period + 1} =============")
        
        # Start of period - record carried users
        users_at_start = len(carried_users_df)
        print(f"Users at start: {users_at_start}")
        
        # Generate new users
        new_user_count = int(initial_users * ((1 + growth_rate) ** period))
        new_users_df = generate_users_for_period(
            num_users=new_user_count,
            catalog=catalog,
            period=period + 1
        )
        print(f"New users added: {len(new_users_df)}")

        # Combine users for this period
        period_users_df = pd.concat([carried_users_df, new_users_df], ignore_index=True)
        total_pool = len(period_users_df)
        print(f"Total users in pool: {total_pool}")
        
        # Set up paths and run matching
        period_dir = os.path.join(run_dir, f"period_{period+1}")
        os.makedirs(period_dir, exist_ok=True)
        period_users_path = os.path.join(period_dir, f"period_{period+1}_users.csv")
        match_results_path = os.path.join(period_dir, f"period_{period+1}_matching.csv")
        
        # Remove redundant 'period' column if it exists
        if 'period' in period_users_df.columns:
            period_users_df = period_users_df.drop('period', axis=1)
        
        # Initialize columns for tracking matches and trades
        period_users_df['proposed_matches_count'] = 0
        period_users_df['unique_matches_count'] = 0  # New column for unique matches
        period_users_df['executed_trade'] = 0
        period_users_df['loop_id'] = 'N/A'
        period_users_df['trade_id'] = 'N/A'
        
        period_users_df.to_csv(period_users_path, index=False)
        run_loop_matching(period_users_path, match_results_path)

        # Count proposed matches and unique matches from matching results
        if os.path.exists(match_results_path):
            try:
                match_df = pd.read_csv(match_results_path)
                if not match_df.empty:
                    # Dictionary to track unique end states for each user
                    user_unique_matches = {user_id: set() for user_id in period_users_df['user_id']}
                    
                    # Count how many times each user appears in proposed matches
                    for _, row in match_df.iterrows():
                        # Get all users in this loop
                        loop_users = []
                        for i in range(1, 4):  # Check user_1, user_2, user_3 columns
                            user_col = f'user_{i}'
                            if user_col in row and pd.notna(row[user_col]):
                                loop_users.append(row[user_col])
                        
                        # For each user in the loop, identify their end state
                        for i, user in enumerate(loop_users):
                            # Get the watch this user would receive
                            received_watch_col = f'received_watch_{i+1}'
                            if received_watch_col in row and pd.notna(row[received_watch_col]):
                                # Add to unique matches set: (user_id, received_watch)
                                user_unique_matches[user].add(row[received_watch_col])
                            
                            # Increment proposed matches count
                            period_users_df.loc[period_users_df['user_id'] == user, 'proposed_matches_count'] += 1
                    
                    # Update unique matches count for each user
                    for user_id, unique_matches in user_unique_matches.items():
                        period_users_df.loc[period_users_df['user_id'] == user_id, 'unique_matches_count'] = len(unique_matches)
            except pd.errors.EmptyDataError:
                pass

        # Run trade simulation
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
            trade_counter=[period * 1000]
        )

        # Get trade statistics and matched users
        exec_loops_path = os.path.join(period_dir, "executed_loops.csv")
        trades_2way = 0
        trades_3way = 0
        matched_users = set()
        
        if os.path.exists(exec_loops_path):
            try:
                exec_df = pd.read_csv(exec_loops_path)
                if not exec_df.empty:
                    # Only count trades that have a valid trade_id
                    valid_trades = exec_df[exec_df['trade_id'] != 'N/A']
                    trades_2way = (valid_trades["loop_type"] == "2-way").sum()
                    trades_3way = (valid_trades["loop_type"] == "3-way").sum()
                    # Get all matched users and mark them as having executed a trade
                    for _, row in valid_trades.iterrows():
                        users = eval(row["users"])
                        # Verify the number of users matches the trade type
                        if row["loop_type"] == "2-way" and len(users) != 2:
                            print(f"⚠️ Warning: 2-way trade with {len(users)} users")
                        elif row["loop_type"] == "3-way" and len(users) != 3:
                            print(f"⚠️ Warning: 3-way trade with {len(users)} users")
                        matched_users.update(users)
                        # Mark users as having executed a trade and record their linked trade_id and loop_id
                        for user in users:
                            period_users_df.loc[period_users_df['user_id'] == user, 'executed_trade'] = 1
                            period_users_df.loc[period_users_df['user_id'] == user, 'trade_id'] = row['trade_id']
                            period_users_df.loc[period_users_df['user_id'] == user, 'loop_id'] = row['loop_id']
            except pd.errors.EmptyDataError:
                pass

        # Calculate matched users and verify against trade counts
        users_matched = len(matched_users)
        expected_matched = (trades_2way * 2) + (trades_3way * 3)
        
        if users_matched != expected_matched:
            print(f"\n⚠️ WARNING: Matched user count mismatch in period {period + 1}")
            print(f"Found {users_matched} matched users but expected {expected_matched}")
            print(f"Based on {trades_2way} 2-way trades and {trades_3way} 3-way trades")
            # Use the expected number based on trade counts
            users_matched = expected_matched

        # Calculate continuing users based on the corrected matched users count
        continuing_users = total_pool - users_matched
        
        # Users who weren't matched continue to next period
        carried_users_df = period_users_df[~period_users_df["user_id"].isin(matched_users)].copy()
        
        # Save the period users CSV with both match counts
        period_users_df.to_csv(period_users_path, index=False)
        
        # Record period summary
        period_summary = {
            "Period": period + 1,
            "Start Users": users_at_start,
            "New Users": len(new_users_df),
            "Total Pool": total_pool,
            "2-Way Trades": trades_2way,
            "3-Way Trades": trades_3way,
            "Total Trades": trades_2way + trades_3way,
            "Users Matched": users_matched,
            "End Users": continuing_users
        }
        period_summaries.append(period_summary)
        
        print(f"\nPeriod {period + 1} Summary:")
        print(f"Started with: {users_at_start}")
        print(f"Added: {len(new_users_df)}")
        print(f"Total pool: {total_pool}")
        print(f"2-way trades: {trades_2way} ({trades_2way * 2} users)")
        print(f"3-way trades: {trades_3way} ({trades_3way * 3} users)")
        print(f"Total matched: {users_matched}")
        print(f"Continuing: {continuing_users}")
        print("=====================================\n")

    # Create and display summary table
    summary_df = pd.DataFrame(period_summaries)
    
    # Keep only the columns we want, in the order we want
    summary_df = summary_df[[
        "Period",
        "Start Users",
        "New Users",
        "Total Pool",
        "2-Way Trades",
        "3-Way Trades",
        "Total Trades",
        "Users Matched",
        "End Users"
    ]]
    
    print("\n📊 User Flow by Period:")
    print(tabulate(summary_df, headers='keys', tablefmt='grid', showindex=False))
    
    # Save summary to CSV
    summary_path = os.path.join(run_dir, "period_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"\n✅ Summary saved to: {summary_path}")

if __name__ == "__main__":
    run_multi_period_simulation()