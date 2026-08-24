import requests
import json
import datetime
import time
import threading
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread

API_BASE_URL = "https://api.indmoney.com/v1"
ACCESS_TOKEN = os.getenv("INDMONEY_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN_PLACEHOLDER")
ACCOUNT_ID = os.getenv("INDMONEY_ACCOUNT_ID", "YOUR_ACCOUNT_ID_PLACEHOLDER")
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
SYMBOL = "NSE:RELIANCE"
LOT_SIZE = 10
TARGET_PCT = 0.02
MAX_DAILY_LOSS_LIMIT = -5000
IS_PAPER_TRADING = True

current_daily_pnl = 0
orb_high = None
orb_low = None
position_active = False
last_trade = None
highest_price_seen = 0
current_sl_price = 0
algo_running = False

def get_global_market_status():
    if IS_PAPER_TRADING: 
        return 0.65, -0.40
    return 0.0, 0.0

def get_market_data(symbol):
    return {'close': 2500, 'vwap': 2490, 'rsi': 65, 'volume': 10000, 'avg_volume': 5000, 'high': 2510, 'low': 2480}

def place_indmoney_order(symbol, quantity, transaction_type, order_type="MARKET", price=None, trigger_price=None):
    if IS_PAPER_TRADING:
        return {"status": "SUCCESS", "order_id": "PAPER_12345"}
    return None

class TradingBotApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.log_label = Label(
            text="Bot Initialized...\n", 
            size_hint_y=None, 
            halign="left", 
            valign="top"
        )
        self.log_label.bind(size=self._update_text_size, texture_size=self._update_label_size)
        self.scroll.add_widget(self.log_label)
        
        btn_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        self.start_btn = Button(text="Start Algo", background_color=(0, 1, 0, 1))
        self.start_btn.bind(on_press=self.start_algo)
        self.stop_btn = Button(text="Stop Algo", background_color=(1, 0, 0, 1), disabled=True)
        self.stop_btn.bind(on_press=self.stop_algo)
        
        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.stop_btn)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(btn_layout)
        return self.layout

    def _update_text_size(self, instance, value):
        instance.text_size = (value[0], None)

    def _update_label_size(self, instance, value):
        instance.height = value[1]

    @mainthread
    def log_message(self, message):
        self.log_label.text += f"{message}\n"
        self.scroll.scroll_y = 0

    def start_algo(self, instance):
        global algo_running
        if not algo_running:
            algo_running = True
            self.start_btn.disabled = True
            self.stop_btn.disabled = False
            self.log_message("\n=== ALGO STARTED ===")
            threading.Thread(target=self.run_master_algo_system, daemon=True).start()

    def stop_algo(self, instance):
        global algo_running
        if algo_running:
            algo_running = False
            self.start_btn.disabled = False
            self.stop_btn.disabled = True
            self.log_message("=== ALGO STOPPED ===")

    def run_master_algo_system(self):
        global orb_high, orb_low, current_daily_pnl, position_active, algo_running
        us_trend, japan_trend = get_global_market_status()
        self.log_message(f"Global Cues -> US: {us_trend}% | Japan: {japan_trend}%")

        while algo_running:
            try:
                now = datetime.datetime.now()
                current_time = now.time()
                if current_time >= datetime.time(15, 15):
                    self.log_message("Market Closed. Shutting down.")
                    break
                
                tick = get_market_data(SYMBOL)
                if not tick:
                    time.sleep(2)
                    continue
                
                self.log_message(f"[{current_time.strftime('%H:%M:%S')}] PNL: {current_daily_pnl} | LTP: {tick['close']}")
                
                for _ in range(5):
                    if not algo_running:
                        break
                    time.sleep(1)
            except Exception as e:
                self.log_message(f"Error: {e}")
                time.sleep(5)
                
        self.stop_algo(None)

if __name__ == "__main__":
    TradingBotApp().run()
