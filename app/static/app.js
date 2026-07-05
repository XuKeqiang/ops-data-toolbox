const state = {
  batchId: "",
  records: [],
  reportJobId: "",
  transactionJobId: "",
  activeView: "shipment",
  currentUser: null,
  shipmentFilters: {
    query: "",
    status: "all",
    country: "all",
    warehouse: "all",
  },
  shipmentSort: {
    field: "original_filename",
    direction: "asc",
  },
  shipmentColumnFilters: {},
  activeColumnMenu: "",
  selectedShipmentPaths: new Set(),
  historyTasks: [],
  activeHistoryTaskId: "",
  historyFilter: "all",
  selectedHistoryTaskIds: new Set(),
  pendingShipmentFiles: [],
  pendingReportFiles: [],
  reportRows: [],
  transactionRows: [],
  reportReviewFilter: "all",
  reportFilters: {
    query: "",
  },
  reportSort: {
    field: "source_file",
    direction: "asc",
  },
  reportColumnFilters: {},
  activeReportColumnMenu: "",
  shipmentBusy: false,
  reportBusy: false,
  transactionBusy: false,
  shipmentAbortController: null,
  reportAbortController: null,
  transactionAbortController: null,
  lastShipmentTask: null,
  lastReportTask: null,
  lastTransactionTask: null,
};

const els = {
  loginScreen: document.querySelector("#loginScreen"),
  loginForm: document.querySelector("#loginForm"),
  loginUsername: document.querySelector("#loginUsername"),
  loginPassword: document.querySelector("#loginPassword"),
  loginStatus: document.querySelector("#loginStatus"),
  masthead: document.querySelector("#masthead"),
  appShell: document.querySelector("#appShell"),
  userBadge: document.querySelector("#userBadge"),
  logoutButton: document.querySelector("#logoutButton"),
  navItems: document.querySelectorAll("[data-view]"),
  viewPanels: document.querySelectorAll("[data-view-panel]"),
  inspectorPanels: document.querySelectorAll("[data-inspector-panel]"),
  uploadForm: document.querySelector("#uploadForm"),
  fileInput: document.querySelector("#fileInput"),
  folderUploadInput: document.querySelector("#folderUploadInput"),
  dropTarget: document.querySelector("#dropTarget"),
  uploadSelectionText: document.querySelector("#uploadSelectionText"),
  uploadPickers: document.querySelectorAll("[data-upload-picker]"),
  shipmentLogList: document.querySelector("#shipmentLogList"),
  folderForm: document.querySelector("#folderForm"),
  folderInput: document.querySelector("#folderInput"),
  filesMetric: document.querySelector("#filesMetric"),
  boxesMetric: document.querySelector("#boxesMetric"),
  validMetric: document.querySelector("#validMetric"),
  reviewMetric: document.querySelector("#reviewMetric"),
  batchLabel: document.querySelector("#batchLabel"),
  statusText: document.querySelector("#statusText"),
  resultBody: document.querySelector("#resultBody"),
  shipmentSearchInput: document.querySelector("#shipmentSearchInput"),
  shipmentStatusFilter: document.querySelector("#shipmentStatusFilter"),
  shipmentCountryFilter: document.querySelector("#shipmentCountryFilter"),
  shipmentWarehouseFilter: document.querySelector("#shipmentWarehouseFilter"),
  clearShipmentFilters: document.querySelector("#clearShipmentFilters"),
  shipmentFilterSummary: document.querySelector("#shipmentFilterSummary"),
  shipmentSelectionToolbar: document.querySelector("#shipmentSelectionToolbar"),
  shipmentSelectionCount: document.querySelector("#shipmentSelectionCount"),
  selectVisibleShipments: document.querySelector("#selectVisibleShipments"),
  clearShipmentSelection: document.querySelector("#clearShipmentSelection"),
  downloadSelectedShipments: document.querySelector("#downloadSelectedShipments"),
  selectAllVisibleShipments: document.querySelector("#selectAllVisibleShipments"),
  columnMenuButtons: document.querySelectorAll("[data-column-field]"),
  uploadSubmitButton: document.querySelector('#uploadForm button[type="submit"]'),
  folderScanButton: document.querySelector('#folderForm button[type="submit"]'),
  newShipmentTask: document.querySelector("#newShipmentTask"),
  cancelShipmentTask: document.querySelector("#cancelShipmentTask"),
  retryShipmentTask: document.querySelector("#retryShipmentTask"),
  clearShipmentResult: document.querySelector("#clearShipmentResult"),
  exportMenu: document.querySelector("#exportMenu"),
  exportMenuButton: document.querySelector("#exportMenuButton"),
  exportCsv: document.querySelector("#exportCsv"),
  exportXlsx: document.querySelector("#exportXlsx"),
  packageButton: document.querySelector("#packageButton"),
  packageResult: document.querySelector("#packageResult"),
  renameButton: document.querySelector("#renameButton"),
  reportFolderForm: document.querySelector("#reportFolderForm"),
  reportUploadForm: document.querySelector("#reportUploadForm"),
  reportFileInput: document.querySelector("#reportFileInput"),
  reportFolderUploadInput: document.querySelector("#reportFolderUploadInput"),
  reportDropTarget: document.querySelector("#reportDropTarget"),
  reportUploadSelectionText: document.querySelector("#reportUploadSelectionText"),
  reportUploadPickers: document.querySelectorAll("[data-report-upload-picker]"),
  reportFolderInput: document.querySelector("#reportFolderInput"),
  reportFilesMetric: document.querySelector("#reportFilesMetric"),
  reportProcessedMetric: document.querySelector("#reportProcessedMetric"),
  reportDetailsMetric: document.querySelector("#reportDetailsMetric"),
  reportWarningsMetric: document.querySelector("#reportWarningsMetric"),
  reportBatchLabel: document.querySelector("#reportBatchLabel"),
  reportStatusText: document.querySelector("#reportStatusText"),
  reportLogList: document.querySelector("#reportLogList"),
  reportReviewPanel: document.querySelector("#reportReviewPanel"),
  reportSearchInput: document.querySelector("#reportSearchInput"),
  clearReportFilters: document.querySelector("#clearReportFilters"),
  reportFilterSummary: document.querySelector("#reportFilterSummary"),
  reportColumnMenuButtons: document.querySelectorAll("[data-report-column-field]"),
  reportResultBody: document.querySelector("#reportResultBody"),
  reportDownload: document.querySelector("#reportDownload"),
  reportUploadSubmitButton: document.querySelector('#reportUploadForm button[type="submit"]'),
  reportFolderSubmitButton: document.querySelector('#reportFolderForm button[type="submit"]'),
  newReportTask: document.querySelector("#newReportTask"),
  cancelReportTask: document.querySelector("#cancelReportTask"),
  retryReportTask: document.querySelector("#retryReportTask"),
  clearReportResult: document.querySelector("#clearReportResult"),
  transactionFolderForm: document.querySelector("#transactionFolderForm"),
  transactionFolderInput: document.querySelector("#transactionFolderInput"),
  transactionSubmitButton: document.querySelector('#transactionFolderForm button[type="submit"]'),
  transactionFilesMetric: document.querySelector("#transactionFilesMetric"),
  transactionRowsMetric: document.querySelector("#transactionRowsMetric"),
  transactionCountriesMetric: document.querySelector("#transactionCountriesMetric"),
  transactionWarningsMetric: document.querySelector("#transactionWarningsMetric"),
  transactionBatchLabel: document.querySelector("#transactionBatchLabel"),
  transactionStatusText: document.querySelector("#transactionStatusText"),
  transactionLogList: document.querySelector("#transactionLogList"),
  transactionResultBody: document.querySelector("#transactionResultBody"),
  transactionDownload: document.querySelector("#transactionDownload"),
  transactionAuditDownload: document.querySelector("#transactionAuditDownload"),
  newTransactionTask: document.querySelector("#newTransactionTask"),
  cancelTransactionTask: document.querySelector("#cancelTransactionTask"),
  retryTransactionTask: document.querySelector("#retryTransactionTask"),
  clearTransactionResult: document.querySelector("#clearTransactionResult"),
  openHistoryButtons: document.querySelectorAll("[data-open-history]"),
  refreshHistoryButton: document.querySelector("#refreshHistoryButton"),
  cleanupHistoryButton: document.querySelector("#cleanupHistoryButton"),
  historyTypeFilter: document.querySelector("#historyTypeFilter"),
  clearHistoryFilter: document.querySelector("#clearHistoryFilter"),
  historySelectionToolbar: document.querySelector("#historySelectionToolbar"),
  historySelectionCount: document.querySelector("#historySelectionCount"),
  selectVisibleHistory: document.querySelector("#selectVisibleHistory"),
  selectAllHistory: document.querySelector("#selectAllHistory"),
  deleteSelectedHistory: document.querySelector("#deleteSelectedHistory"),
  clearHistorySelection: document.querySelector("#clearHistorySelection"),
  selectAllVisibleHistory: document.querySelector("#selectAllVisibleHistory"),
  historyTotalMetric: document.querySelector("#historyTotalMetric"),
  historyShipmentMetric: document.querySelector("#historyShipmentMetric"),
  historyReportMetric: document.querySelector("#historyReportMetric"),
  historyTransactionMetric: document.querySelector("#historyTransactionMetric"),
  historyReviewMetric: document.querySelector("#historyReviewMetric"),
  historyStatusText: document.querySelector("#historyStatusText"),
  historyResultBody: document.querySelector("#historyResultBody"),
  historyDetailModal: document.querySelector("#historyDetailModal"),
  historyDetailPanel: document.querySelector("#historyDetailPanel"),
  closeHistoryDetail: document.querySelector("#closeHistoryDetail"),
  refreshSettingsButton: document.querySelector("#refreshSettingsButton"),
  serviceSettingsList: document.querySelector("#serviceSettingsList"),
  pathSettingsList: document.querySelector("#pathSettingsList"),
  processingSettingsList: document.querySelector("#processingSettingsList"),
  deploymentSettingsList: document.querySelector("#deploymentSettingsList"),
  userManagementPanel: document.querySelector("#userManagementPanel"),
  userForm: document.querySelector("#userForm"),
  newUsername: document.querySelector("#newUsername"),
  newDisplayName: document.querySelector("#newDisplayName"),
  newPassword: document.querySelector("#newPassword"),
  newRole: document.querySelector("#newRole"),
  userStatusText: document.querySelector("#userStatusText"),
  userTableBody: document.querySelector("#userTableBody"),
};

const hashByView = {
  shipment: "shipment",
  report: "report-pdf",
  transaction: "transaction-csv",
  history: "history",
  settings: "settings",
};

const shipmentColumnLabels = {
  original_filename: "原文件名",
  factory_name: "工厂/供应商",
  sku: "SKU",
  product_name: "产品名",
  destination_country: "国家",
  warehouse: "仓库",
  fba_code: "FBA编码",
  total_units: "箱/件",
  is_valid: "状态",
};

const reportColumnLabels = {
  source_file: "来源文件",
  store: "推断品牌/店铺",
  site: "站点/币种",
  period: "报告期",
  scale: "提取规模",
  status: "复核结论",
  notes: "人工介入原因",
};

els.navItems.forEach((item) => {
  item.addEventListener("click", () => {
    setActiveView(item.dataset.view);
    window.location.hash = hashByView[item.dataset.view] || "shipment";
  });
});

els.openHistoryButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.historyFilter = button.dataset.openHistory || "all";
    els.historyTypeFilter.value = state.historyFilter;
    setActiveView("history");
    window.location.hash = "history";
    loadHistory();
  });
});

els.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = normalizeLoginText(els.loginUsername.value).toLowerCase();
  const password = normalizeLoginPassword(els.loginPassword.value);
  if (!username || !password) {
    els.loginStatus.textContent = "请输入用户名和密码";
    if (!username) {
      els.loginUsername.focus();
    } else {
      els.loginPassword.focus();
    }
    return;
  }
  els.loginStatus.textContent = "正在登录...";
  const response = await fetch("/api/login", {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      password,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    els.loginStatus.textContent = payload.error || "登录失败，请检查账号和密码";
    els.loginPassword.select();
    return;
  }
  applySession(payload.user);
});

els.logoutButton.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  state.currentUser = null;
  showLoggedOut();
});

els.uploadPickers.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.uploadPicker === "folder") {
      els.folderUploadInput.click();
      return;
    }
    els.fileInput.click();
  });
});

els.dropTarget.addEventListener("click", () => {
  els.fileInput.click();
});

els.dropTarget.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  els.fileInput.click();
});

els.fileInput.addEventListener("change", () => {
  setPendingShipmentFiles([...els.fileInput.files].map((file) => ({ file, relativePath: file.name })), "已选择 PDF 文件");
});

els.folderUploadInput.addEventListener("change", () => {
  setPendingShipmentFiles(
    [...els.folderUploadInput.files].map((file) => ({
      file,
      relativePath: file.webkitRelativePath || file.name,
    })),
    "已选择文件夹",
  );
});

["dragenter", "dragover"].forEach((eventName) => {
  els.uploadForm.addEventListener(eventName, (event) => {
    event.preventDefault();
    els.uploadForm.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  els.uploadForm.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName === "dragleave" && els.uploadForm.contains(event.relatedTarget)) return;
    els.uploadForm.classList.remove("drag-over");
  });
});

els.uploadForm.addEventListener("drop", async (event) => {
  resetShipmentLogs("正在读取拖放内容...");
  const droppedFiles = await collectDroppedFiles(event.dataTransfer);
  setPendingShipmentFiles(droppedFiles, "已读取拖放内容");
});

els.cancelShipmentTask.addEventListener("click", () => {
  cancelShipmentTask();
});

els.retryShipmentTask.addEventListener("click", () => {
  retryShipmentTask();
});

els.newShipmentTask.addEventListener("click", () => {
  startNewShipmentTask();
});

els.clearShipmentResult.addEventListener("click", () => {
  clearShipmentResults({ resetInputs: false });
});

els.reportUploadPickers.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.reportUploadPicker === "folder") {
      els.reportFolderUploadInput.click();
      return;
    }
    els.reportFileInput.click();
  });
});

els.reportDropTarget.addEventListener("click", () => {
  els.reportFileInput.click();
});

els.reportDropTarget.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  els.reportFileInput.click();
});

els.reportFileInput.addEventListener("change", () => {
  resetReportLogs("正在读取选择的 PDF 文件...");
  setPendingReportFiles([...els.reportFileInput.files].map((file) => ({ file, relativePath: file.name })), "已选择 PDF 文件");
});

els.reportFolderUploadInput.addEventListener("change", () => {
  resetReportLogs("正在读取选择的文件夹...");
  setPendingReportFiles(
    [...els.reportFolderUploadInput.files].map((file) => ({
      file,
      relativePath: file.webkitRelativePath || file.name,
    })),
    "已选择文件夹",
  );
});

["dragenter", "dragover"].forEach((eventName) => {
  els.reportUploadForm.addEventListener(eventName, (event) => {
    event.preventDefault();
    els.reportUploadForm.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  els.reportUploadForm.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName === "dragleave" && els.reportUploadForm.contains(event.relatedTarget)) return;
    els.reportUploadForm.classList.remove("drag-over");
  });
});

els.reportUploadForm.addEventListener("drop", async (event) => {
  resetReportLogs("正在读取拖放内容...");
  setReportStatus("正在读取拖放内容...");
  const droppedFiles = await collectDroppedFiles(event.dataTransfer);
  setPendingReportFiles(droppedFiles, "已读取拖放内容");
});

els.cancelReportTask.addEventListener("click", () => {
  cancelReportTask();
});

els.retryReportTask.addEventListener("click", () => {
  retryReportTask();
});

els.newReportTask.addEventListener("click", () => {
  startNewReportTask();
});

els.clearReportResult.addEventListener("click", () => {
  clearReportResults({ resetInputs: false });
});

els.folderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.shipmentBusy) return;
  state.lastShipmentTask = () => els.folderForm.requestSubmit();
  resetShipmentLogs("准备扫描服务器文件夹...");
  setBusy("正在扫描服务器文件夹...");
  const controller = new AbortController();
  state.shipmentAbortController = controller;
  updateBusyControls();
  try {
    const response = await fetch("/api/scan-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: els.folderInput.value }),
      signal: controller.signal,
    });
    await handleBatchResponse(response);
  } catch (error) {
    if (isAbortError(error)) {
      addShipmentLog("已终止当前扫描任务", "warning");
      setStatus("已终止当前任务");
      return;
    }
    addShipmentLog("扫描请求失败，请确认服务仍在运行", "error");
    setStatus("扫描请求失败");
  } finally {
    clearShipmentAbortController(controller);
  }
});

els.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.shipmentBusy) return;
  const files = state.pendingShipmentFiles;
  if (!files.length) {
    addShipmentLog("请选择至少一个 PDF 文件或拖放一个文件夹", "warning");
    setStatus("请选择至少一个 PDF 文件");
    return;
  }
  const pdfCount = files.filter((item) => isPdfFile(item.file)).length;
  if (!pdfCount) {
    addShipmentLog("当前选择里没有 PDF 文件，请重新选择", "error");
    setStatus("没有可上传的 PDF 文件");
    return;
  }

  addShipmentLog(`开始上传 ${files.length} 个文件，其中 ${pdfCount} 个 PDF`);
  logSkippedNonPdfFiles(files, addShipmentLog);
  state.lastShipmentTask = () => els.uploadForm.requestSubmit();
  setBusy(`正在上传并识别 ${pdfCount} 个 PDF...`);
  const controller = new AbortController();
  state.shipmentAbortController = controller;
  updateBusyControls();
  const formData = new FormData();
  files.forEach((item) => formData.append("files", item.file, item.relativePath || item.file.name));
  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    await handleBatchResponse(response);
  } catch (error) {
    if (isAbortError(error)) {
      addShipmentLog("已终止当前上传识别任务", "warning");
      setStatus("已终止当前任务");
      return;
    }
    addShipmentLog("上传请求失败，请确认服务仍在运行", "error");
    setStatus("上传请求失败");
  } finally {
    clearShipmentAbortController(controller);
  }
});

els.reportFolderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.reportBusy) return;
  state.lastReportTask = () => els.reportFolderForm.requestSubmit();
  resetReportLogs("准备扫描服务器文件夹...");
  addReportLog(`服务器文件夹：${els.reportFolderInput.value}`);
  setReportBusy("正在预检汇总报告 PDF...");
  disableReportDownload();
  resetReportResults();
  const controller = new AbortController();
  state.reportAbortController = controller;
  updateReportBusyControls();
  try {
    const preflightResponse = await fetch("/api/report-pdf/preflight-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: els.reportFolderInput.value }),
      signal: controller.signal,
    });
    const preflight = await handleReportPreflightResponse(preflightResponse);
    if (!preflight) return;
    if (!confirmReportPreflight(preflight)) {
      addReportLog("用户已取消处理任务", "warning");
      setReportStatus("已取消处理");
      return;
    }
    addReportLog("用户确认继续处理，开始生成 Excel...", "success");
    setReportBusy("正在提取汇总报告 PDF，并生成 Excel...");
    const response = await fetch("/api/report-pdf/process-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: els.reportFolderInput.value }),
      signal: controller.signal,
    });
    await handleReportResponse(response);
  } catch (error) {
    if (isAbortError(error)) {
      addReportLog("已终止当前服务器路径处理任务", "warning");
      setReportStatus("已终止当前任务");
      return;
    }
    addReportLog("处理请求失败，请确认服务仍在运行", "error");
    setReportStatus("处理请求失败，请确认服务仍在运行");
  } finally {
    clearReportAbortController(controller);
    setReportIdle();
  }
});

els.reportUploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.reportBusy) return;
  const files = state.pendingReportFiles;
  if (!files.length) {
    addReportLog("请选择至少一个 PDF 文件或拖放一个文件夹", "warning");
    setReportStatus("请选择至少一个 PDF 文件或拖放一个文件夹");
    return;
  }
  const pdfCount = files.filter((item) => isPdfFile(item.file)).length;
  if (!pdfCount) {
    addReportLog("当前选择里没有 PDF 文件，请重新选择", "error");
    setReportStatus("当前选择里没有 PDF 文件，请重新选择");
    return;
  }

  state.lastReportTask = () => els.reportUploadForm.requestSubmit();
  resetReportLogs(`开始上传预检 ${files.length} 个文件，其中 ${pdfCount} 个 PDF`);
  logSkippedNonPdfFiles(files, addReportLog);
  setReportBusy(`正在上传并预检 ${pdfCount} 个汇总报告 PDF...`);
  disableReportDownload();
  resetReportResults();
  const controller = new AbortController();
  state.reportAbortController = controller;
  updateReportBusyControls();
  const formData = new FormData();
  files.forEach((item) => formData.append("files", item.file, item.relativePath || item.file.name));
  try {
    const preflightResponse = await fetch("/api/report-pdf/preflight-upload", {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    const preflight = await handleReportPreflightResponse(preflightResponse);
    if (!preflight) return;
    if (!confirmReportPreflight(preflight)) {
      addReportLog("用户已取消处理任务", "warning");
      setReportStatus("已取消处理");
      return;
    }
    addReportLog("用户确认继续处理，开始生成 Excel...", "success");
    setReportBusy("正在提取汇总报告 PDF，并生成 Excel...");
    const response = await fetch("/api/report-pdf/process-preflight-upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preflight_id: preflight.preflight_id }),
      signal: controller.signal,
    });
    await handleReportResponse(response);
  } catch (error) {
    if (isAbortError(error)) {
      addReportLog("已终止当前上传提取任务", "warning");
      setReportStatus("已终止当前任务");
      return;
    }
    addReportLog("上传请求失败，请确认服务仍在运行", "error");
    setReportStatus("上传请求失败，请确认服务仍在运行");
  } finally {
    clearReportAbortController(controller);
    setReportIdle();
  }
});

els.transactionFolderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.transactionBusy) return;
  state.lastTransactionTask = () => els.transactionFolderForm.requestSubmit();
  resetTransactionLogs("准备读取交易明细文件夹...");
  addTransactionLog(`服务器文件夹：${els.transactionFolderInput.value}`);
  setTransactionBusy("正在清洗交易明细，并生成 Excel...");
  disableTransactionDownloads();
  const controller = new AbortController();
  state.transactionAbortController = controller;
  updateTransactionBusyControls();
  try {
    const response = await fetch("/api/transaction-csv/process-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: els.transactionFolderInput.value }),
      signal: controller.signal,
    });
    await handleTransactionResponse(response);
  } catch (error) {
    if (isAbortError(error)) {
      addTransactionLog("已终止当前清洗任务", "warning");
      setTransactionStatus("已终止当前任务");
      return;
    }
    addTransactionLog("处理请求失败，请确认服务仍在运行", "error");
    setTransactionStatus("处理请求失败，请确认服务仍在运行");
  } finally {
    clearTransactionAbortController(controller);
    setTransactionIdle();
  }
});

els.cancelTransactionTask.addEventListener("click", () => {
  cancelTransactionTask();
});

els.retryTransactionTask.addEventListener("click", () => {
  retryTransactionTask();
});

els.newTransactionTask.addEventListener("click", () => {
  startNewTransactionTask();
});

els.clearTransactionResult.addEventListener("click", () => {
  clearTransactionResults({ resetInput: false });
});

els.refreshHistoryButton.addEventListener("click", () => {
  loadHistory();
});

els.historyTypeFilter.addEventListener("change", () => {
  state.historyFilter = els.historyTypeFilter.value;
  renderHistoryList();
});

els.clearHistoryFilter.addEventListener("click", () => {
  state.historyFilter = "all";
  els.historyTypeFilter.value = "all";
  renderHistoryList();
});

els.selectVisibleHistory.addEventListener("click", () => {
  getVisibleHistoryTasks().forEach((task) => state.selectedHistoryTaskIds.add(task.id));
  renderHistoryList();
});

els.selectAllHistory.addEventListener("click", () => {
  state.historyTasks.forEach((task) => state.selectedHistoryTaskIds.add(task.id));
  renderHistoryList();
});

els.clearHistorySelection.addEventListener("click", () => {
  state.selectedHistoryTaskIds.clear();
  renderHistoryList();
});

els.deleteSelectedHistory.addEventListener("click", async () => {
  await deleteSelectedHistoryTasks();
});

els.selectAllVisibleHistory.addEventListener("change", () => {
  const visibleTasks = getVisibleHistoryTasks();
  if (els.selectAllVisibleHistory.checked) {
    visibleTasks.forEach((task) => state.selectedHistoryTaskIds.add(task.id));
  } else {
    visibleTasks.forEach((task) => state.selectedHistoryTaskIds.delete(task.id));
  }
  renderHistoryList();
});

els.cleanupHistoryButton.addEventListener("click", async () => {
  await cleanupHistory();
});

els.historyResultBody.addEventListener("click", (event) => {
  const detailButton = event.target.closest("[data-history-detail]");
  if (detailButton) {
    state.activeHistoryTaskId = detailButton.dataset.historyDetail;
    renderHistoryDetail(state.historyTasks.find((task) => task.id === state.activeHistoryTaskId));
    return;
  }
  const deleteButton = event.target.closest("[data-history-delete]");
  if (deleteButton) {
    deleteHistoryTask(deleteButton.dataset.historyDelete);
    return;
  }
  const checkbox = event.target.closest("[data-history-select]");
  if (checkbox) {
    if (checkbox.checked) {
      state.selectedHistoryTaskIds.add(checkbox.dataset.historySelect);
    } else {
      state.selectedHistoryTaskIds.delete(checkbox.dataset.historySelect);
    }
    updateHistorySelectionToolbar();
  }
});

els.closeHistoryDetail.addEventListener("click", () => {
  closeHistoryDetail();
});

els.historyDetailModal.addEventListener("click", (event) => {
  if (event.target === els.historyDetailModal) closeHistoryDetail();
});

els.reportReviewPanel.addEventListener("click", (event) => {
  const filterButton = event.target.closest("[data-report-filter]");
  if (!filterButton) return;
  state.reportReviewFilter = filterButton.dataset.reportFilter || "all";
  renderReportRows();
  renderReportReviewPanel(state.reportRows);
});

els.reportSearchInput.addEventListener("input", () => {
  state.reportFilters.query = els.reportSearchInput.value.trim();
  renderReportRows();
});

els.clearReportFilters.addEventListener("click", () => {
  resetReportTableFilters();
  renderReportRows();
  renderReportReviewPanel(state.reportRows);
});

els.reportFilterSummary.addEventListener("click", (event) => {
  const button = event.target.closest("[data-report-filter-chip]");
  if (!button) return;
  clearReportFilterChip(button.dataset.reportFilterChip);
  renderReportRows();
  renderReportReviewPanel(state.reportRows);
});

els.reportColumnMenuButtons.forEach((button) => {
  button.addEventListener("click", () => {
    toggleReportColumnMenu(button.dataset.reportColumnField, button);
  });
});

els.refreshSettingsButton.addEventListener("click", () => {
  loadSettings();
});

els.userForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createUser();
});

els.exportMenuButton.addEventListener("click", () => {
  if (!state.batchId) return;
  const isOpen = els.exportMenu.classList.toggle("open");
  els.exportMenuButton.setAttribute("aria-expanded", String(isOpen));
});

els.exportCsv.addEventListener("click", (event) => {
  event.preventDefault();
  startShipmentExport("csv");
});

els.exportXlsx.addEventListener("click", (event) => {
  event.preventDefault();
  startShipmentExport("xlsx");
});

els.shipmentSearchInput.addEventListener("input", () => {
  state.shipmentFilters.query = els.shipmentSearchInput.value.trim();
  renderShipmentRecords();
});

els.shipmentStatusFilter.addEventListener("change", () => {
  state.shipmentFilters.status = els.shipmentStatusFilter.value;
  renderShipmentRecords();
});

els.shipmentCountryFilter.addEventListener("change", () => {
  state.shipmentFilters.country = els.shipmentCountryFilter.value;
  renderShipmentRecords();
});

els.shipmentWarehouseFilter.addEventListener("change", () => {
  state.shipmentFilters.warehouse = els.shipmentWarehouseFilter.value;
  renderShipmentRecords();
});

els.clearShipmentFilters.addEventListener("click", () => {
  resetShipmentFilters();
  renderShipmentRecords();
});

els.selectVisibleShipments.addEventListener("click", () => {
  getVisibleShipmentRecords().forEach((record) => state.selectedShipmentPaths.add(record.source_path));
  renderShipmentRecords();
});

els.clearShipmentSelection.addEventListener("click", () => {
  state.selectedShipmentPaths.clear();
  renderShipmentRecords();
});

els.selectAllVisibleShipments.addEventListener("change", () => {
  const visibleRecords = getVisibleShipmentRecords();
  if (els.selectAllVisibleShipments.checked) {
    visibleRecords.forEach((record) => state.selectedShipmentPaths.add(record.source_path));
  } else {
    visibleRecords.forEach((record) => state.selectedShipmentPaths.delete(record.source_path));
  }
  renderShipmentRecords();
});

els.downloadSelectedShipments.addEventListener("click", downloadSelectedShipmentPdfs);

els.resultBody.addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-shipment-select]");
  if (!checkbox) return;
  if (checkbox.checked) {
    state.selectedShipmentPaths.add(checkbox.dataset.shipmentSelect);
  } else {
    state.selectedShipmentPaths.delete(checkbox.dataset.shipmentSelect);
  }
  updateShipmentSelectionToolbar(getVisibleShipmentRecords());
});

els.shipmentFilterSummary.addEventListener("click", (event) => {
  const button = event.target.closest("[data-filter-chip]");
  if (!button) return;
  clearShipmentFilterChip(button.dataset.filterChip);
  renderShipmentRecords();
});

els.columnMenuButtons.forEach((button) => {
  button.addEventListener("click", () => {
    toggleColumnMenu(button.dataset.columnField, button);
  });
});

document.addEventListener("click", (event) => {
  const copyPackagePathButton = event.target.closest("[data-copy-package-path]");
  if (copyPackagePathButton) {
    copyTextToClipboard(copyPackagePathButton.dataset.copyPackagePath || "", "已复制结果文件夹路径");
    return;
  }
  if (!els.exportMenu.contains(event.target)) {
    closeExportMenu();
  }
  if (!event.target.closest(".column-menu-popover") && !event.target.closest(".column-menu-button")) {
    closeColumnMenu();
    closeReportColumnMenu();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeExportMenu();
    closeColumnMenu();
    closeReportColumnMenu();
    closeHistoryDetail();
  }
});

els.renameButton.addEventListener("click", async () => {
  if (!state.batchId) return;
  const validRenameCount = state.records.filter((record) => record.rename.can_apply).length;
  const message = `将重命名 ${validRenameCount} 个文件。此操作会修改服务器上的文件名，是否继续？`;
  if (!window.confirm(message)) return;

  setBusy("正在执行重命名...");
  const response = await fetch("/api/rename", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batch_id: state.batchId, confirm: true }),
  });
  const payload = await response.json();
  if (!response.ok) {
    setStatus(payload.error || "重命名失败");
    return;
  }
  setStatus(`已重命名 ${payload.renamed} 个文件`);
});

els.packageButton.addEventListener("click", async () => {
  if (!state.batchId) return;
  const reviewCount = state.records.filter((record) => !record.is_valid).length;
  const factoryCount = new Set(state.records.map((record) => record.filename_info.factory_name).filter(Boolean)).size;
  const message = reviewCount
    ? `当前还有 ${reviewCount} 个文件需要复核。确认人工核对无误，并按 ${factoryCount} 个工厂打包原始 PDF？`
    : `确认按 ${factoryCount} 个工厂打包原始 PDF？`;
  if (!window.confirm(message)) return;

  setBusy("正在按工厂打包原始 PDF...");
  els.packageButton.disabled = true;
  const response = await fetch("/api/package-by-factory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batch_id: state.batchId, confirm: true }),
  });
  const payload = await response.json();
  if (!response.ok) {
    setStatus(payload.error || "打包失败");
    updateActionButtons();
    return;
  }
  renderPackageResult(payload);
  setStatus(`打包完成：已生成 ${payload.packages.length} 个工厂压缩包，结果在识别表格下方。`);
  els.packageResult.scrollIntoView({ behavior: "smooth", block: "center" });
  if (state.activeView === "history") {
    loadHistory();
  }
  updateActionButtons();
});

window.addEventListener("hashchange", () => {
  if (!state.currentUser) return;
  setActiveView(viewFromHash());
});

if (!["", "#shipment", "#report-pdf", "#transaction-csv", "#history", "#settings"].includes(window.location.hash)) {
  window.history.replaceState(null, "", "#shipment");
}

bootstrapSession();

async function bootstrapSession() {
  const response = await fetch("/api/session");
  const payload = await response.json();
  if (payload.authenticated) {
    applySession(payload.user);
  } else {
    showLoggedOut();
  }
}

function applySession(user) {
  state.currentUser = user;
  els.loginScreen.classList.add("hidden");
  els.masthead.classList.remove("hidden");
  els.appShell.classList.remove("hidden");
  els.userBadge.textContent = `${user.display_name} · ${roleLabel(user.role)}`;
  updateBusyControls();
  updateReportBusyControls();
  updateTransactionBusyControls();
  setActiveView(viewFromHash());
}

function showLoggedOut() {
  state.currentUser = null;
  state.batchId = "";
  state.records = [];
  state.selectedShipmentPaths.clear();
  els.loginScreen.classList.remove("hidden");
  els.masthead.classList.add("hidden");
  els.appShell.classList.add("hidden");
  els.exportMenuButton.disabled = true;
  els.loginPassword.focus();
}

async function handleBatchResponse(response) {
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    renderShipmentLogs(payload.logs || [{ level: "error", message: payload.error || "处理失败" }], false);
    setStatus(payload.error || "处理失败");
    return;
  }
  state.batchId = payload.batch_id;
  state.records = payload.records;
  state.selectedShipmentPaths.clear();
  resetShipmentFilters();
  renderBatch(payload);
  renderShipmentLogs(payload.logs || [], true);
  if (state.activeView === "history") {
    loadHistory();
  }
}

async function handleReportResponse(response) {
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    addReportLog(payload.error || "处理失败", "error");
    logSkippedServerPaths(payload.skipped_paths, addReportLog);
    setReportStatus(payload.error || "处理失败");
    return;
  }
  logSkippedServerPaths(payload.skipped_paths, addReportLog);
  state.reportJobId = payload.job_id;
  addReportLog(`上传/扫描完成：共 ${payload.summary.files || 0} 个 PDF`);
  addReportLog(`解析完成：${payload.summary.processed || 0} 个 PDF，${payload.summary.detail_rows || 0} 条明细`);
  if (payload.summary.failed) {
    addReportLog(`解析失败：${payload.summary.failed} 个 PDF`, "warning");
  }
  if (payload.summary.warnings) {
    addReportLog(`需要复核：${payload.summary.warnings} 项`, "warning");
  }
  addReportLog("Excel 工作簿已生成，可下载复核", "success");
  renderReportJob(payload);
  if (state.activeView === "history") {
    loadHistory();
  }
}

async function handleReportPreflightResponse(response) {
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return null;
  }
  if (!response.ok) {
    addReportLog(payload.error || "预检失败", "error");
    logSkippedServerPaths(payload.skipped_paths, addReportLog);
    setReportStatus(payload.error || "预检失败");
    return null;
  }
  logSkippedServerPaths(payload.skipped_paths, addReportLog);
  addReportLog(`预检完成：${payload.processable || 0} 个可处理 PDF，发现 ${payload.issue_count || 0} 个需确认文件`, payload.issue_count ? "warning" : "success");
  (payload.issues || []).slice(0, 5).forEach((item) => {
    addReportLog(`${item.source_file}：${(item.issues || []).join("；")}`, "warning");
  });
  if ((payload.issues || []).length > 5) {
    addReportLog(`还有 ${(payload.issues || []).length - 5} 个问题文件未在日志中展开，可在处理结果中复核`, "warning");
  }
  return payload;
}

function confirmReportPreflight(preflight) {
  const issues = preflight.issues || [];
  const lines = [
    `预检完成：${preflight.processable || 0} 个可处理 PDF。`,
    issues.length ? `发现 ${issues.length} 个文件存在店铺/国家/期间等信息不一致或无法确认。` : "未发现明显店铺、国家或期间冲突。",
  ];
  issues.slice(0, 8).forEach((item) => {
    lines.push(`- ${item.source_file}: ${(item.issues || []).join("；")}`);
  });
  if (issues.length > 8) lines.push(`...还有 ${issues.length - 8} 个问题文件。`);
  lines.push("");
  lines.push("是否继续生成 Excel？");
  return window.confirm(lines.join("\n"));
}

async function handleTransactionResponse(response) {
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    addTransactionLog(payload.error || "处理失败", "error");
    setTransactionStatus(payload.error || "处理失败");
    return;
  }
  state.transactionJobId = payload.job_id;
  addTransactionLog(`文件读取完成：${payload.summary.source_files || 0} 个源文件`);
  addTransactionLog(`清洗完成：${payload.summary.total_rows || 0} 条明细，覆盖 ${payload.summary.countries || 0} 个国家`);
  const warningCount = (payload.summary.date_parse_failures || 0)
    + (payload.summary.amount_failures || 0)
    + (payload.summary.unresolved_country_files || 0)
    + (payload.summary.unsupported_files || 0);
  if (warningCount) {
    addTransactionLog(`需要复核：${warningCount} 项异常或未识别内容`, "warning");
  }
  addTransactionLog("总表与审计文件已生成，可下载复核", "success");
  renderTransactionJob(payload);
  if (state.activeView === "history") {
    loadHistory();
  }
}

function renderBatch(payload) {
  const { summary } = payload;
  els.filesMetric.textContent = summary.files;
  els.boxesMetric.textContent = summary.label_pages ?? summary.boxes;
  els.boxesMetric.title = summary.unique_carton_codes
    ? `已识别唯一箱码 ${summary.unique_carton_codes} 个`
    : "按 PDF 页数合计；每页通常对应一张外箱标";
  els.validMetric.textContent = summary.valid;
  els.reviewMetric.textContent = summary.needs_review;
  els.batchLabel.textContent = payload.source_label;
  setStatus(`已识别 ${summary.files} 个 PDF，${summary.needs_review} 个需要复核`);
  els.packageResult.classList.add("hidden");
  els.packageResult.innerHTML = "";

  els.exportCsv.href = `/api/export?batch_id=${payload.batch_id}&format=csv`;
  els.exportXlsx.href = `/api/export?batch_id=${payload.batch_id}&format=xlsx`;
  els.exportCsv.classList.remove("disabled");
  els.exportXlsx.classList.remove("disabled");
  els.exportMenuButton.disabled = false;
  setSoftDisabled(els.clearShipmentResult, false);

  updateActionButtons(payload.records);
  updateShipmentFilterOptions(payload.records);

  if (!payload.records.length) {
    els.resultBody.innerHTML = '<tr><td class="empty" colspan="13">该批次没有 PDF 文件。</td></tr>';
    return;
  }

  renderShipmentRecords();
}

function setPendingShipmentFiles(items, label) {
  const files = items.filter((item) => item && item.file && item.file.name);
  state.pendingShipmentFiles = files;
  const pdfCount = files.filter((item) => isPdfFile(item.file)).length;
  const skippedCount = files.length - pdfCount;
  const folderCount = uniqueSorted(files
    .map((item) => item.relativePath || item.file.name)
    .filter((path) => path.includes("/"))
    .map((path) => path.split("/")[0])).length;

  if (!files.length) {
    els.uploadSelectionText.textContent = "没有读取到文件，请重新拖放或选择";
    addShipmentLog("没有读取到文件", "warning");
    return;
  }

  const folderText = folderCount ? `，包含 ${folderCount} 个文件夹` : "";
  const skippedText = skippedCount ? `，${skippedCount} 个非 PDF 会被预处理跳过` : "";
  els.uploadSelectionText.textContent = `${label}：${files.length} 个文件，${pdfCount} 个 PDF${folderText}${skippedText}`;
  addShipmentLog(`${label}：${files.length} 个文件，${pdfCount} 个 PDF${skippedText}`, skippedCount ? "warning" : "info");
  logSkippedNonPdfFiles(files, addShipmentLog);
}

function setPendingReportFiles(items, label) {
  const files = items.filter((item) => item && item.file && item.file.name);
  state.pendingReportFiles = files;
  const pdfCount = files.filter((item) => isPdfFile(item.file)).length;
  const skippedCount = files.length - pdfCount;
  const folderCount = uniqueSorted(files
    .map((item) => item.relativePath || item.file.name)
    .filter((path) => path.includes("/"))
    .map((path) => path.split("/")[0])).length;

  if (!files.length) {
    els.reportUploadSelectionText.textContent = "没有读取到文件，请重新拖放或选择";
    addReportLog("没有读取到文件", "warning");
    setReportStatus("没有读取到文件");
    return;
  }

  const folderText = folderCount ? `，包含 ${folderCount} 个顶层文件夹` : "";
  const skippedText = skippedCount ? `，${skippedCount} 个非 PDF 会被跳过` : "";
  els.reportUploadSelectionText.textContent = `${label}：${files.length} 个文件，${pdfCount} 个 PDF${folderText}${skippedText}`;
  addReportLog(`${label}：${files.length} 个文件，${pdfCount} 个 PDF${skippedText}`, skippedCount ? "warning" : "info");
  logSkippedNonPdfFiles(files, addReportLog);
  setReportStatus(`${label}：${pdfCount} 个 PDF 已就绪${skippedText}`);
}

async function collectDroppedFiles(dataTransfer) {
  if (!dataTransfer) return [];
  const items = [...dataTransfer.items];
  const entries = items
    .filter((item) => item.kind === "file" && typeof item.webkitGetAsEntry === "function")
    .map((item) => item.webkitGetAsEntry())
    .filter(Boolean);

  if (entries.length) {
    const groups = await Promise.all(entries.map((entry) => readDroppedEntry(entry, "")));
    return groups.flat();
  }

  return [...dataTransfer.files].map((file) => ({ file, relativePath: file.name }));
}

function readDroppedEntry(entry, parentPath) {
  if (entry.isFile) {
    return new Promise((resolve) => {
      entry.file((file) => {
        resolve([{ file, relativePath: `${parentPath}${file.name}` }]);
      }, () => resolve([]));
    });
  }

  if (!entry.isDirectory) return Promise.resolve([]);
  const reader = entry.createReader();
  const directoryPath = `${parentPath}${entry.name}/`;
  const batches = [];

  return new Promise((resolve) => {
    const readBatch = () => {
      reader.readEntries(async (entries) => {
        if (!entries.length) {
          const resolved = await Promise.all(batches);
          resolve(resolved.flat());
          return;
        }
        batches.push(...entries.map((child) => readDroppedEntry(child, directoryPath)));
        readBatch();
      }, () => resolve([]));
    };
    readBatch();
  });
}

function isPdfFile(file) {
  return file.name.toLowerCase().endsWith(".pdf") || file.type === "application/pdf";
}

function getUploadItemPath(item) {
  return item.relativePath || item.file.webkitRelativePath || item.file.name;
}

function logSkippedNonPdfFiles(items, logFn, limit = 20) {
  const skippedItems = items.filter((item) => item && item.file && !isPdfFile(item.file));
  if (!skippedItems.length) return;
  logFn(`将跳过 ${skippedItems.length} 个非 PDF 文件，具体位置如下`, "warning");
  skippedItems.slice(0, limit).forEach((item) => {
    logFn(`非 PDF：${getUploadItemPath(item)}`, "warning");
  });
  if (skippedItems.length > limit) {
    logFn(`还有 ${skippedItems.length - limit} 个非 PDF 文件未在日志中展开`, "warning");
  }
}

function logSkippedServerPaths(paths, logFn, limit = 20) {
  if (!paths || !paths.length) return;
  logFn(`服务器实际跳过 ${paths.length} 个非 PDF 或无效文件`, "warning");
  paths.slice(0, limit).forEach((path) => {
    logFn(`已跳过：${path}`, "warning");
  });
  if (paths.length > limit) {
    logFn(`还有 ${paths.length - limit} 个已跳过文件未在日志中展开`, "warning");
  }
}

function resetShipmentLogs(message) {
  els.shipmentLogList.innerHTML = "";
  addShipmentLog(message);
}

function addShipmentLog(message, level = "info") {
  addLogItem(els.shipmentLogList, message, level);
}

function renderShipmentLogs(logs, append = true) {
  if (!append) {
    els.shipmentLogList.innerHTML = "";
  }
  logs.forEach((entry) => {
    addShipmentLog(entry.message || String(entry), entry.level || "info");
  });
}

function resetReportLogs(message) {
  els.reportLogList.innerHTML = "";
  addReportLog(message);
}

function addReportLog(message, level = "info") {
  addLogItem(els.reportLogList, message, level);
}

function resetTransactionLogs(message) {
  els.transactionLogList.innerHTML = "";
  addTransactionLog(message);
}

function addTransactionLog(message, level = "info") {
  addLogItem(els.transactionLogList, message, level);
}

function addLogItem(list, message, level = "info") {
  const item = document.createElement("li");
  item.className = level;
  item.textContent = message;
  list.appendChild(item);
}

function setSoftDisabled(button, disabled) {
  button.disabled = false;
  button.classList.toggle("soft-disabled", Boolean(disabled));
  button.dataset.unavailable = String(Boolean(disabled));
  button.title = disabled ? "当前不可直接执行，点击可查看原因" : "";
}

function renderShipmentRecords() {
  updateSortButtons();
  updateFilterButtonState();
  const visibleRecords = getVisibleShipmentRecords();
  renderShipmentFilterSummary(visibleRecords.length);
  if (!state.records.length) {
    els.resultBody.innerHTML = '<tr><td class="empty" colspan="13">该批次没有 PDF 文件。</td></tr>';
    updateShipmentSelectionToolbar([]);
    return;
  }
  if (!visibleRecords.length) {
    els.resultBody.innerHTML = '<tr><td class="empty" colspan="13">没有符合筛选条件的记录。</td></tr>';
    setStatus(`当前显示 0 / ${state.records.length} 条记录`);
    updateShipmentSelectionToolbar([]);
    return;
  }
  els.resultBody.innerHTML = visibleRecords.map(renderRow).join("");
  updateShipmentSelectionToolbar(visibleRecords);
  setStatus(`当前显示 ${visibleRecords.length} / ${state.records.length} 条记录`);
}

function getVisibleShipmentRecords() {
  const { query, status, country, warehouse } = state.shipmentFilters;
  const normalizedQuery = query.toLowerCase();
  return [...state.records]
    .filter((record) => {
      if (status === "valid" && !record.is_valid) return false;
      if (status === "review" && record.is_valid) return false;
      if (country !== "all" && record.destination_country !== country) return false;
      if (warehouse !== "all" && record.warehouse !== warehouse) return false;
      if (!matchesColumnFilters(record)) return false;
      if (!normalizedQuery) return true;
      return shipmentSearchText(record).toLowerCase().includes(normalizedQuery);
    })
    .sort(compareShipmentRecords);
}

function matchesColumnFilters(record) {
  return Object.entries(state.shipmentColumnFilters).every(([field, expected]) => {
    return shipmentColumnDisplayValue(record, field) === expected;
  });
}

function shipmentSearchText(record) {
  const filenameInfo = record.filename_info || {};
  return [
    record.original_filename,
    filenameInfo.factory_name,
    filenameInfo.sku,
    filenameInfo.product_name,
    record.sku,
    record.product_name,
    record.title_product_name,
    record.label_type,
    record.logistics_code,
    record.destination_country,
    record.warehouse,
    record.fba_code,
    record.shipment_total_boxes ? `${record.shipment_total_boxes}` : "",
    record.suggested_filename,
    ...(record.notes || []),
    ...(filenameInfo.notes || []),
    ...(record.comparison_notes || []),
  ].filter(Boolean).join(" ");
}

function compareShipmentRecords(left, right) {
  const field = state.shipmentSort.field;
  const direction = state.shipmentSort.direction === "desc" ? -1 : 1;
  const leftValue = shipmentSortValue(left, field);
  const rightValue = shipmentSortValue(right, field);
  if (typeof leftValue === "number" && typeof rightValue === "number") {
    return (leftValue - rightValue) * direction;
  }
  return String(leftValue || "").localeCompare(String(rightValue || ""), "zh-Hans-CN", {
    numeric: true,
    sensitivity: "base",
  }) * direction;
}

function shipmentSortValue(record, field) {
  const filenameInfo = record.filename_info || {};
  if (field === "factory_name") return filenameInfo.factory_name || "";
  if (field === "product_name") return record.title_product_name || record.product_name || "";
  if (field === "total_units") return record.total_units ?? record.box_count ?? 0;
  if (field === "is_valid") return record.is_valid ? 1 : 0;
  return record[field] ?? "";
}

function shipmentColumnDisplayValue(record, field) {
  const filenameInfo = record.filename_info || {};
  if (field === "factory_name") return filenameInfo.factory_name || "-";
  if (field === "product_name") return record.title_product_name || record.product_name || "-";
  if (field === "total_units") {
    return record.total_units && record.total_units !== record.box_count
      ? `${record.box_count}箱 / ${record.total_units}个`
      : `${record.box_count}箱`;
  }
  if (field === "is_valid") return record.is_valid ? "通过" : "需复核";
  return String(record[field] || "-");
}

function updateShipmentFilterOptions(records) {
  renderSelectOptions(els.shipmentCountryFilter, uniqueSorted(records.map((record) => record.destination_country)));
  renderSelectOptions(els.shipmentWarehouseFilter, uniqueSorted(records.map((record) => record.warehouse)));
}

function renderSelectOptions(select, values) {
  select.innerHTML = '<option value="all">全部</option>' + values
    .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
    .join("");
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "zh-Hans-CN", {
    numeric: true,
    sensitivity: "base",
  }));
}

function resetShipmentFilters() {
  state.shipmentFilters = {
    query: "",
    status: "all",
    country: "all",
    warehouse: "all",
  };
  state.shipmentColumnFilters = {};
  state.activeColumnMenu = "";
  closeColumnMenu();
  els.shipmentSearchInput.value = "";
  els.shipmentStatusFilter.value = "all";
  els.shipmentCountryFilter.value = "all";
  els.shipmentWarehouseFilter.value = "all";
}

function updateFilterButtonState() {
  const filters = state.shipmentFilters;
  els.clearShipmentFilters.disabled = !filters.query
    && filters.status === "all"
    && filters.country === "all"
    && filters.warehouse === "all"
    && !Object.keys(state.shipmentColumnFilters).length;
}

function renderShipmentFilterSummary(visibleCount = getVisibleShipmentRecords().length) {
  const chips = activeShipmentFilterChips();
  if (!chips.length) {
    els.shipmentFilterSummary.hidden = true;
    els.shipmentFilterSummary.innerHTML = "";
    return;
  }

  els.shipmentFilterSummary.hidden = false;
  els.shipmentFilterSummary.innerHTML = `
    <span>当前显示 ${visibleCount} / ${state.records.length}</span>
    ${chips.map((chip) => `
      <button class="filter-chip" type="button" data-filter-chip="${escapeHtml(chip.key)}">
        ${escapeHtml(chip.label)}
        <span aria-hidden="true">x</span>
      </button>
    `).join("")}
  `;
}

function activeShipmentFilterChips() {
  const filters = state.shipmentFilters;
  const chips = [];
  if (filters.query) chips.push({ key: "query", label: `搜索：${filters.query}` });
  if (filters.status !== "all") chips.push({ key: "status", label: `状态：${filters.status === "valid" ? "通过" : "需复核"}` });
  if (filters.country !== "all") chips.push({ key: "country", label: `国家：${filters.country}` });
  if (filters.warehouse !== "all") chips.push({ key: "warehouse", label: `仓库：${filters.warehouse}` });
  Object.entries(state.shipmentColumnFilters).forEach(([field, value]) => {
    chips.push({ key: `column:${field}`, label: `${shipmentColumnLabels[field] || field}：${value}` });
  });
  return chips;
}

function clearShipmentFilterChip(key) {
  if (key === "query") {
    state.shipmentFilters.query = "";
    els.shipmentSearchInput.value = "";
    return;
  }
  if (key === "status") {
    state.shipmentFilters.status = "all";
    els.shipmentStatusFilter.value = "all";
    return;
  }
  if (key === "country") {
    state.shipmentFilters.country = "all";
    els.shipmentCountryFilter.value = "all";
    return;
  }
  if (key === "warehouse") {
    state.shipmentFilters.warehouse = "all";
    els.shipmentWarehouseFilter.value = "all";
    return;
  }
  if (key.startsWith("column:")) {
    delete state.shipmentColumnFilters[key.replace("column:", "")];
  }
}

function updateSortButtons() {
  els.columnMenuButtons.forEach((button) => {
    const field = button.dataset.columnField;
    const active = field === state.shipmentSort.field;
    const filtered = Boolean(state.shipmentColumnFilters[field]);
    button.classList.toggle("active", active);
    button.classList.toggle("filtered", filtered);
    button.dataset.direction = active ? state.shipmentSort.direction : "";
    button.title = filtered
      ? `${shipmentColumnLabels[field]}：已筛选 ${state.shipmentColumnFilters[field]}`
      : `${shipmentColumnLabels[field]}：排序和筛选`;
  });
}

function toggleColumnMenu(field, button) {
  if (state.shipmentBusy) {
    els.statusText.textContent = "正在处理，完成后会刷新结果";
    return;
  }
  if (!state.records.length) {
    setStatus("请先扫描或上传一批 PDF，再使用列筛选");
    return;
  }
  if (state.activeColumnMenu === field) {
    closeColumnMenu();
    return;
  }
  renderColumnMenu(field, button);
}

function renderColumnMenu(field, button) {
  closeColumnMenu();
  state.activeColumnMenu = field;
  const menu = document.createElement("div");
  menu.className = "column-menu-popover";
  menu.innerHTML = columnMenuMarkup(field);
  document.body.appendChild(menu);
  positionColumnMenu(menu, button);

  menu.querySelector('[data-column-action="sort-asc"]').addEventListener("click", () => {
    applyColumnSort(field, "asc");
  });
  menu.querySelector('[data-column-action="sort-desc"]').addEventListener("click", () => {
    applyColumnSort(field, "desc");
  });
  menu.querySelector('[data-column-action="clear"]').addEventListener("click", () => {
    delete state.shipmentColumnFilters[field];
    closeColumnMenu();
    renderShipmentRecords();
  });
  renderColumnValueList(field, menu, "");
  const searchInput = menu.querySelector("[data-column-value-search]");
  searchInput.addEventListener("input", () => {
    renderColumnValueList(field, menu, searchInput.value);
  });
  searchInput.focus();
}

function columnMenuMarkup(field) {
  const label = shipmentColumnLabels[field] || field;
  const currentFilter = state.shipmentColumnFilters[field] || "";

  return `
    <div class="column-menu-title">${escapeHtml(label)}</div>
    <button class="column-menu-action" type="button" data-column-action="sort-asc">升序排序</button>
    <button class="column-menu-action" type="button" data-column-action="sort-desc">降序排序</button>
    <button class="column-menu-action" type="button" data-column-action="clear" ${currentFilter ? "" : "disabled"}>清除此列筛选</button>
    <div class="column-menu-section">按值筛选</div>
    <input class="column-value-search" type="search" placeholder="输入筛选值" data-column-value-search />
    <div class="column-value-count" data-column-value-count></div>
    <div class="column-value-list" data-column-value-list></div>
  `;
}

function renderColumnValueList(field, menu, query) {
  const currentFilter = state.shipmentColumnFilters[field] || "";
  const normalizedQuery = query.trim().toLowerCase();
  const values = shipmentColumnFilterValues(field).filter((value) => {
    return !normalizedQuery || value.toLowerCase().includes(normalizedQuery);
  });
  const list = menu.querySelector("[data-column-value-list]");
  const counter = menu.querySelector("[data-column-value-count]");
  counter.textContent = normalizedQuery
    ? `匹配 ${values.length} 个值`
    : `共 ${values.length} 个值`;
  list.innerHTML = "";
  if (!values.length) {
    list.innerHTML = '<div class="column-menu-empty">没有匹配的值</div>';
    return;
  }
  values.forEach((value) => {
    const item = document.createElement("button");
    item.className = `column-value ${value === currentFilter ? "selected" : ""}`;
    item.type = "button";
    item.dataset.filterValue = value;
    item.innerHTML = `<span>${escapeHtml(value)}</span>`;
    item.addEventListener("click", () => {
      state.shipmentColumnFilters[field] = value;
      closeColumnMenu();
      renderShipmentRecords();
    });
    list.appendChild(item);
  });
}

function shipmentColumnFilterValues(field) {
  return uniqueSorted(state.records.map((record) => shipmentColumnDisplayValue(record, field)).filter((value) => value && value !== "-"));
}

function applyColumnSort(field, direction) {
  state.shipmentSort = { field, direction };
  closeColumnMenu();
  renderShipmentRecords();
}

function positionColumnMenu(menu, button) {
  const rect = button.getBoundingClientRect();
  const width = 250;
  const left = Math.min(Math.max(12, rect.left), window.innerWidth - width - 12);
  const top = Math.min(rect.bottom + 8, window.innerHeight - 360);
  menu.style.left = `${left}px`;
  menu.style.top = `${Math.max(12, top)}px`;
}

function closeColumnMenu() {
  document.querySelector(".column-menu-popover")?.remove();
  state.activeColumnMenu = "";
}

function startShipmentExport(format) {
  if (!state.batchId) {
    setStatus("请先扫描或上传一批 PDF，再导出");
    return;
  }
  const label = format === "xlsx" ? "Excel 工作簿" : "CSV 文件";
  const url = `/api/export?batch_id=${encodeURIComponent(state.batchId)}&format=${encodeURIComponent(format)}`;
  closeExportMenu();
  setStatus(`正在导出${label}...`);
  startDownload(url, label);
}

function startDownload(url, label) {
  const iframe = document.createElement("iframe");
  iframe.className = "download-frame";
  iframe.src = url;
  document.body.appendChild(iframe);
  window.setTimeout(() => {
    iframe.remove();
    setStatus(`${label}下载已开始`);
  }, 1200);
}

function startNewShipmentTask() {
  clearShipmentResults({ resetInputs: true });
}

function clearShipmentResults({ resetInputs = false } = {}) {
  if (state.shipmentBusy) {
    addShipmentLog("请先终止当前货件任务，再新建或清空", "warning");
    setStatus("请先终止当前任务");
    return;
  }
  if (!resetInputs && !state.records.length) {
    addShipmentLog("当前没有货件处理结果可清空", "warning");
    setStatus("当前没有结果可清空");
    return;
  }
  state.batchId = "";
  state.records = [];
  state.selectedShipmentPaths.clear();
  resetShipmentFilters();
  els.filesMetric.textContent = "0";
  els.boxesMetric.textContent = "0";
  els.boxesMetric.title = "";
  els.validMetric.textContent = "0";
  els.reviewMetric.textContent = "0";
  els.batchLabel.textContent = "尚未扫描批次";
  els.resultBody.innerHTML = '<tr><td class="empty" colspan="13">扫描或上传一批 PDF 后，识别结果会显示在这里。</td></tr>';
  els.packageResult.classList.add("hidden");
  els.packageResult.innerHTML = "";
  disableShipmentOutputs();
  updateShipmentSelectionToolbar([]);
  if (resetInputs) {
    state.pendingShipmentFiles = [];
    state.lastShipmentTask = null;
    els.fileInput.value = "";
    els.folderUploadInput.value = "";
    els.uploadSelectionText.textContent = "支持一批 PDF 文件，也支持把一个文件夹直接拖进来";
  }
  resetShipmentLogs(resetInputs ? "已新建货件 PDF 任务，等待导入" : "已清空当前货件处理结果");
  setStatus("等待导入");
}

function disableShipmentOutputs() {
  els.exportCsv.href = "#";
  els.exportXlsx.href = "#";
  els.exportCsv.classList.add("disabled");
  els.exportXlsx.classList.add("disabled");
  els.exportMenuButton.disabled = true;
  els.packageButton.disabled = true;
  els.renameButton.disabled = true;
  setSoftDisabled(els.clearShipmentResult, true);
  closeExportMenu();
}

function renderReportJob(payload) {
  const { summary } = payload;
  state.reportRows = payload.rows || [];
  resetReportTableFilters();
  els.reportFilesMetric.textContent = summary.files;
  els.reportProcessedMetric.textContent = summary.processed;
  els.reportDetailsMetric.textContent = summary.detail_rows;
  els.reportWarningsMetric.textContent = summary.warnings;
  els.reportBatchLabel.textContent = payload.source_label;
  setReportStatus(`已解析 ${summary.processed} 个 PDF，${summary.warnings} 个需要复核`);

  els.reportDownload.href = payload.download_url;
  els.reportDownload.classList.remove("disabled");
  setSoftDisabled(els.clearReportResult, false);

  renderReportReviewPanel(state.reportRows);
  renderReportRows();
}

function renderTransactionJob(payload) {
  const { summary } = payload;
  state.transactionRows = payload.rows || [];
  const warningCount = (summary.date_parse_failures || 0)
    + (summary.amount_failures || 0)
    + (summary.unresolved_country_files || 0)
    + (summary.unsupported_files || 0);
  els.transactionFilesMetric.textContent = summary.source_files || 0;
  els.transactionRowsMetric.textContent = summary.total_rows || 0;
  els.transactionCountriesMetric.textContent = summary.countries || 0;
  els.transactionWarningsMetric.textContent = warningCount;
  els.transactionBatchLabel.textContent = payload.source_label;
  setTransactionStatus(`已清洗 ${summary.source_files || 0} 个文件，${summary.total_rows || 0} 条明细`);

  els.transactionDownload.href = payload.download_url;
  els.transactionAuditDownload.href = payload.audit_download_url;
  els.transactionDownload.classList.remove("disabled");
  els.transactionAuditDownload.classList.remove("disabled");
  setSoftDisabled(els.clearTransactionResult, false);

  if (!state.transactionRows.length) {
    els.transactionResultBody.innerHTML = '<tr><td class="empty" colspan="8">该文件夹没有可处理的交易明细文件。</td></tr>';
    return;
  }

  els.transactionResultBody.innerHTML = state.transactionRows.map(renderTransactionRow).join("");
}

async function loadHistory() {
  els.historyStatusText.textContent = "正在读取历史任务...";
  const response = await fetch("/api/history");
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    els.historyStatusText.textContent = payload.error || "历史任务读取失败";
    return;
  }
  renderHistory(payload);
}

async function loadSettings() {
  const response = await fetch("/api/settings");
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    renderSettingsError(payload.error || "设置读取失败");
    return;
  }
  renderSettings(payload);
}

function renderRow(record) {
  const statusClass = record.is_valid ? "ok" : "warn";
  const statusText = record.is_valid ? "通过" : "需复核";
  const actionText = record.rename.can_apply ? "可重命名" : record.rename.reason;
  const isForwarderLabel = record.label_type === "forwarder";
  const filenameInfo = record.filename_info || {};
  const productName = filenameInfo.product_name || record.title_product_name || record.product_name || (isForwarderLabel ? "货代标签" : "-");
  const hasShipmentTotal = record.shipment_total_boxes && record.shipment_total_boxes !== record.box_count;
  const boxText = hasShipmentTotal
    ? `${record.box_count}箱 / 大货${record.shipment_total_boxes}箱`
    : record.total_units && record.total_units !== record.box_count
    ? `${record.box_count}箱 / ${record.total_units}个`
    : `${record.box_count}箱`;
  const filenameSummary = [
    filenameInfo.logistics_code ? `物流 ${filenameInfo.logistics_code}` : "",
    filenameInfo.sku ? `SKU ${filenameInfo.sku}` : "",
    filenameInfo.product_name ? `产品 ${filenameInfo.product_name}` : "",
    filenameInfo.country || "",
    filenameInfo.total_units ? `${filenameInfo.total_units}个` : "",
    filenameInfo.box_count ? `${filenameInfo.box_count}箱` : "",
    filenameInfo.warehouse || "",
    filenameInfo.fba_code || "",
  ].filter(Boolean).join(" / ") || "-";
  const warnings = [
    ...(record.notes || []),
    ...(filenameInfo.notes || []),
    ...(record.comparison_notes || []),
  ];

  return `
    <tr>
      <td class="select-col">
        <input type="checkbox" data-shipment-select="${escapeHtml(record.source_path)}" ${state.selectedShipmentPaths.has(record.source_path) ? "checked" : ""} aria-label="选择 ${escapeHtml(record.original_filename)}" />
      </td>
      <td class="filename">${escapeHtml(record.original_filename)}</td>
      <td>${escapeHtml(filenameInfo.factory_name || "-")}</td>
      <td>${escapeHtml(record.sku || "-")}</td>
      <td>${escapeHtml(productName)}</td>
      <td>${escapeHtml(record.destination_country || "-")}</td>
      <td>${escapeHtml(record.warehouse || "-")}</td>
      <td>${escapeHtml(record.fba_code || "-")}</td>
      <td>${escapeHtml(boxText)}</td>
      <td class="filename-check">${escapeHtml(filenameSummary)}</td>
      <td>
        <span class="badge ${statusClass}">${statusText}</span>
        ${warnings.length ? `<ul class="warning-list">${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>` : ""}
      </td>
      <td class="suggested">${escapeHtml(record.suggested_filename)}</td>
      <td>${escapeHtml(actionText)}</td>
    </tr>
  `;
}

function updateActionButtons(records = state.records) {
  const hasBatch = Boolean(state.batchId);
  const hasRecords = records && records.length > 0;
  const hasFactory = hasRecords && records.some((record) => record.filename_info && record.filename_info.factory_name);
  const canRename = hasRecords && records.some((record) => record.rename.can_apply);
  els.packageButton.disabled = !(hasBatch && hasFactory);
  els.renameButton.disabled = !(hasBatch && canRename);
}

function updateShipmentSelectionToolbar(visibleRecords = getVisibleShipmentRecords()) {
  const selectedCount = state.selectedShipmentPaths.size;
  const visibleSelectedCount = visibleRecords.filter((record) => state.selectedShipmentPaths.has(record.source_path)).length;
  els.shipmentSelectionToolbar.hidden = !state.records.length;
  els.shipmentSelectionCount.textContent = `已选 ${selectedCount} 个 PDF`;
  els.downloadSelectedShipments.disabled = selectedCount === 0;
  els.clearShipmentSelection.disabled = selectedCount === 0;
  els.selectVisibleShipments.disabled = !visibleRecords.length;
  els.selectAllVisibleShipments.checked = visibleRecords.length > 0 && visibleSelectedCount === visibleRecords.length;
  els.selectAllVisibleShipments.indeterminate = visibleSelectedCount > 0 && visibleSelectedCount < visibleRecords.length;
}

async function downloadSelectedShipmentPdfs() {
  if (!state.batchId || !state.selectedShipmentPaths.size) {
    setStatus("请先勾选要下载的 PDF");
    return;
  }
  setBusy("正在打包选中的 PDF...");
  const response = await fetch("/api/shipment-selection/package", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      batch_id: state.batchId,
      source_paths: Array.from(state.selectedShipmentPaths),
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    setStatus(payload.error || "选中文件打包失败");
    updateShipmentSelectionToolbar();
    return;
  }
  startDownload(payload.package.download_url, "选中 PDF 压缩包");
  setStatus(`已打包 ${payload.package.file_count} 个选中 PDF，下载已开始`);
  updateShipmentSelectionToolbar();
}

function renderPackageResult(payload) {
  const packages = payload.packages || [];
  const skipped = payload.skipped || [];
  const bundle = payload.bundle || {};
  const totalFiles = packages.reduce((sum, item) => sum + (item.file_count || 0), 0);
  const packageLinks = packages.length
    ? packages.map((item) => `
        <a class="package-download" href="${escapeHtml(item.download_url)}" download>
          <strong>${escapeHtml(item.factory_name)} 压缩包</strong>
          <span>${escapeHtml(item.file_count)} 个 PDF</span>
        </a>
      `).join("")
    : '<span class="package-empty">没有生成压缩包</span>';
  const skippedText = skipped.length
    ? `
      <div class="package-warning">
        <strong>未打包文件</strong>
        <p>${escapeHtml(skipped.map((item) => `${item.filename}：${item.reason}`).join("；"))}</p>
      </div>
    `
    : "";
  els.packageResult.innerHTML = `
    <div class="package-result-main">
      <div class="package-result-heading">
        <span class="badge ok">打包完成</span>
        <strong>已按工厂生成 ${escapeHtml(packages.length)} 个压缩包</strong>
      </div>
      <p>${escapeHtml(totalFiles)} 个 PDF 已归档。可以直接点击下方按钮下载，也可以在服务器保存位置中查找。</p>
      ${bundle.download_url ? `
        <a class="package-download package-download-all" href="${escapeHtml(bundle.download_url)}" download>
          <strong>下载全部压缩包</strong>
          <span>${escapeHtml(bundle.package_count || packages.length)} 个工厂压缩包</span>
        </a>
      ` : ""}
      <dl class="package-path">
        <dt>服务器保存位置</dt>
        <dd>${escapeHtml(payload.package_root || "")}</dd>
      </dl>
      <button class="button secondary compact package-copy-button" type="button" data-copy-package-path="${escapeHtml(payload.package_root || "")}">
        复制保存路径
      </button>
    </div>
    <div class="package-downloads">${packageLinks}</div>
    ${skippedText}
  `;
  els.packageResult.classList.remove("hidden");
}

function renderReportRows() {
  updateReportSortButtons();
  updateReportFilterButtonState();
  const rows = getVisibleReportRows();
  renderReportFilterSummary(rows.length);
  if (!state.reportRows.length) {
    els.reportResultBody.innerHTML = '<tr><td class="empty" colspan="7">该文件夹没有可处理的汇总报告 PDF。</td></tr>';
    return;
  }
  if (!rows.length) {
    els.reportResultBody.innerHTML = '<tr><td class="empty" colspan="7">当前筛选下没有记录。</td></tr>';
    return;
  }
  els.reportResultBody.innerHTML = rows.map(renderReportRow).join("");
}

function getVisibleReportRows() {
  const normalizedQuery = state.reportFilters.query.toLowerCase();
  return [...state.reportRows]
    .filter((row) => {
      if (state.reportReviewFilter === "review" && row.status === "通过") return false;
      if (state.reportReviewFilter === "ok" && row.status !== "通过") return false;
      if (!matchesReportColumnFilters(row)) return false;
      if (!normalizedQuery) return true;
      return reportSearchText(row).toLowerCase().includes(normalizedQuery);
    })
    .sort(compareReportRows);
}

function matchesReportColumnFilters(row) {
  return Object.entries(state.reportColumnFilters).every(([field, expected]) => {
    return reportColumnDisplayValue(row, field) === expected;
  });
}

function reportSearchText(row) {
  return [
    ...Object.keys(reportColumnLabels).map((field) => reportColumnDisplayValue(row, field)),
    row.country,
    row.country_code,
    row.currency,
    row.filename_store,
    row.display_name,
    row.store_source,
    row.country_source,
    row.pdf_country_code,
    row.period,
    row.notes,
  ].filter(Boolean).join(" ");
}

function compareReportRows(left, right) {
  const field = state.reportSort.field;
  const direction = state.reportSort.direction === "desc" ? -1 : 1;
  const leftValue = reportColumnSortValue(left, field);
  const rightValue = reportColumnSortValue(right, field);
  if (typeof leftValue === "number" && typeof rightValue === "number") {
    return (leftValue - rightValue) * direction;
  }
  return String(leftValue || "").localeCompare(String(rightValue || ""), "zh-Hans-CN", {
    numeric: true,
    sensitivity: "base",
  }) * direction;
}

function reportColumnSortValue(row, field) {
  if (field === "period") return Number(row.year || 0) * 100 + Number(row.month || 0);
  if (field === "scale") {
    return Number(row.summary_count || 0) + Number(row.detail_count || 0) + Number(row.check_count || 0);
  }
  return reportColumnDisplayValue(row, field);
}

function reportColumnDisplayValue(row, field) {
  if (field === "source_file") return row.source_file || "-";
  if (field === "store") return row.store || "-";
  if (field === "site") return [row.country || row.country_code || "-", row.currency].filter(Boolean).join(" / ");
  if (field === "period") return row.year && row.month ? `${row.year}-${String(row.month).padStart(2, "0")}` : (row.period || "-");
  if (field === "scale") {
    return [
      `摘要 ${row.summary_count || 0}`,
      `明细 ${row.detail_count || 0}`,
      `核验 ${row.check_count || 0}`,
    ].join(" / ");
  }
  if (field === "status") return row.status || "需复核";
  if (field === "notes") return row.status === "通过" ? "无需人工介入" : (row.notes || "请人工核对该文件");
  return String(row[field] || "-");
}

function resetReportTableFilters() {
  state.reportReviewFilter = "all";
  state.reportFilters = { query: "" };
  state.reportSort = { field: "source_file", direction: "asc" };
  state.reportColumnFilters = {};
  state.activeReportColumnMenu = "";
  closeReportColumnMenu();
  els.reportSearchInput.value = "";
}

function updateReportSortButtons() {
  els.reportColumnMenuButtons.forEach((button) => {
    const field = button.dataset.reportColumnField;
    const active = field === state.reportSort.field;
    const filtered = Boolean(state.reportColumnFilters[field]);
    button.classList.toggle("active", active);
    button.classList.toggle("filtered", filtered);
    button.dataset.direction = active ? state.reportSort.direction : "";
    button.title = filtered
      ? `${reportColumnLabels[field]}：已筛选 ${state.reportColumnFilters[field]}`
      : `${reportColumnLabels[field]}：排序和筛选`;
  });
}

function updateReportFilterButtonState() {
  els.clearReportFilters.disabled = !state.reportFilters.query
    && state.reportReviewFilter === "all"
    && !Object.keys(state.reportColumnFilters).length;
}

function renderReportFilterSummary(visibleCount = getVisibleReportRows().length) {
  const chips = activeReportFilterChips();
  if (!chips.length) {
    els.reportFilterSummary.hidden = true;
    els.reportFilterSummary.innerHTML = "";
    return;
  }

  els.reportFilterSummary.hidden = false;
  els.reportFilterSummary.innerHTML = `
    <span>当前显示 ${visibleCount} / ${state.reportRows.length}</span>
    ${chips.map((chip) => `
      <button class="filter-chip" type="button" data-report-filter-chip="${escapeHtml(chip.key)}">
        ${escapeHtml(chip.label)}
        <span aria-hidden="true">x</span>
      </button>
    `).join("")}
  `;
}

function activeReportFilterChips() {
  const chips = [];
  if (state.reportFilters.query) chips.push({ key: "query", label: `搜索：${state.reportFilters.query}` });
  if (state.reportReviewFilter !== "all") {
    chips.push({ key: "review", label: `队列：${state.reportReviewFilter === "review" ? "只看需复核" : "通过"}` });
  }
  Object.entries(state.reportColumnFilters).forEach(([field, value]) => {
    chips.push({ key: `column:${field}`, label: `${reportColumnLabels[field] || field}：${value}` });
  });
  return chips;
}

function clearReportFilterChip(key) {
  if (key === "query") {
    state.reportFilters.query = "";
    els.reportSearchInput.value = "";
    return;
  }
  if (key === "review") {
    state.reportReviewFilter = "all";
    return;
  }
  if (key.startsWith("column:")) {
    delete state.reportColumnFilters[key.replace("column:", "")];
  }
}

function toggleReportColumnMenu(field, button) {
  if (state.reportBusy) {
    els.reportStatusText.textContent = "正在处理，完成后会刷新结果";
    return;
  }
  if (!state.reportRows.length) {
    setReportStatus("请先处理一批汇总报告 PDF，再使用列筛选");
    return;
  }
  if (state.activeReportColumnMenu === field) {
    closeReportColumnMenu();
    return;
  }
  renderReportColumnMenu(field, button);
}

function renderReportColumnMenu(field, button) {
  closeColumnMenu();
  closeReportColumnMenu();
  state.activeReportColumnMenu = field;
  const menu = document.createElement("div");
  menu.className = "column-menu-popover";
  menu.innerHTML = reportColumnMenuMarkup(field);
  document.body.appendChild(menu);
  positionColumnMenu(menu, button);

  menu.querySelector('[data-column-action="sort-asc"]').addEventListener("click", () => {
    applyReportColumnSort(field, "asc");
  });
  menu.querySelector('[data-column-action="sort-desc"]').addEventListener("click", () => {
    applyReportColumnSort(field, "desc");
  });
  menu.querySelector('[data-column-action="clear"]').addEventListener("click", () => {
    delete state.reportColumnFilters[field];
    closeReportColumnMenu();
    renderReportRows();
    renderReportReviewPanel(state.reportRows);
  });
  renderReportColumnValueList(field, menu, "");
  const searchInput = menu.querySelector("[data-column-value-search]");
  searchInput.addEventListener("input", () => {
    renderReportColumnValueList(field, menu, searchInput.value);
  });
  searchInput.focus();
}

function reportColumnMenuMarkup(field) {
  const label = reportColumnLabels[field] || field;
  const currentFilter = state.reportColumnFilters[field] || "";

  return `
    <div class="column-menu-title">${escapeHtml(label)}</div>
    <button class="column-menu-action" type="button" data-column-action="sort-asc">升序排序</button>
    <button class="column-menu-action" type="button" data-column-action="sort-desc">降序排序</button>
    <button class="column-menu-action" type="button" data-column-action="clear" ${currentFilter ? "" : "disabled"}>清除此列筛选</button>
    <div class="column-menu-section">按值筛选</div>
    <input class="column-value-search" type="search" placeholder="输入筛选值" data-column-value-search />
    <div class="column-value-count" data-column-value-count></div>
    <div class="column-value-list" data-column-value-list></div>
  `;
}

function renderReportColumnValueList(field, menu, query) {
  const currentFilter = state.reportColumnFilters[field] || "";
  const normalizedQuery = query.trim().toLowerCase();
  const values = reportColumnFilterValues(field).filter((value) => {
    return !normalizedQuery || value.toLowerCase().includes(normalizedQuery);
  });
  const list = menu.querySelector("[data-column-value-list]");
  const counter = menu.querySelector("[data-column-value-count]");
  counter.textContent = normalizedQuery
    ? `匹配 ${values.length} 个值`
    : `共 ${values.length} 个值`;
  list.innerHTML = "";
  if (!values.length) {
    list.innerHTML = '<div class="column-menu-empty">没有匹配的值</div>';
    return;
  }
  values.forEach((value) => {
    const item = document.createElement("button");
    item.className = `column-value ${value === currentFilter ? "selected" : ""}`;
    item.type = "button";
    item.dataset.filterValue = value;
    item.innerHTML = `<span>${escapeHtml(value)}</span>`;
    item.addEventListener("click", () => {
      state.reportColumnFilters[field] = value;
      closeReportColumnMenu();
      renderReportRows();
      renderReportReviewPanel(state.reportRows);
    });
    list.appendChild(item);
  });
}

function reportColumnFilterValues(field) {
  return uniqueSorted(state.reportRows.map((row) => reportColumnDisplayValue(row, field)).filter((value) => value && value !== "-"));
}

function applyReportColumnSort(field, direction) {
  state.reportSort = { field, direction };
  closeReportColumnMenu();
  renderReportRows();
}

function closeReportColumnMenu() {
  document.querySelector(".column-menu-popover")?.remove();
  state.activeReportColumnMenu = "";
}

function renderReportReviewPanel(rows) {
  if (!rows.length) {
    els.reportReviewPanel.classList.add("hidden");
    els.reportReviewPanel.innerHTML = "";
    return;
  }
  const reviewRows = rows.filter((row) => row.status !== "通过");
  const okRows = rows.length - reviewRows.length;
  const reasonCounts = reportReviewReasonCounts(reviewRows);
  const reasonText = reasonCounts.length
    ? reasonCounts.map((item) => `${item.label} ${item.count}`).join(" / ")
    : "暂无需人工介入项";
  els.reportReviewPanel.classList.remove("hidden");
  els.reportReviewPanel.innerHTML = `
    <div class="review-workbench-main">
      <span class="section-label">复核队列</span>
      <strong>${escapeHtml(reviewRows.length)} 个文件需要人工介入</strong>
      <p>${escapeHtml(reasonText)}</p>
    </div>
    <div class="review-workbench-actions">
      <button class="button secondary compact ${state.reportReviewFilter === "all" ? "active" : ""}" type="button" data-report-filter="all">全部 ${escapeHtml(rows.length)}</button>
      <button class="button secondary compact ${state.reportReviewFilter === "review" ? "active" : ""}" type="button" data-report-filter="review">只看需复核 ${escapeHtml(reviewRows.length)}</button>
      <button class="button secondary compact ${state.reportReviewFilter === "ok" ? "active" : ""}" type="button" data-report-filter="ok">通过 ${escapeHtml(okRows)}</button>
    </div>
  `;
}

function reportReviewReasonCounts(rows) {
  const reasons = [
    { label: "解析失败", match: (row) => row.status === "解析失败" },
    { label: "核验异常", match: (row) => String(row.status).includes("核验异常") },
    { label: "文件名需复核", match: (row) => String(row.status).includes("文件名需复核") },
    { label: "疑似重复报告期", match: (row) => String(row.status).includes("疑似重复报告期") },
  ];
  return reasons
    .map((reason) => ({ label: reason.label, count: rows.filter(reason.match).length }))
    .filter((reason) => reason.count > 0);
}

function renderReportRow(row) {
  const statusClass = row.status === "通过" ? "ok" : "warn";
  const period = row.year && row.month ? `${row.year}-${String(row.month).padStart(2, "0")}` : (row.period || "-");
  const site = [row.country || row.country_code || "-", row.currency].filter(Boolean).join(" / ");
  const scale = [
    `摘要 ${row.summary_count || 0}`,
    `明细 ${row.detail_count || 0}`,
    `核验 ${row.check_count || 0}`,
  ].join(" / ");
  const notes = row.status === "通过" ? "无需人工介入" : (row.notes || "请人工核对该文件");
  const storeSource = row.store_source === "pdf_display_name"
    ? `PDF Display name${row.filename_store && row.filename_store !== row.store ? `；文件名/目录为 ${row.filename_store}` : ""}`
    : "来自文件名或文件夹推断";
  const countrySource = row.pdf_country_code
    ? `PDF 货币/时区交叉核验：${row.pdf_country_code}`
    : "文件名/目录，PDF 无唯一国家线索";

  return `
    <tr>
      <td class="filename">${escapeHtml(row.source_file || "-")}</td>
      <td>
        <strong>${escapeHtml(row.store || "-")}</strong>
        <span class="cell-subtle">${escapeHtml(storeSource)}</span>
      </td>
      <td>
        ${escapeHtml(site)}
        <span class="cell-subtle">${escapeHtml(countrySource)}</span>
      </td>
      <td>${escapeHtml(period)}</td>
      <td>${escapeHtml(scale)}</td>
      <td><span class="badge ${statusClass}">${escapeHtml(row.status || "需复核")}</span></td>
      <td class="suggested">${escapeHtml(notes)}</td>
    </tr>
  `;
}

function renderTransactionRow(row) {
  const statusClass = row.status === "通过" ? "ok" : "warn";
  const rowCounts = `${row.source_rows || 0} / ${row.parsed_rows || 0}`;
  const dateRange = [row.date_min, row.date_max].filter(Boolean).join(" 至 ") || "-";
  return `
    <tr>
      <td class="filename">${escapeHtml(row.source_file || "-")}</td>
      <td>${escapeHtml(row.brand || "-")}</td>
      <td>${escapeHtml(row.country || "-")}</td>
      <td>${escapeHtml(row.currency || "-")}</td>
      <td>${escapeHtml(rowCounts)}</td>
      <td>${escapeHtml(dateRange)}</td>
      <td><span class="badge ${statusClass}">${escapeHtml(row.status || "需复核")}</span></td>
      <td class="suggested">${escapeHtml(row.notes || "-")}</td>
    </tr>
  `;
}

function renderHistory(payload) {
  const { summary, tasks } = payload;
  state.historyTasks = tasks || [];
  pruneHistorySelection();
  els.historyTotalMetric.textContent = summary.total;
  els.historyShipmentMetric.textContent = summary.shipment_pdf;
  els.historyReportMetric.textContent = summary.report_pdf;
  els.historyTransactionMetric.textContent = summary.transaction_csv || 0;
  els.historyReviewMetric.textContent = summary.needs_review;
  els.historyStatusText.textContent = summary.total
    ? `已记录 ${summary.total} 个任务`
    : "记录当前服务运行期间的处理任务";
  els.cleanupHistoryButton.hidden = !(state.currentUser && state.currentUser.role === "admin");
  renderHistoryList();
}

function renderHistoryList() {
  const tasks = getVisibleHistoryTasks();
  els.historyTypeFilter.value = state.historyFilter;
  els.clearHistoryFilter.disabled = state.historyFilter === "all";

  if (!tasks.length) {
    els.historyResultBody.innerHTML = '<tr><td class="empty" colspan="8">当前筛选下没有历史任务。</td></tr>';
    els.historyDetailPanel.innerHTML = "";
    closeHistoryDetail();
    updateHistorySelectionToolbar();
    return;
  }

  els.historyResultBody.innerHTML = tasks.map(renderHistoryRow).join("");
  updateHistorySelectionToolbar(tasks);
  const activeTask = tasks.find((task) => task.id === state.activeHistoryTaskId);
  if (!activeTask) {
    closeHistoryDetail();
  }
}

function getVisibleHistoryTasks() {
  if (state.historyFilter === "all") return state.historyTasks;
  return state.historyTasks.filter((task) => task.type === state.historyFilter);
}

function pruneHistorySelection() {
  const ids = new Set(state.historyTasks.map((task) => task.id));
  [...state.selectedHistoryTaskIds].forEach((taskId) => {
    if (!ids.has(taskId)) state.selectedHistoryTaskIds.delete(taskId);
  });
}

function updateHistorySelectionToolbar(visibleTasks = getVisibleHistoryTasks()) {
  const selectedCount = state.selectedHistoryTaskIds.size;
  const visibleSelectedCount = visibleTasks.filter((task) => state.selectedHistoryTaskIds.has(task.id)).length;
  els.historySelectionToolbar.hidden = !state.historyTasks.length;
  els.historySelectionCount.textContent = `已选 ${selectedCount} 条记录`;
  els.deleteSelectedHistory.disabled = selectedCount === 0;
  els.clearHistorySelection.disabled = selectedCount === 0;
  els.selectVisibleHistory.disabled = !visibleTasks.length;
  els.selectAllHistory.disabled = !state.historyTasks.length;
  els.selectAllVisibleHistory.checked = visibleTasks.length > 0 && visibleSelectedCount === visibleTasks.length;
  els.selectAllVisibleHistory.indeterminate = visibleSelectedCount > 0 && visibleSelectedCount < visibleTasks.length;
}

function renderHistoryRow(task) {
  const statusClass = task.status === "完成" ? "ok" : "warn";
  const summary = historySummaryText(task);
  const activeClass = task.id === state.activeHistoryTaskId ? " active-row" : "";

  return `
    <tr class="${activeClass}">
      <td class="select-col">
        <input type="checkbox" data-history-select="${escapeHtml(task.id)}" ${state.selectedHistoryTaskIds.has(task.id) ? "checked" : ""} aria-label="选择 ${escapeHtml(task.title)}" />
      </td>
      <td class="mono-cell">${escapeHtml(task.created_at)}</td>
      <td>${escapeHtml(task.title)}</td>
      <td>${escapeHtml(task.owner_name || task.owner_username || "-")}</td>
      <td class="filename">${escapeHtml(task.source_label)}</td>
      <td>${escapeHtml(summary)}</td>
      <td><span class="badge ${statusClass}">${escapeHtml(task.status)}</span></td>
      <td class="history-actions">
        <button class="button secondary compact" type="button" data-history-detail="${escapeHtml(task.id)}">查看详情</button>
        <button class="button secondary compact danger" type="button" data-history-delete="${escapeHtml(task.id)}">删除</button>
      </td>
    </tr>
  `;
}

function renderHistoryDetail(task) {
  if (!task) return;
  const statusClass = task.status === "完成" ? "ok" : "warn";
  const downloads = renderHistoryDownloads(task.downloads || []);
  const summaryItems = historySummaryItems(task.summary || {});
  els.historyDetailPanel.innerHTML = `
    <div class="history-detail-main">
      <div class="package-result-heading">
        <span class="badge ${statusClass}">${escapeHtml(task.status)}</span>
        <strong id="historyDetailTitle">${escapeHtml(task.title)} 详情</strong>
      </div>
      <dl class="history-detail-meta">
        <dt>任务时间</dt><dd>${escapeHtml(task.created_at)}</dd>
        <dt>创建人</dt><dd>${escapeHtml(task.owner_name || task.owner_username || "-")}</dd>
        <dt>来源</dt><dd>${escapeHtml(task.source_label || "-")}</dd>
        <dt>任务 ID</dt><dd>${escapeHtml(task.id)}</dd>
      </dl>
      <div class="history-summary-list">
        ${summaryItems.map((item) => `<span>${escapeHtml(item.label)}：${escapeHtml(item.value)}</span>`).join("")}
      </div>
    </div>
    ${downloads}
  `;
  els.historyDetailModal.classList.remove("hidden");
  els.historyResultBody.innerHTML = getVisibleHistoryTasks().map(renderHistoryRow).join("");
}

function closeHistoryDetail() {
  els.historyDetailModal.classList.add("hidden");
  els.historyDetailPanel.innerHTML = "";
}

function renderHistoryDownloads(downloads) {
  if (!downloads.length) {
    return '<div class="history-download-panel"><span class="package-empty">该任务暂无可重新下载的交付物。</span></div>';
  }
  const allFactory = downloads.find((item) => item.label === "全部工厂压缩包");
  const factoryPackages = downloads.filter((item) => item.label.endsWith("压缩包") && item.label !== "全部工厂压缩包");
  const reportFiles = downloads.filter((item) => !item.label.endsWith("压缩包"));

  return `
    <div class="history-download-panel">
      <div class="history-download-header">
        <strong>交付物</strong>
        <span>${escapeHtml(downloads.length)} 个可下载文件</span>
      </div>
      ${allFactory ? renderDownloadCard(allFactory, "primary", "批量下载") : ""}
      ${reportFiles.length ? `
        <div class="history-download-group">
          <span>结果表</span>
          <div class="history-download-list">
            ${reportFiles.map((item) => renderDownloadCard(item, "secondary", "重新下载")).join("")}
          </div>
        </div>
      ` : ""}
      ${factoryPackages.length ? `
        <details class="history-download-details">
          <summary>
            <span>单个工厂压缩包</span>
            <span class="history-download-summary-action">
              <span class="history-download-count">${escapeHtml(factoryPackages.length)} 个</span>
              <span class="history-download-toggle-text" data-open-label="收起">展开查看</span>
            </span>
          </summary>
          <div class="history-download-list compact">
            ${factoryPackages.map((item) => renderDownloadCard(item, "secondary", "重新下载")).join("")}
          </div>
        </details>
      ` : ""}
    </div>
  `;
}

function renderDownloadCard(download, variant, actionLabel) {
  return `
    <a class="history-download-card ${variant}" href="${escapeHtml(download.url)}" download>
      <strong>${escapeHtml(download.label)}</strong>
      <span>${escapeHtml(actionLabel)}</span>
    </a>
  `;
}

function historySummaryItems(summary) {
  const labels = {
    files: "PDF 文件",
    boxes: "箱标页数",
    label_pages: "箱标页数",
    valid: "通过",
    needs_review: "需复核",
    processed: "已处理",
    warnings: "告警",
    detail_rows: "明细行",
    source_files: "源文件",
    total_rows: "总行数",
    countries: "国家数",
  };
  return Object.entries(summary)
    .filter(([key, value]) => {
      if (key === "boxes" && summary.label_pages !== undefined) return false;
      return labels[key] && value !== undefined && value !== null && value !== "";
    })
    .map(([key, value]) => ({ label: labels[key], value: typeof value === "object" ? JSON.stringify(value) : value }));
}

function historySummaryText(task) {
  const summary = task.summary || {};
  if (task.type === "shipment_pdf") {
    return `${summary.files || 0} 个PDF / ${summary.label_pages || summary.boxes || 0} 张箱标 / ${summary.needs_review || 0} 个复核`;
  }
  if (task.type === "report_pdf") {
    return `${summary.processed || 0} 个PDF / ${summary.detail_rows || 0} 条明细 / ${summary.warnings || 0} 个复核`;
  }
  if (task.type === "transaction_csv") {
    return `${summary.source_files || 0} 个文件 / ${summary.total_rows || 0} 条明细 / ${summary.countries || 0} 个国家`;
  }
  return "-";
}

async function deleteHistoryTask(taskId) {
  const task = state.historyTasks.find((item) => item.id === taskId);
  if (!task) return;
  const ok = window.confirm(`确认删除这条历史任务？\n\n${task.title}\n${task.created_at}\n\n系统会同时清理该任务生成的导出文件。`);
  if (!ok) return;
  els.historyStatusText.textContent = "正在删除历史任务...";
  const response = await fetch(`/api/history/${encodeURIComponent(taskId)}`, { method: "DELETE" });
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    els.historyStatusText.textContent = payload.error || "删除失败";
    return;
  }
  if (state.activeHistoryTaskId === taskId) {
    state.activeHistoryTaskId = "";
    closeHistoryDetail();
  }
  state.selectedHistoryTaskIds.delete(taskId);
  els.historyStatusText.textContent = `已删除 1 条历史任务，清理 ${payload.removed_files || 0} 个生成文件`;
  await loadHistory();
}

async function deleteSelectedHistoryTasks() {
  const taskIds = Array.from(state.selectedHistoryTaskIds);
  if (!taskIds.length) return;
  const ok = window.confirm(`确认批量删除 ${taskIds.length} 条历史任务？系统会同时清理这些任务生成的导出文件。`);
  if (!ok) return;
  els.historyStatusText.textContent = "正在批量删除历史任务...";
  const response = await fetch("/api/history/batch-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_ids: taskIds }),
  });
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    els.historyStatusText.textContent = payload.error || "批量删除失败";
    return;
  }
  if (state.selectedHistoryTaskIds.has(state.activeHistoryTaskId)) {
    state.activeHistoryTaskId = "";
    closeHistoryDetail();
  }
  state.selectedHistoryTaskIds.clear();
  els.historyStatusText.textContent = `已删除 ${payload.deleted || 0} 条历史任务，清理 ${payload.removed_files || 0} 个生成文件`;
  await loadHistory();
}

async function cleanupHistory() {
  if (!(state.currentUser && state.currentUser.role === "admin")) return;
  const raw = window.prompt("清理多少天以前的历史记录？", "30");
  if (raw === null) return;
  const days = Number.parseInt(raw, 10);
  if (!Number.isFinite(days) || days < 1) {
    els.historyStatusText.textContent = "请输入大于 0 的保留天数";
    return;
  }
  const ok = window.confirm(`确认清理 ${days} 天以前的历史任务？系统会同时清理对应生成文件。`);
  if (!ok) return;
  els.historyStatusText.textContent = "正在清理旧历史记录...";
  const response = await fetch("/api/history/cleanup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ days }),
  });
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    els.historyStatusText.textContent = payload.error || "清理失败";
    return;
  }
  state.activeHistoryTaskId = "";
  closeHistoryDetail();
  els.historyStatusText.textContent = `已清理 ${payload.deleted || 0} 条历史任务，清理 ${payload.removed_files || 0} 个生成文件`;
  await loadHistory();
}

function renderSettings(payload) {
  state.currentUser = payload.current_user || state.currentUser;
  if (state.currentUser) {
    els.userBadge.textContent = `${state.currentUser.display_name} · ${roleLabel(state.currentUser.role)}`;
  }
  els.serviceSettingsList.innerHTML = renderDefinitionList({
    "服务名称": payload.service.name,
    "访问地址": payload.service.address,
    "状态": payload.service.status,
  });
  els.pathSettingsList.innerHTML = renderDefinitionList({
    "项目目录": payload.paths.project_root,
    "导出目录": payload.paths.output_root,
    "上传目录": payload.paths.upload_root,
    "允许扫描": payload.paths.allowed_input_roots.join("；"),
  });
  els.processingSettingsList.innerHTML = payload.processing.map((item) => `
    <div class="settings-row">
      <strong>${escapeHtml(item.name)}</strong>
      <span>${escapeHtml(item.engine)}</span>
      <em>LLM：${escapeHtml(item.llm)}</em>
    </div>
  `).join("");
  els.deploymentSettingsList.innerHTML = payload.deployment_notes.map((note) => `
    <p>${escapeHtml(note)}</p>
  `).join("");
  const canManageUsers = Boolean(payload.permissions && payload.permissions.can_manage_users);
  els.userManagementPanel.classList.toggle("hidden", !canManageUsers);
  if (canManageUsers) {
    loadUsers();
  }
}

function renderSettingsError(message) {
  els.serviceSettingsList.innerHTML = `<dt>状态</dt><dd>${escapeHtml(message)}</dd>`;
  els.pathSettingsList.innerHTML = "";
  els.processingSettingsList.innerHTML = "";
  els.deploymentSettingsList.innerHTML = "";
}

function renderDefinitionList(items) {
  return Object.entries(items)
    .map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value || "-")}</dd>`)
    .join("");
}

async function loadUsers() {
  els.userStatusText.textContent = "正在读取用户...";
  const response = await fetch("/api/users");
  const payload = await response.json();
  if (response.status === 401) {
    showLoggedOut();
    return;
  }
  if (!response.ok) {
    els.userStatusText.textContent = payload.error || "用户读取失败";
    return;
  }
  els.userStatusText.textContent = `已加载 ${payload.users.length} 个用户`;
  renderUsers(payload.users);
}

async function createUser() {
  els.userStatusText.textContent = "正在新增用户...";
  const response = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: els.newUsername.value,
      display_name: els.newDisplayName.value,
      password: els.newPassword.value,
      role: els.newRole.value,
      active: true,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    els.userStatusText.textContent = payload.error || "新增失败";
    return;
  }
  els.userForm.reset();
  els.newRole.value = "operator";
  els.userStatusText.textContent = `已新增用户 ${payload.user.username}`;
  await loadUsers();
}

function renderUsers(users) {
  if (!users.length) {
    els.userTableBody.innerHTML = '<tr><td class="empty" colspan="5">暂无用户。</td></tr>';
    return;
  }
  els.userTableBody.innerHTML = users.map(renderUserRow).join("");
  els.userTableBody.querySelectorAll("[data-user-action]").forEach((button) => {
    button.addEventListener("click", () => handleUserAction(button.dataset));
  });
}

function renderUserRow(user) {
  const statusClass = user.active ? "ok" : "warn";
  const nextRole = user.role === "admin" ? "operator" : "admin";
  const nextActive = user.active ? "停用" : "启用";
  const self = state.currentUser && state.currentUser.id === user.id;
  return `
    <tr>
      <td>
        <strong>${escapeHtml(user.display_name)}</strong>
        <div class="mono-cell">${escapeHtml(user.username)}</div>
      </td>
      <td>${escapeHtml(roleLabel(user.role))}</td>
      <td><span class="badge ${statusClass}">${user.active ? "启用" : "停用"}</span></td>
      <td class="mono-cell">${escapeHtml(user.created_at || "-")}</td>
      <td>
        <div class="row-actions">
          <button class="small-button" type="button" data-user-action="role" data-user-id="${escapeHtml(user.id)}" data-role="${nextRole}" ${self ? "disabled" : ""}>设为${escapeHtml(roleLabel(nextRole))}</button>
          <button class="small-button" type="button" data-user-action="active" data-user-id="${escapeHtml(user.id)}" data-active="${String(!user.active)}" ${self ? "disabled" : ""}>${nextActive}</button>
          <button class="small-button" type="button" data-user-action="password" data-user-id="${escapeHtml(user.id)}">重置密码</button>
          <button class="small-button" type="button" data-user-action="delete" data-user-id="${escapeHtml(user.id)}" ${self ? "disabled" : ""}>删除</button>
        </div>
      </td>
    </tr>
  `;
}

async function handleUserAction(dataset) {
  const userId = dataset.userId;
  if (dataset.userAction === "role") {
    await updateUser(userId, { role: dataset.role });
    return;
  }
  if (dataset.userAction === "active") {
    await updateUser(userId, { active: dataset.active === "true" });
    return;
  }
  if (dataset.userAction === "password") {
    const password = window.prompt("请输入新密码（至少 6 位）");
    if (!password) return;
    await updateUser(userId, { password });
    return;
  }
  if (dataset.userAction === "delete") {
    if (!window.confirm("确认删除这个用户？")) return;
    await deleteUser(userId);
  }
}

async function updateUser(userId, payload) {
  const response = await fetch(`/api/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  els.userStatusText.textContent = response.ok ? "用户已更新" : (result.error || "更新失败");
  if (response.ok) {
    await loadUsers();
  }
}

async function deleteUser(userId) {
  const response = await fetch(`/api/users/${encodeURIComponent(userId)}`, { method: "DELETE" });
  const result = await response.json();
  els.userStatusText.textContent = response.ok ? "用户已删除" : (result.error || "删除失败");
  if (response.ok) {
    await loadUsers();
  }
}

function setActiveView(view) {
  state.activeView = ["shipment", "report", "transaction", "history", "settings"].includes(view) ? view : "shipment";
  els.navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.view === state.activeView);
  });
  els.viewPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.viewPanel !== state.activeView);
  });
  els.inspectorPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.inspectorPanel !== state.activeView);
  });
  const isShipment = state.activeView === "shipment";
  els.exportMenu.classList.toggle("hidden", !isShipment);
  if (!isShipment) {
    closeExportMenu();
  }
  if (state.activeView === "history") {
    loadHistory();
  }
  if (state.activeView === "settings") {
    loadSettings();
  }
}

function viewFromHash() {
  if (window.location.hash.includes("report")) return "report";
  if (window.location.hash.includes("transaction")) return "transaction";
  if (window.location.hash.includes("history")) return "history";
  if (window.location.hash.includes("settings")) return "settings";
  return "shipment";
}

function setBusy(message) {
  state.shipmentBusy = true;
  els.statusText.textContent = message;
  updateBusyControls();
}

function setStatus(message) {
  state.shipmentBusy = false;
  els.statusText.textContent = message;
  updateBusyControls();
}

async function copyTextToClipboard(text, successMessage) {
  if (!text) {
    setStatus("没有可复制的路径");
    return;
  }
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const input = document.createElement("textarea");
      input.value = text;
      input.setAttribute("readonly", "");
      input.style.position = "fixed";
      input.style.left = "-9999px";
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      input.remove();
    }
    setStatus(successMessage);
  } catch (error) {
    setStatus("复制失败，请手动选中保存路径复制");
  }
}

function updateBusyControls() {
  const busy = state.shipmentBusy;
  els.folderScanButton.disabled = busy;
  els.uploadSubmitButton.disabled = busy;
  setSoftDisabled(els.newShipmentTask, busy);
  setSoftDisabled(els.cancelShipmentTask, !busy || !state.shipmentAbortController);
  setSoftDisabled(els.retryShipmentTask, busy || !state.lastShipmentTask);
  setSoftDisabled(els.clearShipmentResult, busy || !state.records.length);
  els.uploadPickers.forEach((button) => {
    button.disabled = busy;
  });
  els.dropTarget.classList.toggle("disabled", busy);
  els.folderScanButton.textContent = busy ? "处理中..." : "扫描文件夹";
  els.uploadSubmitButton.textContent = busy ? "处理中..." : "上传并识别";
  els.cancelShipmentTask.textContent = busy && state.shipmentAbortController ? "终止当前任务" : "终止当前任务";
}

function retryShipmentTask() {
  if (state.shipmentBusy) {
    addShipmentLog("当前任务仍在进行，请先终止或等待完成后再重试", "warning");
    setStatus("当前任务仍在进行");
    return;
  }
  if (!state.lastShipmentTask) {
    addShipmentLog("暂无上次货件任务可重试，请先上传或扫描一次", "warning");
    setStatus("暂无上次任务可重试");
    return;
  }
  state.lastShipmentTask();
}

function cancelShipmentTask() {
  const controller = state.shipmentAbortController;
  if (!controller) {
    addShipmentLog("当前没有可终止的货件处理任务", "warning");
    setStatus("当前没有正在执行的货件处理任务");
    return;
  }
  controller.abort();
  state.shipmentAbortController = null;
  addShipmentLog("已收到终止请求，正在停止当前货件处理任务...", "warning");
  setStatus("正在终止当前任务...");
  els.cancelShipmentTask.textContent = "正在终止...";
}

function clearShipmentAbortController(controller) {
  if (state.shipmentAbortController !== controller) return;
  state.shipmentAbortController = null;
  updateBusyControls();
}

function normalizeLoginPassword(value) {
  return normalizeLoginText(value);
}

function normalizeLoginText(value) {
  return [...value.normalize("NFKC")]
    .filter((char) => {
      if (char === "\ufeff") return false;
      return !/[\u0000-\u001f\u007f-\u009f\u00ad\u061c\u180e\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufe00-\ufe0f\ufff9-\ufffb]/u.test(char);
    })
    .join("")
    .trim();
}

function setReportBusy(message) {
  state.reportBusy = true;
  els.reportStatusText.textContent = message;
  updateReportBusyControls();
}

function setReportStatus(message) {
  state.reportBusy = false;
  els.reportStatusText.textContent = message;
  updateReportBusyControls();
}

function setReportIdle() {
  state.reportBusy = false;
  updateReportBusyControls();
}

function updateReportBusyControls() {
  els.reportUploadSubmitButton.disabled = state.reportBusy;
  setSoftDisabled(els.newReportTask, state.reportBusy);
  setSoftDisabled(els.cancelReportTask, !state.reportBusy || !state.reportAbortController);
  setSoftDisabled(els.retryReportTask, state.reportBusy || !state.lastReportTask);
  setSoftDisabled(els.clearReportResult, state.reportBusy || !state.reportRows.length);
  els.reportUploadPickers.forEach((button) => {
    button.disabled = state.reportBusy;
  });
  els.reportDropTarget.classList.toggle("disabled", state.reportBusy);
  els.reportFolderSubmitButton.disabled = state.reportBusy;
  els.cancelReportTask.textContent = state.reportBusy && state.reportAbortController ? "终止当前任务" : "终止当前任务";
}

function retryReportTask() {
  if (state.reportBusy) {
    addReportLog("当前任务仍在进行，请先终止或等待完成后再重试", "warning");
    setReportStatus("当前任务仍在进行");
    return;
  }
  if (!state.lastReportTask) {
    addReportLog("暂无上次汇总报告任务可重试，请先上传或扫描一次", "warning");
    setReportStatus("暂无上次任务可重试");
    return;
  }
  state.lastReportTask();
}

function cancelReportTask() {
  const controller = state.reportAbortController;
  if (!controller) {
    addReportLog("当前没有可终止的汇总报告任务", "warning");
    setReportStatus("当前没有正在执行的汇总报告任务");
    return;
  }
  controller.abort();
  state.reportAbortController = null;
  addReportLog("已收到终止请求，正在停止当前汇总报告任务...", "warning");
  setReportStatus("正在终止当前任务...");
  els.cancelReportTask.textContent = "正在终止...";
}

function clearReportAbortController(controller) {
  if (state.reportAbortController !== controller) return;
  state.reportAbortController = null;
  updateReportBusyControls();
}

function disableReportDownload() {
  els.reportDownload.href = "#";
  els.reportDownload.classList.add("disabled");
  setSoftDisabled(els.clearReportResult, true);
}

function resetReportResults() {
  state.reportRows = [];
  resetReportTableFilters();
  els.reportReviewPanel.classList.add("hidden");
  els.reportReviewPanel.innerHTML = "";
  els.reportFilterSummary.hidden = true;
  els.reportFilterSummary.innerHTML = "";
  els.reportResultBody.innerHTML = '<tr><td class="empty" colspan="7">处理一批汇总报告 PDF 后，复核队列会显示在这里。</td></tr>';
}

function startNewReportTask() {
  clearReportResults({ resetInputs: true });
}

function clearReportResults({ resetInputs = false } = {}) {
  if (state.reportBusy) {
    addReportLog("请先终止当前汇总报告任务，再新建或清空", "warning");
    setReportStatus("请先终止当前任务");
    return;
  }
  if (!resetInputs && !state.reportRows.length) {
    addReportLog("当前没有汇总报告结果可清空", "warning");
    setReportStatus("当前没有结果可清空");
    return;
  }
  state.reportJobId = "";
  els.reportFilesMetric.textContent = "0";
  els.reportProcessedMetric.textContent = "0";
  els.reportDetailsMetric.textContent = "0";
  els.reportWarningsMetric.textContent = "0";
  els.reportBatchLabel.textContent = "尚未处理汇总报告";
  disableReportDownload();
  resetReportResults();
  if (resetInputs) {
    state.pendingReportFiles = [];
    state.lastReportTask = null;
    els.reportFileInput.value = "";
    els.reportFolderUploadInput.value = "";
    els.reportUploadSelectionText.textContent = "支持一批 PDF 文件，也支持品牌 / 国家多层文件夹";
  }
  resetReportLogs(resetInputs ? "已新建汇总报告任务，等待导入" : "已清空当前汇总报告结果");
  setReportStatus("等待导入");
}

function setTransactionBusy(message) {
  state.transactionBusy = true;
  els.transactionStatusText.textContent = message;
  updateTransactionBusyControls();
}

function setTransactionStatus(message) {
  state.transactionBusy = false;
  els.transactionStatusText.textContent = message;
  updateTransactionBusyControls();
}

function setTransactionIdle() {
  state.transactionBusy = false;
  updateTransactionBusyControls();
}

function updateTransactionBusyControls() {
  els.transactionSubmitButton.disabled = state.transactionBusy;
  setSoftDisabled(els.newTransactionTask, state.transactionBusy);
  setSoftDisabled(els.cancelTransactionTask, !state.transactionBusy || !state.transactionAbortController);
  setSoftDisabled(els.retryTransactionTask, state.transactionBusy || !state.lastTransactionTask);
  setSoftDisabled(els.clearTransactionResult, state.transactionBusy || !state.transactionRows.length);
  els.cancelTransactionTask.textContent = state.transactionBusy && state.transactionAbortController ? "终止当前任务" : "终止当前任务";
}

function retryTransactionTask() {
  if (state.transactionBusy) {
    addTransactionLog("当前任务仍在进行，请先终止或等待完成后再重试", "warning");
    setTransactionStatus("当前任务仍在进行");
    return;
  }
  if (!state.lastTransactionTask) {
    addTransactionLog("暂无上次交易明细任务可重试，请先处理一次", "warning");
    setTransactionStatus("暂无上次任务可重试");
    return;
  }
  state.lastTransactionTask();
}

function cancelTransactionTask() {
  const controller = state.transactionAbortController;
  if (!controller) {
    addTransactionLog("当前没有可终止的交易明细任务", "warning");
    setTransactionStatus("当前没有正在执行的交易明细任务");
    return;
  }
  controller.abort();
  state.transactionAbortController = null;
  addTransactionLog("已收到终止请求，正在停止当前交易明细任务...", "warning");
  setTransactionStatus("正在终止当前任务...");
  els.cancelTransactionTask.textContent = "正在终止...";
}

function clearTransactionAbortController(controller) {
  if (state.transactionAbortController !== controller) return;
  state.transactionAbortController = null;
  updateTransactionBusyControls();
}

function isAbortError(error) {
  return error && error.name === "AbortError";
}

function disableTransactionDownloads() {
  els.transactionDownload.href = "#";
  els.transactionAuditDownload.href = "#";
  els.transactionDownload.classList.add("disabled");
  els.transactionAuditDownload.classList.add("disabled");
  setSoftDisabled(els.clearTransactionResult, true);
}

function startNewTransactionTask() {
  clearTransactionResults({ resetInput: true });
}

function clearTransactionResults({ resetInput = false } = {}) {
  if (state.transactionBusy) {
    addTransactionLog("请先终止当前交易明细任务，再新建或清空", "warning");
    setTransactionStatus("请先终止当前任务");
    return;
  }
  if (!resetInput && !state.transactionRows.length) {
    addTransactionLog("当前没有交易明细结果可清空", "warning");
    setTransactionStatus("当前没有结果可清空");
    return;
  }
  state.transactionJobId = "";
  state.transactionRows = [];
  els.transactionFilesMetric.textContent = "0";
  els.transactionRowsMetric.textContent = "0";
  els.transactionCountriesMetric.textContent = "0";
  els.transactionWarningsMetric.textContent = "0";
  els.transactionBatchLabel.textContent = "尚未处理交易明细";
  els.transactionResultBody.innerHTML = '<tr><td class="empty" colspan="8">处理一批交易明细 CSV/XLSX 后，结果会显示在这里。</td></tr>';
  disableTransactionDownloads();
  if (resetInput) {
    state.lastTransactionTask = null;
  }
  resetTransactionLogs(resetInput ? "已新建交易明细任务，等待导入" : "已清空当前交易明细结果");
  setTransactionStatus("等待导入");
}

function closeExportMenu() {
  els.exportMenu.classList.remove("open");
  els.exportMenuButton.setAttribute("aria-expanded", "false");
}

function roleLabel(role) {
  return role === "admin" ? "管理员" : "操作员";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
