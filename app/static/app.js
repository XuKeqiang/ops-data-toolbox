const state = {
  batchId: "",
  records: [],
  reportJobId: "",
  activeView: "shipment",
  currentUser: null,
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
  folderForm: document.querySelector("#folderForm"),
  folderInput: document.querySelector("#folderInput"),
  filesMetric: document.querySelector("#filesMetric"),
  boxesMetric: document.querySelector("#boxesMetric"),
  validMetric: document.querySelector("#validMetric"),
  reviewMetric: document.querySelector("#reviewMetric"),
  batchLabel: document.querySelector("#batchLabel"),
  statusText: document.querySelector("#statusText"),
  resultBody: document.querySelector("#resultBody"),
  exportMenu: document.querySelector("#exportMenu"),
  exportMenuButton: document.querySelector("#exportMenuButton"),
  exportCsv: document.querySelector("#exportCsv"),
  exportXlsx: document.querySelector("#exportXlsx"),
  packageButton: document.querySelector("#packageButton"),
  packageResult: document.querySelector("#packageResult"),
  renameButton: document.querySelector("#renameButton"),
  reportFolderForm: document.querySelector("#reportFolderForm"),
  reportFolderInput: document.querySelector("#reportFolderInput"),
  reportFilesMetric: document.querySelector("#reportFilesMetric"),
  reportProcessedMetric: document.querySelector("#reportProcessedMetric"),
  reportDetailsMetric: document.querySelector("#reportDetailsMetric"),
  reportWarningsMetric: document.querySelector("#reportWarningsMetric"),
  reportBatchLabel: document.querySelector("#reportBatchLabel"),
  reportStatusText: document.querySelector("#reportStatusText"),
  reportResultBody: document.querySelector("#reportResultBody"),
  reportDownload: document.querySelector("#reportDownload"),
  refreshHistoryButton: document.querySelector("#refreshHistoryButton"),
  historyTotalMetric: document.querySelector("#historyTotalMetric"),
  historyShipmentMetric: document.querySelector("#historyShipmentMetric"),
  historyReportMetric: document.querySelector("#historyReportMetric"),
  historyReviewMetric: document.querySelector("#historyReviewMetric"),
  historyStatusText: document.querySelector("#historyStatusText"),
  historyResultBody: document.querySelector("#historyResultBody"),
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
  history: "history",
  settings: "settings",
};

els.navItems.forEach((item) => {
  item.addEventListener("click", () => {
    setActiveView(item.dataset.view);
    window.location.hash = hashByView[item.dataset.view] || "shipment";
  });
});

els.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  els.loginStatus.textContent = "正在登录...";
  const response = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: els.loginUsername.value,
      password: els.loginPassword.value,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    els.loginStatus.textContent = payload.error || "登录失败";
    return;
  }
  applySession(payload.user);
});

els.logoutButton.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  state.currentUser = null;
  showLoggedOut();
});

els.folderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy("正在扫描服务器文件夹...");
  const response = await fetch("/api/scan-folder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder: els.folderInput.value }),
  });
  await handleBatchResponse(response);
});

els.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = [...els.fileInput.files];
  if (!files.length) {
    setStatus("请选择至少一个 PDF 文件");
    return;
  }

  setBusy(`正在上传并识别 ${files.length} 个文件...`);
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });
  await handleBatchResponse(response);
});

els.reportFolderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setReportBusy("正在提取交易报告 PDF，并生成 Excel...");
  disableReportDownload();
  const response = await fetch("/api/report-pdf/process-folder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder: els.reportFolderInput.value }),
  });
  await handleReportResponse(response);
});

els.refreshHistoryButton.addEventListener("click", () => {
  loadHistory();
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

document.addEventListener("click", (event) => {
  if (!els.exportMenu.contains(event.target)) {
    closeExportMenu();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeExportMenu();
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
  setStatus(`已生成 ${payload.packages.length} 个工厂压缩包`);
  if (state.activeView === "history") {
    loadHistory();
  }
  updateActionButtons();
});

window.addEventListener("hashchange", () => {
  if (!state.currentUser) return;
  setActiveView(viewFromHash());
});

if (!["", "#shipment", "#report-pdf", "#history", "#settings"].includes(window.location.hash)) {
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
  setActiveView(viewFromHash());
}

function showLoggedOut() {
  state.currentUser = null;
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
    setStatus(payload.error || "处理失败");
    return;
  }
  state.batchId = payload.batch_id;
  state.records = payload.records;
  renderBatch(payload);
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
    setReportStatus(payload.error || "处理失败");
    return;
  }
  state.reportJobId = payload.job_id;
  renderReportJob(payload);
  if (state.activeView === "history") {
    loadHistory();
  }
}

function renderBatch(payload) {
  const { summary } = payload;
  els.filesMetric.textContent = summary.files;
  els.boxesMetric.textContent = summary.boxes;
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

  updateActionButtons(payload.records);

  if (!payload.records.length) {
    els.resultBody.innerHTML = '<tr><td class="empty" colspan="12">该批次没有 PDF 文件。</td></tr>';
    return;
  }

  els.resultBody.innerHTML = payload.records.map(renderRow).join("");
}

function renderReportJob(payload) {
  const { summary } = payload;
  els.reportFilesMetric.textContent = summary.files;
  els.reportProcessedMetric.textContent = summary.processed;
  els.reportDetailsMetric.textContent = summary.detail_rows;
  els.reportWarningsMetric.textContent = summary.warnings;
  els.reportBatchLabel.textContent = payload.source_label;
  setReportStatus(`已解析 ${summary.processed} 个 PDF，${summary.warnings} 个需要复核`);

  els.reportDownload.href = payload.download_url;
  els.reportDownload.classList.remove("disabled");

  if (!payload.rows.length) {
    els.reportResultBody.innerHTML = '<tr><td class="empty" colspan="8">该文件夹没有可处理的交易报告 PDF。</td></tr>';
    return;
  }

  els.reportResultBody.innerHTML = payload.rows.map(renderReportRow).join("");
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
  const productName = record.title_product_name || record.product_name || "-";
  const boxText = record.total_units && record.total_units !== record.box_count
    ? `${record.box_count}箱 / ${record.total_units}个`
    : `${record.box_count}箱`;
  const filenameInfo = record.filename_info || {};
  const filenameSummary = [
    filenameInfo.sku ? `SKU ${filenameInfo.sku}` : "",
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

function renderPackageResult(payload) {
  const packages = payload.packages || [];
  const skipped = payload.skipped || [];
  const packageLinks = packages.length
    ? packages.map((item) => `
        <a class="text-link" href="${escapeHtml(item.download_url)}">
          ${escapeHtml(item.factory_name)} · ${escapeHtml(item.file_count)} 个 PDF
        </a>
      `).join("")
    : "<span>没有生成压缩包</span>";
  const skippedText = skipped.length
    ? `<p>${escapeHtml(skipped.map((item) => `${item.filename}：${item.reason}`).join("；"))}</p>`
    : "";
  els.packageResult.innerHTML = `
    <div>
      <strong>工厂压缩包</strong>
      <span>${escapeHtml(payload.package_root || "")}</span>
    </div>
    <div class="action-links">${packageLinks}</div>
    ${skippedText}
  `;
  els.packageResult.classList.remove("hidden");
}

function renderReportRow(row) {
  const statusClass = row.status === "通过" ? "ok" : "warn";
  const period = row.year && row.month ? `${row.year}-${String(row.month).padStart(2, "0")}` : (row.period || "-");
  const counts = `${row.summary_count || 0} / ${row.detail_count || 0}`;

  return `
    <tr>
      <td class="filename">${escapeHtml(row.source_file || "-")}</td>
      <td>${escapeHtml(row.store || "-")}</td>
      <td>${escapeHtml(row.country || row.country_code || "-")}</td>
      <td>${escapeHtml(period)}</td>
      <td>${escapeHtml(row.currency || "-")}</td>
      <td>${escapeHtml(counts)}</td>
      <td><span class="badge ${statusClass}">${escapeHtml(row.status || "需复核")}</span></td>
      <td class="suggested">${escapeHtml(row.notes || "-")}</td>
    </tr>
  `;
}

function renderHistory(payload) {
  const { summary, tasks } = payload;
  els.historyTotalMetric.textContent = summary.total;
  els.historyShipmentMetric.textContent = summary.shipment_pdf;
  els.historyReportMetric.textContent = summary.report_pdf;
  els.historyReviewMetric.textContent = summary.needs_review;
  els.historyStatusText.textContent = summary.total
    ? `已记录 ${summary.total} 个任务`
    : "记录当前服务运行期间的处理任务";

  if (!tasks.length) {
    els.historyResultBody.innerHTML = '<tr><td class="empty" colspan="7">完成一次扫描或提取后，历史任务会显示在这里。</td></tr>';
    return;
  }

  els.historyResultBody.innerHTML = tasks.map(renderHistoryRow).join("");
}

function renderHistoryRow(task) {
  const statusClass = task.status === "完成" ? "ok" : "warn";
  const summary = historySummaryText(task);
  const downloads = task.downloads && task.downloads.length
    ? task.downloads.map((download) => `<a class="text-link" href="${escapeHtml(download.url)}">${escapeHtml(download.label)}</a>`).join("")
    : "-";

  return `
    <tr>
      <td class="mono-cell">${escapeHtml(task.created_at)}</td>
      <td>${escapeHtml(task.title)}</td>
      <td>${escapeHtml(task.owner_name || task.owner_username || "-")}</td>
      <td class="filename">${escapeHtml(task.source_label)}</td>
      <td>${escapeHtml(summary)}</td>
      <td><span class="badge ${statusClass}">${escapeHtml(task.status)}</span></td>
      <td class="action-links">${downloads}</td>
    </tr>
  `;
}

function historySummaryText(task) {
  const summary = task.summary || {};
  if (task.type === "shipment_pdf") {
    return `${summary.files || 0} 个PDF / ${summary.boxes || 0} 个箱码 / ${summary.needs_review || 0} 个复核`;
  }
  if (task.type === "report_pdf") {
    return `${summary.processed || 0} 个PDF / ${summary.detail_rows || 0} 条明细 / ${summary.warnings || 0} 个复核`;
  }
  return "-";
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
  state.activeView = ["shipment", "report", "history", "settings"].includes(view) ? view : "shipment";
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
  if (window.location.hash.includes("history")) return "history";
  if (window.location.hash.includes("settings")) return "settings";
  return "shipment";
}

function setBusy(message) {
  els.statusText.textContent = message;
}

function setStatus(message) {
  els.statusText.textContent = message;
}

function setReportBusy(message) {
  els.reportStatusText.textContent = message;
}

function setReportStatus(message) {
  els.reportStatusText.textContent = message;
}

function disableReportDownload() {
  els.reportDownload.href = "#";
  els.reportDownload.classList.add("disabled");
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
