import json
import os
import pandas as pd

# Paths
filename = "perrv_labeled.json"
data_folder = "C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/perrv"
reformatted_filename = "perrv_labeled_renamed.json"

initial_file_path = os.path.join(data_folder, filename)
col_names_path = os.path.join(data_folder, "column_labels_from_web.json")
district_codes_path = "C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/District_codes_PLFS_Panel_4_202324_2024.xlsx"
destination_path = os.path.join(data_folder, reformatted_filename)

# Load column label mapping
with open(col_names_path, "r", encoding="utf-8") as f:
    column_mapping = json.load(f)

# Load district code mappings
df = pd.read_excel(district_codes_path, skiprows=3)  # Skip first 2 header rows
df.columns = df.columns.str.strip()
df = df[["State Name", "DISTRICT CODE", "DISTRICT NAME"]]
df["DISTRICT CODE"] = df["DISTRICT CODE"].astype(str).str.zfill(2)  # Ensure leading 0s

# Create dictionary: {(State Name, District Code) : District Name}
district_mapping = {
    (row["State Name"].strip().upper(), row["DISTRICT CODE"].strip()): row["DISTRICT NAME"].strip()
    for _, row in df.iterrows()
}


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
