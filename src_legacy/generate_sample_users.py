import pandas as pd
import random
import uuid
import os

# Set up safe file path resolution
base_dir = os.path.dirname(os.path.dirname(__file__))
catalog_path = os.path.join(base_dir, "seed_catalogs_w", "watch_catalog.csv")
output_path = os.path.join(base_dir, "simulations", "sample_users.csv")

# Load the seed catalog
catalog_df = pd.read_csv(catalog_path)
catalog_df["full_name"] = catalog_df["brand"] + " " + catalog_df["model"]
watch_catalog = dict(zip(catalog_df["full_name"], catalog_df["base_price"]))

def generate_price(base, variance=0.05):
    return round(base * random.uniform(1 - variance, 1 + variance), 2)

def generate_user():
    have = random.choice(list(watch_catalog.keys()))
    have_value = generate_price(watch_catalog[have])

    # --- FLOOR: min acceptable item value ---
    if have_value < 5000:
        floor_min = 0.50 * have_value
    elif have_value < 15000:
        floor_min = 0.60 * have_value
    else:
        floor_min = 0.75 * have_value

    floor_max = 1.10 * have_value
    min_acceptable_value = round(random.uniform(floor_min, floor_max), 2)

    # --- CEILING: max cash top-up (must meet or exceed what's required) ---
    required_top_up = max(min_acceptable_value - have_value, 0)

    if have_value < 5000:
        top_up_ceiling = 0.40 * have_value
    elif have_value < 15000:
        top_up_ceiling = 0.25 * have_value
    else:
        top_up_ceiling = 0.15 * have_value

    max_cash_top_up = round(random.uniform(required_top_up, required_top_up + top_up_ceiling), 2)

    return {
        "user_id": str(uuid.uuid4())[:8],
        "have_watch": have,
        "have_value": have_value,
        "min_acceptable_item_value": min_acceptable_value,
        "max_cash_top_up": max_cash_top_up
    }

# Generate 100 sample users
users = [generate_user() for _ in range(100)]
df = pd.DataFrame(users)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_csv(output_path, index=False)

print("Sample users saved to simulations/sample_users.csv")