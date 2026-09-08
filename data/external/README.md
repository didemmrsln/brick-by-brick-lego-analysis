# Harici veri kaynakları (data/external/)

Bu klasördeki dosyalar Rebrickable/BrickEconomy/Brickset dışında, üçüncü
parti kaynaklardan indirilen fiyat verilerini içerir. Henüz `sets_clean.csv`
ile birleştirilmedi — sadece toplandı ve yapıları raporlandı (bkz. proje
sohbet geçmişi / commit mesajı).

## rpmoo/lego-eda (GitHub)

Kaynak: https://github.com/rpmoo/lego-eda — BrickLink API (9527 unique set)
üzerinden toplanmış new/used piyasa fiyatı verisi.

- `lego-eda_df_sets_new.csv` — 15.497 satır. Kolonlar: `set_num, name, year,
  theme_id, num_parts, price_mean_N, price_min_N, price_max_N, set_qty_N,
  currency_N`. "Yeni (açılmamış)" BrickLink piyasa fiyatı. 9.527 satırda
  gerçek (>0) fiyat var, geri kalanı 0.0 + `currency_N="none"` ile
  dolduruimuş (NaN değil, sentinel değer).
- `lego-eda_df_sets_used.csv` — aynı şema, `_N` son eki olmadan
  (`price_mean, price_min, price_max, set_qty, currency`). "Kullanılmış"
  piyasa fiyatı. 8.538 satırda gerçek (>0) fiyat var.
- `set_num` formatı bizimkiyle **birebir uyumlu** (`"001-1"`, `"10278-1"` gibi,
  rebrickable formatı) — normalize etmeye gerek yok.
- Repo'nun `data/` klasöründeki diğer dosyalar (colors.csv, sets.csv,
  parts.csv, vb.) Rebrickable'ın ham tablolarının birebir kopyası —
  bunları indirmedik, zaten `data/raw/` altında elimizde var.

## Kaggle: alexracape/lego-sets-and-prices-over-time

**İndirilmedi.** `~/.kaggle/kaggle.json` yok, `kaggle` CLI kurulu değil.
Kurulum sonrası şu komutla indirilebilir:

```bash
kaggle datasets download -d alexracape/lego-sets-and-prices-over-time -p data/external/ --unzip
```
