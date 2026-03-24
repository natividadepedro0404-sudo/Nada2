"""
Script para testar se a API da Misticpay está gerando PIX reais
Execute: python test_pix_real.py
"""
import os
import requests
import json
import time

MISTICPAY_CLIENT_ID = os.environ.get("MISTICPAY_CLIENT_ID", "ci_libdweclsjyry50")
MISTICPAY_CLIENT_SECRET = os.environ.get("MISTICPAY_CLIENT_SECRET", "cs_kknlfy76fe2ir4nqjydf8ebee")
MISTICPAY_API_URL = "https://api.misticpay.com/api"

def test_pix_creation():
    """Testa a criação de um PIX real"""
    
    headers = {
        "ci": MISTICPAY_CLIENT_ID,
        "cs": MISTICPAY_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    
    transaction_id = f"TEST_{int(time.time())}"
    
    payload = {
        "amount": 10.00,
        "payerName": "Cliente Teste",
        "payerDocument": "00000000000",
        "transactionId": transaction_id,
        "description": "Teste PIX Real",
        "projectWebhook": "https://seu-dominio.com/api/webhook/misticpay"
    }
    
    print("=" * 80)
    print("TESTANDO API MISTICPAY - CRIAÇÃO DE PIX")
    print("=" * 80)
    print(f"\n[1] Enviando requisição para: {MISTICPAY_API_URL}/transactions/create")
    print(f"[2] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        url = f"{MISTICPAY_API_URL}/transactions/create"
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\n[3] Status Code: {response.status_code}")
        print(f"[4] Response Headers: {dict(response.headers)}")
        print(f"[5] Response Body (Raw):\n{response.text}")
        
        if response.status_code in [200, 201]:
            response_json = response.json()
            print(f"\n[6] Response JSON (Formatted):\n{json.dumps(response_json, indent=2, ensure_ascii=False)}")
            
            # Extrair dados
            data = response_json.get('data', response_json)
            
            print("\n" + "=" * 80)
            print("DADOS EXTRAÍDOS:")
            print("=" * 80)
            
            pix = data.get('copyPaste') or data.get('pixCopiaECola') or data.get('pix') or "NÃO ENCONTRADO"
            qr_url = data.get('qrcodeUrl') or data.get('qrCodeUrl') or "NÃO ENCONTRADO"
            qr_base64 = data.get('qrCodeBase64') or "NÃO ENCONTRADO"
            transaction_id_response = data.get('transactionId', "NÃO ENCONTRADO")
            
            print(f"\n✓ PIX Copia e Cola:\n  {pix[:50]}..." if len(str(pix)) > 50 else f"\n✓ PIX Copia e Cola:\n  {pix}")
            print(f"\n✓ QR Code URL:\n  {qr_url}")
            print(f"\n✓ QR Code Base64: {'Presente' if qr_base64 != 'NÃO ENCONTRADO' else 'Não encontrado'}")
            print(f"\n✓ Transaction ID:\n  {transaction_id_response}")
            
            # Validar se o PIX começa com o padrão correto
            if isinstance(pix, str) and pix.startswith("00020"):
                print("\n✅ PIX REAL DETECTADO! (começa com 00020)")
            else:
                print("\n❌ PIX pode não ser real ou está em formato diferente")
                
        else:
            print(f"\n❌ Erro na requisição!")
            print(f"Message: {response.json().get('message', 'Sem mensagem')}")
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar com Misticpay: {str(e)}")

if __name__ == "__main__":
    test_pix_creation()
