"""
Alternative Trade Simulation
=========================

This module provides an alternative implementation of the trade simulation
that focuses on end states and competitive bidding.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import os
from collections import deque
import random
import logging
from datetime import datetime
from alternatives.user_decision_model import UserDecisionModel, UserProfile
from alternatives.end_state_tracking import EndState

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def simulate_trade_loops_alt(user_csv_path: str, loop_csv_path: str, output_dir: str, catalog_path: str = None, 
                           catalog: pd.DataFrame = None, user_trade_log: List[Dict] = None,
                           user_history_tracker: Dict = None, period: int = None, timestamp: str = None,
                           trade_counter: List[int] = None, market_volatility: float = 0.5,
                           competition_level: float = 0.5, acceptance_threshold: float = 0.5,
                           overbid_factor: float = 0.1):
    """
    Alternative implementation of trade simulation focusing on end states.
    Users can explicitly accept or reject end states, and rank their accepted end states.
    For accepted end states that require trading up, users can add overbids to make their trade more competitive.
    The system optimizes trade execution based on:
    1. Number of users satisfied
    2. User rankings of end states
    3. Total overbids in the loop
    
    An end state represents a specific outcome for a user (watch received + cash flow).
    Multiple loops can achieve the same end state for a specific user, but these loops
    may result in different end states for other users in the loop.
    
    Args:
        user_csv_path: Path to user data CSV
        loop_csv_path: Path to loop data CSV
        output_dir: Directory to save output files
        catalog_path: Path to watch catalog CSV (optional if catalog is provided)
        catalog: Watch catalog DataFrame (optional if catalog_path is provided)
        user_trade_log: Optional list to track user trade history
        user_history_tracker: Optional dictionary to track user trading history
        period: Optional period number for tracking trade history
        timestamp: Optional timestamp for tracking trade history
        trade_counter: Optional list containing a single integer to track total trades
        market_volatility: Market volatility factor (0-1)
        competition_level: Competition level factor (0-1)
        acceptance_threshold: Base threshold for accepting trades (0-1)
        overbid_factor: Factor influencing overbid amounts (0-1)
    """
    try:
        logger.debug("Starting simulation with parameters:")
        logger.debug(f"user_csv_path: {user_csv_path}")
        logger.debug(f"loop_csv_path: {loop_csv_path}")
        logger.debug(f"output_dir: {output_dir}")
        logger.debug(f"catalog_path: {catalog_path}")
        logger.debug(f"period: {period}")
        logger.debug(f"timestamp: {timestamp}")

        # Set default values for period and timestamp if not provided
        if period is None:
            period = 0
            logger.debug("Using default period value: 0")
        
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.debug(f"Using default timestamp value: {timestamp}")

        # Initialize trade counter if not provided
        if trade_counter is None:
            trade_counter = [0]
            logger.debug("Initialized trade counter")
        
        # Initialize user trade log if not provided
        if user_trade_log is None:
            user_trade_log = []
            logger.debug("Initialized user trade log")
        
        # Initialize user history tracker if not provided
        if user_history_tracker is None:
            user_history_tracker = {}
            logger.debug("Initialized user history tracker")
        
        # Load data
        logger.debug("Loading user data...")
        users_df = pd.read_csv(user_csv_path)
        logger.debug(f"Loaded {len(users_df)} users")
        
        logger.debug("Loading loop data...")
        loops_df = pd.read_csv(loop_csv_path)
        logger.debug(f"Loaded {len(loops_df)} loops")
        
        # Load catalog
        if catalog is None:
            if catalog_path is None:
                raise ValueError("Either catalog_path or catalog must be provided")
            logger.debug("Loading catalog...")
            catalog = pd.read_csv(catalog_path)
            logger.debug(f"Loaded {len(catalog)} catalog entries")
        
        # Convert catalog to dictionary for faster lookups
        logger.debug("Converting catalog to dictionary...")
        catalog_dict = {}
        for _, row in catalog.iterrows():
            key = f"{row['brand']} {row['model']}"
            catalog_dict[key] = row['base_price']
        logger.debug(f"Created catalog dictionary with {len(catalog_dict)} entries")
        
        # Initialize user status tracking
        logger.debug("Initializing user status tracking...")
        user_status = {}
        for _, user in users_df.iterrows():
            user_id = user['user_id']
            current_watch = user['have_watch']
            current_value = user['have_value']
            
            user_status[user_id] = {
                'current_watch': current_watch,
                'current_value': current_value,
                'history': [],
                'active': True
            }
            
            # Initialize user history tracker
            user_history_tracker[user_id] = {
                "offered": 0,
                "accepted": False,
                "first_seen_period": period,
                "exit_period": None,
                "first_seen_timestamp": timestamp
            }
        logger.debug(f"Initialized status tracking for {len(user_status)} users")
        
        # Initialize end states, rankings, and overbids for each user
        logger.debug("Initializing end states, rankings, and overbids...")
        user_end_states = {}  # user_id -> list of end state groups
        user_rankings = {}    # user_id -> ranked list of accepted end states
        user_overbids = {}    # user_id -> {end_state_key -> overbid_amount}
        for user_id in user_status.keys():
            user_end_states[user_id] = []
            user_rankings[user_id] = []
            user_overbids[user_id] = {}
        
        # Process each loop to build end states
        logger.debug("Building end states from loops...")
        for loop_idx, loop in loops_df.iterrows():
            if loop_idx % 100 == 0:
                logger.debug(f"Processing loop {loop_idx}/{len(loops_df)}")
            
            # Get user IDs and their end states from the loop
            loop_users = []
            for i in range(1, 4):  # Handle up to 3 users per loop
                user_col = f'user_{i}'
                if user_col in loop and pd.notna(loop[user_col]):
                    user_id = loop[user_col]
                    loop_users.append(user_id)
                    received_watch = loop.get(f'received_watch_{i}')
                    cash_flow = loop.get(f'cash_flow_{i}', 0)
                    
                    # Create end state key (watch + cash flow)
                    end_state_key = (received_watch, cash_flow)
                    
                    # Find or create end state group for this user
                    end_state_group = None
                    for group in user_end_states[user_id]:
                        if group['end_state'] == end_state_key:
                            end_state_group = group
                            break
                    
                    if end_state_group is None:
                        end_state_group = {
                            'end_state': end_state_key,
                            'received_watch': received_watch,
                            'cash_flow': cash_flow,
                            'is_accepted': False,  # User hasn't made a decision yet
                            'rank': None,         # User hasn't ranked it yet
                            'loops': []  # List of loops that achieve this end state for this user
                        }
                        user_end_states[user_id].append(end_state_group)
                    
                    # Add this loop to the end state group
                    end_state_group['loops'].append({
                        'loop_id': loop['loop_id'],
                        'loop_type': loop.get('loop_type', 'unknown'),
                        'loop_users': loop_users.copy(),
                        'other_users_end_states': {
                            u: {
                                'received_watch': loop.get(f'received_watch_{j+1}'),
                                'cash_flow': loop.get(f'cash_flow_{j+1}', 0)
                            }
                            for j, u in enumerate(loop_users) if u != user_id
                        }
                    })
        
        # Initialize user decision model with market parameters
        decision_model = UserDecisionModel(catalog_path)
        decision_model.market_volatility = market_volatility
        decision_model.competition_level = competition_level
        decision_model.time_sensitivity = acceptance_threshold

        # Process user decisions for end states
        logger.debug("Processing user decisions for end states...")
        for user_id, end_states in user_end_states.items():
            if not user_status[user_id]['active']:
                continue
            
            # First, validate each end state
            valid_end_states = []
            for end_state in end_states:
                # Create a loop-like structure for validation
                loop_data = {
                    'user_1': user_id,
                    'received_watch_1': end_state['received_watch'],
                    'cash_flow_1': end_state['cash_flow']
                }
                
                # Validate the end state
                is_valid, reason = validate_trade_alt(loop_data, user_status, users_df)
                if is_valid:
                    valid_end_states.append(end_state)
            
            # For each valid end state, simulate user decision
            accepted_end_states = []
            for end_state in valid_end_states:
                # Create user profile
                user_data = users_df[users_df['user_id'] == user_id].iloc[0]
                
                # Calculate risk tolerance based on user's preferences
                value_risk = 1 - (user_data['min_acceptable_value'] / user_data['have_value'])  # How much value they're willing to lose
                cash_risk = user_data['max_cash_top_up'] / user_data['have_value']  # How much they're willing to add
                
                # Combine factors to get overall risk tolerance (0-1 scale)
                risk_tolerance = (value_risk + cash_risk) / 2
                
                user_profile = UserProfile(
                    brand_loyalty={},  # Initialize with empty dict
                    risk_tolerance=risk_tolerance,  # Calculated risk tolerance
                    financial_capacity=user_data['max_cash_top_up'] / user_data['have_value'],
                    collection_goals={},  # Initialize with empty dict
                    trading_history={}  # Initialize with empty dict
                )
                
                # Create end state object
                end_state_obj = EndState(
                    watch=end_state['received_watch'],
                    watch_value=user_data['have_value'],  # Use current watch value as base
                    cash_flow=end_state['cash_flow'],
                    trade_sources=[],  # Initialize empty list of trade sources
                    value_efficiency=0.0  # Initialize with default efficiency
                )
                
                # Make decision using the model
                is_accepted, overbid = decision_model.make_decision(
                    end_state=end_state_obj,
                    user_profile=user_profile,
                    current_watch=user_data['have_watch'],
                    current_value=user_data['have_value'],
                    max_cash_top_up=user_data['max_cash_top_up']
                )
                
                end_state['is_accepted'] = is_accepted
                
                if is_accepted:
                    accepted_end_states.append(end_state)
                    
                    # If this end state requires trading up, use the calculated overbid
                    if end_state['cash_flow'] < 0:
                        user_overbids[user_id][end_state['end_state']] = overbid
            
            # Rank accepted end states
            random.shuffle(accepted_end_states)
            for i, end_state in enumerate(accepted_end_states):
                end_state['rank'] = i + 1
            
            # Store ranked accepted end states
            user_rankings[user_id] = sorted(accepted_end_states, key=lambda x: x['rank'])
        
        # Find optimal set of trades
        logger.debug("Finding optimal set of trades...")
        executed_trades = []
        rejected_loops = []
        
        # Create a graph of compatible end states
        end_state_graph = {}  # loop_id -> set of users who have ranked compatible end states
        for user_id, rankings in user_rankings.items():
            for end_state in rankings:
                # For each loop in this end state
                for loop in end_state['loops']:
                    loop_id = loop['loop_id']
                    if loop_id not in end_state_graph:
                        end_state_graph[loop_id] = set()
                    end_state_graph[loop_id].add(user_id)
        
        # Find loops where all users have ranked compatible end states
        valid_loops = []
        for loop_id, users in end_state_graph.items():
            # Get the original loop data
            loop_data = loops_df[loops_df['loop_id'] == loop_id].iloc[0]
            loop_users = [loop_data[f'user_{i}'] for i in range(1, 4) if pd.notna(loop_data.get(f'user_{i}'))]
            
            # Check if all users in the loop have ranked compatible end states
            if all(user in users for user in loop_users):
                valid_loops.append(loop_id)
        
        # Sort valid loops by:
        # 1. Number of users (descending)
        # 2. Average rank of end states (ascending)
        # 3. Total overbids in the loop (descending)
        valid_loops.sort(key=lambda x: (
            len(end_state_graph[x]),  # Primary: Number of users
            -sum(                     # Secondary: Average rank of end states
                next(
                    (end_state['rank'] for end_state in user_rankings[user] 
                     if any(loop['loop_id'] == x for loop in end_state['loops'])),
                    float('inf')
                )
                for user in end_state_graph[x]
            ) / len(end_state_graph[x]),
            -sum(                     # Tertiary: Total overbids
                user_overbids[user].get(
                    next(
                        (end_state['end_state'] for end_state in user_rankings[user]
                         if any(loop['loop_id'] == x for loop in end_state['loops'])),
                        None
                    ),
                    0
                )
                for user in end_state_graph[x]
            )
        ), reverse=True)
        
        # Execute trades from valid loops
        used_users = set()
        for loop_id in valid_loops:
            # Get users in this loop
            loop_users = end_state_graph[loop_id]
            
            # Skip if any user has already traded
            if any(user in used_users for user in loop_users):
                continue
            
            # Execute the trade
            loop_data = loops_df[loops_df['loop_id'] == loop_id].iloc[0]
            trade_id = f"T{trade_counter[0]+1:05d}" if trade_counter else f"T{len(executed_trades)+1:05d}"
            if trade_counter:
                trade_counter[0] += 1
            
            # Process each user's trade
            for i, user_id in enumerate(loop_users):
                process_trade_decision_alt(user_id, 'accept', user_status, user_history_tracker, period)
                used_users.add(user_id)
            
            # Record the trade
            trade_record = {
                'loop_id': loop_id,
                'trade_id': trade_id,
                'user_ids': ','.join(loop_users),
                'from_watches': ','.join(loop_data[f'watch_{i+1}'] for i in range(len(loop_users))),
                'to_watches': ','.join(loop_data[f'received_watch_{i+1}'] for i in range(len(loop_users))),
                'cash_flows': ','.join(str(loop_data[f'cash_flow_{i+1}']) for i in range(len(loop_users))),
                'overbids': ','.join(
                    str(user_overbids[user_id].get(
                        next(
                            (end_state['end_state'] for end_state in user_rankings[user_id]
                             if any(loop['loop_id'] == loop_id for loop in end_state['loops'])),
                            (None, 0)
                        )[0],
                        0
                    ))
                    for user_id in loop_users
                ),
                'period': period,
                'timestamp': timestamp
            }
            executed_trades.append(trade_record)
        
        # Record rejected loops
        rejected_loops = [loop for loop in loops_df.iterrows() if loop[1]['loop_id'] not in valid_loops]
        
        logger.debug("Saving results...")
        # Save results
        os.makedirs(output_dir, exist_ok=True)
        
        # Save executed trades
        if executed_trades:
            executed_df = pd.DataFrame(executed_trades)
            executed_df.to_csv(os.path.join(output_dir, 'executed_trades.csv'), index=False)
            logger.debug(f"Saved {len(executed_trades)} executed trades")
        else:
            # Create empty DataFrame with correct columns
            pd.DataFrame(columns=['loop_id', 'trade_id', 'user_ids', 'from_watches', 'to_watches', 
                                'cash_flows', 'overbids', 'period', 'timestamp']).to_csv(
                os.path.join(output_dir, 'executed_trades.csv'), index=False)
            logger.debug("Created empty executed trades file")
        
        # Save rejected loops
        if rejected_loops:
            rejected_df = pd.DataFrame(rejected_loops)
            rejected_df.to_csv(os.path.join(output_dir, 'rejected_loops.csv'), index=False)
            logger.debug(f"Saved {len(rejected_loops)} rejected loops")
        else:
            # Create empty DataFrame with correct columns
            pd.DataFrame(columns=loops_df.columns).to_csv(
                os.path.join(output_dir, 'rejected_loops.csv'), index=False)
            logger.debug("Created empty rejected loops file")
        
        # Save user final states
        final_states = []
        for user_id, status in user_status.items():
            final_states.append({
                'user_id': user_id,
                'final_watch': status['current_watch'],
                'final_value': status['current_value'],
                'trade_count': len(status['history']),
                'period': period,
                'timestamp': timestamp
            })
        if final_states:
            pd.DataFrame(final_states).to_csv(os.path.join(output_dir, 'user_final_states.csv'), index=False)
            logger.debug(f"Saved {len(final_states)} user final states")
        else:
            # Create empty DataFrame with correct columns
            pd.DataFrame(columns=['user_id', 'final_watch', 'final_value', 'trade_count', 
                                'period', 'timestamp']).to_csv(
                os.path.join(output_dir, 'user_final_states.csv'), index=False)
            logger.debug("Created empty user final states file")
        
        logger.debug("Simulation completed successfully")
        return {
            'executed_trades': executed_trades,
            'rejected_loops': rejected_loops,
            'total_users': len(user_status)
        }
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}", exc_info=True)
        raise

def validate_trade_alt(loop: Dict, user_status: Dict[str, str], users_df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate a trade loop based on end states from each user's perspective.
    Returns (is_valid, reason)
    """
    # Extract users and their watches
    loop_users = []
    for i in range(1, 4):  # Support up to 3-way trades
        user_col = f'user_{i}'
        if user_col in loop and pd.notna(loop[user_col]):
            loop_users.append(loop[user_col])
    
    # Check if users are available and haven't traded
    if not all(user_status[u]['active'] for u in loop_users):
        return False, "One or more users not available for trade"
    
    # For each user, validate their end state (received watch + cash flow + overbid)
    for i, user_id in enumerate(loop_users):
        user_data = users_df[users_df['user_id'] == user_id].iloc[0]
        received_watch = loop.get(f'received_watch_{i+1}')
        cash_flow = loop.get(f'cash_flow_{i+1}', 0)
        overbid = loop.get(f'overbid_{i+1}', 0)
        
        # Get the value of the received watch
        received_watch_data = users_df[users_df['have_watch'] == received_watch].iloc[0]
        received_value = received_watch_data['have_value']
        
        # Check minimum acceptable value (end state value)
        if received_value < user_data['min_acceptable_value']:
            return False, f"User {user_id} end state value {received_value:.2f} below minimum acceptable {user_data['min_acceptable_value']:.2f}"
        
        # Check maximum cash top-up (end state cash flow + overbid)
        total_cash = cash_flow + overbid
        if total_cash > user_data['max_cash_top_up']:
            return False, f"User {user_id} total cash flow {total_cash:.2f} (base: {cash_flow:.2f}, overbid: {overbid:.2f}) exceeds maximum top-up {user_data['max_cash_top_up']:.2f}"
    
    return True, "Trade valid"

def get_trade_weights(value_efficiency=None, max_value_diff=None, avg_watch_value=None):
    """
    Calculate acceptance weights based on end states.
    Since we validate trades based on user preferences and end states,
    use a simple 50/50 probability for trade acceptance.
    """
    return [0.5, 0.5]  # [decline, accept]

def process_trade_decision_alt(user, decision, user_status, user_history_tracker, period):
    """
    Process a user's trade decision and update their status.
    """
    if decision == 'accept':
        # Update user history
        user_history_tracker[user]["accepted"] = True
        user_history_tracker[user]["exit_period"] = period
        # Mark user as inactive after trade
        user_status[user]['active'] = False

if __name__ == "__main__":
    with open("configs/config_simulate_trades_alt.json", "r") as f:
        cfg = json.load(f)
    
    simulate_trade_loops_alt(
        user_csv_path=cfg["paths"]["user_data"],
        loop_csv_path=cfg["paths"]["matching_data"],
        output_dir=cfg["paths"]["output_dir"],
        catalog_path=cfg["paths"]["catalog_path"]
    ) 