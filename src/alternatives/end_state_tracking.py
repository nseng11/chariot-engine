"""
End State Tracking Module
========================

This module handles the tracking of unique end states for each user,
regardless of whether they come from 2-way or 3-way trades.

Key Concepts:
------------
1. End State: A user's final state after a trade, including:
   - Watch received
   - Watch value
   - Cash flow
   - Trade sources
   - Value efficiency

2. Unique End States: Different trade combinations leading to the same
   end state are considered equivalent from the user's perspective.

3. Trade Source: The original trade loop(s) that led to this end state.
"""

import pandas as pd
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

@dataclass(frozen=True)  # Make the class immutable and hashable
class EndState:
    """Represents a unique end state for a user"""
    watch: str
    watch_value: float  # Value of the watch being received
    cash_flow: float
    trade_sources: List[str]
    value_efficiency: float

    def __hash__(self):
        """Make the class hashable based on watch and cash flow"""
        return hash((self.watch, self.cash_flow))

    def __eq__(self, other):
        """Define equality based on watch and cash flow"""
        if not isinstance(other, EndState):
            return NotImplemented
        return (self.watch == other.watch and 
                self.cash_flow == other.cash_flow)

class EndStateTracker:
    def __init__(self):
        self.user_end_states: Dict[str, Set[EndState]] = {}
        
    def process_trade_loop(self, loop_data: pd.Series):
        """Process a trade loop and extract end states for each user"""
        loop_id = loop_data['loop_id']
        loop_type = loop_data['loop_type']
        
        # Process each user in the loop
        for i in range(1, 4):  # Support up to 3-way trades
            user_col = f'user_{i}'
            if user_col not in loop_data or pd.isna(loop_data[user_col]):
                continue
                
            user_id = loop_data[user_col]
            received_watch = loop_data[f'received_watch_{i}']
            watch_value = loop_data[f'value_{i}']  # Get the watch value
            cash_flow = loop_data[f'cash_flow_{i}']
            value_efficiency = loop_data['value_efficiency']
            
            # Create end state
            end_state = EndState(
                watch=received_watch,
                watch_value=watch_value,
                cash_flow=cash_flow,
                trade_sources=[loop_id],
                value_efficiency=value_efficiency
            )
            
            # Add to user's end states
            if user_id not in self.user_end_states:
                self.user_end_states[user_id] = set()
            
            # Check if this is a duplicate end state
            existing_state = next(
                (state for state in self.user_end_states[user_id] 
                 if state.watch == received_watch and state.cash_flow == cash_flow),
                None
            )
            
            if existing_state:
                # Create a new EndState with updated trade sources
                updated_state = EndState(
                    watch=existing_state.watch,
                    watch_value=existing_state.watch_value,
                    cash_flow=existing_state.cash_flow,
                    trade_sources=existing_state.trade_sources + [loop_id],
                    value_efficiency=existing_state.value_efficiency
                )
                self.user_end_states[user_id].remove(existing_state)
                self.user_end_states[user_id].add(updated_state)
            else:
                self.user_end_states[user_id].add(end_state)
    
    def get_user_end_states(self, user_id: str) -> List[EndState]:
        """Get all unique end states for a user"""
        return list(self.user_end_states.get(user_id, set()))
    
    def get_all_end_states(self) -> Dict[str, List[EndState]]:
        """Get all end states for all users"""
        return {user_id: list(states) for user_id, states in self.user_end_states.items()} 