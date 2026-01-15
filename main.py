import requests
import time
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
RECHERCHE = os.environ.get('RECHERCHE', 'nike')
PRIX_MAX = int(os.environ.get('PRIX_MAX', '30'))
INTERVALLE_HEURES = int(os.environ.get('INTERVALLE_HEURES', '2'))

class VintedScanner:
    def __init__(self):
        self.base_url = "https://www.vinted.fr/api/v2/catalog/items"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        self.seen_items = set()
    
    def send_telegram(self, message):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            response = requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def search_items(self, params):
        try:
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def analyze_item(self, item):
        price = float(item.get('price', 0))
        brand = item.get('brand_title', '')
        title = item.get('title', '').lower()
        reasons = []
        
        if price < 10:
            reasons.append(f"💰 {price}€")
        if brand in ['Nike', 'Adidas', 'Zara'] and price < 25:
            reasons.append(f"🏷️ {brand}")
        if any(w in title for w in ['neuf', 'new']) and price < 30:
            reasons.append("🆕 Neuf")
        
        return len(reasons) > 0, reasons
    
    def format_message(self, item, reasons):
        title = item.get('title', '')[:80]
        price = item.get('price', '')
        url = f"https://www.vinted.fr/items/{item.get('id', '')}"
        reasons_text = "\n".join([f"✓ {r}" for r in reasons])
        return f"🎯 AFFAIRE!\n\n{title}\n\n{reasons_text}\n\n💰 {price}€\n🔗 {url}"
    
    def scan(self):
        params = {'search_text': RECHERCHE, 'price_to': PRIX_MAX, 'order': 'newest_first'}
        print(f"\n🔍 Scan [{datetime.now().strftime('%H:%M')}]")
        data = self.search_items(params)
        if not data:
            return
        
        new_deals = 0
        for item in data.get('items', []):
            item_id = str(item.get('id'))
            if item_id not in self.seen_items:
                self.seen_items.add(item_id)
                is_good, reasons = self.analyze_item(item)
                if is_good:
                    new_deals += 1
                    print(f"✅ {item.get('title', '')[:40]}...")
                    self.send_telegram(self.format_message(item, reasons))
        print(f"✓ {new_deals} affaire(s)")
    
    def run(self):
        print(f"🤖 SCANNER DÉMARRÉ\n⏰ {INTERVALLE_HEURES}h | 💰 {PRIX_MAX}€\n")
        if self.send_telegram("🤖 Scanner démarré!"):
            print("✅ Telegram OK\n")
        while True:
            self.scan()
            print(f"💤 Prochaine vérif dans {INTERVALLE_HEURES}h\n")
            time.sleep(INTERVALLE_HEURES * 3600)

if __name__ == "__main__":
    scanner = VintedScanner()
    scanner.run()
