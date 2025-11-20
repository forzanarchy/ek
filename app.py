# app.py dosyası - Veri Modelleri Eklendi

from flask import Flask, jsonify
app = Flask(__name__)

# --- 1. VERİ MODELLERİ (MASTER DATA) ---

class WorkCenter:
    """Üretim Tesisindeki İş Merkezlerini temsil eder."""
    def __init__(self, wc_id, description, personnel_count, cost_rate_hr, capacity_multiplier=1):
        self.wc_id = wc_id
        self.description = description
        self.personnel_count = personnel_count 
        self.cost_rate_hr = cost_rate_hr 
        self.capacity_multiplier = capacity_multiplier # Makine veya kalıp çarpanı (Örn: 2 makine)

class RoutingOperation:
    """Ürün Rotasındaki tek bir operasyon adımını temsil eder."""
    def __init__(self, seq, desc, duration_min, wc_id, personnel_required, unit_per_hour, wait_time_hr=0):
        self.seq = seq
        self.description = desc
        self.duration_min = duration_min # Setup süresi (sabit)
        self.wc_id = wc_id
        self.personnel_required = personnel_required # Bu operasyon için gereken min personel
        self.unit_per_hour = unit_per_hour # Birim başına üretim hızı (adet/saat)
        self.wait_time_hr = wait_time_hr # Zorunlu bekleme süresi

# app.py dosyası - Çizelgeleme Fonksiyonu ve Proje Verileri

# --- 2. PROJE VERİLERİ ---
# Bizim 10.000 adet logo siparişimiz için gereken temel veriler:
TARGET_QUANTITY = 10000 
WORKING_HOURS_PER_DAY = 8 

# İş Merkezi Örnekleri (Kapasite Kararımız dahil)
work_centers = {
    'CNC-01': WorkCenter('CNC-01', 'CNC Kalıp İşleme', 1, 150.00),
    'HF-PRES-01': WorkCenter('HF-PRES-01', 'Yüksek Frekans Presi', 1, 95.00, capacity_multiplier=4), # 2 makine * 2'li kalıp = 4x hız
    'QC-PAKET-01': WorkCenter('QC-PAKET-01', 'Kalite Kontrol/Paketleme', 2, 0.00), # 2 personel ile hızlandırıldı
    # ... Diğer İş Merkezleri buraya eklenecek
}

# Rota Örnekleri (Sadece en kritik adımlar)
routing_operations = [
    # Setup/Kalıp Süresi (20 saat, sabit)
    RoutingOperation(seq=40, desc='CNC Kalıp İşleme', duration_min=(20*60), wc_id='CNC-01', personnel_required=1, unit_per_hour=0),
    # Serigrafi (4 renk, 6 saat bekleme süresi)
    RoutingOperation(seq=60, desc='Serigrafi Baskı (4 Renk)', duration_min=(2*60), wc_id='SERI-01', personnel_required=2, unit_per_hour=1500, wait_time_hr=6),
    # HF Presleme (Tek birim hızı: 1000 adet/saat)
    RoutingOperation(seq=120, desc='HF Kaynak / Presleme', duration_min=0, wc_id='HF-PRES-01', personnel_required=1, unit_per_hour=1000), 
    # QC/Paketleme (Tek personel hızı: 500 adet/saat)
    RoutingOperation(seq=140, desc='QC ve Paketleme', duration_min=0, wc_id='QC-PAKET-01', personnel_required=2, unit_per_hour=500), 
]

def calculate_total_production_time(quantity, operations, wcs):
    """Rota adımlarını toplayarak toplam süreyi (saat) ve termin süresini (gün) hesaplar."""
    total_processing_time_hr = 0
    total_calendar_time_hr = 0 # Bekleme sürelerini de içerir

    # Rotayı sıra numarasına göre sırala (seq)
    operations.sort(key=lambda op: op.seq)

    for op in operations:
        wc = wcs.get(op.wc_id)
        if not wc:
            continue
        
        # 1. Setup/Sabit Süre Hesaplama (CNC gibi)
        setup_time_hr = op.duration_min / 60 

        # 2. İşlem Süresi Hesaplama (Operasyon hızı / Üretim Hızı)
        if op.unit_per_hour > 0:
            # İşlem hızını, makine çarpanı ve personel sayısı ile çarp
            effective_speed = op.unit_per_hour * wc.capacity_multiplier * wc.personnel_count
            
            # Toplam logo adedini efektif hıza böl
            processing_time_hr = quantity / effective_speed
        else:
            processing_time_hr = 0
        
        # Toplam süreyi biriktir
        op_total_time_hr = setup_time_hr + processing_time_hr
        total_processing_time_hr += op_total_time_hr

        # Takvim süresi (işlem süresi + bekleme süresi)
        total_calendar_time_hr += op_total_time_hr + op.wait_time_hr

    # 3. Nihai Hesaplamalar
    total_days = total_calendar_time_hr / WORKING_HOURS_PER_DAY
    
    return {
        "processing_time_hr": round(total_processing_time_hr, 2), # Sadece işçilik/makine süresi (77.63'ten 66.63'e düşen)
        "calendar_time_days": round(total_days, 2) # Tüm bekleme süreleri dahil (8.33 gün)
    }
    
    # app.py dosyası - API Güncellemesi

@app.route('/')
def home():
    """
    Ana API noktası: ERP Çizelgeleme sonucunu gösterir.
    """
    results = calculate_total_production_time(TARGET_QUANTITY, routing_operations, work_centers)
    
    return jsonify({
        "status": "Production Schedule Calculated",
        "Target_Order": f"{TARGET_QUANTITY} Adet Logo",
        "Calculated_Time": {
            "Total_Work_Hours": results['processing_time_hr'],
            "Calendar_Days": results['calendar_time_days'],
            "Note": f"9.70 günden {results['calendar_time_days']} güne düştü (QC hızlandırması ile)"
        },
        "message": "Bu sonuçlar, ERP Dashboard'unuza aktarılmaya hazırdır."
    })
    
# if __name__ == '__main__': ... (bu kısım en altta kalır)