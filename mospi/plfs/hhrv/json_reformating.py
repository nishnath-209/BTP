import json

# Load mapping
with open("column_labels_from_web.json", "r", encoding="utf-8") as f:
    column_mapping = json.load(f)

# Load original labeled data
with open("hhrv_labeled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Apply renaming
renamed_data = []
for row in data:
    renamed_row = {}
    for key, value in row.items():
        new_key = column_mapping.get(key, key)  # Use mapped name if available
        renamed_row[new_key] = value
    renamed_data.append(renamed_row)

# Save renamed output
with open("hhrv_labeled_renamed.json", "w", encoding="utf-8") as f:
    json.dump(renamed_data, f, indent=2, ensure_ascii=False)

print(f"✅ Saved renamed JSON with {len(renamed_data)} rows to hhrv_labeled_renamed.json")
