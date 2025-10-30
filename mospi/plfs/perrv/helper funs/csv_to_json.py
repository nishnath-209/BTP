import pandas as pd
import json

# Load CSV safely
df = pd.read_csv("filtered_groups.csv", engine="python", on_bad_lines='skip')

# Select first (key) and second (value) columns (index 1 & 2 in zero-indexed)
df_selected = df.iloc[:, 1:3]  # adjust if your first column is actually at 0

# Create a dictionary: key = first column, value = second column
kv_dict = dict(zip(df_selected.iloc[:,0], df_selected.iloc[:,1]))

# Save to JSON
with open("final.json", "w", encoding="utf-8") as f:
    json.dump(kv_dict, f, ensure_ascii=False, indent=2)

print("✅ JSON saved as key:value pairs in final.json")
