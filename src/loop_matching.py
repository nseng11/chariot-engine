"""
Trade Loop Matching Module
=========================

This module implements the core trade matching algorithms for the Chariot Engine.
It uses graph theory to find valid trading loops between users, supporting both
2-way and 3-way trades.

Key Components:
-------------
- TradeGraph: Directed graph representation of possible trades
- Loop Finding: Algorithms to find valid trading cycles
- Trade Enrichment: Adding metadata and calculations to found trades

Metrics Calculated:
-----------------
- total_watch_value: Sum of all watch values in the loop
- total_cash_flow: Total cash movement needed
- value_efficiency: Ratio of watch value to total value movement
- relative_fairness_score: Measure of value distribution fairness

Example:
-------
>>> df = load_users("users.csv")
>>> G = build_trade_graph(df)
>>> loops = find_valid_loops(df, G)
>>> enriched_loops = enrich_loops(df, loops)
"""

import os
import json
import pandas as pd
import networkx as nx
import numpy as np
from typing import List, Dict, Any
from chariot_engine_core import TradeGraph  # This is our Rust module


def load_users(user_csv_path: str) -> pd.DataFrame:
    """
    Load user data from CSV file.

    Parameters:
    -----------
    user_csv_path : str
        Path to CSV file containing user data

    Returns:
    --------
    pd.DataFrame
        DataFrame containing user information with columns:
        - user_id: Unique identifier for each user
        - have_watch: Watch currently owned
        - have_value: Value of current watch
        - min_acceptable_value: Minimum acceptable trade value
        - max_cash_top_up: Maximum cash willing to add
    """
    return pd.read_csv(user_csv_path)


def build_trade_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed graph representing possible trades between users.

    Parameters:
    -----------
    df : pd.DataFrame
        User data containing trade preferences and constraints

    Returns:
    --------
    nx.DiGraph
        Directed graph where:
        - Nodes represent users
        - Edges represent possible trades
        - Edge (u,v) means u can trade with v

    Notes:
    ------
    Trade constraints checked:
    1. Users cannot trade with themselves
    2. Cannot trade for same watch model
    3. Trade value must meet minimum acceptable value
    4. Cash top-up must not exceed maximum limit
    """
    G = nx.DiGraph()
    
    # Pre-compute arrays for faster comparison
    values = df['have_value'].values
    min_values = df['min_acceptable_item_value'].values
    max_tops = df['max_cash_top_up'].values
    watches = df['have_watch'].values
    
    # Create nodes all at once
    G.add_nodes_from(enumerate(df.to_dict('records')))
    
    # Vectorized edge creation
    n = len(df)
    for i in range(n):
        # Create mask for valid trades
        valid_trades = (
            (values[i] >= min_values) &  # Value meets minimum
            (watches[i] != watches) &     # Different watches
            ((values[i] - values) <= max_tops)  # Within top-up limit
        )
        
        # Add edges for valid trades
        edges = [(i, j) for j in np.where(valid_trades)[0] if i != j]
        G.add_edges_from(edges)
    
    return G


def find_valid_loops(df: pd.DataFrame, G: nx.DiGraph) -> List[Dict[str, Any]]:
    """
    Find valid trading loops in the graph.

    Parameters:
    -----------
    df : pd.DataFrame
        User data
    G : nx.DiGraph
        Trade graph

    Returns:
    --------
    List[Dict[str, Any]]
        List of valid trading loops, each containing:
        - indexes: List of user indices in the loop
        - loop_type: '2-way' or '3-way'

    Notes:
    ------
    Currently supports:
    - 2-way trades (direct swaps)
    - 3-way trades (triangular trades)
    
    Future enhancements could include:
    - n-way trades for n > 3
    - Optimized loop finding algorithms
    """
    loops = []

    # Find 2-way loops
    for u, v in G.edges():
        if G.has_edge(v, u) and u < v:
            loops.append({'indexes': [u, v], 'loop_type': '2-way'})

    # Find 3-way loops
    for a in G.nodes():
        for b in G.successors(a):
            for c in G.successors(b):
                if G.has_edge(c, a) and a < b < c:
                    if len(set([a, b, c])) == 3:
                        loops.append({'indexes': [a, b, c], 'loop_type': '3-way'})
    return loops


def enrich_loops(df: pd.DataFrame, raw_loops: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Enrich raw trading loops with additional metrics and calculations.

    Parameters:
    -----------
    df : pd.DataFrame
        User data
    raw_loops : List[Dict[str, Any]]
        List of raw trading loops

    Returns:
    --------
    pd.DataFrame
        Enriched loops with additional columns:
        - total_watch_value: Sum of watch values
        - total_cash_flow: Total cash movement
        - value_efficiency: Trade efficiency metric
        - relative_fairness_score: Fairness metric
        - Various user and watch specific columns

    Notes:
    ------
    Metrics Calculated:
    1. total_watch_value: Sum of all watch values in loop
    2. total_cash_flow: Sum of absolute cash flows
    3. value_efficiency: watch_value / (watch_value + cash_flow)
    4. relative_fairness_score: Based on value distribution
    """
    output = []

    for loop_id_num, loop in enumerate(raw_loops, start=1):
        idxs = loop['indexes']
        n = len(idxs)

        users = [df.iloc[i]['user_id'] for i in idxs]
        watches = [df.iloc[i]['have_watch'] for i in idxs]
        values = [df.iloc[i]['have_value'] for i in idxs]

        cash_flows = [round(values[i] - values[(i + 1) % n], 2) for i in range(n)]
        received = [watches[(i + 1) % n] for i in range(n)]

        total_watch_value = sum(values)
        total_cash_flow = sum(abs(x) for x in cash_flows)
        avg_watch_value = total_watch_value / n if n else 1
        
        # Calculate fairness score based on value distribution
        deviation = pd.Series(values).std()
        relative_fairness_score = round(1 - deviation / avg_watch_value, 4) if avg_watch_value and deviation >= 0 else 0.5

        row = {
            'loop_id': f"L{loop_id_num:04d}",
            'loop_type': loop['loop_type'],
            'total_watch_value': round(total_watch_value, 2),
            'total_cash_flow': round(total_cash_flow, 2),
            'relative_fairness_score': relative_fairness_score,
            'trade_id': f"T{loop_id_num:05d}"
        }

        for i in range(n):
            row[f"user_{i+1}"] = users[i]
            row[f"user_sub_id_{i+1}"] = f"T{loop_id_num:05d}_{i+1}"
            row[f"watch_{i+1}"] = watches[i]
            row[f"value_{i+1}"] = values[i]
            row[f"received_watch_{i+1}"] = received[i]
            row[f"cash_flow_{i+1}"] = cash_flows[i]

        output.append(row)

    return pd.DataFrame(output)


def run_loop_matching(input_users_path: str, output_results_path: str) -> pd.DataFrame:
    """Run loop matching using Rust implementation."""
    print("\n🔄 Starting loop matching...")
    
    # Load users
    df = pd.read_csv(input_users_path)
    n_users = len(df)
    print(f"📊 Processing {n_users} users")
    
    # Convert DataFrame to Rust-compatible format
    trades = df.to_dict('records')
    
    # Create and build graph using Rust
    graph = TradeGraph()
    graph.build_from_trades(trades)
    
    # Find loops using Rust
    max_loops = min(1000, n_users * 2)
    loops = graph.find_loops(max_loops)
    
    # Convert results to DataFrame
    result_df = pd.DataFrame(loops)
    
    # Save results
    os.makedirs(os.path.dirname(output_results_path), exist_ok=True)
    if not result_df.empty:
        result_df.to_csv(output_results_path, index=False)
    else:
        with open(output_results_path, 'w') as f:
            f.write('')
    
    print(f"✅ Found {len(loops)} loops")
    return result_df


if __name__ == "__main__":
    with open("configs/config_loop_matching.json", "r") as f:
        config = json.load(f)

    run_loop_matching(
        input_users_path=config["input_users_path"],
        output_results_path=config["output_results_path"]
    )