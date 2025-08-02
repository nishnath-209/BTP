import pyreadstat
import json

# === Step 1: Read the .sav file with value labels ===
df, meta = pyreadstat.read_sav("hhrv.sav", apply_value_formats=True)

# Now df contains readable labels (e.g., 'Urban', 'Rural' instead of 1, 2)

# === Step 2: Save to JSON ===
df.to_json("hhrv_labeled.json", orient="records", force_ascii=False, indent=2)
print("✅ Saved as: hhrv_labeled.json")

