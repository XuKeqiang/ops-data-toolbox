from unittest import TestCase

from app.amazon_toolbox.report_pdf.batch import _duplicate_report_keys, _result_row


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
