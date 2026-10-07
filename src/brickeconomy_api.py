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
DAILY_QUOTA_STOP_AT = 100  # BrickEconomy Premium günlük limiti; 429 gelirse gün erken biter
NETWORK_RETRY_WAITS = (30, 60, 120)  # bağlantı koparsa bu kadar saniye bekleyip yeniden dene
NETWORK_ERROR = -2  # tüm denemeler ağ hatasıyla bittiğinde dönen status
AUTH_STATUSES = (401, 402, 403)  # anahtar reddedildi — üyelik bitmiş/iptal olmuş olabilir
EARLY_429_BELOW = 90  # 429 bu sayıdan önce gelirse günlük limit düşmüş demektir (üyelik seviyesi?)
MAX_CONSECUTIVE_FAILURES = 3  # 3.000+ istekte tek hata görüldü; art arda 3 hata tesadüf değil


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


def load_skip_list(skip_path: Path | None) -> set[str]:
    """Daha önce HTTP 400 almış (BrickEconomy'nin tanımadığı) kodlar."""
    if skip_path is None or not skip_path.exists():
        return set()
    return set(json.loads(skip_path.read_text()))


def add_to_skip_list(skip_path: Path | None, code: str) -> None:
    if skip_path is None:
        return
    codes = load_skip_list(skip_path)
    codes.add(code)
    skip_path.parent.mkdir(parents=True, exist_ok=True)
    skip_path.write_text(json.dumps(sorted(codes), indent=2))


def remove_from_skip_list(skip_path: Path | None, codes: list[str]) -> None:
    if skip_path is None or not codes:
        return
    remaining = load_skip_list(skip_path) - set(codes)
    skip_path.write_text(json.dumps(sorted(remaining), indent=2))


def _throttled_get(path: str, api_key: str, state_path: Path, log=print) -> tuple[dict | None, int, dict]:
    """Tek bir GET isteği atar; öncesinde günlük kota kontrolü yapar, sonrasında
    THROTTLE_SECONDS bekler. Kota aşılmışsa (None, -1, state) döner (istek
    atmadan).

    Bağlantı koparsa / zaman aşımına uğrarsa NETWORK_RETRY_WAITS kadar bekleyip
    yeniden dener; hepsi başarısız olursa (None, NETWORK_ERROR, state) döner ve
    çağıran taraf günü durdurur. Başarısız denemeler sayaca yazılmaz (sunucuya
    ulaşmadılar); sayacımız geride kalırsa sunucu 429 döner ve gün yine düzgünce biter."""
    state = load_quota_state(state_path)
    if state["count"] >= DAILY_QUOTA_STOP_AT:
        return None, -1, state

    for attempt, wait in enumerate((*NETWORK_RETRY_WAITS, None), start=1):
        try:
            resp = requests.get(f"{BASE_URL}{path}", headers={"x-apikey": api_key}, timeout=30)
            break
        except requests.RequestException as e:
            if wait is None:
                log(f"[{path}] ağ hatası ({type(e).__name__}), {attempt}. deneme de başarısız — vazgeçiliyor.")
                return None, NETWORK_ERROR, state
            log(f"[{path}] ağ hatası ({type(e).__name__}), {wait} sn sonra yeniden deneniyor ({attempt}/{len(NETWORK_RETRY_WAITS)}).")
            time.sleep(wait)
    state["count"] += 1
    save_quota_state(state_path, state)
    time.sleep(THROTTLE_SECONDS)

    try:
        body = resp.json()
    except ValueError:
        body = None
    return body, resp.status_code, state


def fetch_set(set_num: str, api_key: str, state_path: Path, log=print) -> tuple[dict | None, int, dict]:
    return _throttled_get(f"/set/{set_num}", api_key, state_path, log=log)


def fetch_minifig(minifig_number: str, api_key: str, state_path: Path, log=print) -> tuple[dict | None, int, dict]:
    return _throttled_get(f"/minifig/{minifig_number}", api_key, state_path, log=log)


def _fetch_resumable(codes: list[str], fetch_one, api_key: str, raw_dir: Path, state_path: Path,
                     log=print, skip_path: Path | None = None) -> dict:
    """Verilen kod listesini sırayla çeker; raw_dir/{kod}.json zaten varsa atlar (resumable).
    Günlük kota dolarsa, 429 gelirse ya da ağ tamamen koparsa DURUR (kalanları ertesi güne bırakır).
    skip_path verilirse HTTP 400 alan kodlar oraya yazılır ve sonraki çalıştırmalarda atlanır.

    Sonuçtaki "alert" doluysa çekim, üyelik/yetki sorununa işaret eden bir nedenle durdurulmuştur
    (bkz. AUTH_STATUSES, EARLY_429_BELOW, MAX_CONSECUTIVE_FAILURES) — çağıran taraf kullanıcıyı uyarmalı."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    fetched, skipped_cached, failed = [], [], []
    stopped_at = alert = None
    skip = load_skip_list(skip_path)
    streak, streak_skipped = [], []  # art arda başarısız istekler / bu seride skip listesine eklenenler

    for code in codes:
        path = raw_dir / f"{code}.json"
        if path.exists() or code in skip:
            skipped_cached.append(code)
            continue

        state = load_quota_state(state_path)
        if state["count"] >= DAILY_QUOTA_STOP_AT:
            log(f"DURDURULDU: günlük kullanım {state['count']} >= {DAILY_QUOTA_STOP_AT}. "
                f"'{code}' ve sonrası ertesi güne bırakıldı.")
            stopped_at = code
            break

        body, status, state = fetch_one(code, api_key, state_path, log=log)
        if status == 429:
            log(f"DURDURULDU: HTTP 429 (limit). '{code}' ve sonrası ertesi güne bırakıldı.")
            if state["count"] < EARLY_429_BELOW:
                alert = (f"HTTP 429 (limit aşıldı) günün {state['count']}. isteğinde geldi; normalde ~100. istekte gelir. "
                         "Günlük limit düşmüş — üyelik bitmiş ya da seviyesi değişmiş olabilir.")
            stopped_at = code
            break
        if status == NETWORK_ERROR:
            log(f"DURDURULDU: ağ hatası ({len(NETWORK_RETRY_WAITS) + 1} deneme başarısız). '{code}' ve sonrası ertesi güne bırakıldı.")
            stopped_at = code
            break
        if status in AUTH_STATUSES:
            log(f"DURDURULDU: HTTP {status} — API anahtarı reddedildi. Yanıt: {str(body)[:200]}")
            alert = f"BrickEconomy API anahtarı reddetti (HTTP {status}). Üyelik bitmiş ya da anahtar geçersiz olabilir."
            stopped_at = code
            break

        ok = status == 200 and isinstance(body, dict) and "data" in body
        if not ok:
            log(f"[{code}] HATA (HTTP {status}): {str(body)[:200]}")
            failed.append(code)
            streak.append(f"{code}: HTTP {status}")
            if status == 400:
                add_to_skip_list(skip_path, code)
                streak_skipped.append(code)
            if len(streak) >= MAX_CONSECUTIVE_FAILURES:
                # Bu kadar art arda hata "tanınmayan kod" değil, hesap/servis sorunu: skip eklemelerini geri al
                remove_from_skip_list(skip_path, streak_skipped)
                log(f"DURDURULDU: art arda {len(streak)} istek başarısız ({'; '.join(streak)}).")
                alert = (f"Art arda {len(streak)} istek başarısız oldu ({'; '.join(streak)}). "
                         "Üyelik bitmiş ya da BrickEconomy tarafında bir sorun olabilir.")
                stopped_at = code
                break
            continue

        streak, streak_skipped = [], []
        path.write_text(json.dumps(body, ensure_ascii=False, indent=2))
        fetched.append(code)
        log(f"[{code}] kaydedildi (bugünkü kullanım: {state['count']}/100)")

    return {
        "fetched": fetched,
        "skipped_cached": skipped_cached,
        "failed": failed,
        "stopped_at": stopped_at,
        "alert": alert,
        "final_usage": load_quota_state(state_path)["count"],
    }


def fetch_sets_resumable(set_nums: list[str], api_key: str, raw_dir: Path, state_path: Path,
                         log=print, skip_path: Path | None = None) -> dict:
    return _fetch_resumable(set_nums, fetch_set, api_key, raw_dir, state_path, log=log, skip_path=skip_path)


def fetch_minifigs_resumable(minifig_numbers: list[str], api_key: str, raw_dir: Path, state_path: Path,
                             log=print, skip_path: Path | None = None) -> dict:
    return _fetch_resumable(minifig_numbers, fetch_minifig, api_key, raw_dir, state_path, log=log, skip_path=skip_path)
