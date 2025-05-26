"""
Trade Prioritization Module
=========================

This module handles the prioritization of trades based on user preferences
and cash flow considerations.

Key Concepts:
------------
1. Trade Priority: Determined by:
   - Number of users accepting the trade
   - Total cash flow involved
   - Value efficiency
   - User preferences

2. Cash Flow: The amount of cash that needs to be exchanged
   to balance the trade.

3. Value Efficiency: The ratio of watch value to total cash flow.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
from end_state_tracking import EndState
from user_preferences import UserPreferenceManager

@dataclass
class Trade:
    """Represents a prioritized trade"""
    loop_id: str
    users: List[str]  # List of user IDs involved in the trade
    total_cash_flow: float
    cash_overbids: Dict[str, float]  # User ID -> cash overbid amount
    value_efficiency: float

class TradePrioritizer:
    """Prioritizes trades based on user preferences and cash flow"""
    
    def __init__(self, preference_manager: UserPreferenceManager):
        self.preference_manager = preference_manager
    
    def prioritize_trades(self, loops: List[Dict]) -> List[Trade]:
        """Prioritize trades based on user preferences and cash flow"""
        prioritized_trades = []
        
        for loop in loops:
            # Extract users involved in the trade
            users = []
            for i in range(1, 4):  # Support up to 3-way trades
                user_col = f'user_{i}'
                if user_col in loop and pd.notna(loop[user_col]):
                    users.append(loop[user_col])
            
            # Skip if no users found
            if not users:
                continue
            
            # Calculate total cash flow
            total_cash_flow = sum(abs(loop.get(f'cash_flow_{i}', 0)) 
                                for i in range(1, len(users) + 1))
            
            # Get cash overbids for each user
            cash_overbids = {}
            for user_id in users:
                user_prefs = self.preference_manager.get_user_preferences(user_id)
                if user_prefs:
                    # Get the highest overbid for this user
                    max_overbid = max((pref.cash_overbid for pref in user_prefs.values()), default=0)
                    cash_overbids[user_id] = max_overbid
            
            # Create trade object
            trade = Trade(
                loop_id=loop['loop_id'],
                users=users,
                total_cash_flow=total_cash_flow,
                cash_overbids=cash_overbids,
                value_efficiency=loop.get('value_efficiency', 0)
            )
            
            prioritized_trades.append(trade)
        
        # Sort trades by:
        # 1. Number of users accepting (descending)
        # 2. Value efficiency (descending)
        # 3. Total cash flow (ascending)
        prioritized_trades.sort(
            key=lambda t: (
                len(t.users),
                t.value_efficiency,
                -t.total_cash_flow
            ),
            reverse=True
        )
        
        return prioritized_trades
    
    def _calculate_value_efficiency(self, loop: Dict) -> float:
        """Calculate the value efficiency of a trade loop"""
        # TODO: Implement value efficiency calculation
        return 1.0  # Placeholder 