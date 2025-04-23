# Chariot Engine - Technical Architecture (v1)

# -----------------------------
# 1. DATA INGESTION LAYER
# -----------------------------
# - Source: Manual input (Google Form / Airtable) or file upload (CSV/JSON)
# - Transforms data into unified format

# Fields:
# - User ID
# - Have: [Item ID, Value]
# - Want: [Item ID, Value]
# - Max Cash Delta Willing to Pay/Receive (optional)

# -----------------------------
# 2. DATA STORE
# -----------------------------
# - Airtable, Firebase Firestore, or Postgres DB
# - Stores user inventory, trade preferences, item metadata

# Tables:
# - Users
# - Items (with average market values)
# - Trade Requests (have/want pairs)

# -----------------------------
# 3. MATCHING ENGINE (CORE)
# -----------------------------
# - Language: Python
# - Libraries: networkx, pandas, numpy

# Pseudocode Scaffold:

import pandas as pd
import networkx as nx

# Load updated user data
df = pd.read_csv("simulations/sample_users.csv")

# Step 1: Build graph with user index IDs instead of watch names
G = nx.DiGraph()
for idx, row in df.iterrows():
    G.add_node(idx, **row)

# Step 2: Add possible edges (user i could give their watch to user j)
for i, giver in df.iterrows():
    for j, receiver in df.iterrows():
        if i == j:
            continue

        # Receiver must receive a watch ≥ their floor
        if giver['have_value'] < receiver['min_acceptable_item_value']:
            continue

        # Receiver must not have to pay more than they’re willing
        delta = giver['have_value'] - receiver['have_value']
        if delta > receiver['max_cash_top_up']:
            continue

        # Add edge: i gives to j
        G.add_edge(i, j)

# Step 3: Find 2- and 3-way cycles
cycles = list(nx.simple_cycles(G))
valid_loops = []

for cycle in cycles:
    if len(cycle) not in [2, 3]:
        continue

    valid = True
    cash_flows = []
    user_chain = []

    for i in range(len(cycle)):
        giver_idx = cycle[i]
        receiver_idx = cycle[(i + 1) % len(cycle)]

        giver = df.iloc[giver_idx]
        receiver = df.iloc[receiver_idx]

        # Check that receiver's min floor is met
        if giver['have_value'] < receiver['min_acceptable_item_value']:
            valid = False
            break

        # Check that cash delta is acceptable
        cash_delta = giver['have_value'] - receiver['have_value']
        if cash_delta > receiver['max_cash_top_up']:
            valid = False
            break

        user_chain.append(giver['user_id'])
        cash_flows.append(cash_delta)

    if valid:
        valid_loops.append({
            'users': user_chain,
            'user_indexes': cycle,
            'cash_flows': cash_flows
        })

# Step 4: Output
print(f"✅ Found {len(valid_loops)} valid 2- or 3-way trade loops.\n")
for loop in valid_loops:
    print("Users:", loop['users'])
    print("Indexes:", loop['user_indexes'])
    print("Cash Flows:", loop['cash_flows'])
    print("---")

# -----------------------------
# 4. LOOP APPROVAL + TRACKING
# -----------------------------
# - Notify matched users (via email or app)
# - Users can accept or decline proposed trade
# - Approved loops get locked and moved to logistics layer

# -----------------------------
# 5. OPTIONAL TRUST + ROUTING LAYER
# -----------------------------
# - TradeKit shipment initiation
# - Masked shipping label generation (Stamps.com, Shippo, EasyPost)
# - Optional: escrow trigger, ID verification, insurance

# -----------------------------
# 6. FRONT-END (LATER)
# -----------------------------
# - Streamlit or React interface for testing
# - Basic dashboard to display trade loop suggestions + accept/decline options

# -----------------------------
# 7. ANALYTICS + LOGGING
# -----------------------------
# - % Users matched
# - Avg loop length
# - Avg cash delta per loop
# - Loop acceptance rate
# - Inventory turnover rate

# -----------------------------
# 8. EXPORT / LICENSING
# -----------------------------
# - Engine API wrapper (Flask/FastAPI)
# - Can be licensed to other verticals: cards, watches, art, sneakers, etc.
