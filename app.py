# app.py dosyası
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "OK",
        "message": "ERP Backend Servisi başarıyla çalışıyor.",
        "next_step": "Çizelgeleme Algoritması fonksiyonu buraya eklenecek."
    })