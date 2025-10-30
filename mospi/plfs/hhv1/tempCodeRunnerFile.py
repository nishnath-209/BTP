import json
import os

# === User input ===
input_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhv1\hhv1_labeled_final.json"  

output_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhv1\hhv1_cleaned.json"

required_keys = {
"State/Ut Code",
"District Code",
"Household Size",
"Household Type",
"Religion",
"Social Group",
"Household's usual consumer Expenditure in A Month for purposes out of Goods and Services(Rs.)",
"Imputed value of usual consumption in a month out of Home Grown stock (Rs.)",
"Imputed value of usual consumption in a Month from wages in kind:free collection: gifts etc. (Rs.)",
"Household's Annual Expenditure on purchase of items like clothing: footwear etc.(Rs.)",
"Household's Annual Expenditure on purchase of durables like Bedstead: TV: fridge etc.(Rs.)",
"Household'S Usual Consumer Expenditure In A Month (Rs.)"
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
