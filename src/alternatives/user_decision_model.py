"""
User Decision Model Module
========================

This module models realistic user decisions and overbids for end states.
It takes into account various factors that influence real-world trading decisions:

1. Watch Value Factors:
   - Relative value difference (trading up/down)
   - Brand prestige
   - Model popularity
   - Condition/age of watch

2. Cash Flow Factors:
   - User's financial capacity
   - Market conditions
   - Time sensitivity
   - Competition level

3. User Preference Factors:
   - Brand loyalty
   - Collection goals
   - Trading history
   - Risk tolerance
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from end_state_tracking import EndState
from watch_attributes import WatchAttributeManager

@dataclass
class UserProfile:
    """Represents a user's trading profile and preferences"""
    brand_loyalty: Dict[str, float]  # Brand name -> loyalty score (0-1)
    risk_tolerance: float  # 0-1 scale
    financial_capacity: float  # 0-1 scale
    collection_goals: Dict[str, float]  # Brand/model -> goal score (0-1)
    trading_history: Dict[str, int]  # Brand -> number of trades

class UserDecisionModel:
    def __init__(self, catalog_path: str):
        """
        Initialize the decision model
        
        Args:
            catalog_path: Path to the watch catalog CSV file
        """
        # Initialize watch attribute manager
        self.watch_attributes = WatchAttributeManager(catalog_path)
        
        # Market condition parameters
        self.market_volatility = 0.5  # 0-1 scale
        self.competition_level = 0.5  # 0-1 scale
        self.time_sensitivity = 0.5  # 0-1 scale
    
    def calculate_acceptance_probability(
        self,
        end_state: EndState,
        user_profile: UserProfile,
        current_watch: str,
        current_value: float
    ) -> float:
        """
        Calculate the probability of a user accepting an end state.
        Returns a value between 0 and 1.
        """
        # Get watch attributes
        target_attrs = self.watch_attributes.get_watch_attributes(end_state.watch)
        current_attrs = self.watch_attributes.get_watch_attributes(current_watch)
        
        # Value difference factor
        value_diff = (end_state.watch_value - current_value) / current_value
        value_factor = 1 / (1 + np.exp(-5 * value_diff))  # Sigmoid function
        
        # Brand prestige factor
        prestige_factor = target_attrs.prestige_score
        
        # Model popularity factor
        popularity_factor = target_attrs.popularity_score
        
        # Brand loyalty factor
        loyalty_factor = user_profile.brand_loyalty.get(target_attrs.brand, 0.5)
        
        # Collection goals factor
        goal_factor = user_profile.collection_goals.get(end_state.watch, 0.5)
        
        # Trading history factor
        history_factor = 1 / (1 + np.exp(-0.1 * user_profile.trading_history.get(target_attrs.brand, 0)))
        
        # Market condition factors
        market_factor = (
            (1 - self.market_volatility) * 
            (1 - self.competition_level) * 
            target_attrs.market_trend
        )
        
        # Value retention factor
        retention_factor = target_attrs.value_retention
        
        # Trading frequency factor
        frequency_factor = target_attrs.trading_frequency
        
        # Combine all factors with weights
        weights = {
            'value': 0.25,
            'prestige': 0.1,
            'popularity': 0.1,
            'loyalty': 0.1,
            'goals': 0.1,
            'history': 0.05,
            'market': 0.1,
            'retention': 0.1,
            'frequency': 0.1
        }
        
        probability = (
            weights['value'] * value_factor +
            weights['prestige'] * prestige_factor +
            weights['popularity'] * popularity_factor +
            weights['loyalty'] * loyalty_factor +
            weights['goals'] * goal_factor +
            weights['history'] * history_factor +
            weights['market'] * market_factor +
            weights['retention'] * retention_factor +
            weights['frequency'] * frequency_factor
        )
        
        # Adjust for risk tolerance
        probability = probability * (0.5 + 0.5 * user_profile.risk_tolerance)
        
        return min(max(probability, 0), 1)  # Ensure between 0 and 1
    
    def calculate_overbid(
        self,
        end_state: EndState,
        user_profile: UserProfile,
        max_cash_top_up: float
    ) -> float:
        """
        Calculate a realistic cash overbid when trading up.
        Returns the overbid amount.
        """
        if end_state.cash_flow >= 0:
            return 0.0
            
        # Get watch attributes
        target_attrs = self.watch_attributes.get_watch_attributes(end_state.watch)
        
        # Base overbid factors
        value_difference = abs(end_state.cash_flow)
        financial_capacity = user_profile.financial_capacity
        risk_tolerance = user_profile.risk_tolerance
        
        # Market condition factors
        competition_factor = self.competition_level
        time_factor = self.time_sensitivity
        market_trend = target_attrs.market_trend
        value_retention = target_attrs.value_retention
        
        # Calculate base overbid percentage (0-20% of value difference)
        base_percentage = (
            0.1 * financial_capacity +     # Financial capacity influence
            0.05 * risk_tolerance +        # Risk tolerance influence
            0.03 * competition_factor +    # Competition influence
            0.02 * time_factor +           # Time sensitivity influence
            0.03 * market_trend +          # Market trend influence
            0.02 * value_retention         # Value retention influence
        )
        
        # Calculate actual overbid amount
        overbid = value_difference * base_percentage
        
        # Ensure overbid doesn't exceed max cash top up
        remaining_capacity = max_cash_top_up - abs(end_state.cash_flow)
        overbid = min(overbid, remaining_capacity)
        
        # Add some randomness (±10%)
        random_factor = 0.9 + 0.2 * np.random.random()
        overbid *= random_factor
        
        return round(overbid, 2)  # Round to 2 decimal places
    
    def make_decision(
        self,
        end_state: EndState,
        user_profile: UserProfile,
        current_watch: str,
        current_value: float,
        max_cash_top_up: float
    ) -> Tuple[bool, float]:
        """
        Make a complete decision for an end state.
        Returns (accepted: bool, overbid: float)
        """
        # Calculate acceptance probability
        prob = self.calculate_acceptance_probability(
            end_state, user_profile, current_watch, current_value
        )
        
        # Make decision
        accepted = np.random.random() < prob
        
        # Calculate overbid if accepted and trading up
        overbid = 0.0
        if accepted and end_state.cash_flow < 0:
            overbid = self.calculate_overbid(
                end_state, user_profile, max_cash_top_up
            )
        
        return accepted, overbid 