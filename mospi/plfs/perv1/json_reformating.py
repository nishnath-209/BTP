import json
import os
import pandas as pd

# Paths
filename = "perv1_labeled.json"
data_folder = "C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/perv1"
reformatted_filename = "perv1_labeled_renamed.json"

initial_file_path = os.path.join(data_folder, filename)
col_names_path = os.path.join(data_folder, "column_labels_from_web.json")
destination_path = os.path.join(data_folder, reformatted_filename)

# Load column label mapping
with open(col_names_path, "r", encoding="utf-8") as f:
    column_mapping = json.load(f)

# Load original labeled JSON
with open(initial_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

renamed_data = []
for row in data:
    renamed_row = {}

    for key, value in row.items():
        new_key = column_mapping.get(key, key)  # Use mapped name if available
        renamed_row[new_key] = value
    renamed_data.append(renamed_row)


# Save output
with open(destination_path, "w", encoding="utf-8") as f:
    json.dump(renamed_data, f, indent=2, ensure_ascii=False)

print(f"✅ Succesfully reformatted {len(data)} rows from {filename} to {len(renamed_data)} rows and saved in {reformatted_filename}")


