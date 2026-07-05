from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.amazon_toolbox.report_pdf.batch import _duplicate_report_keys, _result_row
from app.amazon_toolbox.report_pdf.extract_amazon_reports import collect_pdfs


class ReportPdfBatchTest(TestCase):
    def test_result_row_marks_filename_audit_for_review(self) -> None:
        result = {
            "meta": {
                "store": "TARNABY",
                "country": "日本",
                "country_code": "JP",
                "source_file": "202605-TARNABY-日本-汇总报告.pdf",
                "source_path": "/tmp/202605-TARNABY-日本-汇总报告.pdf",
                "currency": "JPY",
                "period": "",
                "year": 2026,
                "month": 5,
                "quarter": "Q2",
                "filename_audit_status": "未解析到报告期，已采用文件名年月",
            },
            "summaries": [{}, {}, {}, {}],
            "details": [{}, {}],
            "checks": [{}, {}, {}, {}],
            "errors": [],
        }

        row = _result_row(result, {})

        self.assertEqual(row["status"], "文件名需复核")
        self.assertIn("未解析到报告期", row["notes"])

    def test_result_row_marks_duplicate_report_period(self) -> None:
        result = _fake_result("a.pdf")
        duplicate_keys = _duplicate_report_keys([result, _fake_result("b.pdf")])

        row = _result_row(result, duplicate_keys)

        self.assertEqual(row["status"], "疑似重复报告期")

    def test_collect_pdfs_accepts_direct_root_pdfs(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "Bikoney-US-2026Q2-summary.pdf").write_bytes(b"%PDF")

            rows = collect_pdfs(str(base))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Bikoney")
        self.assertEqual(rows[0][2], "美国")
        self.assertEqual(rows[0][3], "US")

    def test_collect_pdfs_infers_brand_and_country_from_nested_folders(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "TARNABY" / "欧洲" / "德国" / "202605-汇总报告.pdf"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"%PDF")

            rows = collect_pdfs(str(base))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "TARNABY")
        self.assertEqual(rows[0][2], "德国")
        self.assertEqual(rows[0][3], "DE")


def _fake_result(source_file: str) -> dict:
    return {
        "meta": {
            "store": "Bikoney",
            "country": "美国",
            "country_code": "US",
            "source_file": source_file,
            "source_path": f"/tmp/{source_file}",
            "currency": "USD",
            "period": "May 1, 2026 ~ May 31, 2026",
            "year": 2026,
            "month": 5,
            "quarter": "Q2",
            "filename_audit_status": "✓ 文件名年月与报告期一致",
        },
        "summaries": [],
        "details": [],
        "checks": [],
        "errors": [],
    }
