"""
Watch Catalog Generator
=====================

This script generates an expanded watch catalog with 100 models,
including variations, special editions, and additional brands.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class WatchModel:
    brand: str
    model: str
    base_value: float
    base_trading_freq: float
    base_value_retention: float
    base_market_trend: float
    variations: List[str]
    special_editions: List[str]

# Define base models with their characteristics
BASE_MODELS = [
    # Rolex
    WatchModel("Rolex", "Submariner", 12500, 0.85, 0.95, 0.90,
              ["Date", "No Date", "Hulk", "Kermit", "Starbucks"],
              ["50th Anniversary", "James Cameron", "Smurf"]),
    WatchModel("Rolex", "Daytona", 35000, 0.75, 0.98, 0.95,
              ["Steel", "Gold", "Platinum", "Ceramic"],
              ["Paul Newman", "John Player Special", "Zenith"]),
    WatchModel("Rolex", "GMT-Master II", 15000, 0.80, 0.92, 0.88,
              ["Pepsi", "Batman", "Root Beer", "Sprite"],
              ["50th Anniversary", "Meteorite"]),
    
    # Patek Philippe
    WatchModel("Patek Philippe", "Nautilus", 85000, 0.60, 0.99, 0.98,
              ["5711", "5712", "5726", "5990"],
              ["Tiffany", "40th Anniversary"]),
    WatchModel("Patek Philippe", "Aquanaut", 45000, 0.70, 0.97, 0.95,
              ["5167", "5168", "5968"],
              ["Travel Time", "Chronograph"]),
    
    # Audemars Piguet
    WatchModel("Audemars Piguet", "Royal Oak", 55000, 0.65, 0.96, 0.92,
              ["Jumbo", "Chronograph", "Perpetual Calendar"],
              ["50th Anniversary", "Concept"]),
    WatchModel("Audemars Piguet", "Royal Oak Offshore", 35000, 0.70, 0.94, 0.90,
              ["Diver", "Chronograph", "Tourbillon"],
              ["Muhammad Ali", "Safari"]),
    
    # Omega
    WatchModel("Omega", "Speedmaster", 7500, 0.90, 0.88, 0.85,
              ["Professional", "Reduced", "Racing", "Dark Side"],
              ["Moonwatch", "Snoopy", "Apollo 11"]),
    WatchModel("Omega", "Seamaster", 5500, 0.85, 0.85, 0.82,
              ["300M", "Planet Ocean", "Aqua Terra"],
              ["007", "America's Cup"]),
    
    # Additional brands and models...
    WatchModel("Vacheron Constantin", "Overseas", 25000, 0.65, 0.93, 0.85,
              ["Chronograph", "Dual Time", "World Time"],
              ["Everest", "Panda"]),
    WatchModel("A. Lange & Söhne", "Lange 1", 45000, 0.55, 0.96, 0.90,
              ["Moon Phase", "Tourbillon", "Perpetual Calendar"],
              ["25th Anniversary", "Grand Lange 1"]),
    WatchModel("Hublot", "Big Bang", 15000, 0.75, 0.82, 0.80,
              ["Unico", "Fusion", "Integral"],
              ["Ferrari", "Spirit of Big Bang"]),
    WatchModel("Panerai", "Luminor", 8000, 0.80, 0.85, 0.78,
              ["Base", "Marina", "Submersible"],
              ["Bronzo", "Destro"]),
    WatchModel("Zenith", "El Primero", 7000, 0.85, 0.80, 0.75,
              ["Chronomaster", "Defy", "Pilot"],
              ["A384", "Revival"]),
    WatchModel("Grand Seiko", "Spring Drive", 6000, 0.75, 0.83, 0.80,
              ["Snowflake", "Peacock", "Mt. Iwate"],
              ["Kodo", "Elegance"])
]

def generate_watch_catalog(output_path: str, num_models: int = 100):
    """Generate an expanded watch catalog"""
    watches = []
    
    # Generate variations and special editions
    for base_model in BASE_MODELS:
        # Add base model
        watches.append({
            'brand': base_model.brand,
            'model': f"{base_model.model} {base_model.variations[0]}",
            'value': base_model.base_value,
            'trading_frequency': base_model.base_trading_freq,
            'value_retention': base_model.base_value_retention,
            'market_trend': base_model.base_market_trend,
            'condition': 'excellent',
            'production_year': np.random.randint(2019, 2023),
            'limited_edition': False
        })
        
        # Add variations
        for variation in base_model.variations[1:]:
            value_multiplier = np.random.uniform(0.9, 1.1)
            watches.append({
                'brand': base_model.brand,
                'model': f"{base_model.model} {variation}",
                'value': base_model.base_value * value_multiplier,
                'trading_frequency': base_model.base_trading_freq * np.random.uniform(0.9, 1.1),
                'value_retention': base_model.base_value_retention * np.random.uniform(0.95, 1.05),
                'market_trend': base_model.base_market_trend * np.random.uniform(0.95, 1.05),
                'condition': 'excellent',
                'production_year': np.random.randint(2019, 2023),
                'limited_edition': False
            })
        
        # Add special editions
        for edition in base_model.special_editions:
            value_multiplier = np.random.uniform(1.2, 1.5)
            watches.append({
                'brand': base_model.brand,
                'model': f"{base_model.model} {edition}",
                'value': base_model.base_value * value_multiplier,
                'trading_frequency': base_model.base_trading_freq * 0.8,  # Less frequent trading
                'value_retention': min(1.0, base_model.base_value_retention * 1.1),  # Better retention
                'market_trend': min(1.0, base_model.base_market_trend * 1.1),  # Stronger trend
                'condition': 'excellent',
                'production_year': np.random.randint(2019, 2023),
                'limited_edition': True
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(watches)
    
    # Ensure we have exactly num_models
    if len(df) > num_models:
        df = df.sample(n=num_models, random_state=42)
    elif len(df) < num_models:
        # Generate additional models by adding small variations
        additional = []
        while len(additional) + len(df) < num_models:
            base = df.sample(n=1).iloc[0]
            additional.append({
                'brand': base['brand'],
                'model': f"{base['model']} Special",
                'value': base['value'] * np.random.uniform(0.95, 1.05),
                'trading_frequency': base['trading_frequency'] * np.random.uniform(0.9, 1.1),
                'value_retention': base['value_retention'] * np.random.uniform(0.95, 1.05),
                'market_trend': base['market_trend'] * np.random.uniform(0.95, 1.05),
                'condition': 'excellent',
                'production_year': np.random.randint(2019, 2023),
                'limited_edition': np.random.random() < 0.3
            })
        df = pd.concat([df, pd.DataFrame(additional)], ignore_index=True)
    
    # Sort by brand and model
    df = df.sort_values(['brand', 'model'])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Generated watch catalog with {len(df)} models at {output_path}")

if __name__ == "__main__":
    generate_watch_catalog("data/watch_catalog.csv", num_models=100) 