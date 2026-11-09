from flask import Flask, render_template, request, jsonify
import sys
import os

# Menambahkan root direktori ke path agar bisa membaca main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mengimpor variabel dan fungsi langsung dari file main.py asli Anda
from main import PROVIDERS, normalize_phone

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/spam', methods=['POST'])
def run_spam():
    data = request.get_json()
    if not data or 'phone' not in data:
        return jsonify({"status": "error", "message": "Nomor HP tidak boleh kosong"}), 400

    # Menggunakan fungsi normalisasi dari main.py asli
    no_hp = normalize_phone(data['phone'])
    
    # Validasi awal panjang nomor HP
    if not no_hp.startswith("08") or len(no_hp) < 10:
        return jsonify({"status": "error", "message": "Nomor HP tidak valid."}), 400

    results = []
    
    # Menjalankan 1 siklus ke semua provider menggunakan data dari main.py asli
    for name, send_fn in PROVIDERS:
        try:
            ok = send_fn(no_hp)
        except Exception:
            ok = False
        
        results.append({
            "provider": name,
            "status": "OK" if ok else "Gagal"
        })

    return jsonify({
        "status": "success",
        "target": no_hp,
        "results": results
    })

app.debug = True