import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from app.ops_toolbox import server
from app.ops_toolbox.shipment_pdf import batch as shipment_batch
from app.ops_toolbox.shipment_pdf.batch import build_suggested_filename, package_by_factory, plan_renames
from app.ops_toolbox.shipment_pdf.extractor import parse_filename_info, parse_label_text


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


FORWARDER_SA_LABEL_TEXT_1 = """FASA202605228410SY0001
Receiver:
Code: CUS250400097
Wt: 1.000
Cbm: 0.000
ShortNo:
50967221
FBA
FBA15LSJCSYS/140
JED4
沙特(普货)
YB89933 海运
1/140
"""


FORWARDER_SA_LABEL_TEXT_2 = FORWARDER_SA_LABEL_TEXT_1.replace("SY0001", "SY0002").replace("1/140", "2/140")


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

    def test_parse_underscore_filename_keeps_supplier_name(self):
        info = parse_filename_info("晟通_2000301_舒曼收纳架（加拿大站）_50箱_50个_XYY4_FBA19H5JJ81N(1-50)_加拿大.pdf")

        self.assertEqual(info.factory_name, "晟通")
        self.assertEqual(info.sku, "2000301")
        self.assertEqual(info.product_name, "舒曼收纳架（加拿大站）")
        self.assertEqual(info.box_count, 50)
        self.assertEqual(info.total_units, 50)
        self.assertEqual(info.warehouse, "XYY4")
        self.assertEqual(info.fba_code, "FBA19H5JJ81N")
        self.assertEqual(info.country, "加拿大")
        self.assertEqual(info.notes, ())

    def test_parse_underscore_filename_keeps_product_quantity_words(self):
        info = parse_filename_info("鹏鑫达_2002701_多芬 2个装 烧火色桐木（加拿大站）_11箱_231个_XYY4_FBA19H5JJ81N(216-226)_加拿大.pdf")

        self.assertEqual(info.factory_name, "鹏鑫达")
        self.assertEqual(info.sku, "2002701")
        self.assertEqual(info.product_name, "多芬 2个装 烧火色桐木（加拿大站）")
        self.assertEqual(info.box_count, 11)
        self.assertEqual(info.total_units, 231)
        self.assertEqual(info.warehouse, "XYY4")
        self.assertEqual(info.fba_code, "FBA19H5JJ81N")
        self.assertEqual(info.country, "加拿大")
        self.assertEqual(info.notes, ())

    def test_parse_underscore_filename_detects_country_embedded_in_product_with_continent_suffix(self):
        # 末段为「洲」（欧洲）而非国家，国家内嵌在产品名分段中
        info = parse_filename_info(
            "华越_120341_瑞思收纳架-英国_20箱_20个_BHX4_FBA15M107PW1（9-28）_欧洲.pdf"
        )

        self.assertEqual(info.factory_name, "华越")
        self.assertEqual(info.sku, "120341")
        self.assertEqual(info.product_name, "瑞思收纳架-英国")
        self.assertEqual(info.country, "英国")
        self.assertEqual(info.warehouse, "BHX4")
        self.assertEqual(info.fba_code, "FBA15M107PW1")
        self.assertEqual(info.notes, ())

    def test_parse_underscore_filename_detects_country_across_hyphenated_product(self):
        info = parse_filename_info(
            "鹏鑫达_120231_卡蒂收纳架-泡白-英国_6箱_30个_DTM2_FBA15M0WS1B5_欧洲.pdf"
        )

        self.assertEqual(info.sku, "120231")
        self.assertEqual(info.country, "英国")
        self.assertEqual(info.notes, ())

    def test_parse_label_text_falls_back_to_filename_when_pdf_text_lacks_sku_country(self):
        # PDF 文本无法识别 SKU / 国家 / Single SKU，但文件名是权威来源
        source_path = Path(
            "华越_120341_瑞思收纳架-英国_1箱_1个_BHX4_FBA15M107PW1（9-28）_欧洲.pdf"
        )
        page_texts = [
            "瑞思-BHX4 Created: 2026/09/28 10:00\n"
            "FBA15M107PW1U000001\n"
            "数量 1\n"
            "瑞思收纳架\n"
            "请不要遮住此标签\n"
        ]

        record = parse_label_text(source_path=source_path, page_texts=page_texts)

        self.assertEqual(record.sku, "120341")
        self.assertEqual(record.destination_country, "英国")
        self.assertEqual(record.warehouse, "BHX4")
        self.assertEqual(record.fba_code, "FBA15M107PW1")
        self.assertTrue(record.is_single_sku)
        self.assertEqual(record.notes, ())
        self.assertTrue(record.is_valid)

    def test_parse_label_text_prefers_pdf_sku_and_flags_mismatch(self):
        source_path = Path(
            "华越_120341_瑞思收纳架-英国_1箱_1个_BHX4_FBA15M107PW1（9-28）_欧洲.pdf"
        )
        page_texts = [
            "9999999\n"
            "瑞思-BHX4 Created: 2026/09/28 10:00\n"
            "FBA15M107PW1U000001\n"
            "数量 1\n"
            "瑞思收纳架\n"
            "Single SKU\n"
            "请不要遮住此标签\n"
        ]

        record = parse_label_text(source_path=source_path, page_texts=page_texts)

        # 顶层 sku 优先采用 PDF 文本识别到的值
        self.assertEqual(record.sku, "9999999")
        self.assertEqual(record.destination_country, "英国")
        # PDF 与文件名 SKU 不一致 => 应产生对比提示而非静默通过
        self.assertTrue(any("SKU不一致" in n for n in record.comparison_notes))
        self.assertFalse(record.is_valid)

    def test_parse_forwarder_filename_info(self):
        info = parse_filename_info("沙特-FASA202605228410S（1-20）晟通.pdf")

        self.assertEqual(info.factory_name, "晟通")
        self.assertEqual(info.logistics_code, "FASA202605228410S")
        self.assertEqual(info.country, "沙特")
        self.assertEqual(info.box_count, 20)
        self.assertEqual(info.notes, ())

    def test_parse_forwarder_label_text(self):
        record = parse_label_text(
            source_path=Path("沙特-FASA202605228410S（1-2）晟通.pdf"),
            page_texts=[FORWARDER_SA_LABEL_TEXT_1, FORWARDER_SA_LABEL_TEXT_2],
        )

        self.assertEqual(record.label_type, "forwarder")
        self.assertEqual(record.filename_info.factory_name, "晟通")
        self.assertEqual(record.logistics_code, "FASA202605228410S")
        self.assertEqual(record.destination_country, "沙特")
        self.assertEqual(record.warehouse, "JED4")
        self.assertEqual(record.fba_code, "FBA15LSJCSYS")
        self.assertEqual(record.box_count, 2)
        self.assertEqual(record.shipment_total_boxes, 140)
        self.assertFalse(record.is_single_sku)
        self.assertEqual(record.sku, "")
        self.assertEqual(record.product_name, "")
        self.assertEqual(record.notes, ())
        self.assertTrue(record.is_valid)
        self.assertEqual(
            build_suggested_filename(record),
            "晟通-FASA202605228410S-2箱-JED4-FBA15LSJCSYS-沙特.pdf",
        )

    def test_standard_label_keeps_declared_shipment_total_as_context(self):
        record = parse_label_text(
            source_path=Path("晟通_2000301_舒曼收纳架_50箱_50个_XYY4_FBA19H5JJ81N(1-50)_加拿大.pdf"),
            page_texts=[
                AU_LABEL_TEXT.replace("共 1 个纸箱", "共 356 个纸箱"),
                AU_LABEL_TEXT.replace("共 1 个纸箱", "共 356 个纸箱").replace("U000001", "U000002"),
            ],
        )

        self.assertEqual(record.box_count, 2)
        self.assertEqual(record.shipment_total_boxes, 356)
        self.assertNotIn("纸箱总数 356 与 PDF 页数 2 不一致", record.notes)

    def test_suggested_filename_and_export_keep_supplier_name(self):
        record = parse_label_text(
            source_path=Path("晟通_2000301_舒曼收纳架（加拿大站）_50箱_50个_XYY4_FBA19H5JJ81N(1-50)_加拿大.pdf"),
            page_texts=[AU_LABEL_TEXT],
        )
        rows = shipment_batch.records_to_rows([record])

        self.assertTrue(build_suggested_filename(record).startswith("晟通-"))
        self.assertEqual(rows[0]["工厂/供应商"], "晟通")
        self.assertEqual(rows[0]["工厂名"], "晟通")
        self.assertEqual(rows[0]["文件名产品名"], "舒曼收纳架（加拿大站）")

    def test_suggested_filename_prefers_filename_product_name(self):
        record = parse_label_text(
            source_path=Path("鹏鑫达_2002701_多芬 2个装 烧火色桐木（加拿大站）_11箱_231个_XYY4_FBA19H5JJ81N(216-226)_加拿大.pdf"),
            page_texts=[AU_LABEL_TEXT.replace("3006502", "2002701")],
        )

        self.assertIn("多芬 2个装 烧火色桐木（加拿大站）", build_suggested_filename(record))

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
            "鹏鑫达-3006502-达利白-1个-BWU2-FBA15GCL9X61-澳大利亚.pdf",
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
            package_by_name = {package["factory_name"]: package for package in packaged["packages"]}
            self.assertEqual(package_by_name["鹏鑫达"]["country_count"], 1)
            self.assertEqual(package_by_name["鹏鑫达"]["countries"], ["澳大利亚"])
            self.assertEqual(package_by_name["海达"]["country_count"], 1)
            self.assertEqual(package_by_name["海达"]["countries"], ["美国"])

            px_zip = root / "outputs" / "batch001-factory-packages" / "鹏鑫达-batch001.zip"
            hd_zip = root / "outputs" / "batch001-factory-packages" / "海达-batch001.zip"
            self.assertTrue(px_zip.exists())
            self.assertTrue(hd_zip.exists())
            with zipfile.ZipFile(px_zip) as archive:
                self.assertEqual(archive.namelist(), [f"澳大利亚/{record_a.original_filename}"])
            with zipfile.ZipFile(hd_zip) as archive:
                self.assertEqual(archive.namelist(), [f"美国/{record_b.original_filename}"])

    def test_scan_folder_finds_pdfs_recursively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "top.pdf").write_text("pdf placeholder", encoding="utf-8")
            (root / "notes.txt").write_text("skip", encoding="utf-8")
            nested = root / "folder"
            nested.mkdir()
            (nested / "nested.PDF").write_text("pdf placeholder", encoding="utf-8")

            with patch.object(shipment_batch, "extract_pdf", side_effect=lambda path: path.name):
                records = shipment_batch.scan_folder(root)

        self.assertEqual(records, ["nested.PDF", "top.pdf"])

    def test_upload_paths_are_sanitized_and_deduplicated(self):
        self.assertEqual(
            server._safe_upload_relative_path("批次/子目录/鹏鑫达:001.pdf"),
            Path("批次/子目录/鹏鑫达001.pdf"),
        )
        self.assertEqual(server._safe_upload_relative_path("../../bad?.pdf"), Path("bad.pdf"))

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "same.pdf"
            target.write_text("existing", encoding="utf-8")

            self.assertEqual(server._unique_upload_target(target).name, "same-2.pdf")

    def test_build_shipment_package_bundle_contains_factory_zips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_paths = []
            for name in ("晟通-batch.zip", "华越-batch.zip"):
                zip_path = root / name
                with zipfile.ZipFile(zip_path, "w") as archive:
                    archive.writestr("placeholder.pdf", "pdf")
                package_paths.append(zip_path)

            bundle = server._build_shipment_package_bundle(
                "batch001",
                [{"zip_filename": path.name, "zip_path": str(path)} for path in package_paths],
                str(root),
            )

            self.assertEqual(bundle["zip_filename"], "全部工厂-batch001.zip")
            with zipfile.ZipFile(bundle["zip_path"]) as archive:
                self.assertEqual(set(archive.namelist()), {"晟通-batch.zip", "华越-batch.zip"})

    def test_history_payload_enriches_shipment_package_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_root = root / "task001-factory-packages"
            package_root.mkdir()
            for name in ("晟通-task001.zip", "华越-task001.zip"):
                with zipfile.ZipFile(package_root / name, "w") as archive:
                    archive.writestr("placeholder.pdf", "pdf")

            with patch.object(server, "OUTPUT_ROOT", root):
                task = server._task_with_available_downloads(
                    {"id": "task001", "type": "shipment_pdf", "downloads": []}
                )

            labels = {item["label"] for item in task["downloads"]}
            self.assertIn("全部工厂/国家压缩包", labels)
            self.assertIn("晟通 压缩包", labels)
            self.assertTrue((package_root / "全部工厂-task001.zip").exists())


if __name__ == "__main__":
    unittest.main()
