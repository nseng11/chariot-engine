import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter
import os
import sys

# Ensure UTF-8 encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

# Resolve base path
base_dir = os.path.dirname(__file__)
sim_dir = os.path.join(base_dir, "..", "simulations")

# Find latest run folder with matching_results.csv
runs = [f for f in os.listdir(sim_dir) if f.startswith("run_")]
runs.sort(reverse=True)
latest_results_path = None
latest_plot_dir = None
for r in runs:
    candidate = os.path.join(sim_dir, r, "matching_results.csv")
    if os.path.exists(candidate):
        latest_results_path = candidate
        latest_plot_dir = os.path.join(sim_dir, r, "plots")
        break

if latest_results_path is None:
    raise FileNotFoundError("No matching_results.csv found in simulations folder.")

# Create plot directory if needed
os.makedirs(latest_plot_dir, exist_ok=True)

# Load matched loop data
df = pd.read_csv(latest_results_path)

# Compute fairness
cash_cols = ['cash_flow_1', 'cash_flow_2', 'cash_flow_3']
def compute_fairness(row):
    cash_flows = [row.get(c) for c in cash_cols if pd.notna(row.get(c))]
    return pd.Series({
        "cash_flow_stddev": pd.Series(cash_flows).std(),
        "total_cash_flow": sum(abs(v) for v in cash_flows)
    })
df[['fairness_score', 'total_cash_flow']] = df.apply(compute_fairness, axis=1)

# 1. Loop Type Breakdown
plt.figure()
df['loop_type'].value_counts().plot(kind='pie', autopct='%1.1f%%', title="2-way vs 3-way Loops")
plt.ylabel("")
plt.tight_layout()
plt.savefig(os.path.join(latest_plot_dir, "loop_type_pie.png"))
plt.close()

# 2. Cash Flow Distribution
plt.figure()
all_cash = pd.concat([df[c] for c in cash_cols], ignore_index=True).dropna()
plt.hist(all_cash, bins=30)
plt.title("Distribution of Cash Flow Adjustments")
plt.xlabel("Cash Delta")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(os.path.join(latest_plot_dir, "cash_flow_hist.png"))
plt.close()

# 3. Watch Popularity
plt.figure()
watch_cols = ['watch_1', 'watch_2', 'watch_3']
all_watches = pd.concat([df[c] for c in watch_cols], ignore_index=True).dropna()
watch_counts = all_watches.value_counts().head(10)
watch_counts.plot(kind='barh', title="Top 10 Most Traded Watches")
plt.xlabel("Count")
plt.tight_layout()
plt.savefig(os.path.join(latest_plot_dir, "watch_popularity.png"))
plt.close()

# 4. User Match Frequency
plt.figure()
user_cols = ['user_1', 'user_2', 'user_3']
all_users = pd.concat([df[c] for c in user_cols], ignore_index=True).dropna()
user_counts = pd.Series(Counter(all_users)).sort_values(ascending=False).head(20)
user_counts.plot(kind='barh', title="Top 20 Matched Users")
plt.xlabel("Number of Appearances")
plt.tight_layout()
plt.savefig(os.path.join(latest_plot_dir, "user_match_freq.png"))
plt.close()

# 5. Loop Network
plt.figure(figsize=(12, 10))
G = nx.DiGraph()
for _, row in df.iterrows():
    u1, u2, u3 = row.get("user_1"), row.get("user_2"), row.get("user_3")
    if u1 and u2: G.add_edge(u1, u2)
    if u2 and u3: G.add_edge(u2, u3)
    if u3 and u1: G.add_edge(u3, u1)
top_users = set(user_counts.head(50).index)
G_sub = G.subgraph(top_users)
nx.draw_networkx(G_sub, with_labels=True, node_color='lightblue', edge_color='gray', node_size=1000, font_size=10)
plt.title("Trade Loop Network (Top 50 Users)")
plt.tight_layout()
plt.savefig(os.path.join(latest_plot_dir, "loop_network.png"))
plt.close()

# 6. Fairness vs Total Value Moved
plt.figure(figsize=(10, 6))
df['total_value_moved'] = df[['value_1', 'value_2', 'value_3']].sum(axis=1, skipna=True)
def grade_value_moved(val):
    if val <= 1000: return "Great"
    elif val <= 2000: return "Fair"
    elif val <= 3000: return "Acceptable"
    return "Needs Review"
df['value_grade'] = df['total_value_moved'].apply(grade_value_moved)
plt.scatter(df['loop_fairness_score'], df['total_value_moved'], alpha=0.7)
plt.title("Fairness vs. Total Value Moved per Loop")
plt.xlabel("Loop Fairness Score (std of cash flows)")
plt.ylabel("Total Value Moved ($)")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(latest_plot_dir, "fairness_vs_value.png"))
plt.close()