import os
import time
import hmac
import hashlib
import requests
from fastapi import FastAPI
from threading import Thread
import uvicorn

app = FastAPI()

# ==========================================
# [사용자 설정 영역] 본인 정보 확인!
# ==========================================
API_KEY = '여기에_바이낸스_읽기전용_API_키_입력'
SECRET_KEY = '여기에_바이낸스_시크릿_키_입력'
GOOGLE_WEBHOOK_URL = '여기에_구글_웹앱_URL_입력'
# ==========================================

BASE_URL = 'https://fapi.binance.com'

@app.get("/")
def home():
    return {"status": "Bot is running!"}

def get_signature(query_string):
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def check_binance_trades():
    last_checked_time = 0
    
    while True:
        try:
            endpoint = '/fapi/v1/userTrades'
            timestamp = int(time.time() * 1000)
            query_string = f'timestamp={timestamp}&limit=5'
            signature = get_signature(query_string)
            
            url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
            headers = {'X-MBX-APIKEY': API_KEY}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                trades = response.json()
                for trade in trades:
                    if trade['time'] > last_checked_time:
                        trade_data = {
                            "symbol": trade.get("symbol"),
                            "side": "BUY" if trade.get("buyer") else "SELL",
                            "price": trade.get("price"),
                            "qty": trade.get("qty")
                        }
                        requests.post(GOOGLE_WEBHOOK_URL, json=trade_data)
                        last_checked_time = trade['time']
        except Exception as e:
            print(f"백그라운드 에러 발생: {e}")
            
        time.sleep(30)

@app.on_event("startup")
def startup_event():
    thread = Thread(target=check_binance_trades)
    thread.daemon = True
    thread.start()

# Render 포트 바인딩을 완벽하게 잡아주는 핵심 구동부
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
