import csv
import json

csv_file = "microdata.csv"
json_file = "column_labels_from_web.json"

data = {}
with open(csv_file, mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:
            data[row[0]] = row[1]

with open(json_file, mode="w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print("CSV converted to key:value JSON successfully!")