"""
Script to display watch attributes from the catalog
"""

import pandas as pd
from alternatives.watch_attributes import WatchAttributeManager
import pprint

def main():
    # Initialize the watch attribute manager with your catalog
    catalog_path = "seed_catalogs_w/watch_catalog.csv"
    manager = WatchAttributeManager(catalog_path)
    
    # Load the catalog to get watch names
    catalog_df = pd.read_csv(catalog_path)
    
    # Get unique brands
    print("\nBrand Level Attributes (from brand_scores):")
    print("-" * 80)
    for brand, scores in manager.brand_scores.items():
        prestige = scores.get(('prestige_score', ''), 0.5)
        popularity = scores.get(('popularity_score', ''), 0.5)
        print(f"{brand:20} Prestige: {prestige:.3f}  Popularity: {popularity:.3f}")
    
    # Diagnostic: print brand_scores keys and catalog brands
    print("\n[DIAGNOSTIC] Keys in manager.brand_scores:")
    print(list(manager.brand_scores.keys()))
    print("\n[DIAGNOSTIC] Brands in catalog_df:")
    print(list(catalog_df['brand'].unique()))
    
    # Print the full brand_scores dictionary
    print("\n[DIAGNOSTIC] Full manager.brand_scores dictionary:")
    pprint.pprint(manager.brand_scores)
    
    # Get some sample watches
    print("\nWatch Level Attributes:")
    print("-" * 80)
    print(f"{'Watch':40} {'Value Retention':15} {'Market Trend':15} {'Trading Frequency':15}")
    print("-" * 80)
    
    # Show attributes for a few watches from different brands
    sample_watches = [
        "Rolex Submariner Date",
        "Patek Philippe Nautilus",
        "Omega Speedmaster",
        "Grand Seiko Snowflake",
        "Tudor Black Bay"
    ]
    
    for watch in sample_watches:
        attrs = manager.get_watch_attributes(watch)
        print(f"{watch:40} {attrs.value_retention:15.3f} {attrs.market_trend:15.3f} {attrs.trading_frequency:15.3f}")

if __name__ == "__main__":
    main() 