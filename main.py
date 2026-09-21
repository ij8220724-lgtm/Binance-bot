import os
import time
import hmac
import hashlib
import requests
from fastapi import FastAPI
from threading import Thread

app = FastAPI()

# ==========================================
# [사용자 설정 영역] 본인 정보로 채워주세요!
# ==========================================
API_KEY = 'c9VMqfaLyimfqWmZhJ4CNfZ9VD0Jk1dCONE16ehdZAWHsQn5T3KStrraSb6hDMVP'
SECRET_KEY = 'gn4c2frizi1qL2kKxHsiurHoq5i1xfO9wrgeI34ylBDzawng0DSSSIHxumvDuPb4'
GOOGLE_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbztM4AS5Zas7l6-Bt-9IDu-84peShTUUa1kqSWzSZHPLZ3INDNtLRV648r2ffOiU_wC-w/exec'
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
    # 24시간 백그라운드에서 돌면서 주기적으로 바이낸스 확인
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
                # 여기에 최신 거래를 감지해서 구글 시트로 쏘는 로직이 들어갑니다.
                # (테스트용 기본 구조)
                for trade in trades:
                    if trade['time'] > last_checked_time:
                        trade_data = {
                            "symbol": trade.get("symbol"),
                            "side": "BUY" if trade.get("buyer") else "SELL", # 예시
                            "price": trade.get("price"),
                            "qty": trade.get("qty")
                        }
                        # 구글 시트 웹앱으로 전송
                        requests.post(GOOGLE_WEBHOOK_URL, json=trade_data)
                        last_checked_time = trade['time']
        except Exception as e:
            print(f"백그라운드 에러 발생: {e}")
            
        # 30초마다 체크 (실시간에 가깝게 작동)
        time.sleep(30)

# 서버가 켜질 때 백그라운드 스레드에서 봇 작동 시작
@app.on_event("startup")
def startup_event():
    thread = Thread(target=check_binance_trades)
    thread.daemon = True
    thread.start()
