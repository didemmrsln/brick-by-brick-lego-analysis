"""
BrickEconomy günlük çekim driver'ı (Faz 5c/Faz 3).

Çok günlük bir süreç: her çalıştırma, o günkü 100 çağrılık kotayı
kullanır, sonra kendiliğinden durur. Zaten önbellekte olan setler atlanır
(resumable) — bu yüzden her gün aynı komutu tekrar çalıştırmak yeterli:

    source venv/bin/activate && python scripts/fetch_brickeconomy_daily.py

launchd (~/Library/LaunchAgents/com.brickbybrick.fetch.plist) her gün 10:00'da
ve login/yüklemede otomatik tetikler. Aynı gün tekrar tetiklenirse kota sayacı
(_quota_state.json) dolu olduğu için istek atmadan çıkar. Çıktı ayrıca
logs/brickeconomy_fetch.log dosyasına zaman damgasıyla eklenir.

Sırasıyla:
  1) data/processed/brickeconomy_priority_sets.csv'deki 2.200 seti çeker
  2) 2.200'ü bitince, çekilen setlerin "minifigs" alanlarından benzersiz
     minifig kodları çıkarıp (~800 hedef) onları çeker
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv(PROJECT_ROOT / ".env")
api_key = os.environ["BRICKECONOMY_API_KEY"]

from brickeconomy_api import (
    DAILY_QUOTA_STOP_AT, fetch_sets_resumable, fetch_minifigs_resumable, load_quota_state, load_skip_list,
)

SETS_RAW_DIR = PROJECT_ROOT / "data/raw/brickeconomy/sets"
MINIFIGS_RAW_DIR = PROJECT_ROOT / "data/raw/brickeconomy/minifigs"
STATE_PATH = PROJECT_ROOT / "data/raw/brickeconomy/_quota_state.json"
SKIP_PATH = PROJECT_ROOT / "data/raw/brickeconomy/_skip_http400.json"  # BrickEconomy'nin tanımadığı kodlar
LOG_PATH = PROJECT_ROOT / "logs/brickeconomy_fetch.log"
MINIFIG_TARGET = 800


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    state = load_quota_state(STATE_PATH)
    if state["count"] >= DAILY_QUOTA_STOP_AT:
        log(f"Bugünkü kota zaten dolu ({state['date']} UTC, {state['count']}/100) — istek atılmadan çıkılıyor.")
        return

    priority = pd.read_csv(PROJECT_ROOT / "data/processed/brickeconomy_priority_sets.csv")
    set_nums = priority["set_num"].tolist()

    cached_sets = len(list(SETS_RAW_DIR.glob("*.json"))) if SETS_RAW_DIR.exists() else 0
    skipped = len(load_skip_list(SKIP_PATH) & set(set_nums))
    log(f"Set aşaması: {cached_sets}/{len(set_nums)} zaten önbellekte, {skipped} HTTP 400 nedeniyle atlanıyor.")

    if cached_sets + skipped < len(set_nums):
        result = fetch_sets_resumable(set_nums, api_key, SETS_RAW_DIR, STATE_PATH, log=log, skip_path=SKIP_PATH)
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

    result = fetch_minifigs_resumable(minifig_codes, api_key, MINIFIGS_RAW_DIR, STATE_PATH, log=log, skip_path=SKIP_PATH)
    log("=== Minifig aşaması (bu çalıştırma) bitti ===")
    log(f"Yeni çekilen: {len(result['fetched'])}, hatalı: {len(result['failed'])}, "
        f"durdurulan: {result['stopped_at']}, bugünkü kullanım: {result['final_usage']}/100")


if __name__ == "__main__":
    try:
        main()
    finally:
        # Drive for Desktop kurulu değilse script sessizce atlar (logs/drive_backup.log)
        subprocess.run(["/bin/zsh", str(PROJECT_ROOT / "scripts/backup_to_drive.sh")])
