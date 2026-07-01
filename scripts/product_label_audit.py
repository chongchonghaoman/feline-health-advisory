#!/usr/bin/env python3
"""
Helper for cat-food product label audits.

The script does not decide whether a product is good. It helps gather auditable
label evidence from local images, image URLs, and static HTML pages, then OCRs
candidate images and extracts label-like lines.
"""

from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


LABEL_PATTERNS = [
    r"原料组成",
    r"配料(?:表)?",
    r"添加剂组成",
    r"营养成分",
    r"成分分析(?:保证值)?",
    r"产品成分分析保证值",
    r"粗蛋白",
    r"粗脂肪",
    r"粗纤维",
    r"粗灰分",
    r"水分",
    r"钙",
    r"磷",
    r"牛磺酸",
    r"适用(?:生命)?阶段",
    r"全价",
    r"补充",
    r"零食",
    r"净含量",
    r"产品标准",
    r"生产许可证",
    r"生产企业",
    r"委托",
    r"保质期",
    r"进口登记",
    r"备案",
    r"raw\s+material\s+composition",
    r"additive\s+composition",
    r"dry\s+matter\s+basis",
    r"ingredients?",
    r"analytical\s+constituents?",
    r"guaranteed\s+analysis",
    r"composition",
    r"crude\s+protein",
    r"crude\s+fat",
    r"crude\s+fiber",
    r"crude\s+fibre",
    r"crude\s+ash",
    r"moisture",
    r"taurine",
    r"total\s+phosphorus",
    r"phosphorus",
    r"calcium",
]

LABEL_RE = re.compile("|".join(LABEL_PATTERNS), re.I)

STRONG_LABEL_PATTERNS = [
    r"原料组成",
    r"配料(?:表)?",
    r"添加剂组成",
    r"营养成分",
    r"成分分析(?:保证值)?",
    r"产品成分分析保证值",
    r"粗蛋白",
    r"粗脂肪",
    r"粗纤维",
    r"粗灰分",
    r"牛磺酸",
    r"产品标准",
    r"生产许可证",
    r"生产企业",
    r"进口登记",
    r"备案",
    r"raw\s+material\s+composition",
    r"additive\s+composition",
    r"dry\s+matter\s+basis",
    r"ingredients?",
    r"analytical\s+constituents?",
    r"guaranteed\s+analysis",
    r"crude\s+protein",
    r"crude\s+fat",
    r"crude\s+fiber",
    r"crude\s+fibre",
    r"moisture",
    r"taurine",
    r"total\s+phosphorus",
    r"calcium",
]

STRONG_LABEL_RE = re.compile("|".join(STRONG_LABEL_PATTERNS), re.I)

SOURCE_SCORE_PATTERNS = [
    (re.compile(r"原料|配料|成分|保证值|背标|详情|包装|营养|标签|label|composition|ingredient|analysis|constituent", re.I), 6),
    (re.compile(r"主食|全价|猫饭|猫粮|餐盒|餐包|罐|猫条|湿粮", re.I), 3),
    (re.compile(r"alicdn|360buyimg|jd|tmall|taobao|pdd|shopee|lazada|amazon|susercontent|kua?nf[u]?|toptrees", re.I), 1),
]

IMAGE_EXT_RE = re.compile(r"\.(?:jpg|jpeg|png|webp)(?:[?#].*)?$", re.I)


class ImageExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.images: list[dict[str, str]] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "img":
            candidates = [
                attr.get("src", ""),
                attr.get("data-src", ""),
                attr.get("data-original", ""),
                attr.get("lay-src", ""),
            ]
            for src in candidates:
                if src:
                    self.images.append(
                        {
                            "url": urljoin(self.base_url, html.unescape(src)),
                            "alt": html.unescape(attr.get("alt", "")),
                            "title": html.unescape(attr.get("title", "")),
                        }
                    )
                    break
        if tag.lower() == "a":
            href = attr.get("href", "")
            if href:
                self.links.append(urljoin(self.base_url, html.unescape(href)))


def fetch_bytes(url: str, timeout: int = 20) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def stable_name(value: str, suffix: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{digest}{suffix}"


def ensure_tesseract() -> str | None:
    exe = shutil.which("tesseract")
    if exe:
        return exe
    common = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if common.exists():
        return str(common)
    return None


def tessdata_dir() -> str | None:
    user_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tessdata"
    if user_dir.exists():
        return str(user_dir)
    prefix = os.environ.get("TESSDATA_PREFIX")
    if prefix:
        p = Path(prefix)
        if p.name.lower() == "tessdata" and p.exists():
            return str(p)
        if (p / "tessdata").exists():
            return str(p / "tessdata")
    return None


def ocr_image(path: Path, lang: str = "chi_sim+eng", psm: str = "11") -> tuple[str, list[str]]:
    exe = ensure_tesseract()
    if not exe:
        return "", ["tesseract_not_found"]
    cmd = [exe]
    data_dir = tessdata_dir()
    if data_dir:
        cmd += ["--tessdata-dir", data_dir]
    cmd += [str(path), "stdout", "-l", lang, "--psm", psm]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    warnings: list[str] = []
    if proc.returncode != 0:
        warnings.append(f"tesseract_exit_{proc.returncode}")
    if proc.stderr.strip():
        warnings.append(proc.stderr.strip()[:500])
    return proc.stdout, warnings


def preprocess_image_variants(path: Path, out_dir: Path) -> list[Path]:
    variants = [path]
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    except Exception:
        return variants

    try:
        image = Image.open(path)
        image.load()
    except Exception:
        return variants

    rgb = image.convert("RGB")
    gray = ImageOps.grayscale(rgb)
    scale = 2 if max(gray.size) < 2200 else 1
    if scale > 1:
        gray = gray.resize((gray.width * scale, gray.height * scale))

    processed = ImageEnhance.Contrast(gray).enhance(1.8)
    processed = ImageEnhance.Sharpness(processed).enhance(1.7)
    processed = processed.filter(ImageFilter.SHARPEN)
    processed_path = out_dir / f"{path.stem}.ocr.png"
    processed.save(processed_path)
    variants.append(processed_path)

    inverted = ImageOps.invert(processed)
    inverted_path = out_dir / f"{path.stem}.ocr-invert.png"
    inverted.save(inverted_path)
    variants.append(inverted_path)
    return variants


def ocr_image_best(path: Path, out_dir: Path) -> tuple[str, list[str], list[str]]:
    warnings: list[str] = []
    texts: list[str] = []
    variants = preprocess_image_variants(path, out_dir)
    for variant in variants:
        for psm in ("6", "11"):
            text, local_warnings = ocr_image(variant, psm=psm)
            if text.strip():
                texts.append(f"--- OCR {variant.name} psm={psm} ---\n{text}")
            warnings.extend(local_warnings)
    merged = "\n".join(texts)
    return merged, warnings, [str(p) for p in variants]


def extract_label_hits(text: str, window: int = 2, pattern: re.Pattern[str] = LABEL_RE) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    hit_indexes = [i for i, ln in enumerate(lines) if pattern.search(ln)]
    selected: list[str] = []
    seen: set[str] = set()
    for idx in hit_indexes:
        start = max(0, idx - window)
        end = min(len(lines), idx + window + 1)
        for ln in lines[start:end]:
            if ln not in seen:
                selected.append(ln)
                seen.add(ln)
    return selected


def score_image(item: dict[str, str], product_terms: str = "") -> int:
    text = " ".join([item.get("url", ""), item.get("alt", ""), item.get("title", ""), product_terms])
    score = 0
    for pattern, value in SOURCE_SCORE_PATTERNS:
        if pattern.search(text):
            score += value
    if IMAGE_EXT_RE.search(item.get("url", "")):
        score += 1
    return score


def parse_html_images(url: str, product_terms: str = "", limit: int = 40) -> tuple[list[dict[str, str]], list[str]]:
    raw = fetch_bytes(url)
    text = raw.decode("utf-8", errors="replace")
    parser = ImageExtractor(url)
    parser.feed(text)

    images = parser.images[:]
    for link in parser.links:
        if IMAGE_EXT_RE.search(link):
            images.append({"url": link, "alt": "", "title": ""})

    unique: dict[str, dict[str, str]] = {}
    for item in images:
        if item["url"].startswith("//"):
            item["url"] = "https:" + item["url"]
        if item["url"].startswith(("http://", "https://")):
            unique[item["url"]] = item

    ranked = sorted(unique.values(), key=lambda item: score_image(item, product_terms), reverse=True)
    return ranked[:limit], []


def download_image(url: str, out_dir: Path) -> Path | None:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"
    path = out_dir / stable_name(url, suffix)
    if path.exists() and path.stat().st_size > 0:
        return path
    try:
        data = fetch_bytes(url)
        if len(data) < 1000:
            return None
        path.write_bytes(data)
        return path
    except Exception:
        return None


def iter_input_images(args: argparse.Namespace, work_dir: Path) -> Iterable[dict[str, str]]:
    for image in args.image or []:
        if image.startswith(("http://", "https://")):
            path = download_image(image, work_dir)
            if path:
                yield {"source": image, "path": str(path), "kind": "image_url"}
        else:
            p = Path(image).expanduser()
            if p.exists():
                yield {"source": str(p), "path": str(p), "kind": "local_image"}

    for url in args.url or []:
        try:
            candidates, _ = parse_html_images(url, args.query or "", args.limit)
        except Exception as exc:
            yield {"source": url, "path": "", "kind": "html_error", "error": str(exc)}
            continue
        for item in candidates:
            path = download_image(item["url"], work_dir)
            if path:
                yield {
                    "source": item["url"],
                    "path": str(path),
                    "kind": "html_image",
                    "alt": item.get("alt", ""),
                    "title": item.get("title", ""),
                }


def search_queries(product_name: str) -> list[str]:
    base = product_name.strip()
    if not base:
        return []
    suffixes = [
        "配料表",
        "原料组成",
        "成分分析保证值",
        "背标",
        "包装背面",
        "详情图",
        "营养成分",
        "产品标准",
        "旗舰店",
        "买家晒图",
        "小红书 背标",
        "Raw Material Composition",
        "Additive Composition",
        "Dry Matter Basis",
        "Ingredients",
        "Analytical constituents",
        "Guaranteed analysis",
    ]
    return [f'"{base}" "{s}"' for s in suffixes] + [
        f'{base} site:detail.tmall.com',
        f'{base} site:item.jd.com',
        f'{base} site:yangkeduo.com',
        f'{base} site:xiaohongshu.com 配料',
        f'{base} site:shopee.com composition',
        f'{base} site:lazada.com composition',
        f'{base} site:amazon.com ingredients',
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR and extract cat-food product label evidence.")
    parser.add_argument("--query", help="Exact product name or SKU text.")
    parser.add_argument("--url", action="append", help="HTML/product/aggregator page URL to scan for images.")
    parser.add_argument("--image", action="append", help="Local image path or image URL to OCR.")
    parser.add_argument("--out-dir", default="", help="Directory for downloaded images and JSON output.")
    parser.add_argument("--limit", type=int, default=40, help="Max image candidates per URL.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()

    if not (args.query or args.url or args.image):
        parser.error("provide --query, --url, or --image")

    out_dir = Path(args.out_dir) if args.out_dir else Path(tempfile.gettempdir()) / "catfood-label-audit" / time.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    for item in iter_input_images(args, out_dir):
        if item.get("kind") == "html_error":
            results.append(item)
            continue
        path = Path(str(item["path"]))
        text, warnings, variants = ocr_image_best(path, out_dir)
        hits = extract_label_hits(text)
        strong_hits = extract_label_hits(text, pattern=STRONG_LABEL_RE)
        text_path = out_dir / f"{path.stem}.ocr.txt"
        text_path.write_text(text, encoding="utf-8")
        results.append(
            {
                **item,
                "ocr_chars": len(text),
                "label_hits": hits,
                "strong_label_hits": strong_hits,
                "has_label_evidence": bool(strong_hits),
                "ocr_text_path": str(text_path),
                "ocr_variants": variants,
                "warnings": warnings,
            }
        )

    payload = {
        "query": args.query or "",
        "search_queries": search_queries(args.query or ""),
        "out_dir": str(out_dir),
        "results": results,
    }
    (out_dir / "audit.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"out_dir: {out_dir}")
    if payload["search_queries"]:
        print("\nrecommended_search_queries:")
        for q in payload["search_queries"]:
            print(f"- {q}")
    print("\nlabel_evidence_candidates:")
    any_hit = False
    for item in results:
        if item.get("has_label_evidence"):
            any_hit = True
            print(f"\nsource: {item.get('source')}")
            print(f"image: {item.get('path')}")
            for line in item.get("label_hits", []):
                print(f"  {line}")
    if not any_hit:
        print("- none found; try more official/detail/review images or package-back photos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
