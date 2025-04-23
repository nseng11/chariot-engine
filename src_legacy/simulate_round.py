import pandas as pd
import random
from collections import deque
import networkx as nx
import os
import json

# Determine correct simulation file path
base_dir = os.path.dirname(os.path.dirname(__file__))
sim_dir = os.path.join(base_dir, "simulations")
file_path = os.path.join(sim_dir, "sample_users.csv")

# Load user data
original_users_df = pd.read_csv(file_path)

# Track user status and FIFO queue
user_queue = deque(original_users_df['user_id'].tolist())
user_status = {uid: 'available' for uid in original_users_df['user_id']}

executed_loops = []
rejected_loops = []
matched_loops = []
round_counter = 1

while True:
    matched_this_round = False
    round_exec_count = 0
    round_reject_count = 0

    available_users = [u for u in user_status if user_status[u] == 'available']
    current_users_df = original_users_df[original_users_df['user_id'].isin(available_users)].reset_index(drop=True)

    # Build graph
    G = nx.DiGraph()
    for idx, row in current_users_df.iterrows():
        G.add_node(idx, **row)

    for i, giver in current_users_df.iterrows():
        for j, receiver in current_users_df.iterrows():
            if i == j or giver['have_watch'] == receiver['have_watch']:
                continue
            if giver['have_value'] < receiver['min_acceptable_item_value']:
                continue
            delta = giver['have_value'] - receiver['have_value']
            if delta > receiver['max_cash_top_up']:
                continue
            G.add_edge(i, j)

    valid_loops = []
    for u, v in G.edges():
        if G.has_edge(v, u) and u < v:
            users = [current_users_df.iloc[u]['user_id'], current_users_df.iloc[v]['user_id']]
            watches = [current_users_df.iloc[u]['have_watch'], current_users_df.iloc[v]['have_watch']]
            values = [current_users_df.iloc[u]['have_value'], current_users_df.iloc[v]['have_value']]
            cash_flows = [values[0] - values[1], values[1] - values[0]]
            received_watches = [watches[1], watches[0]]
            fairness = pd.Series(cash_flows).std()
            total_value = sum(values)
            rel_fairness = fairness / (total_value / len(values)) if total_value else None
            loop = {
                'loop_type': '2-way',
                'users': users,
                'initial_watches': watches,
                'received_watches': received_watches,
                'values': values,
                'cash_flows': cash_flows,
                'total_value_moved': total_value,
                'fairness_score': fairness,
                'relative_fairness_score': rel_fairness
            }
            valid_loops.append(loop)
            matched_loops.append(loop)

    for a in G.nodes():
        for b in G.successors(a):
            for c in G.successors(b):
                if G.has_edge(c, a) and a < b < c:
                    if len(set([a, b, c])) != 3:
                        continue
                    users = [current_users_df.iloc[a]['user_id'], current_users_df.iloc[b]['user_id'], current_users_df.iloc[c]['user_id']]
                    watches = [current_users_df.iloc[a]['have_watch'], current_users_df.iloc[b]['have_watch'], current_users_df.iloc[c]['have_watch']]
                    values = [current_users_df.iloc[a]['have_value'], current_users_df.iloc[b]['have_value'], current_users_df.iloc[c]['have_value']]
                    received_watches = [watches[1], watches[2], watches[0]]
                    cash_flows = [values[0] - values[1], values[1] - values[2], values[2] - values[0]]
                    fairness = pd.Series(cash_flows).std()
                    total_value = sum(values)
                    rel_fairness = fairness / (total_value / len(values)) if total_value else None
                    loop = {
                        'loop_type': '3-way',
                        'users': users,
                        'initial_watches': watches,
                        'received_watches': received_watches,
                        'values': values,
                        'cash_flows': cash_flows,
                        'total_value_moved': total_value,
                        'fairness_score': fairness,
                        'relative_fairness_score': rel_fairness
                    }
                    valid_loops.append(loop)
                    matched_loops.append(loop)

    # Prioritize fairer loops
    valid_loops.sort(key=lambda x: x.get('relative_fairness_score', float('inf')))

    if not valid_loops:
        print("\nNo more loops can be formed with available users.")
        break

    # Compute quartiles for relative fairness scores
    fairness_values = [loop['relative_fairness_score'] for loop in valid_loops if loop['relative_fairness_score'] is not None]
    if fairness_values:
        q1, q2, q3 = pd.Series(fairness_values).quantile([0.25, 0.50, 0.75])

    for loop in valid_loops:
        loop_users = loop['users']
        if all(user_status[u] == 'available' for u in loop_users):
            fairness = loop.get('relative_fairness_score', None)

            if fairness is None or not fairness_values:
                weights = [0.5, 0.5]  # fallback
            elif fairness <= q1:
                weights = [0.8, 0.2]
            elif fairness <= q2:
                weights = [0.6, 0.4]
            elif fairness <= q3:
                weights = [0.4, 0.6]
            else:
                weights = [0.2, 0.8]

            decisions = {u: random.choices(['accept', 'decline'], weights=weights)[0] for u in loop_users}

            loop_copy = loop.copy()
            loop_copy['users'] = json.dumps(loop_users)

            if all(decision == 'accept' for decision in decisions.values()):
                loop_copy['round_executed'] = round_counter
                executed_loops.append(loop_copy)
                for u in loop_users:
                    user_status[u] = 'matched'
                    if u in user_queue:
                        user_queue.remove(u)
                matched_this_round = True
                round_exec_count += 1
            else:
                loop_copy['round_rejected'] = round_counter
                for u, decision in decisions.items():
                    if decision == 'decline':
                        user_status[u] = 'declined'
                        if u in user_queue:
                            user_queue.remove(u)
                            user_queue.append(u)
                rejected_loops.append(loop_copy)
                matched_this_round = True
                round_reject_count += 1

    print(f"\nRound {round_counter} summary:")
    print(f"  Executed loops: {round_exec_count}")
    print(f"  Rejected loops: {round_reject_count}")

    round_counter += 1

# Save results
executed_df = pd.DataFrame(executed_loops)
rejected_df = pd.DataFrame(rejected_loops)
matched_df = pd.DataFrame(matched_loops)

executed_df.to_csv(os.path.join(sim_dir, "executed_loops.csv"), index=False)
rejected_df.to_csv(os.path.join(sim_dir, "rejected_loops.csv"), index=False)
matched_df.to_csv(os.path.join(sim_dir, "all_matched_loops.csv"), index=False)

available_users = [u for u, status in user_status.items() if status == 'available']
declined_users = [u for u, status in user_status.items() if status == 'declined']

print("\nSimulation complete")
print(f"Executed loops: {len(executed_df)}")
print(f"Rejected loops: {len(rejected_df)}")
print(f"Users still in queue: {len(available_users) + len(declined_users)}")
print(f"Still available but unmatched: {len(available_users)}")
print(f"Users who declined and remain in queue: {len(declined_users)}")