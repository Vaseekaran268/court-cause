import os 
import time
import datetime
import base64
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dateutil import parser as dateparser
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ----------------- Config -----------------
ECOURTS_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=999af70e3228e4c73736b14e53143cc8215edf44df7868a06331996cdf179d97#"
CHROME_DRIVER_PATH = None
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ----------------- Helpers -----------------
def save_captcha_image(driver, save_path="captcha.png"):
    try:
        captcha_img = driver.find_element(By.XPATH, "//img[contains(@src,'captcha') or contains(@id,'imgCaptcha') or @alt='Captcha']")
        src = captcha_img.get_attribute("src")
        if src and src.startswith("data:"):
            captcha_img.screenshot(save_path)
            return save_path
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(src, headers=headers, cookies=cookies, stream=True, timeout=15)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return save_path
    except Exception as e:
        print("❌ Captcha image not found:", e)
    return None


def download_file(url, dst_folder=DOWNLOAD_DIR):
    try:
        os.makedirs(dst_folder, exist_ok=True)
        local_name = os.path.join(dst_folder, os.path.basename(urlparse(url).path) or "file.pdf")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_name, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_name
    except Exception as e:
        print("❌ Download failed:", e)
        return None


def parse_date_nullable(text):
    try:
        return dateparser.parse(text, dayfirst=True).date()
    except Exception:
        return None


def save_fullpage_pdf(driver, output_path):
    """Capture the full currently loaded page as a PDF file."""
    try:
        result = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})
        data = base64.b64decode(result['data'])
        Path(output_path).write_bytes(data)
        print(f"✅ Saved full cause list page as PDF: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save page as PDF: {e}")


def extract_case_details(driver):
    """Extract key case details including correct 16-digit CNR Number."""
    soup = BeautifulSoup(driver.page_source, "html.parser")

    details = {
        "CNR Number": None,
        "Case Type": None,
        "Court Number and Judge": None,
        "Filing Number": None,
        "Registration Number": None,
    }

    text = soup.get_text(" ", strip=True)

    # --- Extract correct CNR Number ---
    cnr_match = re.search(r'\b([A-Z0-9]{16})\s*\(Note the CNR number', text, re.IGNORECASE)
    if cnr_match:
        details["CNR Number"] = cnr_match.group(1).strip()
    else:
        fallback = re.search(r'\b[A-Z0-9]{16}\b', text)
        if fallback:
            details["CNR Number"] = fallback.group(0).strip()

    # --- Extract other details ---
    for key in [k for k in details.keys() if k != "CNR Number"]:
        pattern = re.compile(rf"{key}[:\-\s]*([A-Za-z0-9\/\.\-\s]+)", re.IGNORECASE)
        m = pattern.search(text)
        if m:
            details[key] = m.group(1).strip()

    return details


def extract_cases_from_soup(soup_obj):
    cases = []
    table = soup_obj.find("table")
    rows = table.find_all("tr") if table else soup_obj.select(".cause-list li")
    h = soup_obj.find(["h1", "h2", "h3"])
    court_name = h.get_text(strip=True) if h else "Unknown Court"

    DATE_LABEL_REGEX = re.compile(
        r"(Next\s+Hearing\s+Date|Next\s+Date|Next\s+Hearing|NextDate)[:\-\s]*",
        flags=re.IGNORECASE,
    )

    for tr in rows:
        cols = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if not cols:
            txt = tr.get_text(" ", strip=True)
            if not txt:
                continue
            cols = [txt]

        serial = cols[0] if cols else ""
        row_text = tr.get_text(" ", strip=True)
        next_hearing_date = None

        m = DATE_LABEL_REGEX.search(row_text)
        if m:
            after = row_text[m.end():].strip()
            token = re.findall(r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}", after)
            if token:
                next_hearing_date = parse_date_nullable(token[0])

        if not next_hearing_date:
            token = re.findall(r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}", row_text)
            if token and "Next" in row_text:
                next_hearing_date = parse_date_nullable(token[0])

        cases.append({
            "serial": serial.strip(),
            "cols": cols,
            "court_name": court_name,
            "next_hearing_date": next_hearing_date,
        })
    return cases


# ----------------- Main Scraper -----------------
def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(CHROME_DRIVER_PATH, options=options) if CHROME_DRIVER_PATH else webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    driver.get(ECOURTS_URL)
    print("🌐 Loaded:", ECOURTS_URL)

    input("\n👉 Select State, District, Court Complex & Cause List Date.\nThen press Enter to continue...")

    captcha_file = save_captcha_image(driver)
    if captcha_file:
        print(f"🧩 Captcha saved to: {os.path.abspath(captcha_file)}")
        try:
            if os.name == "nt":
                os.startfile(os.path.abspath(captcha_file))
        except Exception:
            pass
    captcha_value = input("🔐 Enter captcha shown in image: ").strip()

    try:
        captcha_input = driver.find_element(By.XPATH, "//input[contains(@id,'captcha') or contains(@name,'captcha')]")
        captcha_input.clear()
        captcha_input.send_keys(captcha_value)
    except Exception:
        print("⚠️ Could not auto-fill captcha input. Please ensure it's entered manually.")

    for btn_text in ["Civil", "Criminal"]:
        try:
            btn = driver.find_element(By.XPATH, f"//button[contains(.,'{btn_text}') or //input[@value='{btn_text}']]")
            btn.click()
            break
        except Exception:
            continue

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    all_cases = []
    page_index = 1

    while True:
        print(f"\n📄 Parsing page {page_index} ...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cases = extract_cases_from_soup(soup)
        all_cases.extend(cases)

        try:
            next_btn = driver.find_element(By.LINK_TEXT, "Next")
            if next_btn.is_enabled():
                next_btn.click()
                page_index += 1
                time.sleep(1.5)
                continue
        except:
            try:
                next_btn = driver.find_element(By.XPATH, "//a[contains(@class,'next') or contains(@aria-label,'Next')]")
                next_btn.click()
                page_index += 1
                time.sleep(1.5)
                continue
            except:
                break
        break

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    matches = []
    print("\n--- 📅 Cases with Next Hearing Date = today or tomorrow ---")
    for c in all_cases:
        listed = c.get("next_hearing_date")
        if listed and (listed == today or listed == tomorrow):
            print(f"Serial: {c['serial']}\tCourt: {c['court_name']}\tNext Hearing Date: {listed}")
            matches.append(c)

    if not matches:
        print("⚠️ No matching cases found.")
        driver.quit()
        return

    pending_path = os.path.join(DOWNLOAD_DIR, "pending_cases.xlsx")
    pd.DataFrame(matches).to_excel(pending_path, index=False)
    print(f"\n📝 Pending serials saved to: {pending_path}")

    # ---- Modified Capture Mode ----
    dl_choice = input("\n⬇️ Enter capture mode to record details manually? (y/N): ").strip().lower()
    if dl_choice == "y":
        captured_records = []
        for c in matches:
            serial = c['serial']
            print(f"\n👉 Open 'View' page for Serial {serial} manually, then press Enter to capture...")
            input()

            # Save full page as PDF
            pdf_path = os.path.join(DOWNLOAD_DIR, f"serial_{serial}.pdf")
            save_fullpage_pdf(driver, pdf_path)

            # Extract case details
            details = extract_case_details(driver)

            # Find and download linked PDFs
            soup_now = BeautifulSoup(driver.page_source, "html.parser")
            pdfs = []
            for a in soup_now.find_all("a", href=True):
                if a['href'].lower().endswith(".pdf"):
                    href = urljoin(driver.current_url, a['href'])
                    dl = download_file(href, dst_folder=DOWNLOAD_DIR)
                    if dl:
                        pdfs.append(dl)

            # Add record with hyperlink to PDF
            record = {
                "Serial": serial,
                "Court": c["court_name"],
                "Next Hearing Date": c["next_hearing_date"],
                **details,
                "Captured Page": f'=HYPERLINK("{pdf_path}", "View Full Page PDF")',
                "PDFs": ", ".join([f'=HYPERLINK("{p}", "PDF")' for p in pdfs]) if pdfs else "None"
            }
            captured_records.append(record)

        if captured_records:
            df = pd.DataFrame(captured_records)
            excel_path = os.path.join(DOWNLOAD_DIR, "captured_case_details.xlsx")
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            print(f"\n📊 Captured details saved to: {excel_path}")

            # --- NEW FEATURE: Show all CNR Numbers and ask verification ---
            print("\n🔎 All captured CNR Numbers:")
            cnr_list = [r.get("CNR Number") for r in captured_records if r.get("CNR Number")]
            if cnr_list:
                for idx, cnr in enumerate(cnr_list, start=1):
                    print(f"{idx}. {cnr}")
            else:
                print("⚠️ No CNR Numbers were captured.")

            verify_choice = input("\nDo you want to verify CNR Numbers? (y/N): ").strip().lower()
            if verify_choice == "y":
                verify_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
                print(f"\n🌐 Opening verification page: {verify_url}")
                driver.get(verify_url)
                input("🔍 Press Enter after verification to close the program...")
            else:
                print("\n✅ CNR verification skipped.")

    # Save full cause list as PDF at end
    pdf_output = os.path.join(DOWNLOAD_DIR, f"cause_list_{datetime.date.today()}.pdf")
    save_fullpage_pdf(driver, pdf_output)

    driver.quit()
    print(f"\n✅ Done. All files saved in: {DOWNLOAD_DIR}")


# ----------------- Entry -----------------
if __name__ == "__main__":
    main()
