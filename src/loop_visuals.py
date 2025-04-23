import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter


def analyze_watch_frequencies(df, label, output_prefix, plot_dir):
    from collections import Counter
    import matplotlib.pyplot as plt
    import os

    os.makedirs(plot_dir, exist_ok=True)
    df = df.copy()
    df = df[df['relative_fairness_score'].notna()]

    if df['relative_fairness_score'].nunique() < 4:
        # Not enough unique values to create quartiles — plot overall stats
        watch_cols = [f"watch_{i}" for i in range(1, 4)]
        all_watches = pd.concat([df[c] for c in watch_cols if c in df], ignore_index=True).dropna()
        top_watches = pd.Series(Counter(all_watches)).sort_values(ascending=False).head(10)

        plt.figure()
        top_watches.plot(kind='barh')
        plt.title(f"Top 10 {label} Watches (Aggregate View)")
        plt.xlabel("Count")
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, f"{output_prefix}_watches_aggregate.png"))
        plt.close()
    else:
        df['fairness_quartile'] = pd.qcut(df['relative_fairness_score'], 4, labels=["Q1 (Most Fair)", "Q2", "Q3", "Q4 (Least Fair)"])
        for quartile in df['fairness_quartile'].unique():
            sub_df = df[df['fairness_quartile'] == quartile]
            watch_cols = [f"watch_{i}" for i in range(1, 4)]
            all_watches = pd.concat([sub_df[c] for c in watch_cols if c in sub_df], ignore_index=True).dropna()
            top_watches = pd.Series(Counter(all_watches)).sort_values(ascending=False).head(10)

            plt.figure()
            top_watches.plot(kind='barh')
            plt.title(f"Top 10 {label} Watches\n{quartile}")
            plt.xlabel("Count")
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir, f"{output_prefix}_watches_{quartile.replace(' ', '_')}.png"))
            plt.close()