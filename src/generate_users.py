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
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic user data for trading simulation.

    Parameters:
    -----------
    num_users : int
        Number of users to generate
    watch_catalog : Union[str, Dict]
        Path to watch catalog JSON or catalog dictionary
    output_path : Optional[str]
        Path to save generated users CSV
    value_range : Tuple[float, float]
        (min, max) values for watch preferences
    top_up_factor : float
        Maximum cash top-up as fraction of watch value
    seed : Optional[int]
        Random seed for reproducibility

    Returns:
    --------
    pd.DataFrame
        Generated user data with columns:
        - user_id: Unique identifier
        - have_watch: Currently owned watch
        - have_value: Current watch value
        - min_acceptable_value: Minimum acceptable trade value
        - max_cash_top_up: Maximum cash willing to add

    Notes:
    ------
    Generation process:
    1. Load/validate watch catalog
    2. Generate user IDs
    3. Assign watches and values
    4. Calculate trading constraints
    5. Save to CSV if output_path provided
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
        # Generate user profile
        user = _generate_user_profile(
            user_idx=i,
            catalog=catalog,
            value_range=value_range,
            top_up_factor=top_up_factor
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
    top_up_factor: float = 0.3  # Increased to 30%
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
    2. Select random watch
    3. Calculate value preferences
    4. Set trading constraints
    """
    # Select random watch and value
    watch = np.random.choice(list(catalog.keys()))
    base_value = catalog[watch]
    
    # Add some random variation to value
    value_variation = np.random.uniform(-0.1, 0.1)  # ±10%
    have_value = round(base_value * (1 + value_variation), 2)

    # More flexible trading constraints
    min_acceptable = round(have_value * 0.8, 2)  # Accept up to 20% less
    max_top_up = round(have_value * top_up_factor, 2)  # Up to 30% top-up

    return {
        'user_id': f"U{user_idx+1:05d}",
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
        seed=seed if seed is None else seed + period  # Vary seed by period
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