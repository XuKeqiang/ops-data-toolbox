from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from .extractor import extract_pdf
from .models import RenamePlan, ShipmentRecord


EXPORT_COLUMNS = [
    "原文件名",
    "标签类型",
    "工厂/供应商",
    "工厂名",
    "物流单号",
    "文件名SKU",
    "文件名产品名",
    "文件名国家",
    "文件名箱数",
    "文件名总数",
    "文件名仓库",
    "文件名FBA编码",
    "SKU",
    "产品名",
    "标题产品名",
    "目的地国家",
    "仓库",
    "FBA物流编码",
    "箱码个数",
    "每箱数量",
    "总件数",
    "大货总箱数",
    "Single SKU",
    "状态",
    "问题说明",
    "文件名解析问题",
    "内容比对告警",
    "建议文件名",
]


def scan_folder(folder: Path) -> list[ShipmentRecord]:
    pdf_paths = sorted(path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf")
    return [extract_pdf(path) for path in pdf_paths]


def build_suggested_filename(record: ShipmentRecord) -> str:
    if record.label_type == "forwarder":
        total_part = f"{record.box_count}箱"
        parts = [
            record.filename_info.factory_name,
            record.logistics_code or record.filename_info.logistics_code,
            total_part,
            record.warehouse,
            record.fba_code,
            _country_filename_token(record.destination_country),
        ]
        safe_parts = [_sanitize_filename_part(part) for part in parts if part]
        return "-".join(safe_parts) + ".pdf"

    product_name = record.filename_info.product_name or record.title_product_name or record.product_name
    factory_name = record.filename_info.factory_name
    total_part = f"{record.total_units}个" if record.total_units is not None else f"{record.box_count}箱"
    parts = [
        factory_name,
        record.sku,
        product_name,
        total_part,
        record.warehouse,
        record.fba_code,
        _country_filename_token(record.destination_country),
    ]
    safe_parts = [_sanitize_filename_part(part) for part in parts if part]
    return "-".join(safe_parts) + ".pdf"


def plan_renames(records: list[ShipmentRecord]) -> list[RenamePlan]:
    plans: list[RenamePlan] = []
    planned_targets: set[Path] = set()

    for record in records:
        target_path = record.source_path.with_name(build_suggested_filename(record))
        if not record.is_valid:
            plans.append(RenamePlan(record.source_path, target_path, False, "记录存在未解决问题"))
        elif target_path == record.source_path:
            plans.append(RenamePlan(record.source_path, target_path, False, "文件名已经符合规范"))
        elif target_path.exists():
            plans.append(RenamePlan(record.source_path, target_path, False, "目标文件已存在"))
        elif target_path in planned_targets:
            plans.append(RenamePlan(record.source_path, target_path, False, "批次内目标文件名重复"))
        else:
            plans.append(RenamePlan(record.source_path, target_path, True, "可以重命名"))
            planned_targets.add(target_path)

    return plans


def apply_renames(records: list[ShipmentRecord]) -> list[RenamePlan]:
    plans = plan_renames(records)
    for plan in plans:
        if plan.can_apply:
            plan.source_path.rename(plan.target_path)
    return plans


def records_to_rows(records: list[ShipmentRecord]) -> list[dict]:
    return [
        {
            "原文件名": record.original_filename,
            "标签类型": _label_type_name(record.label_type),
            "工厂/供应商": record.filename_info.factory_name,
            "工厂名": record.filename_info.factory_name,
            "物流单号": record.logistics_code or record.filename_info.logistics_code,
            "文件名SKU": record.filename_info.sku,
            "文件名产品名": record.filename_info.product_name,
            "文件名国家": record.filename_info.country,
            "文件名箱数": record.filename_info.box_count,
            "文件名总数": record.filename_info.total_units,
            "文件名仓库": record.filename_info.warehouse,
            "文件名FBA编码": record.filename_info.fba_code,
            "SKU": record.sku,
            "产品名": record.product_name,
            "标题产品名": record.title_product_name,
            "目的地国家": record.destination_country,
            "仓库": record.warehouse,
            "FBA物流编码": record.fba_code,
            "箱码个数": record.box_count,
            "每箱数量": record.quantity_per_box,
            "总件数": record.total_units,
            "大货总箱数": record.shipment_total_boxes,
            "Single SKU": "是" if record.is_single_sku else "否",
            "状态": "通过" if record.is_valid else "需复核",
            "问题说明": "；".join(record.notes),
            "文件名解析问题": "；".join(record.filename_info.notes),
            "内容比对告警": "；".join(record.comparison_notes),
            "建议文件名": build_suggested_filename(record),
        }
        for record in records
    ]


def export_csv(records: list[ShipmentRecord], output_path: Path) -> Path:
    rows = records_to_rows(records)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def export_xlsx(records: list[ShipmentRecord], output_path: Path) -> Path:
    rows = records_to_rows(records)
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        pd.DataFrame(rows, columns=EXPORT_COLUMNS).to_excel(tmp_path, index=False)
        tmp_path.replace(output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return output_path


def _sanitize_filename_part(value: str) -> str:
    cleaned = value.strip()
    cleaned = cleaned.replace("/", "-").replace("\\", "-").replace(":", "-")
    cleaned = cleaned.replace("*", "").replace("?", "")
    cleaned = cleaned.replace('"', "").replace("<", "").replace(">", "").replace("|", "")
    return " ".join(cleaned.split())


def _country_filename_token(country: str) -> str:
    return {
        "澳大利亚": "澳大利亚",
        "美国": "美国",
        "沙特": "沙特",
        "阿联酋": "阿联酋",
    }.get(country, country)


def _label_type_name(label_type: str) -> str:
    return {
        "forwarder": "货代/冷门站点标签",
        "amazon": "Amazon 官方外箱标",
    }.get(label_type, label_type or "Amazon 官方外箱标")


def package_by_factory(records: list[ShipmentRecord], output_dir: Path, batch_id: str) -> dict:
    package_root = output_dir / f"{batch_id}-factory-packages"
    package_root.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[ShipmentRecord]] = {}
    skipped: list[dict] = []

    for record in records:
        factory_name = record.filename_info.factory_name.strip()
        if not factory_name:
            skipped.append({"filename": record.original_filename, "reason": "缺少工厂名"})
            continue
        groups.setdefault(factory_name, []).append(record)

    packages = []
    for factory_name, factory_records in sorted(groups.items()):
        zip_name = f"{_sanitize_filename_part(factory_name)}-{batch_id}.zip"
        zip_path = package_root / zip_name
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for record in factory_records:
                archive.write(record.source_path, arcname=record.original_filename)
        packages.append(
            {
                "factory_name": factory_name,
                "file_count": len(factory_records),
                "zip_filename": zip_name,
                "zip_path": str(zip_path),
            }
        )

    return {
        "package_root": str(package_root),
        "packages": packages,
        "skipped": skipped,
    }
