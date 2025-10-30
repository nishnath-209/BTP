import ijson
import json
import os
from decimal import Decimal

# === User input ===
input_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perv1\perv1_labeled_final.json"  

output_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perv1\perv1_cleaned.json"

required_keys = {
    "State/Ut Code",
    "District Name",
    "Gender",
    "Age",
    "Sector",
    "Marital Status",
    "General Educaion Level",
    "Technical Educaion Level",
    "No. of years in Formal Education",
    "Whether received any Vocational/Technical Training",
    "Status Code",
    "Industry Code (NIC)",
    "Occupation Code (NCO)",
    "Earnings For Regular Salaried/Wage Activity",
    "Earnings For Self Employed",
    "Sub-sample wise Multiplier",
    "Ns count for sector x stratum x substratum x sub-sample",
    "Ns count for sector x stratum x substratum",
    "Count of contributing State x Sector x Stratum x SubStratum in 4 Quarters"
}

per_required = [
                
                'Occupation Code (NCO)', 'Occupation Code (CWS)',
                ]

# Read JSON file
def safe_json_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# === Stream processing with pretty printing ===
with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8") as fout:
    fout.write("[\n")
    first = True
    for record in ijson.items(fin, "item"):
        filtered = {k: v for k, v in record.items() if k in required_keys}
        # renamed = {rename_map.get(k, k): v for k, v in filtered.items()}

        if not first:
            fout.write(",\n")
        # write this record as pretty JSON (each field on its own line)
        fout.write(json.dumps(filtered, ensure_ascii=False, indent=4, default=safe_json_default))
        first = False
    fout.write("\n]")

print(f"✅ Cleaned and formatted JSON saved to: {output_file}")
