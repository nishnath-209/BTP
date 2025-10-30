import json
import os

# === User input ===
input_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhrv\hhrv_labeled_final.json"  

output_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhrv\hhrv_cleaned.json"

required_keys = {
  "State/Ut Code",
  "District Name",
  "Sector",
  "Household Size",
  "Household Type",
  "Religion",
  "Social Group",
  "Household'S Usual Consumer Expenditure In A Month(Rs.)",
  "Sub-sample wise Multiplier",
  "Ns count for sector x stratum x substratum x sub-sample",
  "Ns count for sector x stratum x substratum",
  "Survey Code",
  "Response Code",
  "Count of contributing State x Sector x Stratum x SubStratum in 4 Quarters"
}



# Read JSON file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ensure the file is a list of dicts
if isinstance(data, dict):
    data = [data]

# Filter each record to only keep required keys
filtered_data = [
    {key: record[key] for key in required_keys if key in record}
    for record in data
]

# Write filtered data to new JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=4, ensure_ascii=False)

print(f"✅ Filtered file saved as: {output_file}")
