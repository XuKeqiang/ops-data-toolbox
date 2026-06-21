from __future__ import annotations

import re
import traceback
from dataclasses import dataclass
from pathlib import Path

from . import extract_amazon_reports as report_parser


@dataclass
class ReportPdfJob:
    job_id: str
    source_label: str
    output_path: Path
    summary: dict
    rows: list[dict]


def process_report_folder(folder: Path, output_path: Path, job_id: str) -> ReportPdfJob:
    pdfs = report_parser.collect_pdfs(str(folder))
    all_pdf_count = _count_pdf_files(folder)
    skipped_range_count = _count_quarter_range_files(folder)

    results = []
    failed_rows: list[dict] = []
    for pdf_path, store, country, country_code in pdfs:
        try:
            results.append(report_parser.extract_pdf(pdf_path, store, country, country_code))
        except Exception as exc:  # Keep batch running and surface the file for manual review.
            failed_rows.append(
                {
                    "source_file": Path(pdf_path).name,
                    "source_path": str(pdf_path),
                    "store": store,
                    "country": country,
                    "country_code": country_code,
                    "status": "解析失败",
                    "notes": str(exc),
                    "traceback": traceback.format_exc(limit=3),
                }
            )

    report_parser.write_excel(results, str(output_path))

    duplicate_keys = _duplicate_report_keys(results)
    rows = [_result_row(result, duplicate_keys) for result in results]
    rows.extend(failed_rows)

    warning_rows = [row for row in rows if row["status"] != "通过"]
    summary = {
        "files": all_pdf_count,
        "processable": len(pdfs),
        "processed": len(results),
        "failed": len(failed_rows),
        "skipped_range": skipped_range_count,
        "warnings": len(warning_rows),
        "summary_rows": sum(len(result.get("summaries", [])) for result in results),
        "detail_rows": sum(len(result.get("details", [])) for result in results),
        "check_rows": sum(len(result.get("checks", [])) for result in results),
        "output_filename": output_path.name,
    }
    return ReportPdfJob(
        job_id=job_id,
        source_label=str(folder),
        output_path=output_path,
        summary=summary,
        rows=rows,
    )


def _result_row(result: dict, duplicate_keys: dict[tuple, list[str]]) -> dict:
    meta = result["meta"]
    status_parts = []

    if result.get("errors"):
        status_parts.append("核验异常")

    audit_status = meta.get("filename_audit_status") or ""
    if audit_status and not audit_status.startswith("✓"):
        status_parts.append("文件名需复核")

    key = (
        meta.get("store"),
        meta.get("country_code"),
        meta.get("year"),
        meta.get("month"),
        meta.get("quarter"),
    )
    duplicates = duplicate_keys.get(key, [])
    if len(duplicates) > 1:
        status_parts.append("疑似重复报告期")

    status = "通过" if not status_parts else "；".join(dict.fromkeys(status_parts))
    notes = []
    if result.get("errors"):
        notes.extend(result["errors"])
    if audit_status and not audit_status.startswith("✓"):
        notes.append(audit_status)
    if len(duplicates) > 1:
        notes.append("同店铺/站点/年月存在多个文件")

    return {
        "source_file": meta.get("source_file") or "",
        "source_path": meta.get("source_path") or "",
        "store": meta.get("store") or "",
        "country": meta.get("country") or "",
        "country_code": meta.get("country_code") or "",
        "currency": meta.get("currency") or "",
        "period": meta.get("period") or "",
        "year": meta.get("year"),
        "month": meta.get("month"),
        "quarter": meta.get("quarter"),
        "summary_count": len(result.get("summaries", [])),
        "detail_count": len(result.get("details", [])),
        "check_count": len(result.get("checks", [])),
        "status": status,
        "notes": "；".join(notes),
    }


def _duplicate_report_keys(results: list[dict]) -> dict[tuple, list[str]]:
    duplicate_keys: dict[tuple, list[str]] = {}
    for result in results:
        meta = result["meta"]
        if not (meta.get("year") and meta.get("month")):
            continue
        key = (
            meta.get("store"),
            meta.get("country_code"),
            meta.get("year"),
            meta.get("month"),
            meta.get("quarter"),
        )
        duplicate_keys.setdefault(key, []).append(meta.get("source_file") or "")
    return duplicate_keys


def _count_pdf_files(folder: Path) -> int:
    return sum(1 for path in folder.rglob("*.pdf") if path.is_file())


def _count_quarter_range_files(folder: Path) -> int:
    pattern = re.compile(r"Q[1-4]-Q[1-4]", re.IGNORECASE)
    return sum(1 for path in folder.rglob("*.pdf") if path.is_file() and pattern.search(path.name))
