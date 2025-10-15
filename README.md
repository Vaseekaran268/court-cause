🏛️ eCourts Cause List Scraper

This Python automation script scrapes daily cause lists and case details from eCourts India
, captures case information (including CNR Numbers), downloads related PDFs, and exports everything into Excel.

It also optionally allows you to verify CNR numbers directly through the eCourts portal.

📦 Features

✅ Automated navigation through eCourts cause list pages
✅ Captcha image extraction (manual solving required)
✅ Full-page PDF capture of cause lists and case pages
✅ Case details extraction including CNR Number, Court Name, and Hearing Dates
✅ Download of linked case PDFs
✅ Export of all cases (and filtered cases) to Excel
✅ Prompted verification of CNR numbers on the official website

🧰 Requirements

Before running the script, ensure you have the following installed:

1. Python

Version: Python 3.8+

Check your version:

python --version

2. Google Chrome

Install the latest version of Google Chrome.

3. Chrome WebDriver

Required for Selenium automation.

Download matching ChromeDriver for your Chrome version from:
🔗 https://chromedriver.chromium.org/downloads

Place it in your project folder or in a directory included in your system PATH.

📚 Install Dependencies

In your project directory, create a virtual environment (optional but recommended):

python -m venv venv


Activate it:

Windows:

venv\Scripts\activate


Mac/Linux:

source venv/bin/activate


Then install required packages:

pip install selenium beautifulsoup4 requests pandas python-dateutil openpyxl

⚙️ Configuration

The script defines a few constants at the top:

ECOURTS_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=999af70e3228e4c73736b14e53143cc8215edf44df7868a06331996cdf179d97#"
CHROME_DRIVER_PATH = None  # Optional: specify ChromeDriver path manually
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")


If ChromeDriver is not in PATH, set it manually:

CHROME_DRIVER_PATH = r"C:\path\to\chromedriver.exe"


All generated PDFs and Excel files will be saved inside the downloads/ folder.

🚀 How to Run

Run the scraper with:

python app.py

Step-by-step Process:

The script will open the eCourts website in Chrome.

You must manually select:

State

District

Court Complex

Cause List Date

Press Enter in the console to continue.

The script will capture the captcha image and save it as captcha.png.

Open the captcha image, read the text, and enter it in the console.

The script will automatically:

Load all cause list pages

Extract case details

Highlight cases with Next Hearing Date = Today or Tomorrow

Export results to Excel

Optionally, you can:

Capture detailed case PDFs manually

Review and verify CNR Numbers at the end

📁 Output Files

All files are stored in the downloads/ directory:

File Name	Description
cause_list_YYYY-MM-DD.pdf	Full cause list PDF for the date
pending_cases.xlsx	All cases with next hearing today/tomorrow
serial_X.pdf	Full-page PDF of each manually captured case
captured_case_details.xlsx	Detailed case info including CNR & hyperlinks
🔎 Example Console Flow
🌐 Loaded: https://services.ecourts.gov.in/ecourtindia_v6/...
👉 Select State, District, Court Complex & Cause List Date.
Then press Enter to continue...
🧩 Captcha saved to: D:\court1\captcha.png
🔐 Enter captcha shown in image: xyz123
📄 Parsing page 1 ...
📄 Parsing page 2 ...
--- 📅 Cases with Next Hearing Date = today or tomorrow ---
Serial: 12   Court: ACJ Court, XYZ District   Next Hearing Date: 2025-10-15
📝 Pending serials saved to: downloads/pending_cases.xlsx

🧾 CNR Verification

After capturing case details, the script will display all CNR Numbers and ask:

Do you want to verify CNR Numbers? (y/N):


If you enter y, it automatically redirects to:
🔗 https://services.ecourts.gov.in/ecourtindia_v6/

⚠️ Notes & Limitations

Captcha solving is manual (cannot be automated due to legal restrictions).

eCourts portal layout may change; minor XPath adjustments might be required.

Ensure a stable internet connection during scraping.

Recommended to run during non-peak hours to avoid server timeouts.#
