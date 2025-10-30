import camelot
import pandas as pd

file_path = "occu_codes.pdf"

# 🔹 Specify page range here (e.g., "3-10" or "3,5,7")
page_range = "46-250"

# Extract tables
tables = camelot.read_pdf(file_path, pages=page_range, flavor='stream')  # or 'lattice' if table has visible lines

# Combine all extracted tables into one DataFrame
df_all = pd.concat([t.df for t in tables], ignore_index=True)

df_filtered = df_all.iloc[:, :3]

# Save to CSV
df_filtered.to_csv("tables_3_to_10_cols_1_2.csv", index=False)
print(f"✅ Extracted pages {page_range} — only first and second columns saved to tables_3_to_10_cols_1_2.csv")
