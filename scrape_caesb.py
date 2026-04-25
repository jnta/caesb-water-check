import os
import re
import requests
import urllib3
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Disable insecure request warnings for verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    response.raise_for_status()


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram credentials not found. Exiting.")
        return

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        cities_to_check = [c.lower() for c in config.get("cities", [])]
    except FileNotFoundError:
        print("Config file not found.")
        return

    # URL for Caesb Water Check
    url = "https://www.caesb.df.gov.br/portal-servicos/app/publico/consultarfaltadagua"

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
    )

    try:
        print("Fetching initial page...")
        r = session.get(url, verify=False, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Extract ViewState for the JSF AJAX request
        view_state_input = soup.find("input", {"name": "javax.faces.ViewState"})
        if not view_state_input:
            print("Could not find ViewState. The site structure might have changed.")
            return
        view_state = view_state_input.get("value")

        # Find the AJAX trigger script that populates the table
        source = None
        form = None
        for s in soup.find_all("script"):
            if (
                s.string
                and "PrimeFaces.ab" in s.string
                and "tabView:formFaltaDeAgua" in s.string
            ):
                s_match = re.search(r's:"([^"]+)"', s.string)
                f_match = re.search(r'f:"([^"]+)"', s.string)
                if s_match and f_match:
                    source = s_match.group(1)
                    form = f_match.group(1)
                    break

        if not source or not form:
            print(
                "Could not find AJAX parameters. The site structure might have changed."
            )
            return

        print(f"Triggering AJAX update to fetch water outage data...")
        data = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": source,
            "javax.faces.partial.execute": source,
            "javax.faces.partial.render": "tabView:formFaltaDeAgua",
            source: source,
            form: form,
            "javax.faces.ViewState": view_state,
        }

        # POST to the current session URL (which includes execution param)
        r_ajax = session.post(r.url, data=data, verify=False, timeout=30)
        r_ajax.raise_for_status()

        # Parse the partial XML response
        ajax_soup = BeautifulSoup(r_ajax.text, "xml")
        update_tag = ajax_soup.find("update", {"id": "tabView:formFaltaDeAgua"})

        if not update_tag or not update_tag.string:
            print("Could not find the table update in the AJAX response.")
            return

        html_content = update_tag.string
        table_soup = BeautifulSoup(html_content, "html.parser")

        table = table_soup.find("table")
        if not table:
            print("Table not found in the populated content.")
            return

        rows = table.find_all("tr")
        if len(rows) <= 1:
            print("No data rows found in the table.")
            return

        # Skip header
        data_rows = rows[1:]
        found_vicente_pires = False
        messages = []

        for row in data_rows:
            cols = row.find_all(["td", "th"])
            if len(cols) < 6:
                continue

            ra = cols[0].get_text(separator=" ", strip=True)
            areas_afetadas = cols[1].get_text(separator=" ", strip=True)
            inicio = cols[2].get_text(separator=" ", strip=True)
            normalizacao = cols[3].get_text(separator=" ", strip=True)
            tipo = cols[4].get_text(separator=" ", strip=True)
            motivo = cols[5].get_text(separator=" ", strip=True)

            ra_lower = ra.lower()
            # Check if any configured city matches the RA
            match_found = any(city in ra_lower for city in cities_to_check)

            if match_found:
                msg = (
                    f"🚨 <b>Falta de Água Identificada</b> 🚨\n\n"
                    f"<b>RA:</b> {ra}\n"
                    f"<b>Áreas Afetadas:</b> {areas_afetadas}\n"
                    f"<b>Início:</b> {inicio}\n"
                    f"<b>Normalização:</b> {normalizacao}\n"
                    f"<b>Tipo:</b> {tipo}\n"
                    f"<b>Motivo:</b> {motivo}"
                )
                messages.append(msg)

        if messages:
            print(
                f"Found entries for {', '.join(cities_to_check)}. Sending {len(messages)} Telegram message(s)..."
            )
            for msg in messages:
                try:
                    send_telegram_message(token, chat_id, msg)
                    print("Message sent successfully.")
                except Exception as e:
                    print(f"Failed to send message: {e}")
        else:
            print(f"No entries found for: {', '.join(cities_to_check)}")

    except Exception as e:
        print(f"An error occurred during scraping: {e}")


if __name__ == "__main__":
    main()
