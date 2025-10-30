from PyPDF2 import PdfReader
import re
import os
import json
print("Current working directory:", os.getcwd())

script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, "NSS.pdf")

# Path to your PDF file
pdf_path = os.path.join(os.getcwd(), "BTP","mospi", "plfs", "hhrv", "NSS.pdf")


# Read all text from PDF
reader = PdfReader(pdf_path)
all_text = ""
for page in reader.pages:
    txt = page.extract_text()
    if txt:
        all_text += txt + "\n"

# Regex to capture region code + description
# Example match: "281 Coastal Northern"
pattern = re.compile(r'(\d{3})\s+([A-Za-z\-\&\. ]+?)\s+(?=[A-Za-z]+\s*\(\d+\))')

matches = pattern.findall(all_text)

# Build mapping dictionary
mapping = {code.strip(): desc.strip() for code, desc in matches}

print(mapping)

# Print first 20 to verify
json_path = os.path.join(script_dir, "nss_regions.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=4, ensure_ascii=False)

print(f"Mapping saved to {json_path}")
