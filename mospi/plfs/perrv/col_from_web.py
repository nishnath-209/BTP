from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

# Launch browser
driver = webdriver.Chrome()
driver.get("https://microdata.gov.in/NADA/index.php/catalog/213/data-dictionary/F8?file_name=perrv")

destination_folder = "C:/Users/nishn/OneDrive/Desktop/BTP/Data BTP/Data/mospi/plfs/perrv"
output_path = os.path.join(destination_folder, "column_labels_from_web.json")

input("➡️ Press Enter after the page is fully loaded...")

wait = WebDriverWait(driver, 10)

column_labels = {}

# Find container (for future scoping if needed)
main_block = driver.find_element(By.XPATH, "//div[contains(@class, 'container-fluid table-variable-list data-dictionary')]")

# Get all variable rows
rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'row') and contains(@class, 'var-row')]")

i=0
for row in rows:
    try:
        # Scroll to the row and click it
        driver.execute_script("arguments[0].scrollIntoView(true);", row)
        time.sleep(0.5)
        row.click()

        # ✅ Wait until the heading in expanded panel appears
        panel = main_block.find_element(By.XPATH, "//div[contains(@class, 'row var-info-panel') and contains(@style, 'display: block')]")
        
        time.sleep(1)
        heading_elem = panel.find_element(By.XPATH, ".//div[contains(@class, 'variable-container')]//h2")
        heading_text = heading_elem.text.strip()
        print(heading_text)

        if '(' in heading_text and ')' in heading_text:
            label = heading_text.split('(')[0].strip()
            var_name = heading_text.split('(')[-1].split(')')[0].strip()
        else:
            continue  # skip if malformed

        column_labels[var_name] = label


        time.sleep(0.5)

    except Exception as e:
        print(f"⚠️ Skipped row due to error: {e}")
        continue
    i=i+1

# Save mappings
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(column_labels, f, indent=2, ensure_ascii=False)


print(f"✅ Extracted {len(column_labels)} column labels.")
driver.quit()
