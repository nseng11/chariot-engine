"""
User Preferences Module
=====================

This module manages user preferences for end states, including:
- Accepting or rejecting end states
- Placing cash overbids
- Tracking user preferences over time

Key Concepts:
------------
1. End State Preference: A user's preference for a specific end state:
   - Whether they accept or reject it
   - Any cash overbid they're willing to make
   - The maximum cash they can add

2. Cash Overbid: Additional cash a user is willing to add to make a trade
   more attractive to other users.

3. Preference History: Track of all preferences a user has expressed.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from end_state_tracking import EndState

@dataclass
class UserPreference:
    """Represents a user's preference for an end state"""
    end_state: EndState
    is_accepted: bool
    cash_overbid: float
    max_cash_top_up: float

class UserPreferenceManager:
    def __init__(self):
        self.preferences: Dict[str, Dict[EndState, UserPreference]] = {}
    
    def set_preference(self, user_id: str, end_state: EndState, 
                      is_accepted: bool, cash_overbid: float, 
                      max_cash_top_up: float):
        """Set a user's preference for an end state"""
        if user_id not in self.preferences:
            self.preferences[user_id] = {}
        
        self.preferences[user_id][end_state] = UserPreference(
            end_state=end_state,
            is_accepted=is_accepted,
            cash_overbid=cash_overbid,
            max_cash_top_up=max_cash_top_up
        )
    
    def get_user_preferences(self, user_id: str) -> Dict[EndState, UserPreference]:
        """Get all preferences for a user"""
        return self.preferences.get(user_id, {})
    
    def get_accepted_end_states(self, user_id: str) -> List[EndState]:
        """Get all end states that a user has accepted"""
        user_prefs = self.get_user_preferences(user_id)
        return [end_state for end_state, pref in user_prefs.items() 
                if pref.is_accepted]
    
    def get_all_preferences(self, user_id: str) -> List[UserPreference]:
        """Get all preferences for a user"""
        return list(self.get_user_preferences(user_id).values())
    
    def clear_preferences(self, user_id: str):
        """Clear all preferences for a user"""
        if user_id in self.preferences:
            del self.preferences[user_id]
    
    def has_preference(self, user_id: str, end_state: EndState) -> bool:
        """Check if a user has a preference for an end state"""
        return (user_id in self.preferences and 
                end_state in self.preferences[user_id])
    
    def get_preference(self, user_id: str, end_state: EndState) -> Optional[UserPreference]:
        """Get a user's preference for a specific end state"""
        if self.has_preference(user_id, end_state):
            return self.preferences[user_id][end_state]
        return None

    def get_rejected_end_states(self, user_id: str) -> List[EndState]:
        """Get all end states rejected by a user"""
        if user_id not in self.preferences:
            return []
        return [p.end_state for p in self.preferences[user_id] if not p.is_accepted]
    
    def validate_cash_overbid(self, user_id: str, end_state: EndState, 
                            cash_overbid: float) -> bool:
        """Validate if a cash overbid is within user's limits"""
        if user_id not in self.preferences:
            return False
            
        for pref in self.preferences[user_id]:
            if pref.end_state == end_state:
                return cash_overbid <= pref.max_cash_top_up
        return False 