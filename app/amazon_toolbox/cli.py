from __future__ import annotations

import argparse
from pathlib import Path

from .shipment_pdf.batch import export_csv, export_xlsx, records_to_rows, scan_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Amazon operations toolbox CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan-shipments", help="Scan shipment label PDFs in a folder")
    scan.add_argument("folder", help="Folder containing shipment label PDF files")
    scan.add_argument("--csv", dest="csv_path", help="Write CSV results to this path")
    scan.add_argument("--xlsx", dest="xlsx_path", help="Write Excel results to this path")

    args = parser.parse_args()
    if args.command == "scan-shipments":
        records = scan_folder(Path(args.folder))
        rows = records_to_rows(records)
        for row in rows:
            print(
                f"{row['状态']}\t{row['SKU']}\t{row['产品名']}\t{row['目的地国家']}\t"
                f"{row['仓库']}\t{row['FBA物流编码']}\t{row['箱码个数']}\t{row['建议文件名']}"
            )
        if args.csv_path:
            export_csv(records, Path(args.csv_path))
        if args.xlsx_path:
            export_xlsx(records, Path(args.xlsx_path))


if __name__ == "__main__":
    main()
