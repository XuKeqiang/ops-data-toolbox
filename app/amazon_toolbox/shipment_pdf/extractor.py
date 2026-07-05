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
    "沙特",
    "阿联酋",
)

WAREHOUSE_RE = re.compile(r"([\w\u4e00-\u9fff（）()\-\s]+)-([A-Z]{2,4}\d?)\s+Created:")
CARTON_RE = re.compile(r"\b(FBA[A-Z0-9]{8,20}U\d{6})\b")
FORWARDER_LABEL_RE = re.compile(r"(?m)^(FA[A-Z]{2}\d{12}S[YU]?\d{4})$")
FORWARDER_FILENAME_RE = re.compile(
    r"^(?P<country>[^-－—–]+)[-－—–](?P<logistics>FA[A-Z]{2}\d{12}S)[（(](?P<start>\d+)[-－—–](?P<end>\d+)[）)](?P<factory>.+)$"
)
FORWARDER_FBA_TOTAL_RE = re.compile(r"\b(FBA[A-Z0-9]{8,20})/(\d+)\b")
FORWARDER_COUNTRY_RE = re.compile(r"(?m)^([\u4e00-\u9fff]+)\([^)]*\)$")
FORWARDER_PAGE_MARK_RE = re.compile(r"(?m)^(\d+)/(\d+)$")
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
    "SA": "沙特",
    "KSA": "沙特",
    "沙特": "沙特",
    "沙特阿拉伯": "沙特",
    "AE": "阿联酋",
    "UAE": "阿联酋",
    "阿联酋": "阿联酋",
}


def extract_pdf(path: Path) -> ShipmentRecord:
    with pdfplumber.open(path) as pdf:
        page_texts = tuple(
            page.extract_text(x_tolerance=2, y_tolerance=3) or "" for page in pdf.pages
        )
    return parse_label_text(path, page_texts)


def parse_label_text(source_path: Path, page_texts: list[str] | tuple[str, ...]) -> ShipmentRecord:
    all_text = "\n".join(page_texts)
    if _looks_like_forwarder_label(all_text):
        return _parse_forwarder_label_text(source_path, page_texts)

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
    if claimed_total is not None and claimed_total < box_count:
        notes.append(f"PDF 声明纸箱总数 {claimed_total} 小于 PDF 页数 {box_count}")

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
        shipment_total_boxes=claimed_total,
        label_title=label_title,
        title_product_name=title_product_name,
        created_at=created_at,
        filename_info=filename_info,
        comparison_notes=tuple(comparison_notes),
        notes=tuple(notes),
    )


def parse_filename_info(filename: str) -> FilenameShipmentInfo:
    stem = Path(filename).stem.strip()
    forwarder_info = _parse_forwarder_filename_info(stem)
    if forwarder_info:
        return forwarder_info
    underscore_info = _parse_underscore_filename_info(stem)
    if underscore_info:
        return underscore_info

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
        logistics_code="",
        sku=sku,
        product_name=product_name,
        country=country,
        warehouse=warehouse,
        fba_code=fba_code,
        box_count=box_count,
        total_units=total_units,
        notes=tuple(notes),
    )


def _parse_underscore_filename_info(stem: str) -> FilenameShipmentInfo | None:
    if "_" not in stem and "＿" not in stem:
        return None

    parts = [part.strip() for part in re.split(r"[_＿]+", stem) if part.strip()]
    if len(parts) < 7:
        return None

    notes: list[str] = []
    factory_name = parts[0]
    if not factory_name:
        notes.append("文件名未识别到工厂/供应商")

    sku = parts[1] if len(parts) > 1 else ""
    if not sku:
        notes.append("文件名未识别到 SKU")

    country = _normalize_filename_country(parts[-1])
    if not country:
        notes.append("文件名未识别到国家")

    fba_index = next((idx for idx in range(len(parts) - 2, -1, -1) if parts[idx].upper().startswith("FBA")), -1)
    if fba_index <= 0:
        notes.append("文件名未识别到 FBA 编码")
        fba_code = ""
        warehouse = ""
    else:
        fba_match = FBA_BASE_RE.search(parts[fba_index].upper())
        fba_code = fba_match.group(0)[:12] if fba_match else parts[fba_index].upper()[:12]
        warehouse = parts[fba_index - 1].upper() if fba_index >= 1 else ""
        if warehouse and not WAREHOUSE_TOKEN_RE.match(warehouse):
            notes.append("文件名仓库格式可能异常")

    box_count = None
    total_units = None
    quantity_indices: list[int] = []
    quantity_scan_end = fba_index - 1 if fba_index > 0 else len(parts) - 1
    for index in range(2, max(2, quantity_scan_end)):
        token = parts[index]
        token_box_count, token_total_units = _parse_strict_filename_quantity_token(token)
        if token_box_count is not None:
            box_count = token_box_count
            quantity_indices.append(index)
        if token_total_units is not None:
            total_units = token_total_units
            quantity_indices.append(index)

    if not quantity_indices:
        notes.append("文件名未识别到箱数或总数")
        product_parts = parts[2:quantity_scan_end]
    else:
        product_parts = parts[2:min(quantity_indices)]

    product_name = "_".join(product_parts).strip()
    if not product_name:
        notes.append("文件名未识别到产品名")

    return FilenameShipmentInfo(
        factory_name=factory_name,
        logistics_code="",
        sku=sku,
        product_name=product_name,
        country=country,
        warehouse=warehouse,
        fba_code=fba_code,
        box_count=box_count,
        total_units=total_units,
        notes=tuple(notes),
    )


def _looks_like_forwarder_label(text: str) -> bool:
    return bool(FORWARDER_LABEL_RE.search(text) and FORWARDER_FBA_TOTAL_RE.search(text))


def _parse_forwarder_label_text(source_path: Path, page_texts: list[str] | tuple[str, ...]) -> ShipmentRecord:
    all_text = "\n".join(page_texts)
    notes: list[str] = []
    label_codes = tuple(dict.fromkeys(FORWARDER_LABEL_RE.findall(all_text)))
    logistics_code = _common_forwarder_logistics_code(label_codes)
    fba_code, shipment_total_boxes = _extract_forwarder_fba_and_total(all_text)
    destination_country = _extract_forwarder_country(all_text) or _normalize_filename_country(Path(source_path).stem.split("-")[0])
    warehouse = _extract_forwarder_warehouse(page_texts[0] if page_texts else "")
    box_count = len(page_texts)
    filename_info = parse_filename_info(source_path.name)
    comparison_notes = _compare_forwarder_filename_info(
        filename_info=filename_info,
        pdf_country=destination_country,
        pdf_logistics_code=logistics_code,
        pdf_box_count=box_count,
    )

    if not label_codes:
        notes.append("未识别到物流箱码")
    if not logistics_code:
        notes.append("未识别到物流单号")
    if not destination_country:
        notes.append("未识别到目的地国家")
    if not warehouse:
        notes.append("未识别到仓库名称")
    if not fba_code:
        notes.append("未识别到 FBA 物流编码")
    if shipment_total_boxes is None:
        notes.append("未识别到大货总箱数")
    if label_codes and len(label_codes) != box_count:
        notes.append(f"物流箱码数量 {len(label_codes)} 与 PDF 页数 {box_count} 不一致")

    page_mark_count, page_mark_total = _extract_forwarder_page_marks(all_text)
    if page_mark_count and page_mark_count != box_count:
        notes.append(f"箱码序号数量 {page_mark_count} 与 PDF 页数 {box_count} 不一致")
    if page_mark_total is not None and shipment_total_boxes is not None and page_mark_total != shipment_total_boxes:
        notes.append(f"大货总箱数不一致：FBA 行 {shipment_total_boxes} / 页码行 {page_mark_total}")

    return ShipmentRecord(
        source_path=source_path,
        original_filename=source_path.name,
        sku="",
        product_name="",
        destination_country=destination_country,
        warehouse=warehouse,
        fba_code=fba_code,
        box_count=box_count,
        carton_codes=label_codes,
        is_single_sku=False,
        quantity_per_box=None,
        total_units=None,
        label_type="forwarder",
        logistics_code=logistics_code,
        shipment_total_boxes=shipment_total_boxes,
        label_title="货代/冷门站点标签",
        title_product_name="",
        created_at="",
        filename_info=filename_info,
        comparison_notes=tuple(comparison_notes),
        notes=tuple(notes),
    )


def _parse_forwarder_filename_info(stem: str) -> FilenameShipmentInfo | None:
    match = FORWARDER_FILENAME_RE.match(stem)
    if not match:
        return None
    start = int(match.group("start"))
    end = int(match.group("end"))
    notes: list[str] = []
    if end < start:
        notes.append("文件名箱码范围异常")
        box_count = None
    else:
        box_count = end - start + 1
    country = _normalize_filename_country(match.group("country"))
    if not country:
        notes.append("文件名未识别到国家")
    factory_name = match.group("factory").strip()
    if not factory_name:
        notes.append("文件名未识别到工厂名")
    return FilenameShipmentInfo(
        factory_name=factory_name,
        logistics_code=match.group("logistics").upper(),
        country=country,
        box_count=box_count,
        notes=tuple(notes),
    )


def _common_forwarder_logistics_code(label_codes: tuple[str, ...]) -> str:
    prefixes = {re.sub(r"[YU]?\d{4}$", "", code.upper()) for code in label_codes}
    return next(iter(prefixes)) if len(prefixes) == 1 else ""


def _extract_forwarder_fba_and_total(text: str) -> tuple[str, int | None]:
    match = FORWARDER_FBA_TOTAL_RE.search(text)
    if not match:
        return "", None
    return match.group(1)[:12], int(match.group(2))


def _extract_forwarder_country(text: str) -> str:
    for match in FORWARDER_COUNTRY_RE.findall(text):
        country = _normalize_country(match)
        if country in set(COUNTRY_ALIASES.values()):
            return country
    return ""


def _extract_forwarder_warehouse(first_page_text: str) -> str:
    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if FORWARDER_FBA_TOTAL_RE.fullmatch(line) and index + 1 < len(lines):
            return lines[index + 1].strip()
    return ""


def _extract_forwarder_page_marks(text: str) -> tuple[int, int | None]:
    matches = [(int(current), int(total)) for current, total in FORWARDER_PAGE_MARK_RE.findall(text)]
    if not matches:
        return 0, None
    totals = {total for _, total in matches}
    return len(matches), next(iter(totals)) if len(totals) == 1 else None


def _compare_forwarder_filename_info(
    filename_info: FilenameShipmentInfo,
    pdf_country: str,
    pdf_logistics_code: str,
    pdf_box_count: int,
) -> list[str]:
    notes: list[str] = []
    _compare_text(notes, "国家", filename_info.country, _normalize_country(pdf_country))
    _compare_text(notes, "物流单号", filename_info.logistics_code, pdf_logistics_code)
    if filename_info.box_count is not None and filename_info.box_count != pdf_box_count:
        notes.append(f"箱数不一致：文件名 {filename_info.box_count} / PDF {pdf_box_count}")
    return notes


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


def _parse_strict_filename_quantity_token(token: str) -> tuple[int | None, int | None]:
    text = token.strip()
    box_count = None
    total_units = None
    if re.fullmatch(r"\d+\s*箱", text):
        box_count = int(re.search(r"\d+", text).group(0))
    elif re.fullmatch(r"\d+\s*个", text):
        total_units = int(re.search(r"\d+", text).group(0))
    elif NUMERIC_TOKEN_RE.fullmatch(text):
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
