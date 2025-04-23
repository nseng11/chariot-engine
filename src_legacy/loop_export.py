import pandas as pd
import networkx as nx
import time
import os


def loop_matching_main():
    start = time.time()

    # Resolve the file path to sample_users.csv relative to script location
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, "..", "simulations", "sample_users.csv")

    # Load user data
    df = pd.read_csv(input_path)

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

    # Flatten into individual columns
    expanded_data = []
    singular_keys = {
        'indexes': 'index',
        'users': 'user',
        'watches': 'watch'
    }

    for loop_id_num, loop in enumerate(valid_loops, start=1):
        row = loop.copy()
        row['loop_id'] = f"L{loop_id_num:04d}"

        for key in ['indexes', 'users', 'watches']:
            singular = singular_keys[key]
            for i in range(3):
                col_key = f"{singular}_{i+1}"
                row[col_key] = loop[key][i] if i < len(loop[key]) else None

        for i in range(3):
            giver_idx = loop['indexes'][i] if i < len(loop['indexes']) else None
            receiver_idx = loop['indexes'][(i + 1) % len(loop['indexes'])] if i < len(loop['indexes']) else None
            received_watch = df.iloc[receiver_idx]['have_watch'] if receiver_idx is not None else None
            row[f"received_watch_{i+1}"] = received_watch

        for key in ['values', 'cash_flows']:
            items = loop[key].split(", ")
            singular = 'cash_flow' if key == 'cash_flows' else key[:-1]
            for i in range(3):
                col_key = f"{singular}_{i+1}"
                row[col_key] = float(items[i]) if i < len(items) else None

        try:
            cash_flow_values = [float(val.strip()) for val in loop['cash_flows'].split(', ')]
            value_values = [float(val.strip()) for val in loop['values'].split(', ')]

            abs_fairness = pd.Series(cash_flow_values).std() if len(cash_flow_values) >= 2 else 0.0
            avg_value = sum(value_values) / len(value_values) if value_values else 1
            rel_fairness = abs_fairness / avg_value

        except:
            abs_fairness = None
            rel_fairness = None

        row['loop_fairness_score'] = abs_fairness
        row['relative_fairness_score'] = rel_fairness


        for key in ['indexes', 'users', 'watches', 'values', 'cash_flows']:
            if key in row:
                del row[key]

        expanded_data.append(row)

    # Export results
    output_path = os.path.join(base_dir, "..", "simulations", "matching_results.csv")
    results_df = pd.DataFrame(expanded_data)
    results_df.to_csv(output_path, index=False, encoding='utf-8')
    print("Matching results saved to simulations/matching_results.csv")

    # Summary
    print(f"Found {len(valid_loops)} valid 2- or 3-way trade loops")
    print(f"2-way loops: {count_2way}, 3-way loops: {count_3way}")
    print(f"Total unique users matched: {len(set(str(uid) for loop in valid_loops for uid in loop['users']))}")
    print(f"Avg users per loop: {round(sum(len(loop['users']) for loop in valid_loops) / len(valid_loops), 2) if valid_loops else 0}")
    print(f"Loop matching completed in {round(time.time() - start, 2)} seconds")


if __name__ == "__main__":
    loop_matching_main()