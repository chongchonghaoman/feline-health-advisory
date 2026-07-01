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
URL_RE = re.compile(r"https?://\S+", re.I)
ASCII_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+&/-]{1,}")
ITEM_ID_RE = re.compile(r"(?:id|itemNumId|skuId)=([0-9]{5,})|(?<!\d)([0-9]{9,})(?!\d)")

PLATFORMS = {
    "0": "all",
    "1": "taobao_tmall",
    "2": "jd",
    "3": "pdd",
    "4": "suning",
    "5": "vip",
    "6": "kaola",
    "7": "douyin",
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
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
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
                        "ocr_text_path": item.get("ocr_text_path", ""),
                        "ocr_variants": item.get("ocr_variants", []),
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


def label_found(candidates: list[dict[str, Any]]) -> bool:
    for item in candidates:
        for audit in item.get("label_ocr", []):
            if audit.get("has_label_evidence"):
                return True
    return False


def acquisition_status(payload: dict[str, Any]) -> str:
    if payload.get("ingredient_candidate_found"):
        return "ingredient_candidate_found_needs_sku_and_human_transcription"
    if payload.get("search_count", 0):
        return "sku_candidates_found_continue_ingredient_acquisition"
    return "no_sku_candidate_found_continue_text_web_search"


def label_status(item: dict[str, Any]) -> str:
    if not item.get("detail"):
        return "detail_not_fetched"
    detail = item.get("detail") or {}
    if not detail.get("image_urls"):
        return "no_detail_images"
    if "label_ocr" not in item:
        return "ocr_not_run"
    for audit in item.get("label_ocr", []):
        if audit.get("has_label_evidence"):
            return "label_candidate_found"
    return "no_label_candidate_in_detail_images"


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip()
        if key and key.lower() not in seen:
            seen.add(key.lower())
            out.append(key)
    return out


def extract_ascii_phrase(text: str) -> str:
    words = [w.strip("-_/") for w in ASCII_WORD_RE.findall(text)]
    words = [w for w in words if len(w) > 1]
    return " ".join(unique_preserve(words)[:8])


def extract_numeric_ids(text: str) -> list[str]:
    ids: list[str] = []
    for match in ITEM_ID_RE.finditer(text):
        value = match.group(1) or match.group(2)
        if value:
            ids.append(value)
    return unique_preserve(ids)


def clean_search_keyword(text: str) -> str:
    cleaned = URL_RE.sub(" ", text)
    cleaned = re.sub(r"\b(?:id|itemNumId|skuId)=[0-9]{5,}\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or text.strip()


def web_queries(keyword: str, candidates: list[dict[str, Any]], search_keyword: str | None = None) -> list[str]:
    base = search_keyword or keyword
    titles = [base]
    for item in candidates[:3]:
        title = item.get("title", "")
        if title and title not in titles:
            titles.append(title)
    suffixes = ["配料表", "原料组成", "成分分析保证值", "背标", "包装背面", "详情图", "产品标准"]
    queries: list[str] = []
    for item_id in extract_numeric_ids(keyword):
        queries.extend(
            [
                f'"{item_id}" "配料"',
                f'"{item_id}" "原料组成"',
                f'"{item_id}" "背标"',
                f'"{item_id}" "详情图"',
                f'"{item_id}" "商品条码"',
                f'"{item_id}" "GTIN"',
                f'"{item_id}" "EAN"',
            ]
        )
    for title in titles:
        for suffix in suffixes:
            queries.append(f'"{title}" "{suffix}"')
        english = extract_ascii_phrase(title)
        if english:
            queries.extend(
                [
                    f'"{english}" "composition"',
                    f'"{english}" "analytical constituents"',
                    f'"{english}" "ingredients"',
                    f'"{english}" "complementary pet food"',
                    f'"{english}" official',
                ]
            )
    brand_terms = " ".join(titles[:2])
    queries.extend(
        [
            f'{brand_terms} site:tmall.com 配料',
            f'{brand_terms} site:jd.com 配料',
            f'{brand_terms} site:yangkeduo.com 配料',
            f'{brand_terms} site:xiaohongshu.com 背标',
            f'{brand_terms} 官方 配料 保证分析',
        ]
    )
    seen: set[str] = set()
    return [q for q in queries if not (q in seen or seen.add(q))]


def next_actions(payload: dict[str, Any]) -> list[str]:
    if payload.get("ingredient_candidate_found") or payload.get("label_found"):
        return [
            "人工核对 OCR 命中的图片是否为同一 SKU、同一规格、同一口味、同一生命阶段。",
            "把配料/添加剂/保证分析/适用阶段/标准号逐项摘录，不能只摘卖点文案。",
        ]
    top = payload.get("candidates", [])[:3]
    actions = [
        "不要把本次结果写成最终的“未验证”。先逐条执行 web_queries 中的搜索式，继续找官方配料字段、背标图或保证分析。",
        "打开候选商品购买链接或原平台详情页，在已登录浏览器里查看规格选择和详情长图。",
        "优先保存这些图：规格选择截图、商品详情长截图、包装背面/中文标签/保证分析图。",
        "把保存的本地图片交给 product_label_audit.py：python scripts/product_label_audit.py --query \"商品名\" --image \"图片路径\"",
        "如果平台详情仍没有背标，问旗舰店客服要：配料表、添加剂组成、产品成分分析保证值、适用生命阶段、中文标签照片。",
        "客服不给或只给卖点图时，把该商品标为 D 级证据；同时记录被阻断路径和下一步最小补证动作，不把“未验证”当作配料获取成果。",
    ]
    for item in top:
        detail = item.get("detail") or {}
        link = detail.get("purchase_link")
        if link:
            actions.append(f"优先核对候选 {item.get('idx')}: {link}")
    return actions


def build_probe(args: argparse.Namespace) -> dict[str, Any]:
    maishou_dir = find_maishou_dir(args.maishou_dir)
    search_keyword = clean_search_keyword(args.keyword)
    search_text = maishou_command(
        maishou_dir,
        "search",
        ["--source", str(args.source), "--keyword", search_keyword],
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
            item["label_status"] = label_status(item)
        candidates.append(item)
    payload = {
        "keyword": args.keyword,
        "search_keyword": search_keyword,
        "source": str(args.source),
        "source_name": PLATFORMS.get(str(args.source), str(args.source)),
        "maishou_dir": str(maishou_dir),
        "search_count": len(rows),
        "candidates": candidates,
    }
    label_hit = label_found(candidates)
    payload["label_found"] = label_hit
    payload["label_candidate_found"] = label_hit
    payload["ingredient_candidate_found"] = label_hit
    payload["sku_verified_label"] = False
    payload["web_queries"] = web_queries(args.keyword, candidates, search_keyword)[: args.query_limit]
    payload["acquisition_status"] = acquisition_status(payload)
    payload["next_actions"] = next_actions(payload)
    return payload


def print_text(payload: dict[str, Any]) -> None:
    print(f"keyword: {payload['keyword']}")
    if payload.get("search_keyword") and payload.get("search_keyword") != payload.get("keyword"):
        print(f"search_keyword: {payload['search_keyword']}")
    print(f"source: {payload['source_name']}")
    print(f"maishou_dir: {payload['maishou_dir']}")
    print(f"search_count: {payload['search_count']}")
    print(f"ingredient_candidate_found: {payload.get('ingredient_candidate_found')}")
    print(f"label_candidate_found: {payload.get('label_candidate_found')}")
    print(f"sku_verified_label: {payload.get('sku_verified_label')}")
    print(f"acquisition_status: {payload.get('acquisition_status')}")
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
        if item.get("label_status"):
            print(f"  label_status={item['label_status']}")
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
                    if hit.get("ocr_text_path"):
                        print(f"    ocr_text={hit['ocr_text_path']}")
                    for line in hit.get("label_hits", [])[:12]:
                        print(f"    {line}")
        print("")
    print("web_queries:")
    for query in payload.get("web_queries", [])[:20]:
        print(f"  - {query}")
    print("")
    print("next_actions:")
    for action in payload.get("next_actions", []):
        print(f"  - {action}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search CN e-commerce candidates and optional label OCR.")
    parser.add_argument("keyword", help="Product name, URL text, or SKU keywords.")
    parser.add_argument("--source", default="0", help="0 all, 1 Taobao/Tmall, 2 JD, 3 PDD, 4 Suning, 5 Vip, 6 Kaola, 7 Douyin, 8 Kuaishou, 10 1688.")
    parser.add_argument("--top", type=int, default=10, help="Search candidates to keep.")
    parser.add_argument("--detail-top", type=int, default=3, help="Fetch details for the first N candidates.")
    parser.add_argument("--ocr", action="store_true", help="Run product_label_audit OCR on detail images.")
    parser.add_argument("--ocr-images", type=int, default=5, help="Max images per detailed candidate to OCR.")
    parser.add_argument("--query-limit", type=int, default=30, help="Max follow-up web search queries to emit.")
    parser.add_argument("--require-label", action="store_true", help="Exit 2 if no label-like OCR evidence is found.")
    parser.add_argument("--report", help="Write the full JSON evidence package to this file.")
    parser.add_argument("--maishou-dir", help="Override installed maishou skill directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    payload = build_probe(args)
    if args.report:
        report_path = Path(args.report).expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)
    if args.require_label and not payload.get("label_found"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
