import pandas as pd
import networkx as nx
import time
import os

def loop_matching_main():
    start = time.time()

    # Resolve path safely
    base_dir = os.path.dirname(__file__)
    user_file_path = os.path.join(base_dir, "..", "simulations", "sample_users.csv")
    df = pd.read_csv(user_file_path)

    # Build graph
    G = nx.DiGraph()
    for idx, row in df.iterrows():
        G.add_node(idx, **row)

    for i, giver in df.iterrows():
        for j, receiver in df.iterrows():
            if i == j:
                continue
            if giver['have_watch'] == receiver['have_watch']:
                continue
            if giver['have_value'] < receiver['min_acceptable_item_value']:
                continue
            delta = giver['have_value'] - receiver['have_value']
            if delta > receiver['max_cash_top_up']:
                continue
            G.add_edge(i, j)

    valid_loops = []
    count_2way = 0
    count_3way = 0

    # 2-way loops
    for u, v in G.edges():
        if G.has_edge(v, u) and u < v:
            count_2way += 1
            users_chain = [df.iloc[u]['user_id'], df.iloc[v]['user_id']]
            watches_chain = [df.iloc[u]['have_watch'], df.iloc[v]['have_watch']]
            values_chain = [df.iloc[u]['have_value'], df.iloc[v]['have_value']]
            cash_flows = [round(df.iloc[u]['have_value'] - df.iloc[v]['have_value'], 2),
                          round(df.iloc[v]['have_value'] - df.iloc[u]['have_value'], 2)]
            valid_loops.append({
                'users': users_chain,
                'indexes': [u, v],
                'watches': watches_chain,
                'values': ', '.join([f"{float(v):.2f}" for v in values_chain]),
                'cash_flows': ', '.join([f"{float(c):.2f}" for c in cash_flows]),
                'loop_type': '2-way'
            })

    # 3-way loops
    for a in G.nodes():
        for b in G.successors(a):
            for c in G.successors(b):
                if G.has_edge(c, a) and a < b < c:
                    if len(set([a, b, c])) != 3:
                        continue
                    loop = [a, b, c]
                    is_valid = True
                    users_chain = []
                    watches_chain = []
                    values_chain = []
                    cash_flows = []
                    for i in range(3):
                        giver_idx = loop[i]
                        receiver_idx = loop[(i + 1) % 3]
                        giver = df.iloc[giver_idx]
                        receiver = df.iloc[receiver_idx]
                        if giver['have_value'] < receiver['min_acceptable_item_value']:
                            is_valid = False
                            break
                        delta = giver['have_value'] - receiver['have_value']
                        if delta > receiver['max_cash_top_up']:
                            is_valid = False
                            break
                        users_chain.append(giver['user_id'])
                        watches_chain.append(giver['have_watch'])
                        values_chain.append(round(giver['have_value'], 2))
                        cash_flows.append(round(delta, 2))
                    if is_valid:
                        count_3way += 1
                        valid_loops.append({
                            'users': users_chain,
                            'indexes': loop,
                            'watches': watches_chain,
                            'values': ', '.join([f"{float(v):.2f}" for v in values_chain]),
                            'cash_flows': ', '.join([f"{float(c):.2f}" for c in cash_flows]),
                            'loop_type': '3-way'
                        })

    # Export
    output_path = os.path.join(base_dir, "..", "simulations", "matching_results.csv")
    results_df = pd.DataFrame(valid_loops)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)

    print(f"\n✅ Found {len(valid_loops)} valid 2- or 3-way trade loops:")
    print(f"🔢 Total loops: {len(valid_loops)}")
    print(f"📁 Matching results saved to {output_path}")

if __name__ == "__main__":
    loop_matching_main()