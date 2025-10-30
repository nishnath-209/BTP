import ijson
import json
import os
from decimal import Decimal

# === Input & Output paths ===
input_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perrv\perrv_labeled_final.json"  

output_file = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perrv\perrv_cleaned.json"


# === Keys to keep ===
required_keys = {
    "State/Ut Code",
    "Gender",
    "Age",
    "Sector",
    "Marital Status",
    "Occupation Code (CWS)",
    "General Educaion Level",
    "Technical Educaion Level",
    "No. of years in Formal Education",
    "Status of Current Attendance in Educational Institution",
    "Status Code for activity 1 on 7 th day",
    "Industry Code (NIC) for activity 1 on 7 th day",
    "wage earning for activity 1 on 7 th day",
    "total hours actually worked on 7th day",
    "Earnings For Regular Salarid/Wage Activity",
    "Earnings For Self Employed",
    "Sub-sample wise Multiplier",
    "Ns count for sector x stratum x substratum x sub-sample",
    "Ns count for sector x stratum x substratum",
    "Count of contributing State x Sector x Stratum x SubStratum in 4 Quarters"
}


# === Rename mapping ===
rename_map = {
    "Status Code for activity 1 on 7 th day": "Status Code",
    "Industry Code (NIC) for activity 1 on 7 th day": "Industry Code (NIC)",
    "wage earning for activity 1 on 7 th day": "wage earning for the activity",
    "total hours actually worked on 7th day": "total hours actually worked on a day",
    "Occupation Code (CWS)" : "Occupation Code (NCO)"
}

# === Handle Decimal safely ===
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
        renamed = {rename_map.get(k, k): v for k, v in filtered.items()}

        if not first:
            fout.write(",\n")
        # write this record as pretty JSON (each field on its own line)
        fout.write(json.dumps(renamed, ensure_ascii=False, indent=4, default=safe_json_default))
        first = False
    fout.write("\n]")

print(f"✅ Cleaned and formatted JSON saved to: {output_file}")
