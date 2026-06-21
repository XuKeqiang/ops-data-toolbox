import tempfile
import unittest
from pathlib import Path

from app.amazon_toolbox.shipment_pdf.batch import build_suggested_filename, package_by_factory, plan_renames
from app.amazon_toolbox.shipment_pdf.extractor import parse_filename_info, parse_label_text


AU_LABEL_TEXT = """FBA 纸箱编号 1，共 1 个纸箱 - 5.4 千克
目的地： 发货地：
FBA: shenzhenshiyuhenglikejiyouxiangongsi shenzhenshiyuhenglikejiyouxiangongsi
BWU2 Guangdong - shenzhen - 518000
13 Emporium Avenue xixiangjiedaotaoyuanshequtaoyuanjushierqu12dong5danyuan703
Kemps Creek, NSW 2178 中国
澳大利亚
达利白色25个-BWU2 Created: 2026/06/10 16:10 AEST (+10)
FBA15GCL9X61U000001
FNSKU X001D6S79B Single SKU
3006502
数量 1
达利白
请不要遮住此标签
"""


US_LABEL_TEXT = """请不要遮住此标签
FBA
目的地： 发货地：
FBA: shenzhenshihuaruiyikejiyouxiangongsi Beslley
SWF2 Guangdong - shenzhenshi - 518000
76 Patriot Way minzhijiedao Shenzhenshihuaruiyikejiyouxiangongsiyuhuahuayua
Hopewell Junction, NY 12533-6159 n yujinge511
美国 中国
1004201-BKYUS-吉米烧火144-US-SWF2 Created: 2026/06/08 05:33 EDT (-04)
FBA19FRGM282U000001
Single SKU
1004201-BKYUS
数量 48
吉米烧火
"""


class ShipmentPdfParsingTest(unittest.TestCase):
    def test_parse_australia_label_text(self):
        record = parse_label_text(
            source_path=Path("鹏鑫达-3006502-达利白-2箱2个-BWU2-FBA15GCL9X61-澳大利亚.pdf"),
            page_texts=[
                AU_LABEL_TEXT.replace("共 1 个纸箱", "共 2 个纸箱"),
                AU_LABEL_TEXT.replace("共 1 个纸箱", "共 2 个纸箱").replace("U000001", "U000002"),
            ],
        )

        self.assertEqual(record.sku, "3006502")
        self.assertEqual(record.product_name, "达利白")
        self.assertEqual(record.destination_country, "澳大利亚")
        self.assertEqual(record.warehouse, "BWU2")
        self.assertEqual(record.fba_code, "FBA15GCL9X61")
        self.assertEqual(record.box_count, 2)
        self.assertEqual(record.total_units, 2)
        self.assertEqual(record.filename_info.factory_name, "鹏鑫达")
        self.assertEqual(record.filename_info.total_units, 2)
        self.assertTrue(record.is_single_sku)
        self.assertTrue(record.is_valid)

    def test_parse_us_label_text_with_hyphenated_sku(self):
        record = parse_label_text(
            source_path=Path("鹏鑫达-1004201-BKYUS-吉米烧火-48-SWF2-FBA19FRGM282-美国.pdf"),
            page_texts=[US_LABEL_TEXT],
        )

        self.assertEqual(record.sku, "1004201-BKYUS")
        self.assertEqual(record.product_name, "吉米烧火")
        self.assertEqual(record.destination_country, "美国")
        self.assertEqual(record.warehouse, "SWF2")
        self.assertEqual(record.fba_code, "FBA19FRGM282")
        self.assertEqual(record.box_count, 1)
        self.assertTrue(record.is_valid)

    def test_parse_standard_filename_info(self):
        info = parse_filename_info("鹏鑫达-1006702-瑞奇白-40-CLT2-FBA19D8ZT5XR-美国.pdf")

        self.assertEqual(info.factory_name, "鹏鑫达")
        self.assertEqual(info.sku, "1006702")
        self.assertEqual(info.product_name, "瑞奇白")
        self.assertEqual(info.total_units, 40)
        self.assertIsNone(info.box_count)
        self.assertEqual(info.warehouse, "CLT2")
        self.assertEqual(info.fba_code, "FBA19D8ZT5XR")
        self.assertEqual(info.country, "美国")
        self.assertEqual(info.notes, ())

    def test_filename_comparison_marks_total_mismatch(self):
        record = parse_label_text(
            source_path=Path("鹏鑫达-3006502-达利白-40-BWU2-FBA15GCL9X61-澳大利亚.pdf"),
            page_texts=[AU_LABEL_TEXT],
        )

        self.assertFalse(record.is_valid)
        self.assertIn("总数不一致：文件名 40 / PDF 1", record.comparison_notes)

    def test_suggested_filename_uses_normalized_business_fields(self):
        record = parse_label_text(
            source_path=Path("鹏鑫达-3006502-达利白-1-BWU2-FBA15GCL9X61-澳大利亚.pdf"),
            page_texts=[AU_LABEL_TEXT],
        )

        self.assertEqual(
            build_suggested_filename(record),
            "鹏鑫达-3006502-达利白色-1个-BWU2-FBA15GCL9X61-澳大利亚.pdf",
        )

    def test_rename_plan_skips_invalid_and_conflicting_rows(self):
        valid = parse_label_text(
            source_path=Path("鹏鑫达-3006502-达利白-1-BWU2-FBA15GCL9X61-澳大利亚.pdf"),
            page_texts=[AU_LABEL_TEXT],
        )
        invalid = parse_label_text(source_path=Path("bad.pdf"), page_texts=["FBA\n"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / valid.original_filename).write_text("pdf placeholder", encoding="utf-8")
            (root / "bad.pdf").write_text("pdf placeholder", encoding="utf-8")
            (root / build_suggested_filename(valid)).write_text("existing", encoding="utf-8")
            valid = valid.with_paths(root / valid.original_filename)
            invalid = invalid.with_paths(root / "bad.pdf")

            plans = plan_renames([valid, invalid])

        self.assertEqual(len(plans), 2)
        self.assertFalse(plans[0].can_apply)
        self.assertIn("目标文件已存在", plans[0].reason)
        self.assertFalse(plans[1].can_apply)
        self.assertIn("记录存在未解决问题", plans[1].reason)

    def test_package_by_factory_creates_factory_zip_files(self):
        record_a = parse_label_text(
            source_path=Path("鹏鑫达-3006502-达利白-1-BWU2-FBA15GCL9X61-澳大利亚.pdf"),
            page_texts=[AU_LABEL_TEXT],
        )
        record_b = parse_label_text(
            source_path=Path("海达-1004201-BKYUS-吉米烧火-48-SWF2-FBA19FRGM282-美国.pdf"),
            page_texts=[US_LABEL_TEXT],
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for record in (record_a, record_b):
                (root / record.original_filename).write_text("pdf placeholder", encoding="utf-8")
            packaged = package_by_factory(
                [record_a.with_paths(root / record_a.original_filename), record_b.with_paths(root / record_b.original_filename)],
                root / "outputs",
                "batch001",
            )

            self.assertEqual(len(packaged["packages"]), 2)
            self.assertTrue((root / "outputs" / "batch001-factory-packages" / "鹏鑫达-batch001.zip").exists())
            self.assertTrue((root / "outputs" / "batch001-factory-packages" / "海达-batch001.zip").exists())


if __name__ == "__main__":
    unittest.main()
