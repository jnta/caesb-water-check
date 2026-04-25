import os
import requests
from bs4 import BeautifulSoup

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram credentials not found. Exiting.")
        return

    # URL for Caesb Water Check
    url = "https://www.caesb.df.gov.br/portal-servicos/app/publico/consultarfaltadagua"
    
    try:
        # Use a session to handle redirects and cookies properly
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        })
        
        # We allow redirects.
        response = session.get(url, verify=False, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
    except Exception as e:
        print(f"Failed to fetch data from CAESB: {e}")
        return

    soup = BeautifulSoup(html_content, "html.parser")
    
    # Locate the "Em andamento" tab content
    tab_andamento = soup.find(id="tabView:tabAndamento")
    if not tab_andamento:
        print("Could not find the 'Em andamento' tab.")
        return
        
    table = tab_andamento.find("table")
    if not table:
        print("Could not find the table inside 'Em andamento' tab.")
        return
        
    rows = table.find_all("tr")
    if len(rows) <= 1:
        print("No data rows found in the table.")
        return
        
    # Skip the header row
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
        
        # Check for variations of Vicente Pires
        # Converting to lowercase without accents could be better, but simple lower() is a good start
        ra_lower = ra.lower()
        if "vicente pires" in ra_lower or "vp" in ra_lower.split():
            found_vicente_pires = True
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
            
    if found_vicente_pires:
        print("Found Vicente Pires in 'Em andamento'. Sending Telegram message(s)...")
        for msg in messages:
            try:
                send_telegram_message(token, chat_id, msg)
                print("Message sent successfully.")
            except Exception as e:
                print(f"Failed to send message: {e}")
    else:
        print("Vicente Pires not found in 'Em andamento'. No action taken.")

if __name__ == "__main__":
    # Disable insecure request warnings for verify=False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
