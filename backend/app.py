import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# backend 디렉토리가 파이썬 경로에 포함되도록 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.crypto_helper import CryptoHelper
from backend.services.kis_client import KISClient

load_dotenv()

app = Flask(__name__)
# 프론트엔드 연동을 위해 CORS 활성화
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 환경 변수에서 암호화 키 로드
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default-dev-encryption-key-32bytes!")

crypto = CryptoHelper(ENCRYPTION_KEY)

@app.route("/api/keys/test", methods=["POST"])
def test_keys():
    """
    한국투자증권(KIS) API Key 유효성을 검증합니다.
    평문 키를 수신하여 암호화하고, 다시 복호화하여 일치 여부를 검증한 후,
    토큰 발급 및 잔고 조회를 요청하여 KIS 연결을 최종 확인합니다.
    """
    data = request.json or {}
    appkey = data.get("appkey")
    appsecret = data.get("appsecret")
    cano = data.get("cano")
    acnt_prdt_cd = data.get("acnt_prdt_cd", "01")
    env = data.get("env", "MOCK")
    
    if not appkey or not appsecret or not cano:
        return jsonify({
            "success": False,
            "message": "Missing required fields: appkey, appsecret, or cano."
        }), 400
        
    try:
        # 1. 암호화/복호화 주기 테스트
        enc_appkey = crypto.encrypt(appkey)
        enc_appsecret = crypto.encrypt(appsecret)
        enc_cano = crypto.encrypt(cano)
        
        dec_appkey = crypto.decrypt(enc_appkey)
        dec_appsecret = crypto.decrypt(enc_appsecret)
        dec_cano = crypto.decrypt(enc_cano)
        
        # 2. 복호화된 크리덴셜을 사용하여 KIS API 연결 테스트
        client = KISClient(
            appkey=dec_appkey,
            appsecret=dec_appsecret,
            cano=dec_cano,
            acnt_prdt_cd=acnt_prdt_cd,
            env=env
        )
        
        balance = client.get_balance()
        
        return jsonify({
            "success": True,
            "message": "API key validated and connection established successfully.",
            "data": {
                "balance": balance,
                "encrypted": {
                    "appkey": enc_appkey,
                    "appsecret": enc_appsecret,
                    "cano": enc_cano
                }
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Validation failed: {str(e)}"
        }), 500

@app.route("/api/dashboard/balance", methods=["POST"])
def get_dashboard_balance():
    """
    암호화된 크리덴셜을 복호화하여 실시간 잔고를 조회합니다.
    ENCRYPTION_KEY를 사용하여 키를 복호화한 후, KIS에 요청을 수행합니다.
    """
    data = request.json or {}
    enc_appkey = data.get("appkey")
    enc_appsecret = data.get("appsecret")
    enc_cano = data.get("cano")
    acnt_prdt_cd = data.get("acnt_prdt_cd", "01")
    env = data.get("env", "MOCK")
    
    if not enc_appkey or not enc_appsecret or not enc_cano:
        return jsonify({
            "success": False,
            "message": "Missing encrypted credentials."
        }), 400
        
    try:
        dec_appkey = crypto.decrypt(enc_appkey)
        dec_appsecret = crypto.decrypt(enc_appsecret)
        dec_cano = crypto.decrypt(enc_cano)
        
        client = KISClient(
            appkey=dec_appkey,
            appsecret=dec_appsecret,
            cano=dec_cano,
            acnt_prdt_cd=acnt_prdt_cd,
            env=env
        )
        
        balance = client.get_balance()
        return jsonify({
            "success": True,
            "data": balance
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve balance: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
