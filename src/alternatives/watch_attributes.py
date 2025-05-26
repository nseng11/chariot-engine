"""
Watch Attributes Module
=====================

This module handles watch attributes and their scoring, including:
- Brand prestige
- Model popularity
- Market trends
- Value retention
- Trading frequency

All attributes are loaded from the watch catalog and can be updated dynamically.
"""

import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class WatchAttributes:
    """Represents attributes and scores for a watch"""
    brand: str
    model: str
    prestige_score: float
    popularity_score: float
    value_retention: float
    trading_frequency: float
    market_trend: float

class WatchAttributeManager:
    def __init__(self, catalog_path: str):
        """
        Initialize the manager with watch catalog data
        
        Args:
            catalog_path: Path to the watch catalog CSV file
        """
        self.catalog_df = pd.read_csv(catalog_path)
        self._initialize_scores()
        
    def _initialize_scores(self):
        """Initialize scores based on catalog data"""
        # Group by brand to calculate brand-level metrics
        brand_stats = self.catalog_df.groupby('brand').agg({
            'base_price': ['mean', 'std', 'count']
        }).reset_index()
        
        # Calculate brand prestige scores (0-1)
        max_value = brand_stats[('base_price', 'mean')].max()
        min_value = brand_stats[('base_price', 'mean')].min()
        brand_stats['prestige_score'] = (brand_stats[('base_price', 'mean')] - min_value) / (max_value - min_value)

        # Debug printout for mean prices and prestige scores
        print("\n[DEBUG] Brand Mean Prices and Prestige Scores:")
        print(f"Min mean price: {min_value}")
        print(f"Max mean price: {max_value}")
        for idx, row in brand_stats.iterrows():
            mean_price = float(row[('base_price', 'mean')])
            prestige = float(row['prestige_score'])
            print(f"Brand: {row['brand']}, Mean Price: {mean_price:.2f}, Prestige: {prestige:.3f}")
        
        # Calculate brand popularity scores (0-1)
        max_count = brand_stats[('base_price', 'count')].max()
        min_count = brand_stats[('base_price', 'count')].min()
        brand_stats['popularity_score'] = (brand_stats[('base_price', 'count')] - min_count) / (max_count - min_count)
        
        # Store brand-level scores
        self.brand_scores = brand_stats.set_index('brand')[['prestige_score', 'popularity_score']].to_dict('index')
        
        # Calculate model-level scores
        model_stats = self.catalog_df.groupby(['brand', 'model']).agg({
            'base_price': ['mean', 'std']
        }).reset_index()
        
        # Store model-level scores with default values for missing metrics
        self.model_scores = {}
        for _, row in model_stats.iterrows():
            key = f"{row['brand']} {row['model']}"
            base_price = row[('base_price', 'mean')]
            max_price = model_stats[('base_price', 'mean')].max()
            
            # Calculate value retention based on price stability (std/mean)
            std_price = row[('base_price', 'std')]
            value_retention = 1 - (std_price / base_price if base_price > 0 else 0)
            
            # Calculate trading frequency based on price tier
            trading_frequency = 0.5 + (base_price / max_price) * 0.5
            
            # Calculate market trend based on price position
            market_trend = 0.5 + (base_price / max_price) * 0.5
            
            self.model_scores[key] = {
                'value_retention': max(0, min(1, value_retention)),
                'trading_frequency': max(0, min(1, trading_frequency)),
                'market_trend': max(0, min(1, market_trend))
            }
    
    def get_brand_prestige(self, brand: str) -> float:
        """Get prestige score for a brand"""
        return self.brand_scores.get(brand, {}).get('prestige_score', 0.5)
    
    def get_brand_popularity(self, brand: str) -> float:
        """Get popularity score for a brand"""
        return self.brand_scores.get(brand, {}).get('popularity_score', 0.5)
    
    def get_model_attributes(self, brand: str, model: str) -> Dict[str, float]:
        """Get all attributes for a specific model"""
        key = f"{brand} {model}"
        attrs = self.model_scores.get(key, None)
        if attrs is not None:
            # If any attribute is missing or not meaningful, use brand-level as fallback
            for attr in ['value_retention', 'trading_frequency', 'market_trend']:
                if attrs[attr] is None or pd.isna(attrs[attr]) or attrs[attr] == 0.5:
                    # Use brand-level prestige for value_retention, popularity for trading_frequency, and prestige for market_trend
                    if attr == 'value_retention':
                        attrs[attr] = self.get_brand_prestige(brand)
                    elif attr == 'trading_frequency':
                        attrs[attr] = self.get_brand_popularity(brand)
                    elif attr == 'market_trend':
                        attrs[attr] = self.get_brand_prestige(brand)
            return attrs
        # Fallback: all brand-level
        return {
            'value_retention': self.get_brand_prestige(brand),
            'trading_frequency': self.get_brand_popularity(brand),
            'market_trend': self.get_brand_prestige(brand)
        }
    
    def get_watch_attributes(self, watch: str) -> WatchAttributes:
        """Get all attributes for a watch"""
        brand = watch.split()[0]
        model = ' '.join(watch.split()[1:])
        
        return WatchAttributes(
            brand=brand,
            model=model,
            prestige_score=self.get_brand_prestige(brand),
            popularity_score=self.get_brand_popularity(brand),
            **self.get_model_attributes(brand, model)
        )
    
    def update_scores(self, new_catalog_path: Optional[str] = None):
        """
        Update scores based on new catalog data
        
        Args:
            new_catalog_path: Optional path to new catalog data
        """
        if new_catalog_path:
            self.catalog_df = pd.read_csv(new_catalog_path)
        self._initialize_scores() 