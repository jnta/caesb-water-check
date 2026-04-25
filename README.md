# CAESB Water Check
> **Automated monitoring for water outages in Brasília (DF).**

This project provides a robust scraping utility to monitor the CAESB (Companhia de Saneamento Ambiental do Distrito Federal) portal for water outages and maintenance alerts. It sends real-time notifications via Telegram whenever an outage is detected in your configured regions.

---

## 🛠 Technical Stack
* **Runtime:** Python 3.10+
* **Scraping:** BeautifulSoup4 + Requests (Handling JSF/PrimeFaces AJAX updates)
* **Automation:** GitHub Actions (Scheduled workflow)
* **Notifications:** Telegram Bot API

---

## 🚀 Key Features
* **AJAX-Aware Scraper:** Successfully navigates the complex PrimeFaces partial-update logic and ViewState transitions on the CAESB website.
* **Region Filtering:** Configure a list of cities or regions (e.g., Vicente Pires, Águas Claras, Taguatinga) to monitor.
* **Scheduled Execution:** Runs automatically via GitHub Actions (optimized for daytime hours in Brasília).
* **Clean Alerts:** Formats raw table data into readable Telegram messages with start times and expected normalization dates.

---

## ⚙️ Setup & Configuration

### 1. Requirements
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Configuration (`config.yaml`)
Add the cities you wish to monitor to the `config.yaml` file:
```yaml
cities:
  - Vicente Pires
  - Águas Claras
```

### 3. Environment Variables
The script requires a `.env` file (or GitHub Secrets for automation) with the following:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🤖 Automated Workflow
The project includes a GitHub Action (`scrape.yml`) that:
1. Installs dependencies.
2. Executes the scraper every hour.
3. Only runs between **06:00 and 00:00 (BRT)** to avoid redundant checks during static night hours.
