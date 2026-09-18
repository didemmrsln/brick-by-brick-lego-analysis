# Brick by Brick: LEGO Setlerinin Evrimi Üzerine Bir Veri Analizi

[Rebrickable](https://rebrickable.com) veri setini kullanarak LEGO setlerinin 1949'dan
günümüze nasıl değiştiğini inceleyen bir veri analizi projesi.

## Araştırma Sorusu

LEGO setleri zaman içinde **karmaşıklık** (parça sayısı), **fiyat**, **renk paleti** ve
**tema başarısı/ömrü** açısından nasıl evrildi — ve bu eğilimlerden gelecekteki setler için
ne öğrenilebilir?

Bu soru dört alt bölümde ele alınıyor (bkz. [TASKS.md](TASKS.md)):

1. **Karmaşıklık trendi** — Set başına ortalama parça sayısı yıllar içinde nasıl değişti?
2. **Fiyat tahmini** — Set özelliklerinden (parça sayısı, tema, yıl vb.) `scikit-learn` ile
   fiyat tahmini yapılabilir mi?
3. **Renk paleti evrimi** — Kullanılan renkler zaman içinde nasıl değişti?
4. **Tema ömrü/başarı tahmini** — Bir temanın ne kadar süre / kaç set boyunca devam edeceği
   önceden kestirilebilir mi?

## Klasör Yapısı

```
brick_by_brick_data/
├── data/
│   ├── raw/          # Rebrickable'dan indirilen ham CSV'ler (git'e girmez, bkz. .gitignore)
│   └── processed/    # Temizlenmiş / zenginleştirilmiş, analiz-hazır tablolar (git'e girer)
├── notebooks/         # Sıra numaralı Jupyter notebook'lar (01_..., 02_..., ...)
├── src/                # Notebook'lar arasında paylaşılan yeniden kullanılabilir Python kodu
├── reports/            # Üretilen grafikler, özetler, dışa aktarılan raporlar
├── requirements.txt    # Python bağımlılıkları
├── TASKS.md            # Faz/bölüm bazlı to-do listesi
└── README.md           # Bu dosya
```

Ham veri (`data/raw/`) büyük olduğu ve yeniden üretilebilir olduğu için repoya dahil edilmiyor;
`data/processed/` altındaki temizlenmiş tablolar ise tekrarlanabilirlik için repoya dahil ediliyor.

**İstisna — Brickset ve BrickEconomy verileri:** Bu kaynaklar veriyi üyelik/API anahtarı ile
sağlıyor ve kullanım koşulları yeniden dağıtıma izin vermiyor. Bu yüzden şu iki tablo repoda
**yer almaz**; kendi API anahtarlarınızla (`.env` → `BRICKSET_API_KEY`, `BRICKECONOMY_API_KEY`)
yerelde yeniden üretebilirsiniz:

| Dosya | Nasıl üretilir |
|---|---|
| `data/processed/brickset_prices.csv` | `notebooks/05_fetch_brickset_prices.ipynb` |
| `data/processed/brickeconomy_priority_sets.csv` | `notebooks/06_brickeconomy_priority_selection.ipynb` (05'in çıktısını kullanır) |

BrickEconomy fiyat verisi `scripts/fetch_brickeconomy_daily.py` ile günlük olarak `data/raw/brickeconomy/`
altına çekilir; o klasör de git'e girmez.

## Veri Kaynağı

[Rebrickable](https://rebrickable.com/downloads/) — LEGO setleri, parçalar, envanterler,
minifigürler, renkler ve temalar hakkında düzenli güncellenen açık veri seti.

## Kurulum

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Ham CSV/zip dosyalarını `data/raw/` altına yerleştirin (bkz. yukarıdaki "Veri Kaynağı"),
ardından `notebooks/01_data_quality_check.ipynb`'i baştan sona çalıştırın.

## İlerleme Durumu

- ✅ **Faz 1 — Veri edinme**: Rebrickable CSV'leri `data/raw/` altında.
- ✅ **Faz 2 — Altyapı**: VS Code, venv, git kuruldu.
- ✅ **Faz 3 — Ham veri**: 11 Rebrickable tablosu `data/raw/` içinde.
- ✅ **Faz 4 — Temizlik/staging**: `data/processed/sets_clean.csv` — merch/promosyon
  temaları ve `num_parts=0` kayıtları filtrelendi; yıl bazlı trend analizleri için
  `is_analysis_ready` bayrağı eklendi (bkz. `notebooks/01_data_quality_check.ipynb`).
- ⏳ **Faz 5 — Zenginleştirme**: `inventory_parts` + `colors` join'i, minifig sayısı (planlanıyor).
- ⏳ **Faz 6 — Analiz-hazır tablolar**: tema/yıl agregasyonları (planlanıyor).

Detaylı, güncel to-do listesi için [TASKS.md](TASKS.md) dosyasına bakın.
