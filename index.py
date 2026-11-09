from flask import Flask, request, jsonify
import re

# Import provider kamu
from provider.adakami_provider import send_otp as adakami_send_otp
from provider.indosaku_provider import send_otp as indosaku_send_otp
from provider.kredione_provider import send_otp as kredione_send_otp
from provider.rc_provider import send_otp as rc_send_otp
from provider.kreditnavigator_provider import send_otp as kreditnavigator_send_otp

# WAJIB UNTUK VERCEL: Variabel harus bernama 'app'
app = Flask(__name__)

PROVIDERS = [
    ("AdaKami",          adakami_send_otp),
    ("Indosaku",         indosaku_send_otp),
    ("KrediOne",         kredione_send_otp),
    ("RupiahCepat",      rc_send_otp),
    ("KreditNavigator",  kreditnavigator_send_otp),
]

def normalize_phone(value: str) -> str:
    value = re.sub(r"\D", "", value)
    if value.startswith("62"):
        value = "0" + value[2:]
    return value

# Kita buat route API-nya
@app.route("/", methods=["GET"])
def home():
    return jsonify({"pesan": "API Spam OTP aktif. Gunakan parameter ?no_hp=08xxx"})

@app.route("/api/spam", methods=["GET"])
def spam_otp():
    # Ambil nomor dari URL, contoh: domainkamu.vercel.app/api/spam?no_hp=08978397772
    no_hp_input = request.args.get("no_hp")
    
    if not no_hp_input:
        return jsonify({"status": "error", "pesan": "Parameter 'no_hp' wajib diisi!"}), 400
        
    no_hp = normalize_phone(no_hp_input)
    
    if not re.fullmatch(r"08\d{8,14}", no_hp):
        return jsonify({"status": "error", "pesan": "Format nomor tidak valid"}), 400

    # Karena Vercel timeout-nya cepet, kita HAPUS fungsi cooldown/loop
    # Kita tembak 1x saja per request
    hasil = {}
    
    for name, send_fn in PROVIDERS:
        try:
            # Panggil fungsi OTP-mu
            ok = send_fn(no_hp)
            hasil[name] = "Sukses" if ok else "Gagal"
        except Exception as e:
            hasil[name] = f"Error: {str(e)}"

    return jsonify({
        "status": "success",
        "target": no_hp,
        "hasil": hasil
    })

# Untuk testing di laptop lokal
if __name__ == "__main__":
    app.run(port=5000)