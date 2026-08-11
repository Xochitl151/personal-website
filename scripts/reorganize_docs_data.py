#!/usr/bin/env python3
"""One-time reorganize docs/ and data/ into numbered folders."""

from __future__ import annotations

import os
import shutil

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

DOC_MOVES = {
    "REQUIREMENTS.md": "01-建站/01-需求说明.md",
    "PREPARATION.md": "01-建站/02-准备清单.md",
    "PROJECTS.md": "01-建站/03-项目协作.md",
    "DEPLOY.md": "01-建站/04-部署说明.md",
    "面试背诵.md": "02-面试/01-面试背诵.md",
    "竞赛口述.md": "02-面试/02-竞赛口述.md",
    "数据说明与面试口径.md": "02-面试/03-数据说明与面试口径.md",
    "BI看板作品.md": "03-数据分析/01-BI看板作品.md",
    "Tableau快速上手.md": "03-数据分析/02-Tableau快速上手.md",
    "Tableau实习级看板指南.md": "03-数据分析/03-Tableau实习级看板指南.md",
    "互动展示构思.md": "04-网站进阶/01-互动展示构思.md",
}

PATH_REPLACEMENTS = [
    ("docs/01-建站/01-需求说明.md", "docs/01-建站/01-需求说明.md"),
    ("docs/01-建站/02-准备清单.md", "docs/01-建站/02-准备清单.md"),
    ("docs/01-建站/03-项目协作.md", "docs/01-建站/03-项目协作.md"),
    ("docs/01-建站/04-部署说明.md", "docs/01-建站/04-部署说明.md"),
    ("docs/02-面试/01-面试背诵.md", "docs/02-面试/01-面试背诵.md"),
    ("docs/02-面试/02-竞赛口述.md", "docs/02-面试/02-竞赛口述.md"),
    ("docs/02-面试/03-数据说明与面试口径.md", "docs/02-面试/03-数据说明与面试口径.md"),
    ("docs/03-数据分析/01-BI看板作品.md", "docs/03-数据分析/01-BI看板作品.md"),
    ("docs/03-数据分析/02-Tableau快速上手.md", "docs/03-数据分析/02-Tableau快速上手.md"),
    ("docs/03-数据分析/03-Tableau实习级看板指南.md", "docs/03-数据分析/03-Tableau实习级看板指南.md"),
    ("docs/04-网站进阶/01-互动展示构思.md", "docs/04-网站进阶/01-互动展示构思.md"),
    ("`docs/01-建站/01-需求说明.md`", "`docs/01-建站/01-需求说明.md`"),
    ("`docs/01-建站/02-准备清单.md`", "`docs/01-建站/02-准备清单.md`"),
    ("`docs/01-建站/03-项目协作.md`", "`docs/01-建站/03-项目协作.md`"),
    ("01-招投标搜索/01-练习小样本.csv", "01-招投标搜索/01-练习小样本.csv"),
    ("01-招投标搜索/02-实习级练习.csv", "01-招投标搜索/02-实习级练习.csv"),
    ("02-电商漏斗/01-漏斗汇总_按渠道.csv", "02-电商漏斗/01-漏斗汇总_按渠道.csv"),
    ("data/02-电商漏斗/02-UCI购物意图/", "data/02-电商漏斗/02-UCI购物意图/"),
    ("data/02-电商漏斗/03-UCI点击流/", "data/02-电商漏斗/03-UCI点击流/"),
    ("data/02-电商漏斗/04-Olist巴西电商/", "data/02-电商漏斗/04-Olist巴西电商/"),
    ("data/00-手动下载说明.md", "data/00-手动下载说明.md"),
    ("data/03-交易明细/", "data/03-交易明细/"),
    ("assets/projects/01-bidding-analytics/raw/01-招投标搜索/02-实习级练习.csv",
     "data/01-招投标搜索/02-实习级练习.csv"),
    ("assets/projects/01-bidding-analytics/raw/01-招投标搜索/01-练习小样本.csv",
     "data/01-招投标搜索/01-练习小样本.csv"),
]


def move_docs() -> None:
    docs_dir = os.path.join(ROOT, "docs")
    for old, new in DOC_MOVES.items():
        src = os.path.join(docs_dir, old)
        dst = os.path.join(docs_dir, new)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            print("doc:", old, "->", new)


def move_file(src: str, dst: str) -> None:
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.normpath(src) != os.path.normpath(dst):
            shutil.move(src, dst)
        print("data:", os.path.basename(src), "->", os.path.relpath(dst, os.path.join(ROOT, "data")))


def move_dir_contents(src_dir: str, dst_dir: str) -> None:
    if not os.path.isdir(src_dir):
        return
    os.makedirs(dst_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        s = os.path.join(src_dir, name)
        d = os.path.join(dst_dir, name)
        if os.path.isfile(s):
            shutil.move(s, d)
    if not os.listdir(src_dir):
        os.rmdir(src_dir)


def move_data() -> None:
    data_dir = os.path.join(ROOT, "data")
    move_file(
        os.path.join(data_dir, "01-招投标搜索/01-练习小样本.csv"),
        os.path.join(data_dir, "01-招投标搜索", "01-练习小样本.csv"),
    )
    move_file(
        os.path.join(data_dir, "01-招投标搜索/02-实习级练习.csv"),
        os.path.join(data_dir, "01-招投标搜索", "02-实习级练习.csv"),
    )
    move_file(
        os.path.join(data_dir, "02-电商漏斗/01-漏斗汇总_按渠道.csv"),
        os.path.join(data_dir, "02-电商漏斗", "01-漏斗汇总_按渠道.csv"),
    )
    move_dir_contents(
        os.path.join(data_dir, "uci_online_shoppers"),
        os.path.join(data_dir, "02-电商漏斗", "02-UCI购物意图"),
    )
    move_dir_contents(
        os.path.join(data_dir, "uci_clickstream_shopping"),
        os.path.join(data_dir, "02-电商漏斗", "03-UCI点击流"),
    )
    move_dir_contents(
        os.path.join(data_dir, "olist_brazilian_ecommerce"),
        os.path.join(data_dir, "02-电商漏斗", "04-Olist巴西电商"),
    )
    manual = os.path.join(data_dir, "MANUAL_DOWNLOAD.md")
    if os.path.isfile(manual):
        shutil.move(manual, os.path.join(data_dir, "00-手动下载说明.md"))

    os.makedirs(os.path.join(data_dir, "03-交易明细"), exist_ok=True)

    for d in ["uci_online_shoppers", "uci_clickstream_shopping", "olist_brazilian_ecommerce"]:
        p = os.path.join(data_dir, d)
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)


def sync_assets_raw() -> None:
    """Point project raw folders at canonical data copies."""
    copies = [
        (
            os.path.join(ROOT, "data", "01-招投标搜索", "02-实习级练习.csv"),
            os.path.join(ROOT, "assets", "projects", "01-bidding-analytics", "raw", "02-实习级练习.csv"),
        ),
        (
            os.path.join(ROOT, "data", "01-招投标搜索", "01-练习小样本.csv"),
            os.path.join(ROOT, "assets", "projects", "01-bidding-analytics", "raw", "01-练习小样本.csv"),
        ),
        (
            os.path.join(ROOT, "data", "02-电商漏斗", "01-漏斗汇总_按渠道.csv"),
            os.path.join(ROOT, "assets", "projects", "03-ecommerce-funnel", "raw", "01-漏斗汇总_按渠道.csv"),
        ),
        (
            os.path.join(ROOT, "data", "02-电商漏斗", "02-UCI购物意图", "online_shoppers_intention.csv"),
            os.path.join(ROOT, "assets", "projects", "03-ecommerce-funnel", "raw", "online_shoppers_intention.csv"),
        ),
    ]
    for src, dst in copies:
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    # remove old filenames in assets if present
    for old in [
        "01-招投标搜索/02-实习级练习.csv",
        "01-招投标搜索/01-练习小样本.csv",
        "02-电商漏斗/01-漏斗汇总_按渠道.csv",
    ]:
        for folder in [
            os.path.join(ROOT, "assets", "projects", "01-bidding-analytics", "raw"),
            os.path.join(ROOT, "assets", "projects", "03-ecommerce-funnel", "raw"),
        ]:
            p = os.path.join(folder, old)
            if os.path.isfile(p):
                os.remove(p)


def patch_text_files() -> None:
    exts = {".md", ".py", ".astro", ".ts"}
    skip_dirs = {"node_modules", ".git", "dist"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if os.path.splitext(fn)[1] not in exts:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                continue
            orig = text
            for old, new in PATH_REPLACEMENTS:
                text = text.replace(old, new)
            if text != orig:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
                print("patched:", os.path.relpath(path, ROOT))


def main() -> None:
    move_docs()
    move_data()
    sync_assets_raw()
    patch_text_files()
    print("Reorganize complete.")


if __name__ == "__main__":
    main()
