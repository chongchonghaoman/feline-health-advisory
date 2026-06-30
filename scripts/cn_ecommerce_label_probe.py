#!/usr/bin/env python3
"""
Probe Chinese e-commerce listings before a cat-food label audit.

This helper uses the installed `maishou` skill to search Taobao/Tmall, JD, and
PDD, then optionally sends candidate product images through product_label_audit.
It does not decide whether a product is suitable; it only gathers auditable
SKU, price, shop, image, and OCR evidence.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

IMAGE_RE = re.compile(
    r"https?://[^\s'\"<>]+?\.(?:jpg|jpeg|png|webp)(?:[^\s'\"<>]*)?",
    re.I,
)

PLATFORMS = {
    "0": "all",
    "1": "taobao_tmall",
    "2": "jd",
    "3": "pdd",
    "6": "douyin",
    "8": "kuaishou",
    "10": "1688",
}


def user_home() -> Path:
    return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser()


def candidate_maishou_dirs() -> list[Path]:
    home = user_home()
    values = []
    env_dir = os.environ.get("MAISHOU_SKILL_DIR")
    if env_dir:
        values.append(Path(env_dir).expanduser())
    values.extend(
        [
            home / ".agents" / "skills" / "maishou",
            home / ".codex" / "skills" / "maishou",
            home / ".workbuddy" / "skills" / "maishou",
        ]
    )
    return values


def find_maishou_dir(explicit: str | None = None) -> Path:
    candidates = [Path(explicit).expanduser()] if explicit else candidate_maishou_dirs()
    for path in candidates:
        script = path / "scripts" / "main.py"
        if script.exists():
            return path
    checked = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"maishou skill not found; checked: {checked}")


def run_command(args: list[str], cwd: Path, timeout: int = 120) -> str:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    text = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{text[:2000]}")
    return text


def maishou_command(maishou_dir: Path, command: str, extra: list[str]) -> str:
    uv = shutil.which("uv")
    if uv:
        args = [uv, "run", "scripts/main.py", command, *extra]
    else:
        args = [sys.executable, str(maishou_dir / "scripts" / "main.py"), command, *extra]
    return run_command(args, maishou_dir)


def parse_search_csv(text: str) -> list[dict[str, str]]:
    lines = [line.strip("\ufeff") for line in text.splitlines() if line.strip()]
    start = next((i for i, line in enumerate(lines) if line.startswith("idx,goodsId,source,")), -1)
    if start < 0:
        return []
    rows: list[dict[str, str]] = []
    for row in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        if not row.get("idx", "").isdigit():
            continue
        if not row.get("goodsId") or not row.get("source"):
            continue
        rows.append({k: (v or "") for k, v in row.items()})
    return rows


def first_value(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.*)$", re.M)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def parse_detail_text(text: str) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "title": first_value(text, "商品标题"),
        "purchase_link": first_value(text, "购买链接"),
        "tao_password": first_value(text, "复制口令"),
        "shop_name": first_value(text, "shopName"),
        "platform_name": first_value(text, "platformName"),
        "source_type_name": first_value(text, "sourceTypeName"),
        "original_price": first_value(text, "originalPrice"),
        "actual_price": first_value(text, "actualPrice"),
        "coupon_price": first_value(text, "couponPrice"),
        "month_sales": first_value(text, "monthSales") or first_value(text, "salesStr"),
        "favorable_rate": first_value(text, "favorableRate"),
        "goods_id": first_value(text, "goodsId"),
        "goods_id_b": first_value(text, "goodsIdB"),
    }
    images = []
    for url in IMAGE_RE.findall(text):
        if url not in images:
            images.append(url)
    detail["image_urls"] = images
    return detail


def run_label_ocr(query: str, image_urls: list[str], limit: int, timeout: int = 120) -> list[dict[str, Any]]:
    audit_script = Path(__file__).with_name("product_label_audit.py")
    if not audit_script.exists():
        return [{"error": f"missing audit script: {audit_script}"}]
    results: list[dict[str, Any]] = []
    for url in image_urls[:limit]:
        proc = subprocess.run(
            [sys.executable, str(audit_script), "--query", query, "--image", url, "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if proc.returncode != 0:
            results.append({"image": url, "error": proc.stderr.strip()[:1000]})
            continue
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            results.append({"image": url, "error": "audit output was not JSON"})
            continue
        hits = []
        for item in payload.get("results", []):
            if item.get("has_label_evidence"):
                hits.append(
                    {
                        "source": item.get("source"),
                        "local_image": item.get("path"),
                        "label_hits": item.get("label_hits", []),
                        "ocr_chars": item.get("ocr_chars", 0),
                    }
                )
        results.append(
            {
                "image": url,
                "has_label_evidence": bool(hits),
                "hits": hits,
                "audit_out_dir": payload.get("out_dir", ""),
            }
        )
    return results


def build_probe(args: argparse.Namespace) -> dict[str, Any]:
    maishou_dir = find_maishou_dir(args.maishou_dir)
    search_text = maishou_command(
        maishou_dir,
        "search",
        ["--source", str(args.source), "--keyword", args.keyword],
    )
    rows = parse_search_csv(search_text)[: args.top]
    candidates: list[dict[str, Any]] = []
    for row in rows:
        item: dict[str, Any] = {
            "idx": row.get("idx", ""),
            "goods_id": row.get("goodsId", ""),
            "source": row.get("source", ""),
            "platform": PLATFORMS.get(row.get("source", ""), row.get("source", "")),
            "title": row.get("title", ""),
            "shop_name": row.get("shopName", ""),
            "original_price": row.get("originalPrice", ""),
            "actual_price": row.get("actualPrice", ""),
            "coupon_price": row.get("couponPrice", ""),
            "month_sales": row.get("monthSales", ""),
            "pic_url": row.get("picUrl", ""),
        }
        if int(row.get("idx", "0")) <= args.detail_top:
            detail_text = maishou_command(
                maishou_dir,
                "detail",
                ["--source", row.get("source", ""), "--id", row.get("goodsId", "")],
            )
            detail = parse_detail_text(detail_text)
            item["detail"] = detail
            images = detail.get("image_urls") or ([row.get("picUrl", "")] if row.get("picUrl") else [])
            if args.ocr:
                item["label_ocr"] = run_label_ocr(item["title"] or args.keyword, images, args.ocr_images)
        candidates.append(item)
    return {
        "keyword": args.keyword,
        "source": str(args.source),
        "source_name": PLATFORMS.get(str(args.source), str(args.source)),
        "maishou_dir": str(maishou_dir),
        "search_count": len(rows),
        "candidates": candidates,
    }


def print_text(payload: dict[str, Any]) -> None:
    print(f"keyword: {payload['keyword']}")
    print(f"source: {payload['source_name']}")
    print(f"maishou_dir: {payload['maishou_dir']}")
    print(f"search_count: {payload['search_count']}")
    print("")
    for item in payload["candidates"]:
        print(f"[{item['idx']}] {item['title']}")
        print(
            "  "
            f"platform={item['platform']} shop={item['shop_name']} "
            f"price={item['actual_price']} original={item['original_price']} "
            f"sales={item['month_sales']}"
        )
        print(f"  goods_id={item['goods_id']}")
        if item.get("pic_url"):
            print(f"  pic={item['pic_url']}")
        detail = item.get("detail") or {}
        if detail.get("purchase_link"):
            print(f"  link={detail['purchase_link']}")
        images = detail.get("image_urls") or []
        if images:
            print("  images:")
            for url in images[:8]:
                print(f"    - {url}")
        for audit in item.get("label_ocr", []):
            if audit.get("has_label_evidence"):
                print(f"  label_candidate={audit.get('image')}")
                for hit in audit.get("hits", []):
                    for line in hit.get("label_hits", [])[:12]:
                        print(f"    {line}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search CN e-commerce candidates and optional label OCR.")
    parser.add_argument("keyword", help="Product name, URL text, or SKU keywords.")
    parser.add_argument("--source", default="0", help="0 all, 1 Taobao/Tmall, 2 JD, 3 PDD, 6 Douyin, 8 Kuaishou, 10 1688.")
    parser.add_argument("--top", type=int, default=10, help="Search candidates to keep.")
    parser.add_argument("--detail-top", type=int, default=3, help="Fetch details for the first N candidates.")
    parser.add_argument("--ocr", action="store_true", help="Run product_label_audit OCR on detail images.")
    parser.add_argument("--ocr-images", type=int, default=5, help="Max images per detailed candidate to OCR.")
    parser.add_argument("--maishou-dir", help="Override installed maishou skill directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    payload = build_probe(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
