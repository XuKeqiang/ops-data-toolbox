# Shipment PDF MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable Amazon operations toolbox workflow for shipment PDF extraction, export, and safe rename confirmation.

**Architecture:** Keep PDF parsing pure and independent from HTTP. Add a standard-library web server that manages uploads, folder scans, exports, and rename actions. Build a code-native browser UI that exposes the shipment workflow and leaves visible module slots for later report and CSV processors.

**Tech Stack:** Python 3 standard library HTTP server, `pdfplumber`, `pandas`, `openpyxl`, vanilla HTML/CSS/JavaScript, `unittest`.

---

## File Structure

- `app/amazon_toolbox/shipment_pdf/models.py`: dataclasses for extracted records, validation, and rename plans.
- `app/amazon_toolbox/shipment_pdf/extractor.py`: PDF text extraction and field parsing.
- `app/amazon_toolbox/shipment_pdf/batch.py`: folder scanning, export table generation, and safe rename execution.
- `app/amazon_toolbox/server.py`: local intranet HTTP server and JSON/export endpoints.
- `app/static/index.html`: single-page internal toolbox UI.
- `app/static/styles.css`: responsive enterprise SaaS styling.
- `app/static/app.js`: upload, scan, table rendering, export, and rename interactions.
- `tests/test_shipment_pdf.py`: parser and batch behavior tests.
- `README.md`: setup, usage, deployment, and GitHub workflow.

## Tasks

### Task 1: Parser Contracts

- [ ] Add dataclasses for shipment extraction records and rename plans.
- [ ] Write tests that parse representative label text for Australia and US shipments.
- [ ] Implement field parsing for `Single SKU`, FBA code prefix, page count, destination country, warehouse, SKU, product name, and validation notes.

### Task 2: Batch Processing

- [ ] Write tests for scanning PDF folders and building suggested names.
- [ ] Implement batch scan with per-file validation and no destructive changes.
- [ ] Implement CSV/XLSX export row generation.
- [ ] Implement safe rename planning and application that skips invalid or conflicting targets.

### Task 3: Web API

- [ ] Add standard-library HTTP routes for health, folder scan, upload scan, export CSV/XLSX, and rename.
- [ ] Store uploaded batches under `data/uploads` and generated outputs under `data/outputs`.
- [ ] Return compact JSON summaries and row-level validation notes.

### Task 4: Frontend

- [ ] Build the internal toolbox layout with module sidebar and shipment workspace.
- [ ] Add drag-and-drop upload, folder path scan, scan status, summary cards, review table, export buttons, and rename confirmation.
- [ ] Keep planned modules visible but disabled.

### Task 5: Documentation And Verification

- [ ] Add setup, usage, deployment, GitHub, and extension documentation.
- [ ] Run tests.
- [ ] Scan the `20260619` sample folder.
- [ ] Start the local server and verify the UI route responds.
