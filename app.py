from flask import Flask, jsonify
app = Flask(__name__)

# --- 1. VERİ MODELLERİ (MASTER DATA) ---

class WorkCenter:
    """Üretim Tesisindeki İş Merkezlerini (Makine/İstasyon) temsil eder."""
    def __init__(self, wc_id, description, personnel_count, cost_rate_hr, capacity_multiplier=1):
        self.wc_id = wc_id
        self.description = description
        self.personnel_count = personnel_count 
        self.cost_rate_hr = cost_rate_hr 
        self.capacity_multiplier = capacity_multiplier

class RoutingOperation:
    """Ürün Rotasındaki tek bir operasyon adımını temsil eder."""
    def __init__(self, seq, desc, duration_min, wc_id, personnel_required, unit_per_hour, wait_time_hr=0):
        self.seq = seq
        self.description = desc
        self.duration_min = duration_min
        self.wc_id = wc_id
        self.personnel_required = personnel_required
        self.unit_per_hour = unit_per_hour 
        self.wait_time_hr = wait_time_hr

# --- 2. PROJE VERİLERİ (GLOBAL VARIABLES) ---

TARGET_QUANTITY = 10000 
WORKING_HOURS_PER_DAY = 8 

# İş Merkezi Örnekleri (Kapasite Kararımız dahil)
work_centers = {
    'CNC-01': WorkCenter('CNC-01', 'CNC Kalıp İşleme', 1, 150.00),
    # HF-PRES-01: 2 makine * 2'li kalıp = 4x hız
    'HF-PRES-01': WorkCenter('HF-PRES-01', 'Yüksek Frekans Presi', 1, 95.00, capacity_multiplier=4), 
    # QC-PAKET-01: 2 personel ile hızlandırıldı
    'QC-PAKET-01': WorkCenter('QC-PAKET-01', 'Kalite Kontrol/Paketleme', 2, 0.00), 
}

# Rota Örnekleri (Sadece en kritik adımlar)
routing_operations = [
    # SEQ 40: Setup/Kalıp Süresi (20 saat, sabit)
    RoutingOperation(seq=40, desc='CNC Kalıp İşleme', duration_min=(20*60), wc_id='CNC-01', personnel_required=1, unit_per_hour=0),
    # SEQ 60: Serigrafi (2 saat işlem + 6 saat bekleme süresi)
    RoutingOperation(seq=60, desc='Serigrafi Baskı (4 Renk)', duration_min=(2*60), wc_id='SERI-01', personnel_required=2, unit_per_hour=1500, wait_time_hr=6),
    # SEQ 120: HF Presleme (1000 adet/saat, 4x çarpan)
    RoutingOperation(seq=120, desc='HF Kaynak / Presleme', duration_min=0, wc_id='HF-PRES-01', personnel_required=1, unit_per_hour=1000), 
    # SEQ 140: QC/Paketleme (500 adet/saat, 2 personel)
    RoutingOperation(seq=140, desc='QC ve Paketleme', duration_min=0, wc_id='QC-PAKET-01', personnel_required=2, unit_per_hour=500), 
]

# --- 3. ÇİZELGELEME FONKSİYONU ---

def calculate_total_production_time(quantity, operations, wcs):
    """Rota adımlarını toplayarak toplam süreyi (saat) ve termin süresini (gün) hesaplar."""
    total_processing_time_hr = 0
    total_calendar_time_hr = 0 

    operations.sort(key=lambda op: op.seq)

    for op in operations:
        wc = wcs.get(op.wc_id)
        if not wc:
            continue
        
        setup_time_hr = op.duration_min / 60 

        if op.unit_per_hour > 0:
            # Etkili Hız = Birim/Saat * Makine Çarpanı * Personel Sayısı (QC'de personel önemli)
            effective_speed = op.unit_per_hour * wc.capacity_multiplier * wc.personnel_count
            
            # İşlem Süresi = Toplam Adet / Etkili Hız
            processing_time_hr = quantity / effective_speed
        else:
            # Sabit süreli operasyonlar (CNC Setup)
            processing_time_hr = 0
        
        op_total_time_hr = setup_time_hr + processing_time_hr
        total_processing_time_hr += op_total_time_hr

        # Takvim süresi: İşlem Süresi + Bekleme Süresi
        total_calendar_time_hr += op_total_time_hr + op.wait_time_hr

    total_days = total_calendar_time_hr / WORKING_HOURS_PER_DAY
    
    return {
        "processing_time_hr": round(total_processing_time_hr, 2),
        "calendar_time_days": round(total_days, 2)
    }

# --- 4. FLASK API BAĞLANTISI ---

@app.route('/')
def home():
    """Ana API noktası: ERP Çizelgeleme sonucunu gösterir."""
    # Hesaplamayı çağır
    results = calculate_total_production_time(TARGET_QUANTITY, routing_operations, work_centers)
    
    return jsonify({
        "status": "Production Schedule Calculated",
        "Target_Order": f"{TARGET_QUANTITY} Adet Logo",
        "Calculated_Time": {
            "Total_Work_Hours": results['processing_time_hr'],
            "Calendar_Days": results['calendar_time_days'],
            "Note": f"9.70 günden {results['calendar_time_days']} güne düştü (QC hızlandırması ve HF çarpanı ile)"
        },
        "message": "Bu sonuçlar, ERP Dashboard'unuza aktarılmaya hazırdır."
    })
    
if __name__ == '__main__':
    app.run(debug=True)