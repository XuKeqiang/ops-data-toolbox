from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .models import FilenameShipmentInfo, ShipmentRecord


COUNTRY_NAMES = (
    "澳大利亚",
    "美国",
    "加拿大",
    "英国",
    "德国",
    "法国",
    "意大利",
    "西班牙",
    "日本",
    "墨西哥",
)

WAREHOUSE_RE = re.compile(r"([\w\u4e00-\u9fff（）()\-\s]+)-([A-Z]{2,4}\d?)\s+Created:")
CARTON_RE = re.compile(r"\b(FBA[A-Z0-9]{8,20}U\d{6})\b")
SKU_RE = re.compile(r"(?m)^(\d{7}(?:-[A-Z0-9]+)?)$")
QUANTITY_RE = re.compile(r"^数量\s*\d+")
QUANTITY_VALUE_RE = re.compile(r"^数量\s*(\d+)")
BOX_TOTAL_RE = re.compile(r"共\s*(\d+)\s*个纸箱")
WAREHOUSE_FALLBACK_RE = re.compile(r"\b([A-Z]{3}\d|[A-Z]{2}\d{1,2}|[A-Z]{4})\b")
FBA_BASE_RE = re.compile(r"FBA[A-Z0-9]{8,20}")
WAREHOUSE_TOKEN_RE = re.compile(r"^[A-Z]{2,4}\d?$")
NUMERIC_TOKEN_RE = re.compile(r"^\d+$")
COUNTRY_ALIASES = {
    "US": "美国",
    "USA": "美国",
    "美国": "美国",
    "AU": "澳大利亚",
    "澳洲": "澳大利亚",
    "澳洲站": "澳大利亚",
    "澳大利亚": "澳大利亚",
    "CA": "加拿大",
    "加拿大": "加拿大",
    "UK": "英国",
    "英国": "英国",
    "DE": "德国",
    "德国": "德国",
    "FR": "法国",
    "法国": "法国",
    "IT": "意大利",
    "意大利": "意大利",
    "ES": "西班牙",
    "西班牙": "西班牙",
    "JP": "日本",
    "日本": "日本",
    "MX": "墨西哥",
    "墨西哥": "墨西哥",
}


def extract_pdf(path: Path) -> ShipmentRecord:
    with pdfplumber.open(path) as pdf:
        page_texts = tuple(
            page.extract_text(x_tolerance=2, y_tolerance=3) or "" for page in pdf.pages
        )
    return parse_label_text(path, page_texts)


def parse_label_text(source_path: Path, page_texts: list[str] | tuple[str, ...]) -> ShipmentRecord:
    all_text = "\n".join(page_texts)
    carton_codes = tuple(dict.fromkeys(CARTON_RE.findall(all_text)))
    notes: list[str] = []

    is_single_sku = "Single SKU" in all_text
    sku = _first_match(SKU_RE, all_text)
    first_page_text = page_texts[0] if page_texts else ""
    product_name = _extract_product_name(first_page_text)
    quantity_per_box = _extract_quantity_per_box(first_page_text)
    label_title, title_product_name, title_warehouse, created_at = _extract_label_title(first_page_text, sku)
    destination_country = _extract_country(all_text)
    warehouse = title_warehouse or _extract_warehouse(all_text)
    fba_code = carton_codes[0][:12] if carton_codes else ""
    box_count = len(page_texts)
    total_units = quantity_per_box * box_count if quantity_per_box is not None else None
    claimed_total = _extract_claimed_total(all_text)

    if not is_single_sku:
        notes.append("未识别到 Single SKU")
    if not sku:
        notes.append("未识别到 SKU")
    if not product_name:
        notes.append("未识别到产品名称")
    if not destination_country:
        notes.append("未识别到目的地国家")
    if not warehouse:
        notes.append("未识别到仓库名称")
    if not fba_code:
        notes.append("未识别到 FBA 物流编码")
    if carton_codes and len(carton_codes) != box_count:
        notes.append(f"箱码数量 {len(carton_codes)} 与 PDF 页数 {box_count} 不一致")
    if claimed_total is not None and claimed_total != box_count:
        notes.append(f"纸箱总数 {claimed_total} 与 PDF 页数 {box_count} 不一致")

    filename_info = parse_filename_info(source_path.name)
    comparison_notes = compare_filename_info(
        filename_info=filename_info,
        pdf_sku=sku,
        pdf_country=destination_country,
        pdf_warehouse=warehouse,
        pdf_fba_code=fba_code,
        pdf_box_count=box_count,
        pdf_total_units=total_units,
    )

    return ShipmentRecord(
        source_path=source_path,
        original_filename=source_path.name,
        sku=sku,
        product_name=product_name,
        destination_country=destination_country,
        warehouse=warehouse,
        fba_code=fba_code,
        box_count=box_count,
        carton_codes=carton_codes,
        is_single_sku=is_single_sku,
        quantity_per_box=quantity_per_box,
        total_units=total_units,
        label_title=label_title,
        title_product_name=title_product_name,
        created_at=created_at,
        filename_info=filename_info,
        comparison_notes=tuple(comparison_notes),
        notes=tuple(notes),
    )


def parse_filename_info(filename: str) -> FilenameShipmentInfo:
    stem = Path(filename).stem.strip()
    parts = [part.strip() for part in re.split(r"[-－—–]+", stem) if part.strip()]
    notes: list[str] = []
    if len(parts) < 6:
        return FilenameShipmentInfo(notes=("文件名未匹配运营命名规范",))

    country = _normalize_filename_country(parts[-1])
    if not country:
        notes.append("文件名未识别到国家")

    fba_index = next((idx for idx in range(len(parts) - 2, -1, -1) if parts[idx].upper().startswith("FBA")), -1)
    if fba_index <= 0:
        notes.append("文件名未识别到 FBA 编码")
        fba_code = ""
        warehouse = ""
        quantity_index = -1
    else:
        fba_match = FBA_BASE_RE.search(parts[fba_index].upper())
        fba_code = fba_match.group(0)[:12] if fba_match else parts[fba_index].upper()[:12]
        warehouse = parts[fba_index - 1].upper() if fba_index >= 1 else ""
        if warehouse and not WAREHOUSE_TOKEN_RE.match(warehouse):
            notes.append("文件名仓库格式可能异常")
        quantity_index = fba_index - 2

    box_count = None
    total_units = None
    if quantity_index >= 0:
        box_count, total_units = _parse_quantity_token(parts[quantity_index])
        if box_count is None and total_units is None:
            notes.append("文件名未识别到箱数或总数")
    else:
        notes.append("文件名缺少数量段")

    left_parts = parts[:quantity_index] if quantity_index > 0 else []
    factory_name = left_parts[0] if left_parts and country else ""
    if not factory_name:
        notes.append("文件名未识别到工厂名")

    sku = ""
    product_parts: list[str] = []
    if len(left_parts) >= 2:
        sku = left_parts[1]
        if len(left_parts) >= 3 and re.fullmatch(r"[A-Z0-9]{2,12}", left_parts[2]) and re.fullmatch(r"\d{6,8}", sku):
            sku = f"{sku}-{left_parts[2]}"
            product_parts = left_parts[3:]
        else:
            product_parts = left_parts[2:]
    else:
        notes.append("文件名未识别到 SKU")

    product_name = "-".join(product_parts).strip()
    if not product_name:
        notes.append("文件名未识别到产品名")

    return FilenameShipmentInfo(
        factory_name=factory_name,
        sku=sku,
        product_name=product_name,
        country=country,
        warehouse=warehouse,
        fba_code=fba_code,
        box_count=box_count,
        total_units=total_units,
        notes=tuple(notes),
    )


def compare_filename_info(
    filename_info: FilenameShipmentInfo,
    pdf_sku: str,
    pdf_country: str,
    pdf_warehouse: str,
    pdf_fba_code: str,
    pdf_box_count: int,
    pdf_total_units: int | None,
) -> list[str]:
    notes: list[str] = []
    _compare_text(notes, "SKU", filename_info.sku, pdf_sku)
    _compare_text(notes, "国家", filename_info.country, _normalize_country(pdf_country))
    _compare_text(notes, "仓库", filename_info.warehouse, pdf_warehouse)
    _compare_text(notes, "FBA编码", filename_info.fba_code, pdf_fba_code)
    if filename_info.box_count is not None and filename_info.box_count != pdf_box_count:
        notes.append(f"箱数不一致：文件名 {filename_info.box_count} / PDF {pdf_box_count}")
    if filename_info.total_units is not None and pdf_total_units is not None and filename_info.total_units != pdf_total_units:
        notes.append(f"总数不一致：文件名 {filename_info.total_units} / PDF {pdf_total_units}")
    return notes


def _compare_text(notes: list[str], label: str, filename_value: str, pdf_value: str) -> None:
    if filename_value and pdf_value and filename_value.strip().upper() != pdf_value.strip().upper():
        notes.append(f"{label}不一致：文件名 {filename_value} / PDF {pdf_value}")


def _parse_quantity_token(token: str) -> tuple[int | None, int | None]:
    text = token.strip()
    box_count = None
    total_units = None
    box_match = re.search(r"(\d+)\s*箱", text)
    unit_match = re.search(r"(\d+)\s*个", text)
    if box_match:
        box_count = int(box_match.group(1))
    if unit_match:
        total_units = int(unit_match.group(1))
    if NUMERIC_TOKEN_RE.match(text):
        total_units = int(text)
    return box_count, total_units


def _normalize_country(value: str) -> str:
    return COUNTRY_ALIASES.get(value.strip().upper(), COUNTRY_ALIASES.get(value.strip(), value.strip()))


def _normalize_filename_country(value: str) -> str:
    normalized = _normalize_country(value)
    if normalized in set(COUNTRY_ALIASES.values()):
        return normalized
    return ""


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _extract_country(text: str) -> str:
    for country in COUNTRY_NAMES:
        if country in text:
            return country
    return ""


def _extract_warehouse(text: str) -> str:
    match = WAREHOUSE_RE.search(text)
    if match:
        return match.group(2)

    for candidate in WAREHOUSE_FALLBACK_RE.findall(text):
        if candidate not in {"FBA", "SKU"}:
            return candidate
    return ""


def _extract_label_title(first_page_text: str, sku: str) -> tuple[str, str, str, str]:
    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
    for line in lines:
        match = re.search(r"^(.+?)-([A-Z]{2,4}\d?)\s+Created:\s*(.+)$", line)
        if not match:
            continue
        title = match.group(1).strip()
        warehouse = match.group(2).strip()
        created_at = match.group(3).strip()
        return line, _clean_title_product(title, sku), warehouse, created_at
    return "", "", "", ""


def _clean_title_product(title: str, sku: str) -> str:
    product = title.strip()
    if sku:
        product = re.sub(rf"^{re.escape(sku)}[-\s]*", "", product)
    product = re.sub(r"-(US|AU|CA|UK)$", "", product)
    product = re.sub(r"\d+\s*个\s*$", "", product)
    product = re.sub(r"\d+\s*$", "", product)
    product = re.sub(r"\s+", " ", product)
    if product.startswith("FBA STA"):
        return ""
    return product.strip("- ")


def _extract_product_name(first_page_text: str) -> str:
    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if QUANTITY_RE.match(line) and index + 1 < len(lines):
            product = lines[index + 1].strip()
            if product != "请不要遮住此标签":
                return product
    return ""


def _extract_quantity_per_box(first_page_text: str) -> int | None:
    for line in first_page_text.splitlines():
        match = QUANTITY_VALUE_RE.match(line.strip())
        if match:
            return int(match.group(1))
    return None


def _extract_claimed_total(text: str) -> int | None:
    match = BOX_TOTAL_RE.search(text)
    return int(match.group(1)) if match else None
