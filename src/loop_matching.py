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
"""

import os
import json
import pandas as pd
import networkx as nx
import numpy as np
from typing import List, Dict, Any
import random

def load_users(user_csv_path: str) -> pd.DataFrame:
    """
    Load user data from CSV file.
    """
    return pd.read_csv(user_csv_path)

def build_trade_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed graph representing possible trades between users.
    """
    G = nx.DiGraph()
    
    # Pre-compute arrays for faster comparison
    values = df["have_value"].values
    min_values = df["min_acceptable_item_value"].values
    max_tops = df["max_cash_top_up"].values
    watches = df["have_watch"].values
    
    # Create nodes all at once
    G.add_nodes_from(enumerate(df.to_dict("records")))
    
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
    """
    loops = []
    
    # Find all possible 2-way loops
    for u, v in G.edges():
        if G.has_edge(v, u) and u < v:
            # Check value constraints
            u_value = df.iloc[u]["have_value"]
            v_value = df.iloc[v]["have_value"]
            u_min = df.iloc[u]["min_acceptable_item_value"]
            v_min = df.iloc[v]["min_acceptable_item_value"]
            
            if u_value >= v_min and v_value >= u_min:
                loops.append({"indexes": [u, v], "loop_type": "2-way"})

    # Find all possible 3-way loops
    for a in G.nodes():
        for b in G.successors(a):
            if b <= a:
                continue
            for c in G.successors(b):
                if c <= b:
                    continue
                if G.has_edge(c, a):
                    # Check value constraints
                    values = [df.iloc[i]["have_value"] for i in (a, b, c)]
                    min_values = [df.iloc[i]["min_acceptable_item_value"] for i in (a, b, c)]
                    
                    # Check if each person gets at least their minimum value
                    if all(values[i] >= min_values[(i+1)%3] for i in range(3)):
                        loops.append({"indexes": [a, b, c], "loop_type": "3-way"})

    # Randomly shuffle the loops to avoid bias
    random.shuffle(loops)
    
    return loops

def enrich_loops(df: pd.DataFrame, raw_loops: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Enrich raw trading loops with additional metrics and calculations.
    """
    output = []

    for loop_id_num, loop in enumerate(raw_loops, start=1):
        idxs = loop["indexes"]
        n = len(idxs)

        users = [df.iloc[i]["user_id"] for i in idxs]
        watches = [df.iloc[i]["have_watch"] for i in idxs]
        values = [df.iloc[i]["have_value"] for i in idxs]

        cash_flows = [round(values[i] - values[(i + 1) % n], 2) for i in range(n)]
        received = [watches[(i + 1) % n] for i in range(n)]

        total_watch_value = sum(values)
        total_cash_flow = sum(abs(flow) for flow in cash_flows)
        
        value_efficiency = round(
            total_watch_value / (total_watch_value + total_cash_flow)
            if total_watch_value + total_cash_flow > 0 else 0,
            4
        )
        
        # Prepare watch columns for visualization
        watch_dict = {}
        for i, w in enumerate(watches, 1):
            watch_dict[f"watch_{i}"] = w
            watch_dict[f"received_watch_{i}"] = received[i-1] if i <= len(received) else None
            watch_dict[f"cash_flow_{i}"] = cash_flows[i-1] if i <= len(cash_flows) else None
            watch_dict[f"user_{i}"] = users[i-1] if i <= len(users) else None
            
        output.append({
            "loop_id": f"L{loop_id_num:04d}",
            "loop_type": loop["loop_type"],
            "users": users,
            **watch_dict,  # Add watch columns in the expected format
            "total_watch_value": total_watch_value,
            "total_cash_flow": total_cash_flow,
            "value_efficiency": value_efficiency
        })
    
    return pd.DataFrame(output)

def run_loop_matching(input_users_path: str, output_results_path: str) -> pd.DataFrame:
    """
    Main function to run the loop matching process.
    """
    df = load_users(input_users_path)
    print(f"\nFinding trade loops for {len(df)} users...")
    
    G = build_trade_graph(df)
    print(f"Built trade graph with {G.number_of_edges()} possible trades")
    
    loops = find_valid_loops(df, G)
    print(f"Found {len(loops)} potential trade loops:")
    print(f"  - 2-way trades: {sum(1 for l in loops if l['loop_type'] == '2-way')}")
    print(f"  - 3-way trades: {sum(1 for l in loops if l['loop_type'] == '3-way')}")
    
    results = enrich_loops(df, loops)
    
    if output_results_path:
        results.to_csv(output_results_path, index=False)
        print(f"Saved {len(results)} enriched trade loops to {output_results_path}")
    
    return results
