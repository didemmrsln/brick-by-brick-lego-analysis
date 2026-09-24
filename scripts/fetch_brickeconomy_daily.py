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

Sırasıyla (bkz. notebooks/06_brickeconomy_priority_selection.ipynb, bölüm 5):
  1) data/processed/brickeconomy_priority_sets.csv'deki sıra 1–2.200 setleri çeker
  2) bu setlerin "minifigs" alanlarından benzersiz minifig kodlarını çıkarıp
     (~800 hedef) onları çeker
  3) sıra 2.201–6.614 setleri çeker (genişleme; üyelik bitince nerede kalırsa)
Bir aşama gün ortasında biterse kalan kota aynı çalıştırmada sonraki aşamaya harcanır.
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
PRIMARY_SET_COUNT = 2200  # ilk plan; minifigler bundan sonra, genişleme en sonda
MINIFIG_TARGET = 800


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def report(phase, result):
    log(f"=== {phase} (bu çalıştırma) bitti — yeni: {len(result['fetched'])}, hatalı: {len(result['failed'])}, "
        f"durdurulan: {result['stopped_at']}, bugünkü kullanım: {result['final_usage']}/100 ===")


def pending(codes, raw_dir, skip):
    return [c for c in codes if c not in skip and not (raw_dir / f"{c}.json").exists()]


def minifig_codes_from(set_nums):
    """Setlerin öncelik sırasına göre, yanıtlarındaki minifig kodları (tekrarsız)."""
    codes, seen = [], set()
    for set_num in set_nums:
        path = SETS_RAW_DIR / f"{set_num}.json"
        if not path.exists():
            continue
        body = json.loads(path.read_text())
        for code in (body.get("data", {}) or {}).get("minifigs", []) or []:
            if code not in seen:
                seen.add(code)
                codes.append(code)
    return codes[:MINIFIG_TARGET]


def main():
    state = load_quota_state(STATE_PATH)
    if state["count"] >= DAILY_QUOTA_STOP_AT:
        log(f"Bugünkü kota zaten dolu ({state['date']} UTC, {state['count']}/100) — istek atılmadan çıkılıyor.")
        return

    priority = pd.read_csv(PROJECT_ROOT / "data/processed/brickeconomy_priority_sets.csv")
    set_nums = priority.sort_values("priority_rank")["set_num"].tolist()
    primary, extension = set_nums[:PRIMARY_SET_COUNT], set_nums[PRIMARY_SET_COUNT:]
    skip = load_skip_list(SKIP_PATH)

    # 1) sıra 1–2.200
    todo = pending(primary, SETS_RAW_DIR, skip)
    log(f"Aşama 1 (set 1–{PRIMARY_SET_COUNT}): {len(primary) - len(todo)}/{len(primary)} tamam.")
    if todo:
        result = fetch_sets_resumable(primary, api_key, SETS_RAW_DIR, STATE_PATH, log=log, skip_path=SKIP_PATH)
        report("Aşama 1", result)
        if result["stopped_at"]:
            return

    # 2) minifigler
    minifig_codes = minifig_codes_from(primary)
    todo = pending(minifig_codes, MINIFIGS_RAW_DIR, load_skip_list(SKIP_PATH))
    log(f"Aşama 2 (minifig): {len(minifig_codes) - len(todo)}/{len(minifig_codes)} tamam (hedef: {MINIFIG_TARGET}).")
    if todo:
        result = fetch_minifigs_resumable(minifig_codes, api_key, MINIFIGS_RAW_DIR, STATE_PATH, log=log, skip_path=SKIP_PATH)
        report("Aşama 2", result)
        if result["stopped_at"]:
            return

    # 3) sıra 2.201+
    todo = pending(extension, SETS_RAW_DIR, load_skip_list(SKIP_PATH))
    log(f"Aşama 3 (set {PRIMARY_SET_COUNT + 1}–{len(set_nums)}): {len(extension) - len(todo)}/{len(extension)} tamam.")
    if todo:
        result = fetch_sets_resumable(extension, api_key, SETS_RAW_DIR, STATE_PATH, log=log, skip_path=SKIP_PATH)
        report("Aşama 3", result)
    else:
        log("Tüm aşamalar tamamlandı — çekilecek bir şey kalmadı.")


if __name__ == "__main__":
    # Çekim + yedek süresince Mac'in uykuya geçmesini engelle (caffeinate bu süreç bitince kendiliğinden kapanır).
    # -i: boşta uyku, -s: sistem uykusu (yalnızca prize takılıyken geçerli). Kapak kapalı ve pildeyken macOS
    # yine uyuyabilir; o durumda ağ hatası yeniden denemesi devreye girer.
    subprocess.Popen(["/usr/bin/caffeinate", "-i", "-s", "-w", str(os.getpid())])
    try:
        main()
    finally:
        # Drive for Desktop kurulu değilse script sessizce atlar (logs/drive_backup.log)
        subprocess.run(["/bin/zsh", str(PROJECT_ROOT / "scripts/backup_to_drive.sh")])
