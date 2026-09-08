"""
BrickEconomy API v1 için yardımcı fonksiyonlar.

notebooks/07_fetch_brickeconomy.ipynb ve scratchpad'teki fetch driver
tarafından kullanılır. BrickEconomy'nin (Brickset'in aksine) bir
getKeyUsageStats benzeri kendi kullanım-sayacı endpoint'i YOK, bu yüzden
günlük kotayı (100/gün) KENDİMİZ, yerel bir sayaç dosyasıyla takip ediyoruz.

Kimlik doğrulama: x-apikey header (.env'deki BRICKECONOMY_API_KEY).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://www.brickeconomy.com/api/v1"
THROTTLE_SECONDS = 15  # dakikada 4 istek sınırına uymak için
DAILY_QUOTA_STOP_AT = 90  # gerçek limit 100 — güvenlik payı bırakıyoruz


def _today_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def load_quota_state(state_path: Path) -> dict:
    """Günlük çağrı sayacını yükler; gün değiştiyse sıfırlar."""
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state.get("date") == _today_str():
            return state
    return {"date": _today_str(), "count": 0}


def save_quota_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))


def _throttled_get(path: str, api_key: str, state_path: Path) -> tuple[dict | None, int, dict]:
    """Tek bir GET isteği atar; öncesinde günlük kota kontrolü yapar, sonrasında
    THROTTLE_SECONDS bekler. Kota aşılmışsa (None, -1, state) döner (istek
    atmadan)."""
    state = load_quota_state(state_path)
    if state["count"] >= DAILY_QUOTA_STOP_AT:
        return None, -1, state

    resp = requests.get(f"{BASE_URL}{path}", headers={"x-apikey": api_key}, timeout=30)
    state["count"] += 1
    save_quota_state(state_path, state)
    time.sleep(THROTTLE_SECONDS)

    try:
        body = resp.json()
    except ValueError:
        body = None
    return body, resp.status_code, state


def fetch_set(set_num: str, api_key: str, state_path: Path) -> tuple[dict | None, int, dict]:
    return _throttled_get(f"/set/{set_num}", api_key, state_path)


def fetch_minifig(minifig_number: str, api_key: str, state_path: Path) -> tuple[dict | None, int, dict]:
    return _throttled_get(f"/minifig/{minifig_number}", api_key, state_path)


def fetch_sets_resumable(
    set_nums: list[str],
    api_key: str,
    raw_dir: Path,
    state_path: Path,
    log=print,
) -> dict:
    """Verilen set_num listesini sırayla çeker; her biri için
    raw_dir/{set_num}.json zaten varsa atlar (resumable). Günlük kota
    dolarsa DURUR (kalanları ertesi güne bırakır)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    fetched, skipped_cached, failed = [], [], []
    stopped_at = None

    for set_num in set_nums:
        path = raw_dir / f"{set_num}.json"
        if path.exists():
            skipped_cached.append(set_num)
            continue

        state = load_quota_state(state_path)
        if state["count"] >= DAILY_QUOTA_STOP_AT:
            log(f"DURDURULDU: günlük kullanım {state['count']} >= {DAILY_QUOTA_STOP_AT}. "
                f"'{set_num}' ve sonrası ertesi güne bırakıldı.")
            stopped_at = set_num
            break

        body, status, state = fetch_set(set_num, api_key, state_path)
        if body is None or status != 200:
            log(f"[{set_num}] HATA (HTTP {status}): {body}")
            failed.append(set_num)
            continue

        path.write_text(json.dumps(body, ensure_ascii=False, indent=2))
        fetched.append(set_num)
        log(f"[{set_num}] kaydedildi (bugünkü kullanım: {state['count']}/100)")

    return {
        "fetched": fetched,
        "skipped_cached": skipped_cached,
        "failed": failed,
        "stopped_at": stopped_at,
        "final_usage": load_quota_state(state_path)["count"],
    }


def fetch_minifigs_resumable(
    minifig_numbers: list[str],
    api_key: str,
    raw_dir: Path,
    state_path: Path,
    log=print,
) -> dict:
    """fetch_sets_resumable ile aynı mantık, minifig endpoint'i için."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    fetched, skipped_cached, failed = [], [], []
    stopped_at = None

    for minifig_number in minifig_numbers:
        path = raw_dir / f"{minifig_number}.json"
        if path.exists():
            skipped_cached.append(minifig_number)
            continue

        state = load_quota_state(state_path)
        if state["count"] >= DAILY_QUOTA_STOP_AT:
            log(f"DURDURULDU: günlük kullanım {state['count']} >= {DAILY_QUOTA_STOP_AT}. "
                f"'{minifig_number}' ve sonrası ertesi güne bırakıldı.")
            stopped_at = minifig_number
            break

        body, status, state = fetch_minifig(minifig_number, api_key, state_path)
        if body is None or status != 200:
            log(f"[{minifig_number}] HATA (HTTP {status}): {body}")
            failed.append(minifig_number)
            continue

        path.write_text(json.dumps(body, ensure_ascii=False, indent=2))
        fetched.append(minifig_number)
        log(f"[{minifig_number}] kaydedildi (bugünkü kullanım: {state['count']}/100)")

    return {
        "fetched": fetched,
        "skipped_cached": skipped_cached,
        "failed": failed,
        "stopped_at": stopped_at,
        "final_usage": load_quota_state(state_path)["count"],
    }
