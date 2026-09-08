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

**İndirildi** → `kaggle_lego_sets_prices.csv` (14.936 satır, 17 kolon).

Kaynak (Kaggle dataset açıklamasına göre): **Brickset API (liste fiyatı/MSRP
+ özellikler) + BrickLink API (resale/ikinci-el fiyatı)**, ikisi de
**"as of 05/10/2023"** (05 Ekim ya da 10 Mayıs 2023 — Kaggle ABD merkezli
olduğu için muhtemelen MM/DD, yani **10 Mayıs 2023**). `expectedUpdateFrequency:
"never"` — tek seferlik statik bir çekim, güncellenmiyor.

Kolonlar: `Set_ID, Name, Year, Theme, Theme_Group, Subtheme, Category,
Packaging, Num_Instructions, Availability, Pieces, Minifigures, Owned,
Rating, USD_MSRP, Total_Quantity, Current_Price`

- `USD_MSRP` doluluk: 5.837/14.936 (%39.1)
- `Current_Price` (BrickLink resale) doluluk: 5.442/14.936 (%36.4)
- Şema Brickset'in kendi alan adlarıyla neredeyse birebir örtüşüyor
  (`Theme_Group`, `Subtheme`, `Availability`, `Packaging`, `Owned`, `Rating`)
  — muhtemelen doğrudan Brickset `getSets` çıktısından türetilmiş.

**`Set_ID` uyumluluğu:** Bizim `set_num` formatıyla (rebrickable, zero-padded)
**12.681/14.936 (%84.9) doğrudan birebir eşleşiyor**. Kalan 2.255'in
leading-zero normalize edilmesiyle (`077-1` ↔ `77-1` gibi) sadece **9 tanesi
daha** kurtarılabiliyor — yani bu bir padding hatası değil, **`77-1` ve
`077-1` gerçekten farklı iki resmi LEGO set numarası** (kontrol ettim: 1975,
"PreSchool Set" vs "Pre-School Set/Duplo" — aynı yıl, farklı setler).
Kalan ~2.246 eşleşmeyen `Set_ID`'nin büyük kısmı **gear/merch ürün kodları**
(`85xxxx-1` formatında, `Category="Gear"` — 629 satır) ve özel/promosyonel
kodlar (`S020-1`, `KSB28-1`, `BK11SPR1990-1` gibi) ile CMF minifig-varyant
kodları (`71037-13`) — yani Brickset'in zaten bildiğimiz merch/gear kapsamı
genişliğinden kaynaklanıyor, bir normalize hatası değil.
**Normalize etme mantığı (henüz uygulanmadı):** `set_num` string olarak
tutulmalı (int'e çevrilmemeli, leading zero kaybolur), doğrudan string eşleşme
yeterli — leading-zero stripping gereksiz overhead + yanlış eşleştirme riski
taşıyor (bkz. 77-1/077-1 örneği).
