import json
import os

filename = "perrv_labeled_renamed.json"
data_folder = "C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/perrv"
final_filename = "perrv_labeled_final.json"

initial_file_path = os.path.join(data_folder, filename)
destination_path = os.path.join(data_folder, final_filename)


with open(initial_file_path, "r", encoding="utf-8") as infile:
    raw_data = json.load(infile)

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\district_mapping.json", "r", encoding="utf-8") as f:
    district_mapping = json.load(f)

decoded_data = []

for row in raw_data:
    decoded_row = row.copy()
    
    state_name = row.get("State/Ut Code", "").upper()
    district_code = row.get("District Name", "").zfill(2)

    decoded_row["District Name"] = district_mapping.get(state_name, {}).get(district_code, "UNKNOWN_DISTRICT")

    decoded_data.append(decoded_row)

# Write the cleaned file
with open(destination_path, "w", encoding="utf-8") as outfile:
    json.dump(decoded_data, outfile, indent=4, ensure_ascii=False)

print(f"✅ Succesfully reformatted {len(raw_data)} rows from {filename} to {len(decoded_data)} rows and saved in {final_filename}")
