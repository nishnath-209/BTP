import os
import time
import pyperclip
import requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager


# def download_pdfs_from_page(driver, wait, page_num):
#     """Download all PDFs from the current page."""
#     downloaded = []
#     failed = 0

#     copy_buttons = driver.find_elements(By.CSS_SELECTOR, 'i[aria-label="Copy URL"]')

#     for idx, icon in enumerate(tqdm(copy_buttons, desc=f"Page {page_num}", unit="file"), start=1):
#         try:
#             driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", icon)
#             time.sleep(0.3)
#             icon.find_element(By.XPATH, "./ancestor::button").click()
#             time.sleep(0.3)

#             url = pyperclip.paste().strip()
#             if not url or not url.startswith("http"):
#                 failed += 1
#                 continue

#             response = requests.get(url, timeout=30)
#             response.raise_for_status()
#             filename = os.path.join("pdfs", f"page{page_num}_file{idx}.pdf")
#             with open(filename, "wb") as f:
#                 f.write(response.content)
#             downloaded.append(filename)

#         except Exception:
#             failed += 1
#         time.sleep(0.5)

#     print(f"✅ Page {page_num} done: {len(downloaded)} downloaded, {failed} failed.")
#     return len(downloaded), failed

import random

curr_qno = 420

def download_pdfs_from_page(driver, wait, page_num):
    """Download all PDFs from the current page with retries and checks."""
    downloaded = []
    failed = 0

    copy_buttons = driver.find_elements(By.CSS_SELECTOR, 'i[aria-label="Copy URL"]')
    curr_qno = 420

    for idx, icon in enumerate(tqdm(copy_buttons, desc=f"Page {page_num}", unit="file"), start=1):
        success = False

        for attempt in range(3):  # Retry clicking and copying
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", icon)
                time.sleep(0.4)

                icon.find_element(By.XPATH, "./ancestor::button").click()
                time.sleep(0.5)  # let clipboard update

                url = pyperclip.paste().strip()
                if not url.startswith("http"):
                    time.sleep(0.5)
                    continue  # retry click

                # Download the file
                for req_try in range(2):  # retry HTTP once
                    try:
                        response = requests.get(url, timeout=30)
                        response.raise_for_status()

                        # Verify PDF content
                        if not response.content.startswith(b"%PDF"):
                            time.sleep(1)
                            continue

                        filename = os.path.join("pdfs", f"page{page_num}_file{idx}.pdf")
                        with open(filename, "wb") as f:
                            f.write(response.content)
                        downloaded.append(filename)
                        success = True
                        # curr_qno -= 1
                        break
                    except Exception:
                        time.sleep(2)

                if success:
                    break  # out of click retry loop
            except Exception:
                time.sleep(1)

        if not success:
            failed += 1

        # Avoid getting blocked
        time.sleep(random.uniform(0.6, 1.4))

    print(f"✅ Page {page_num} done: {len(downloaded)} downloaded, {failed} failed.")
    return len(downloaded), failed



def main():
    os.makedirs("pdfs", exist_ok=True)

    # options = Options()
    # options.add_argument("--user-data-dir=" + r"C:\Temp\selenium_profile")
    # options.add_argument("--no-first-run")
    # options.add_argument("--no-default-browser-check")


    driver = webdriver.Chrome()

    driver.get("https://sansad.in/ls/questions/questions-and-answers")

    input("➡️ Press Enter after the page is fully loaded...")
    
    wait = WebDriverWait(driver, 20)

    page_num = 16
    total_downloaded = 0
    total_failed = 0

    try:
        while True:
            # Wait for page to load
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'i[aria-label="Copy URL"]')))

            d, f = download_pdfs_from_page(driver, wait, page_num)
            total_downloaded += d
            total_failed += f

            # if f > 0:
            #     break

            # Find next button
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Go to next page"]')
                next_class = next_button.get_attribute("class")
                is_disabled = "Mui-disabled" in next_class or next_button.get_attribute("disabled") is not None

                if is_disabled:
                    print("\n🚫 Reached the last page. Stopping.")
                    break

                driver.execute_script("arguments[0].scrollIntoView({behavior: 'center'});", next_button)
                time.sleep(1)
                next_button.click()
                time.sleep(5)
                page_num += 1

                # if page_num > 10:
                #     break

            except TimeoutException:
                print("\n⚠️ Next button not found. Exiting.")
                break

    finally:
        print(f"\n✅ All done: {total_downloaded} PDFs downloaded, {total_failed} failed across {page_num} pages.")
        driver.quit()


if __name__ == "__main__":
    main()
