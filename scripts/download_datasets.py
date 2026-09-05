#!/usr/bin/env python3
"""Download optional public datasets into data/. Re-run if a download fails."""

from __future__ import annotations

import os
import urllib.request

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))

UA = {"User-Agent": "Mozilla/5.0"}

TELCO_DIR = os.path.join(ROOT, "04-用户套餐分析")
TELCO_RAW = os.path.join(TELCO_DIR, "raw-telco-customer-churn.csv")

# IBM Telco 在 Kaggle；无稳定直链时提示手动下载
TELCO_HINT = "https://www.kaggle.com/datasets/blastchar/telco-customer-churn"


def dl_file(url: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading {url} ...")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    print(f"  -> {len(data) // 1024} KB", path)


def main() -> None:
    if os.path.isfile(TELCO_RAW) and os.path.getsize(TELCO_RAW) > 1000:
        print("skip (exists)", TELCO_RAW)
    else:
        print("Telco CSV 需从 Kaggle 手动下载：")
        print(" ", TELCO_HINT)
        print("  保存为:", TELCO_RAW)
        print("  见 data/00-手动下载说明.md")

    print("\nDone. 主线数据见 data/README.md（电商/交易明细已移除）")


if __name__ == "__main__":
    main()
