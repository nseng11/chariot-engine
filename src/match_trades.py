from typing import List, Set, Dict
import pandas as pd
import numpy as np
import random

def find_matches(users_df: pd.DataFrame) -> List[List[str]]:
    """
    Find valid trading matches between users based on watch values.
    
    Args:
        users_df: DataFrame containing user data with columns:
            - user_id: Unique identifier for each user
            - have_watch: ID of watch they have
            - have_value: Value of their watch
            - min_acceptable_item_value: Minimum value they'll accept
    
    Returns:
        List of matches, where each match is a list of user IDs that can trade
    """
    matches = []
    available_users = set(users_df['user_id'].unique())
    
    while len(available_users) >= 2:
        # Try to find a match
        match = find_next_match(users_df[users_df['user_id'].isin(available_users)])
        
        if not match:
            break
            
        matches.append(match)
        available_users -= set(match)
    
    return matches

def find_next_match(users_df: pd.DataFrame) -> List[str]:
    """Find the next valid match among available users."""
    # Try to find both 2-way and 3-way trades
    matches = []
    
    # Find 2-way trades
    for idx1, user1 in users_df.iterrows():
        for idx2, user2 in users_df.iterrows():
            if user1['user_id'] >= user2['user_id']:
                continue
                
            if is_valid_two_way_trade(user1, user2):
                matches.append(([user1['user_id'], user2['user_id']], "2-way"))
    
    # Find 3-way trades
    for idx1, user1 in users_df.iterrows():
        for idx2, user2 in users_df.iterrows():
            if user1['user_id'] >= user2['user_id']:
                continue
                
            for idx3, user3 in users_df.iterrows():
                if user2['user_id'] >= user3['user_id'] or user1['user_id'] >= user3['user_id']:
                    continue
                    
                if is_valid_three_way_trade(user1, user2, user3):
                    matches.append(([user1['user_id'], user2['user_id'], user3['user_id']], "3-way"))
    
    # If no matches found, return empty list
    if not matches:
        return []
    
    # Randomly select a match to avoid bias
    selected_match = random.choice(matches)
    return selected_match[0]

def is_valid_two_way_trade(user1: pd.Series, user2: pd.Series) -> bool:
    """Check if two users can trade watches based on values."""
    # Check if values are within acceptable ranges for both users
    user1_accepts = user2['have_value'] >= user1['min_acceptable_item_value']
    user2_accepts = user1['have_value'] >= user2['min_acceptable_item_value']
    
    return user1_accepts and user2_accepts

def is_valid_three_way_trade(user1: pd.Series, user2: pd.Series, user3: pd.Series) -> bool:
    """Check if three users can trade watches in a cycle based on values."""
    # Check if all values are acceptable in the cycle
    # user1 -> user2 -> user3 -> user1
    cycle1 = (user2['have_value'] >= user1['min_acceptable_item_value'] and
              user3['have_value'] >= user2['min_acceptable_item_value'] and
              user1['have_value'] >= user3['min_acceptable_item_value'])
              
    # Or the reverse cycle: user1 -> user3 -> user2 -> user1
    cycle2 = (user3['have_value'] >= user1['min_acceptable_item_value'] and
              user1['have_value'] >= user2['min_acceptable_item_value'] and
              user2['have_value'] >= user3['min_acceptable_item_value'])
    
    return cycle1 or cycle2 