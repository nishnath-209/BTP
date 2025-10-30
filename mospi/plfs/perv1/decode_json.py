import json
import os
import ijson
from decimal import Decimal

filename = "perv1_labeled_renamed.json"
data_folder = r"C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/perv1"
final_filename = "perv1_labeled_final.json"

initial_file_path = os.path.join(data_folder, filename)
destination_path = os.path.join(data_folder, final_filename)

# --- Load mapping files (safe to load fully) ---
with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\district_mapping.json", "r", encoding="utf-8") as f:
    district_mapping = json.load(f)

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\nss_regions.json", "r", encoding="utf-8") as f:
    nss_mappings = json.load(f)

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\industry_codes.json", "r", encoding="utf-8") as f:
    nic_2digit_mapping = json.load(f)

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\occupation_codes.json", "r", encoding="utf-8") as f:
    occupation_codes_mapping = json.load(f)

# --- Helper for Decimal conversion ---
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

# --- Stream & decode ---
with open(initial_file_path, "r", encoding="utf-8") as infile, \
     open(destination_path, "w", encoding="utf-8") as outfile:

    outfile.write("[")
    first = True
    count = 0

    for row in ijson.items(infile, "item"):
        decoded_row = {}
        state_name = row.get("State/Ut Code", "").upper()

        for k, v in row.items():
            if k == "District Code":
                district_code = str(v).zfill(2)
                district_name = district_mapping.get(state_name, {}).get(district_code, "UNKNOWN_DISTRICT")
                decoded_row["District Name"] = district_name

            elif k == "NSS-Region":
                nss_code = str(v).zfill(2)
                nss_region = nss_mappings.get(nss_code, {})
                decoded_row["NSS-Region"] = nss_region

            elif ("Industry Code (NIC) for activity" in k) or ("Industry Code (CWS)" in k):
                code = str(v).zfill(2)
                decoded_row[k] = nic_2digit_mapping.get(code, None)

            elif "Occupation Code (CWS)" in k:
                code = str(v).zfill(2)
                decoded_row[k] = occupation_codes_mapping.get(code, None)

            elif k == "Quarter":
                quarter_map = {"Q1": "Quarter 1", "Q2": "Quarter 2", "Q3": "Quarter 3", "Q4": "Quarter 4"}
                decoded_row["Quarter"] = quarter_map.get(v, v)

            elif k == "Visit":
                visit_map = {"V1": "Visit 1", "V2": "Visit 2", "V3": "Visit 3", "V4": "Visit 4"}
                decoded_row["Visit"] = visit_map.get(v, v)

            elif k == "FSU":
                decoded_row["First Stage Unit (FSU)"] = v

            elif k == "File Identification":
                decoded_row[k] = "First Visit Person level 7"

            elif row.get(k) == "":
                decoded_row[k] = None
            else:
                decoded_row[k] = v

        # Convert Decimal → float
        decoded_row = convert_decimal(decoded_row)

        # Stream write safely
        if not first:
            outfile.write(",\n")
        json.dump(decoded_row, outfile, ensure_ascii=False, indent=4, default=str)
        first = False

        count += 1
        if count % 10000 == 0:
            print(f"Processed {count:,} rows...")

    outfile.write("]")

print(f"✅ Successfully processed {count:,} rows from {filename} → {final_filename}")
