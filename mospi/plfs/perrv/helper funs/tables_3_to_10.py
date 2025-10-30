import pandas as pd

# Load your CSV
df = pd.read_csv("tables_3_to_10_cols_1_2.csv")

# 🔹 Keep only rows where the first column starts with 'group'
# (case-insensitive match)
filtered_df = df[df.iloc[:, 0].astype(str).str.lower().str.startswith("group")]

# Save filtered result
filtered_df.to_csv("filtered_groups.csv", index=False)

print(f"✅ Filtered rows saved to filtered_groups.csv — kept {len(filtered_df)} rows.")
