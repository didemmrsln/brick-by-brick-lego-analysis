"""
Rebrickable ham tabloları için paylaşılan yardımcılar.

Envanter zinciri (bkz. notebooks/01_data_quality_check.ipynb §10):

    set_num --(inventories.csv, en güncel version)--> inventory_id --> inventory_parts / inventory_minifigs
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

INVENTORY_PARTS_DTYPES = {"inventory_id": "int32", "color_id": "int16", "quantity": "int32", "is_spare": "bool"}


def latest_inventory(inventories: pd.DataFrame) -> pd.DataFrame:
    """Her set_num için en güncel (en yüksek version) envanter → [set_num, inventory_id].

    Bazı setlerin birden fazla envanter versiyonu var; sets.csv'deki num_parts en güncel
    versiyonu yansıtıyor (§10'da 8/8 set ile doğrulandı). 01 §10 ve 03 notebook'undaki
    mantıkla aynı.
    """
    return (
        inventories.sort_values("version")
        .groupby("set_num", as_index=False)
        .tail(1)[["set_num", "id"]]
        .rename(columns={"id": "inventory_id"})
        .reset_index(drop=True)
    )


def read_inventory_parts(raw_dir: str | Path) -> pd.DataFrame:
    """inventory_parts.csv'yi (~133 MB) bellek dostu okur.

    img_url ve part_num okunmaz, sayısal kolonlar dar tiplere indirilir: tam okuma ~293 MB
    bellek tutarken bu yol ~17 MB tutar, bu yüzden chunk'lı okumaya gerek kalmaz.
    """
    return pd.read_csv(
        Path(raw_dir) / "inventory_parts.csv",
        usecols=list(INVENTORY_PARTS_DTYPES),
        dtype=INVENTORY_PARTS_DTYPES,
    )
