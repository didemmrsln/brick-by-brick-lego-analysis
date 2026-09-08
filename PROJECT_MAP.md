# Proje Haritası

**Son güncelleme: 2026-09-08** — Bölüm 1 (karmaşıklık trendi) tamamlandı,
Bölüm 2 (fiyat regresyonu) için veri hazır ama modelleme henüz başlamadı,
BrickEconomy çekimi ~81/2.200 tamamlandı (devam ediyor, ~30 günlük süreç).

## Veri akışı

```mermaid
flowchart TD
    A["sets.csv (Rebrickable ham)<br/>28.180 set"]
    A -->|"num_parts=0 VEYA merch tema filtrelendi — §8"| B
    B["sets_clean.csv<br/>18.899 set (%67,1 kaldı, %32,9 çıkarıldı)"]
    B -->|"year > 2025 çıkarıldı — is_analysis_ready flag, §9"| C
    C["sets_clean (analiz-hazır)<br/>18.190 set"]
    C -->|"minifig_count eklendi — Faz 5a, notebook 03"| C
    C -->|"Brickset retail price join denendi — notebook 05"| D
    D["Brickset ile eşleşen<br/>6.614 set (%36,4)"]
    D --> D2["Bölüm 2 (fiyat regresyonu) ana veri seti"]
    D -->|"üretim süresi + num_parts skoruna göre öncelikli 2.200 seçildi — notebook 06"| E
    E["BrickEconomy'den zenginleştiriliyor<br/>(devam ediyor, ~30 gün)<br/>2.200 set + ~800 minifig"]
    E --> E2["Faz 3 (retired sonrası değer artışı) veri seti"]

    C -->|"inventory_parts + colors join — Faz 5b, HENÜZ YAPILMADI"| F
    F["renk verisi (planlanan)"]
    F --> F2["Bölüm 3 (renk paleti evrimi)"]

    style E2 fill:#2a78d6,color:#fff
    style D2 fill:#2a78d6,color:#fff
    style F fill:#eb6834,color:#fff
    style F2 fill:#eb6834,color:#fff
```

## Bugün nerede kaldık

- **Bölüm 1 (karmaşıklık trendi):** Tamamlandı.
- **Bölüm 2 (fiyat regresyonu):** Veri seti hazır (Brickset, n=6.614) ama
  eşleşme yanlılığı (2015 sonrasına ve büyük/flagship setlere yığılma)
  dokümante edildi (notebook 05, DATA_SOURCES.md) — modelleme henüz
  başlamadı.
- **Bölüm 3 (renk paleti evrimi):** Henüz başlamadı — Faz 5b (inventory_parts
  + colors join) bekliyor.
- **Bölüm 4 (tema ömrü/başarı):** Henüz başlamadı.
- **Faz 3 (retired sonrası değer artışı, BrickEconomy):** Çekim sürüyor —
  günlük 100/dakikada 4 istek limiti nedeniyle resumable, kendi kendini
  günlük ~90 çağrıda durduran bir script ile ~30 güne yayılmış durumda.
  Bugünkü ilerleme: ~81/2.200 set (+ ~800 minifig kotası, setler bitince
  başlayacak).
