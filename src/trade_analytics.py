"""
Trade Analytics Module
=====================

This module provides the core graph building functionality for the Chariot Engine
trading system. It creates a directed graph representing possible trades between users.

Dependencies:
------------
- pandas: Data processing
- networkx: Graph operations
- numpy: Vectorized operations
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict

def build_trade_graph(df: pd.DataFrame) -> nx.DiGraph:
    """Optimized graph building"""
    G = nx.DiGraph()
    
    # Pre-compute node data
    node_data = df.to_dict('records')
    nodes = [(i, data) for i, data in enumerate(node_data)]
    G.add_nodes_from(nodes)
    
    # Vectorized filtering for potential edges
    have_values = df['have_value'].values[:, np.newaxis]
    min_values = df['min_acceptable_item_value'].values
    max_top_ups = df['max_cash_top_up'].values
    watches = df['have_watch'].values
    
    # Create mask for valid trades
    value_mask = have_values >= min_values
    top_up_mask = (have_values - have_values.T) <= max_top_ups
    watch_mask = watches[:, np.newaxis] != watches
    
    # Combine masks
    valid_trades = value_mask & top_up_mask & watch_mask
    
    # Add edges where valid
    edges = np.where(valid_trades)
    G.add_edges_from(zip(edges[0], edges[1]))
    
    return G