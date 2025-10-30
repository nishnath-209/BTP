import json
import os

filename = "hhv1_labeled_renamed.json"
data_folder = "C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/hhv1"
final_filename = "hhv1_labeled_final.json"

initial_file_path = os.path.join(data_folder, filename)
destination_path = os.path.join(data_folder, final_filename)


with open(initial_file_path, "r", encoding="utf-8") as infile:
    raw_data = json.load(infile)

household_type = {
    "rural": {
        "1": "self-employed in agriculture",
        "2": "self-employed in non-agriculture",
        "3": "regular wage/salary earning",
        "4": "casual labour in agriculture",
        "5": "casual labour in non-agriculture",
        "9": "others"
    },
    "urban": {
        "1": "self-employed",
        "2": "regular wage/salary earning",
        "3": "casual labour",
        "9": "others"
    }
}


with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\district_mapping.json", "r", encoding="utf-8") as f:
    district_mapping = json.load(f)

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\nss_regions.json", "r", encoding="utf-8") as f:
    nss_mappings = json.load(f)


decoded_data = []

for row in raw_data:
    decoded_row = {}
    state_name = row.get("State/Ut Code", "").upper()
    for k, v in row.items():
        if k == "District Code":
            district_code = str(v).zfill(2)
            district_name = district_mapping.get(state_name, {}).get(district_code, "UNKNOWN_DISTRICT")
            decoded_row["District Name"] = district_name
        elif k == "NSS-Region":
            nss_code = str(v).zfill(2)
            nss_region = nss_mappings.get(nss_code,{})
            if nss_region == {}:
                print("undetedted",nss_code)
            decoded_row["NSS-Region"] = nss_region
        elif k == "Household Type":
            decoded_row["Household Type"] = household_type.get(row.get("Sector", ""), {}).get(row.get("Household Type", ""), "others")
        elif k == "Quarter":
            quarter_map = {
                "Q1": "Quarter 1",
                "Q2": "Quarter 2",
                "Q3": "Quarter 3",
                "Q4": "Quarter 4"
            }
            decoded_row["Quarter"] = quarter_map.get(v, v)
        elif k == "Visit":
            visit_map = {
                "V1": "Visit 1",
                "V2": "Visit 2",
                "V3": "Visit 3",
                "V4": "Visit 4"
            }
            decoded_row["Visit"] = visit_map.get(v, v)
        elif k == "FSU":
            decoded_row["First Stage Unit(FSU):"] = v
        elif k == "File Identification":
            decoded_row[k] = "First Visit Household 7"
        else:
            decoded_row[k] = v
    decoded_data.append(decoded_row)
    # break

# Write the cleaned file
with open(destination_path, "w", encoding="utf-8") as outfile:
    json.dump(decoded_data, outfile, indent=4, ensure_ascii=False)

print(f"✅ Succesfully reformatted {len(raw_data)} rows from {filename} to {len(decoded_data)} rows and saved in {final_filename}")
