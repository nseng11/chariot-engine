"""
Script to inspect price variation and model counts in the watch catalog
"""

import pandas as pd

def main():
    catalog_path = "seed_catalogs_w/watch_catalog.csv"
    df = pd.read_csv(catalog_path)
    print("\nOverall Price Stats:")
    print("-" * 60)
    print(f"Min price: ${df['base_price'].min():,.2f}")
    print(f"Max price: ${df['base_price'].max():,.2f}")
    print(f"Mean price: ${df['base_price'].mean():,.2f}")
    print(f"Std dev: ${df['base_price'].std():,.2f}")
    print(f"Number of brands: {df['brand'].nunique()}")
    print(f"Number of models: {df['model'].nunique()}")
    print(f"Total entries: {len(df)}")
    print()
    print("Brand-Level Price Stats:")
    print("-" * 60)
    brand_stats = df.groupby('brand')['base_price'].agg(['min', 'max', 'mean', 'std', 'count'])
    print(brand_stats)
    print()
    print("Models per Brand:")
    print("-" * 60)
    models_per_brand = df.groupby('brand')['model'].nunique()
    print(models_per_brand)

if __name__ == "__main__":
    main() 