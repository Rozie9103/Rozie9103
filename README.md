# Rozie Toolkit - Advanced Mode

Toolkit serangan brute force login endpoint dengan deteksi otomatis, proxy, dan statistik lengkap. Versi advanced dengan arsitektur modular dan sistem plugin yang ekstensibel.

## Fitur Utama
- Deteksi otomatis login endpoint dan form field
- Brute force multi-threaded dengan dukungan proxy lengkap:
  - TOR network
  - HTTP proxy
  - SOCKS4/SOCKS5 proxy
- Statistik serangan real-time dan detail
- Sistem logging komprehensif (hasil, error, debug)
- CLI interaktif dengan visualisasi
- Sistem plugin yang mudah dikembangkan
- Arsitektur modular untuk pengembangan berkelanjutan
- Performa tinggi dan siap produksi

## Arsitektur Proyek
```
rozie-toolkit/
├── main.py              # Entry point aplikasi
├── modules/             # Modul fungsional utama
│   ├── detector.py      # Deteksi endpoint & form
│   ├── attacker.py      # Engine brute force
│   ├── analyzer.py      # Analisis respons
│   └── reporter.py      # Pelaporan hasil
├── interfaces/          # Abstract classes & interfaces
│   ├── plugin.py        # Interface plugin
│   └── proxy.py         # Interface proxy
├── plugins/             # Plugin ekstensibel
│   ├── captcha_solver/  # Plugin solver captcha
│   └── custom_auth/     # Plugin autentikasi kustom
├── utils/               # Utilitas pendukung
│   ├── logger.py        # Sistem logging
│   ├── config.py        # Manajemen konfigurasi
│   ├── proxy_handler.py # Handler berbagai jenis proxy
│   └── cli.py           # Interface command line
├── tests/               # Unit & integration tests
└── docs/                # Dokumentasi
```

## Instalasi
```bash
# Clone repository
git clone https://github.com/Rozie9103/rozie-toolkit.git
cd rozie-toolkit

# Buat virtual environment (opsional tapi direkomendasikan)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Penggunaan Dasar
```bash
# Menjalankan dengan konfigurasi default
python main.py

# Menjalankan dengan file konfigurasi kustom
python main.py --config custom_config.json

# Mode verbose untuk debugging
python main.py --verbose

# Menggunakan proxy spesifik
python main.py --proxy socks5://127.0.0.1:9050
```

Ikuti menu CLI interaktif untuk melakukan serangan brute force atau pengaturan lainnya.

## Pengembangan Plugin
Tambahkan file `.py` di folder `plugins/` dan implementasikan `PluginInterface`:

```python
from interfaces.plugin import PluginInterface

class CustomPlugin(PluginInterface):
    def __init__(self):
        self.name = "Custom Plugin"
        self.version = "1.0.0"
        
    def initialize(self):
        # Kode inisialisasi
        pass
        
    def execute(self, context):
        # Implementasi utama
        pass
        
    def cleanup(self):
        # Pembersihan resource
        pass
```

## Kontribusi
Pull request dan issue sangat diterima! Silakan ikuti panduan kontribusi di `docs/CONTRIBUTING.md`.

## Lisensi
MIT License

## Disclaimer
Alat ini dibuat hanya untuk tujuan edukasi dan pengujian keamanan legal. Penggunaan untuk aktivitas ilegal dilarang keras dan di luar tanggung jawab pengembang.
