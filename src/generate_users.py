"""
User Generation Module
=====================

This module generates synthetic user data for the Chariot Engine trading simulation.
It creates realistic user profiles with watch preferences, value thresholds, and
trading constraints.

Key Features:
------------
- Synthetic user generation
- Watch catalog integration
- Value preference distribution
- Trading constraint generation
- Configurable generation parameters

Example:
--------
>>> users = generate_users(
...     num_users=100,
...     watch_catalog="data/catalog.json",
...     output_path="data/users.csv"
... )
>>> print(f"Generated {len(users)} user profiles")
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple


def generate_users(
    num_users: int,
    watch_catalog: Union[str, Dict],
    output_path: Optional[str] = None,
    value_range: Tuple[float, float] = (100, 10000),
    top_up_factor: float = 0.2,
    seed: Optional[int] = None,
    period: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate a set of users with watch preferences and trading constraints.

    Parameters:
    -----------
    num_users : int
        Number of users to generate
    watch_catalog : Union[str, Dict]
        Path to watch catalog JSON or dictionary
    output_path : Optional[str]
        Path to save generated users
    value_range : Tuple[float, float]
        (min, max) values for watch preferences
    top_up_factor : float
        Maximum cash top-up as fraction of watch value
    seed : Optional[int]
        Random seed for reproducibility
    period : Optional[int]
        Current simulation period

    Returns:
    --------
    pd.DataFrame
        Generated user data
    """
    if seed is not None:
        np.random.seed(seed)

    # Load watch catalog
    if isinstance(watch_catalog, str):
        with open(watch_catalog, 'r') as f:
            catalog = json.load(f)
    else:
        catalog = watch_catalog

    # Generate user data
    users = []
    for i in range(num_users):
        user = _generate_user_profile(
            user_idx=i,
            catalog=catalog,
            value_range=value_range,
            top_up_factor=top_up_factor,
            period=period
        )
        users.append(user)

    # Create DataFrame
    users_df = pd.DataFrame(users)

    # Save to CSV if path provided
    if output_path:
        users_df.to_csv(output_path, index=False)
        print(f"✅ Generated {num_users} users and saved to {output_path}")

    return users_df


def _generate_user_profile(
    user_idx: int,
    catalog: Dict,
    value_range: Tuple[float, float],
    top_up_factor: float = 0.3,  # Increased to 30%
    period: Optional[int] = None
) -> Dict:
    """
    Generate a single user profile.

    Parameters:
    -----------
    user_idx : int
        User index for ID generation
    catalog : Dict
        Watch catalog with values
    value_range : Tuple[float, float]
        Value range for preferences
    top_up_factor : float
        Maximum cash top-up factor
    period : Optional[int]
        Current simulation period

    Returns:
    --------
    Dict
        User profile with:
        - user_id
        - have_watch
        - have_value
        - min_acceptable_item_value
        - max_cash_top_up

    Notes:
    ------
    Profile generation:
    1. Create unique ID
    2. Select random watch with value-based weighting
    3. Calculate value preferences
    4. Set trading constraints
    """
    # Calculate selection weights using a more gradual curve for the $500-$25k range
    values = np.array(list(catalog.values()))
    min_value = min(values)
    max_value = max(values)
    
    # Use a power law distribution with exponent 0.5 for more gradual weighting
    # This makes expensive watches less common but not extremely rare
    normalized_values = (values - min_value) / (max_value - min_value)
    weights = 1 / (normalized_values ** 0.5 + 0.1)  # Add small constant to prevent division by zero
    weights = weights / weights.sum()  # Normalize to probabilities
    
    # Select watch using value-based weights
    watches = list(catalog.keys())
    watch = np.random.choice(watches, p=weights)
    base_value = catalog[watch]
    
    # Add some random variation to value
    value_variation = np.random.uniform(-0.1, 0.1)  # ±10%
    have_value = round(base_value * (1 + value_variation), 2)

    # More flexible trading constraints for 3-way trades
    # Accept up to 30% less in value (was 20%)
    min_acceptable = round(have_value * 0.7, 2)
    
    # Allow up to 40% top-up (was 30%)
    max_top_up = round(have_value * 0.4, 2)

    return {
        'user_id': f"U{period:03d}_{user_idx+1:05d}" if period is not None else f"U000_{user_idx+1:05d}",  # Format: U001_00001
        'have_watch': watch,
        'have_value': have_value,
        'min_acceptable_item_value': min_acceptable,
        'max_cash_top_up': max_top_up
    }


def create_watch_catalog(
    num_watches: int,
    value_range: Tuple[float, float],
    output_path: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict:
    """
    Create a synthetic watch catalog.

    Parameters:
    -----------
    num_watches : int
        Number of watches to generate
    value_range : Tuple[float, float]
        (min, max) values for watches
    output_path : Optional[str]
        Path to save catalog JSON
    seed : Optional[int]
        Random seed for reproducibility

    Returns:
    --------
    Dict
        Watch catalog mapping watch IDs to values

    Notes:
    ------
    Catalog generation:
    1. Generate watch IDs
    2. Assign realistic values
    3. Save to JSON if path provided
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate watch values with log-normal distribution
    min_val, max_val = value_range
    mu = np.log((min_val + max_val) / 2)
    sigma = 0.5
    values = np.random.lognormal(mu, sigma, num_watches)
    
    # Scale values to desired range
    values = np.interp(values, (values.min(), values.max()), value_range)
    
    # Create catalog
    catalog = {
        f"W{i+1:05d}": round(val, 2)
        for i, val in enumerate(values)
    }

    # Save to JSON if path provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        print(f"✅ Generated catalog with {num_watches} watches")

    return catalog


def load_watch_catalog(catalog_path: str) -> Dict:
    """
    Load a watch catalog from a CSV file.

    Parameters:
    -----------
    catalog_path : str
        Path to the watch catalog CSV file

    Returns:
    --------
    Dict
        Watch catalog mapping watch IDs (brand + model) to base prices

    Raises:
    -------
    FileNotFoundError
        If catalog file doesn't exist
    """
    try:
        # Read CSV file
        df = pd.read_csv(catalog_path)
        
        # Create watch ID by combining brand and model
        df['watch_id'] = df['brand'] + ' ' + df['model']
        
        # Convert DataFrame to dictionary
        catalog = df.set_index('watch_id')['base_price'].to_dict()
        
        print(f"✅ Loaded watch catalog with {len(catalog)} watches")
        return catalog
    except FileNotFoundError:
        print(f"❌ Watch catalog not found at {catalog_path}")
        raise
    except Exception as e:
        print(f"❌ Error loading watch catalog: {str(e)}")
        raise


def generate_users_for_period(
    num_users: int,
    catalog: Dict,
    period: int,
    value_range: Tuple[float, float] = (6000, 120000),
    top_up_factor: float = 0.2,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate users for a specific simulation period.

    Parameters:
    -----------
    num_users : int
        Number of users to generate
    catalog : Dict
        Watch catalog dictionary
    period : int
        Current simulation period
    value_range : Tuple[float, float]
        (min, max) values for watch preferences
    top_up_factor : float
        Maximum cash top-up as fraction of watch value
    seed : Optional[int]
        Random seed for reproducibility

    Returns:
    --------
    pd.DataFrame
        Generated user data with period information
    """
    # Generate base users
    users_df = generate_users(
        num_users=num_users,
        watch_catalog=catalog,
        value_range=value_range,
        top_up_factor=top_up_factor,
        seed=seed if seed is None else seed + period,  # Vary seed by period
        period=period
    )
    
    # Add period information
    users_df['period'] = period
    users_df['entry_period'] = period
    
    print(f"✅ Generated {num_users} users for period {period}")
    return users_df


if __name__ == "__main__":
    # Example usage
    CATALOG_PATH = "configs/watch_catalog.json"
    USERS_OUTPUT_PATH = "data/generated_users.csv"
    
    # Create watch catalog
    catalog = create_watch_catalog(
        num_watches=100,
        value_range=(1000, 10000),
        output_path=CATALOG_PATH,
        seed=42
    )
    
    # Generate users
    users_df = generate_users(
        num_users=1000,
        watch_catalog=catalog,
        output_path=USERS_OUTPUT_PATH,
        seed=42
    )

    # In run_multi_period_simulation function
    user_history_tracker = {
        'total_unique_users': set(),  # Track all users that ever entered
        'exited_users': set(),       # Track users that completed trades
        'user_details': {}           # Existing user tracking dict
    }

    # When processing results
    for users in executed['users']:
        users_list = json.loads(users)
        user_history_tracker['total_unique_users'].update(users_list)
        user_history_tracker['exited_users'].update(users_list)

    summary_stats = {
        "total_unique_users": len(user_history_tracker['total_unique_users']),
        "total_exited_users": len(user_history_tracker['exited_users']),
        "users_still_in_system": len(carried_users_df),
        "user_completion_rate": round(
            len(user_history_tracker['exited_users']) / 
            len(user_history_tracker['total_unique_users']) * 100, 2
        )
    }