import pandas as pd
import json

# Load Excel file (use raw string for Windows path)
df = pd.read_excel(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\District_codes_PLFS_Panel_4_202324_2024.xlsx", skiprows=3)

# Standardize column names
df.columns = [col.strip().upper() for col in df.columns]

# Set correct column names
state_col = "STATE NAME"
code_col = "DISTRICT CODE"
name_col = "DISTRICT NAME"

# Build nested dictionary mapping
district_mapping = {}

for _, row in df.iterrows():
    state = row[state_col].strip().upper()
    district_code = str(row[code_col]).zfill(2)
    district_name = row[name_col].strip()

    if state not in district_mapping:
        district_mapping[state] = {}

    district_mapping[state][district_code] = district_name

# Save to JSON
with open("district_mapping.json", "w", encoding="utf-8") as f:
    json.dump(district_mapping, f, ensure_ascii=False, indent=2)
