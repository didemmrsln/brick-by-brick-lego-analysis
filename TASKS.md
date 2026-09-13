# TASKS

## Veri altyapısı

- [x] Faz 1 — Veri edinme (Rebrickable CSV'leri)
- [x] Faz 2 — Altyapı (VS Code, venv, git)
- [x] Faz 3 — Ham veri (data/raw/)
- [x] Faz 4 — Temizlik/staging (sets_clean.csv, is_analysis_ready flag)
- [ ] Faz 5 — Zenginleştirme
  - [x] Faz 5a — minifig_count (inventories + inventory_minifigs join, bkz. notebooks/03_add_minifig_count.ipynb)
  - [x] Faz 5b — Renk verisi, **minifig renkleri dahil, tamamlandı** (set parçaları + minifig parçaları birleşik renk dağılımı; bkz. notebooks/07_color_enrichment.ipynb → data/processed/set_colors.csv)
- [ ] Faz 6 — Analiz-hazır tablolar (tema/yıl agregasyonları)

## Analiz bölümleri

- [ ] Bölüm 1 — Karmaşıklık trendi
- [ ] Bölüm 2 — Fiyat tahmini (sklearn regresyon)
- [ ] Bölüm 3 — Renk paleti evrimi
- [ ] Bölüm 4 — Tema ömrü/başarı tahmini

## Proje fazları (harici veri)

- [ ] Faz 2 (proje fazı, Google Trends)
- [ ] Faz 3 (proje fazı, BrickEconomy/BrickLink)

## Teknik borç

- [ ] `notebooks/03_add_minifig_count.ipynb` henüz `src/rebrickable.py`'deki ortak envanter eşleştirme
  fonksiyonuna (`latest_inventory()`) geçirilmedi. Notebook `sets_clean.csv`'yi yerinde güncellediği için
  tekrar çalıştırılırsa `minifig_count` çifte eklenir riski var. İleride düzeltilebilir, şu an acil değil.
