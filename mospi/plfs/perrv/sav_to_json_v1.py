import pyreadstat
import json
import os

# === Step 1: Find the first .sav file in the current working directory ===
current_dir = os.getcwd()  # safer than __file__ for IDEs
sav_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.sav')]

if not sav_files:
    raise FileNotFoundError("No .sav file found in the current directory.")

sav_file = sav_files[0]  # pick the first one found
print(f"📂 Found SAV file: {sav_file}")

# === Step 2: Read the .sav file with value labels ===
df, meta = pyreadstat.read_sav(sav_file, apply_value_formats=True)  # updated for no warnings

# === Step 3: Save to JSON ===
json_filename = os.path.splitext(sav_file)[0] + "_labeled.json"
df.to_json(json_filename, orient="records", force_ascii=False, indent=2)
print(f"✅ Saved as: {json_filename}")
