"""
BrickEconomy günlük çekim driver'ı (Faz 5c/Faz 3).

Çok günlük bir süreç: her çalıştırma, o günkü ~90 çağrılık güvenli payı
kullanır, sonra kendiliğinden durur. Zaten önbellekte olan setler atlanır
(resumable) — bu yüzden her gün aynı komutu tekrar çalıştırmak yeterli:

    source venv/bin/activate && python scripts/fetch_brickeconomy_daily.py

Sırasıyla:
  1) data/processed/brickeconomy_priority_sets.csv'deki 2.200 seti çeker
  2) 2.200'ü bitince, çekilen setlerin "minifigs" alanlarından benzersiz
     minifig kodları çıkarıp (~800 hedef) onları çeker
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv(PROJECT_ROOT / ".env")
api_key = os.environ["BRICKECONOMY_API_KEY"]

from brickeconomy_api import fetch_sets_resumable, fetch_minifigs_resumable

SETS_RAW_DIR = PROJECT_ROOT / "data/raw/brickeconomy/sets"
MINIFIGS_RAW_DIR = PROJECT_ROOT / "data/raw/brickeconomy/minifigs"
STATE_PATH = PROJECT_ROOT / "data/raw/brickeconomy/_quota_state.json"
MINIFIG_TARGET = 800


def log(msg):
    print(msg, flush=True)


def main():
    priority = pd.read_csv(PROJECT_ROOT / "data/processed/brickeconomy_priority_sets.csv")
    set_nums = priority["set_num"].tolist()

    cached_sets = len(list(SETS_RAW_DIR.glob("*.json"))) if SETS_RAW_DIR.exists() else 0
    log(f"Set aşaması: {cached_sets}/{len(set_nums)} zaten önbellekte.")

    if cached_sets < len(set_nums):
        result = fetch_sets_resumable(set_nums, api_key, SETS_RAW_DIR, STATE_PATH, log=log)
        log("=== Set aşaması (bu çalıştırma) bitti ===")
        log(f"Yeni çekilen: {len(result['fetched'])}, hatalı: {len(result['failed'])}, "
            f"durdurulan: {result['stopped_at']}, bugünkü kullanım: {result['final_usage']}/100")
        return  # aynı gün içinde minifig aşamasına geçme — yarın devam eder

    log("Tüm setler tamam. Minifig aşamasına geçiliyor.")

    # çekilen setlerin minifigs alanlarından benzersiz kod listesi çıkar
    minifig_codes = []
    seen = set()
    for path in sorted(SETS_RAW_DIR.glob("*.json")):
        body = json.loads(path.read_text())
        for code in (body.get("data", {}) or {}).get("minifigs", []) or []:
            if code not in seen:
                seen.add(code)
                minifig_codes.append(code)
    minifig_codes = minifig_codes[:MINIFIG_TARGET]
    log(f"Set yanıtlarından çıkarılan benzersiz minifig kodu: {len(minifig_codes)} (hedef: {MINIFIG_TARGET})")

    result = fetch_minifigs_resumable(minifig_codes, api_key, MINIFIGS_RAW_DIR, STATE_PATH, log=log)
    log("=== Minifig aşaması (bu çalıştırma) bitti ===")
    log(f"Yeni çekilen: {len(result['fetched'])}, hatalı: {len(result['failed'])}, "
        f"durdurulan: {result['stopped_at']}, bugünkü kullanım: {result['final_usage']}/100")


if __name__ == "__main__":
    main()
