#!/usr/bin/env python3
"""Download public datasets into data/. Re-run if a download fails."""

from __future__ import annotations

import io
import os
import urllib.request
import zipfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))

UA = {"User-Agent": "Mozilla/5.0"}

FUNNEL = os.path.join(ROOT, "02-电商漏斗")
RETAIL = os.path.join(ROOT, "03-交易明细")
OLIST = os.path.join(FUNNEL, "04-Olist巴西电商")
UCI_SHOPPERS = os.path.join(FUNNEL, "02-UCI购物意图")
UCI_CLICK = os.path.join(FUNNEL, "03-UCI点击流")


def dl_zip(url: str, outdir: str) -> None:
    os.makedirs(outdir, exist_ok=True)
    print(f"Downloading {url} ...")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
        z.extractall(outdir)
    print("  ->", os.listdir(outdir))


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
    tasks = [
        (
            "uci_clickstream",
            lambda: dl_zip(
                "https://archive.ics.uci.edu/static/public/553/clickstream+data+for+online+shopping.zip",
                UCI_CLICK,
            ),
        ),
        (
            "uci_online_shoppers",
            lambda: dl_zip(
                "https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip",
                UCI_SHOPPERS,
            ),
        ),
        (
            "uci_online_retail_ii",
            lambda: dl_zip(
                "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
                RETAIL,
            ),
        ),
    ]

    olist_base = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
    olist_files = [
        "olist_orders_dataset.csv",
        "olist_order_items_dataset.csv",
        "olist_customers_dataset.csv",
        "olist_order_payments_dataset.csv",
        "olist_products_dataset.csv",
        "product_category_name_translation.csv",
    ]
    for fn in olist_files:
        out = os.path.join(OLIST, fn)

        def _dl(f=fn, p=out):
            if os.path.isfile(p) and os.path.getsize(p) > 1000:
                print("skip (exists)", os.path.basename(p))
                return
            dl_file(olist_base + f, p)

        tasks.append((f"olist/{fn}", _dl))

    for name, fn in tasks:
        try:
            fn()
        except Exception as e:
            print(f"FAILED {name}: {e}")
            print("  See data/00-手动下载说明.md")

    print("\nDone. See data/README.md")


if __name__ == "__main__":
    main()
