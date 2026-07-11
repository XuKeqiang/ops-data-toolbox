# Ops Toolbox Design

## Goal

Build an internal browser-based toolbox for weekly Amazon operations data processing. The first implemented workflow is batch extraction and normalized renaming for Amazon FBA shipment label PDFs. The architecture must leave clear extension points for transaction report PDFs, transaction detail CSV files, imports, exports, and future task history.

## First Phase Scope

- Batch scan shipment label PDFs from an uploaded batch or a server-side folder path.
- Extract one record per PDF with source filename, SKU, product name, destination country, warehouse code, FBA shipment code prefix, box count, `Single SKU` status, suggested normalized filename, and validation notes.
- Export results as CSV and XLSX.
- Preview rename actions before applying them.
- Apply rename actions only when each file has an unambiguous valid result.

Out of scope for the first phase:

- User accounts and permissions.
- Persistent database history.
- OCR for image-only PDFs.
- Transaction report PDF and transaction CSV parsing. The UI shows these modules as planned but inactive.

## Architecture

The system is split into focused units:

- `shipment_pdf.extractor`: pure PDF parsing and validation. It does not know about HTTP, uploads, or file renaming.
- `shipment_pdf.batch`: folder scanning, records, export rows, and safe rename planning.
- `server`: standard-library HTTP API for local intranet use. It accepts uploads, scans server folders, returns JSON, exports files, and applies confirmed renames.
- `static`: code-native browser UI with a left module rail, upload/folder import controls, scan summary, dense review table, export actions, and rename confirmation.

This keeps future processors independent. A later `transaction_csv` module can expose the same batch-result shape and reuse the same UI shell, export pattern, and server task conventions.

## Extraction Rules

- Box count is primarily the PDF page count.
- The parser also counts unique FBA carton codes matching `FBA...U000001`; if this differs from page count, the record is flagged.
- The FBA logistics code is the first 12 characters of the carton code, for example `FBA15GCL9X61U000010` becomes `FBA15GCL9X61`.
- SKU comes from the standalone line below `Single SKU`; values such as `1004201-BKYUS` are supported.
- Product name comes from the line after `数量 n`.
- Warehouse comes from the label title line ending in `-<warehouse> Created:` and falls back to known warehouse-code patterns.
- Destination country comes from supported Chinese country names in the destination address block, with current coverage for the sample set: `美国` and `澳大利亚`.
- `Single SKU` must appear in the PDF; missing status is marked invalid.

## Interaction Design

The first screen is the working tool, not a landing page. The visual system is restrained enterprise SaaS:

- Left sidebar for modules: `货件PDF处理`, `交易报告PDF`, `交易明细CSV`, `历史任务`, `设置`.
- Main workspace focused on shipment PDF processing.
- Upload/drop zone and server folder path import are both available.
- Summary cards show files, boxes, valid records, and records needing review.
- Review table is dense, sortable-looking, and scan-friendly.
- Rename is a two-step action: generate suggestions first, then apply only valid rows.
- Export buttons are always visible after a scan.
- Future modules appear as disabled/planned navigation items so the system feels extensible without pretending unfinished functions work.

## Deployment

The first phase runs with one Python command:

```bash
python -m app.ops_toolbox.server --host 0.0.0.0 --port 8080
```

For a company intranet server, the machine opens port `8080`; teammates visit `http://<server-ip>:8080/`. The repository can later be pushed to GitHub and deployed by pulling code on the server. Docker can be added after the Python workflow is stable.

## Testing

Tests cover parser behavior using synthetic extraction text and sample PDFs where available. Batch tests cover filename suggestions, validation flags, and dry-run rename planning. Manual verification uses the `20260619` sample folder and confirms all 55 PDF files are processed without unresolved fields.
