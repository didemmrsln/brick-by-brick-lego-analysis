"""
Brickset API v3 (getSets) için yardımcı fonksiyonlar.

notebooks/05_fetch_brickset_prices.ipynb tarafından kullanılır. Amaç: yıl bazlı
toplu retail price çekimi — dakikada 4 istek / günde 100 getSets çağrısı
limitlerine uyarak, kesintiye dayanıklı (resumable) şekilde.

Kimlik doğrulama: apiKey + boş userHash (public set verisi için userHash
gerekmiyor, bkz. proje notları).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://brickset.com/api/v3.asmx"
THROTTLE_SECONDS = 15  # dakikada 4 istek sınırına uymak için istekler arası bekleme
DAILY_QUOTA_STOP_AT = 90  # getSets için günlük 100 çağrı sınırına yaklaşınca dur


def _throttled_post(endpoint: str, data: dict) -> dict:
    """Brickset'e tek bir POST isteği atar, sonrasında THROTTLE_SECONDS bekler."""
    resp = requests.post(f"{BASE_URL}/{endpoint}", data=data, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    time.sleep(THROTTLE_SECONDS)
    return j


def get_usage_today(api_key: str) -> int:
    """getKeyUsageStats üzerinden bugünkü getSets çağrı sayısını döndürür.

    Bu endpoint günlük getSets kotasına dahil değil (ayrı test edildi), bu
    yüzden güvenle sık sık çağrılabilir.
    """
    j = _throttled_post("getKeyUsageStats", {"apiKey": api_key})
    if j.get("status") != "success":
        raise RuntimeError(f"getKeyUsageStats başarısız: {j}")
    today = datetime.now(timezone.utc).date().isoformat()
    for entry in j.get("apiKeyUsage", []):
        # dateStamp formatı: "2026-09-08T00:00:00Z"
        if entry.get("dateStamp", "").startswith(today):
            return entry.get("count", 0)
    return 0


def fetch_year_raw(api_key: str, year: int, page_size: int = 2000) -> dict:
    """Bir yıl için TÜM setleri (gerekirse sayfalayarak) çeker.

    Dönen dict: {"year", "matches", "fetched_at", "sets": [...]} — "sets" ham
    Brickset set objelerinin (extendedData dahil) birleşik listesi.
    """
    all_sets: list[dict] = []
    matches = None
    page = 1
    while True:
        params = json.dumps(
            {"year": str(year), "pageSize": page_size, "pageNumber": page, "extendedData": 1}
        )
        j = _throttled_post(
            "getSets", {"apiKey": api_key, "userHash": "", "params": params}
        )
        if j.get("status") != "success":
            raise RuntimeError(f"getSets başarısız (year={year}, page={page}): {j}")
        matches = j.get("matches", 0)
        sets = j.get("sets", [])
        all_sets.extend(sets)
        if matches is None or len(all_sets) >= matches or len(sets) < page_size or not sets:
            break
        page += 1
    return {
        "year": year,
        "matches": matches,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sets": all_sets,
    }


def fetch_all_years(
    api_key: str,
    years: list[int],
    raw_dir: Path,
    quota_stop_at: int = DAILY_QUOTA_STOP_AT,
    log=print,
) -> dict:
    """Verilen yıl listesini sırayla çeker; her yıl için:

    - data/raw/brickset/{year}.json zaten varsa atlar (resumable)
    - yoksa önce günlük kullanım kontrolü yapar; quota_stop_at'a ulaşıldıysa
      DURUR (kalan yılları çekmez), nerede kaldığını raporlar
    - aksi halde o yılı çeker ve ham sonucu kaydeder

    Dönen dict: {"fetched": [...], "skipped_cached": [...], "stopped_at": year|None,
                 "last_known_usage": int|None}
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    fetched, skipped_cached = [], []
    stopped_at = None
    last_known_usage = None

    for year in years:
        path = raw_dir / f"{year}.json"
        if path.exists():
            skipped_cached.append(year)
            continue

        usage = get_usage_today(api_key)
        last_known_usage = usage
        log(f"[{year}] bugünkü getSets kullanımı: {usage}/100")
        if usage >= quota_stop_at:
            log(
                f"DURDURULDU: kullanım {usage} >= {quota_stop_at} eşiği. "
                f"{year} ve sonrası ertesi güne bırakıldı."
            )
            stopped_at = year
            break

        result = fetch_year_raw(api_key, year)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        fetched.append(year)
        log(f"[{year}] kaydedildi: {len(result['sets'])} set (matches={result['matches']})")

    return {
        "fetched": fetched,
        "skipped_cached": skipped_cached,
        "stopped_at": stopped_at,
        "last_known_usage": last_known_usage,
    }


def extract_price_row(set_obj: dict) -> dict:
    """Tek bir Brickset set objesinden fiyat tablosu için düz bir satır çıkarır."""
    number = set_obj.get("number")
    variant = set_obj.get("numberVariant")
    brickset_set_num = f"{number}-{variant}" if number is not None and variant is not None else None
    lego_com = set_obj.get("LEGOCom") or {}

    def region(code):
        r = lego_com.get(code) or {}
        return r.get("retailPrice"), r.get("dateFirstAvailable"), r.get("dateLastAvailable")

    us_price, us_first, us_last = region("US")
    uk_price, _, _ = region("UK")
    ca_price, _, _ = region("CA")
    de_price, _, _ = region("DE")

    return {
        "brickset_set_num": brickset_set_num,
        "retail_price_us": us_price,
        "retail_price_uk": uk_price,
        "retail_price_ca": ca_price,
        "retail_price_de": de_price,
        "date_first_available": us_first,
        "date_last_available": us_last,
    }
