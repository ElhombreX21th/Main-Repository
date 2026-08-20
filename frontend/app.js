const API = "/api/v1";
const state = { token: localStorage.getItem("reembolsabr_token"), email: localStorage.getItem("reembolsabr_email") || "", firstName: localStorage.getItem("reembolsabr_first_name") || "você", role: localStorage.getItem("reembolsabr_role") || "", userId: localStorage.getItem("reembolsabr_user_id") || "", expenses: [], policies: [], users: [], authMode: "login" };
window.__reembolsabrReady = false;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const money = (value, currency = "BRL") => new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value || 0));
const dateLabel = (value) => value ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T12:00:00`)).replace(" de ", " ") : "-";
const statusLabel = { draft: "Rascunho", submitted: "Em análise", approved: "Aprovada", rejected: "Rejeitada", reimbursed: "Reembolsada" };
const categoryLabel = { breakfast: "Café da manhã", lunch: "Almoço", dinner: "Jantar", transport: "Transporte", lodging: "Hospedagem", other: "Outra finalidade" };
const roleLabel = { employee: "Funcionário", approver: "Aprovador", admin: "Administrador" };

function resetMainScroll() {
  $(".main-content")?.scrollTo({ top: 0, left: 0, behavior: "auto" });
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
}

function setFeedback(target, message = "", isSuccess = false) {
  const element = typeof target === "string" ? $(target) : target;
  if (!element) return;
  element.textContent = message;
  element.style.color = isSuccess ? "var(--sage)" : "";
}

function setDateLabels() {
  const today = new Date();
  $("#topbar-date").textContent = new Intl.DateTimeFormat("pt-BR", { weekday: "long", day: "2-digit", month: "short", year: "numeric" }).format(today).replace(".", "").toUpperCase();
  $("#period-label").textContent = new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric" }).format(today).toUpperCase();
}

async function request(path, options = {}) {
  const headers = { ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) logout();
    const detail = Array.isArray(payload.detail) ? payload.detail.map((item) => item.msg).join(", ") : payload.detail;
    throw new Error(detail || "Não foi possível concluir a solicitação.");
  }
  return payload;
}

async function showDashboard() {
  window.__reembolsabrReady = false;
  document.body.classList.add("dashboard-mode");
  $("#auth-screen").classList.add("hidden");
  $("#dashboard-screen").classList.remove("hidden");
  $("#user-name").textContent = state.firstName;
  setDateLabels();
  resetMainScroll();
  try {
    await loadProfile();
    applyPermissions();
    await loadData();
  } catch (error) {
    setFeedback("#global-feedback", error.message);
  }
}

function showAuth() {
  document.body.classList.remove("dashboard-mode");
  $("#auth-screen").classList.remove("hidden");
  $("#dashboard-screen").classList.add("hidden");
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
}

async function loadProfile() {
  const profile = await request("/auth/me");
  state.userId = profile.id;
  state.firstName = profile.full_name?.trim().split(/\s+/)[0] || "você";
  state.email = profile.email;
  state.role = profile.role;
  localStorage.setItem("reembolsabr_user_id", state.userId);
  localStorage.setItem("reembolsabr_first_name", state.firstName);
  localStorage.setItem("reembolsabr_email", state.email);
  localStorage.setItem("reembolsabr_role", state.role);
  $("#user-name").textContent = state.firstName;
}

function applyPermissions() {
  const isAdmin = state.role === "admin";
  $("#team-nav").classList.toggle("hidden", !isAdmin);
  $("#policy-form").classList.toggle("hidden", !isAdmin);
  if (!isAdmin && $("#team-view") && !$("#team-view").classList.contains("hidden")) {
    setView("overview");
  }
}

function logout() {
  state.token = null;
  state.role = "";
  state.userId = "";
  localStorage.removeItem("reembolsabr_token");
  localStorage.removeItem("reembolsabr_email");
  localStorage.removeItem("reembolsabr_first_name");
  localStorage.removeItem("reembolsabr_role");
  localStorage.removeItem("reembolsabr_user_id");
  showAuth();
}

function switchAuthMode(mode) {
  state.authMode = mode;
  const register = mode === "register";
  $("#name-field").classList.toggle("hidden", !register);
  $("#name-field input").required = register;
  $("#organization-field").classList.toggle("hidden", !register);
  $("#organization-field input").required = register;
  $("#auth-title").textContent = register ? "Crie sua conta" : "Acesse sua conta";
  $("#auth-subtitle").textContent = register ? "Informe seus dados para iniciar o controle de reembolsos." : "Entre para acompanhar suas despesas.";
  $("#auth-submit-label").textContent = register ? "Criar e entrar" : "Entrar no painel";
  $$('[data-auth-mode]').forEach((button) => button.classList.toggle("is-active", button.dataset.authMode === mode));
  setFeedback("#auth-feedback");
}

async function handleAuth(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const email = form.get("email").toString();
  const password = form.get("password").toString();
  const submit = event.currentTarget.querySelector("button[type=submit]");
  submit.disabled = true;
  setFeedback("#auth-feedback", "Conectando...");
  try {
    let result;
    if (state.authMode === "register") {
      result = await request("/auth/register", { method: "POST", body: JSON.stringify({ full_name: form.get("full_name"), organization_name: form.get("organization_name"), email, password, country_code: "BR" }) });
    } else {
      const body = new URLSearchParams({ username: email, password });
      result = await request("/auth/token", { method: "POST", body, headers: { "Content-Type": "application/x-www-form-urlencoded" } });
    }
    state.token = result.access_token;
    state.email = email;
    state.firstName = result.first_name || form.get("full_name")?.toString().trim().split(/\s+/)[0] || "você";
    state.role = result.role || state.role;
    localStorage.setItem("reembolsabr_token", state.token);
    localStorage.setItem("reembolsabr_email", email);
    localStorage.setItem("reembolsabr_first_name", state.firstName);
    if (state.role) localStorage.setItem("reembolsabr_role", state.role);
    setFeedback("#auth-feedback");
    showDashboard();
  } catch (error) {
    setFeedback("#auth-feedback", error.message);
  } finally {
    submit.disabled = false;
  }
}

async function loadData() {
  try {
    const [expenses, policies, users] = await Promise.all([
      request("/expenses"),
      request("/policies"),
      state.role === "admin" ? request("/auth/users") : Promise.resolve([]),
    ]);
    state.expenses = expenses;
    state.policies = policies;
    state.users = users;
    renderOverview();
    renderExpenses();
    renderPolicies();
    renderUsers();
    window.__reembolsabrReady = true;
  } catch (error) {
    setFeedback("#global-feedback", error.message);
    window.__reembolsabrReady = false;
  }
}

function renderOverview() {
  const total = state.expenses.reduce((sum, item) => sum + Number(item.amount), 0);
  const pending = state.expenses.filter((item) => ["submitted", "draft"].includes(item.status)).length;
  const approved = state.expenses.filter((item) => ["approved", "reimbursed"].includes(item.status)).length;
  $("#metric-total").textContent = money(total);
  $("#metric-pending").textContent = pending;
  $("#metric-approved").textContent = approved;
  const recent = state.expenses.slice(0, 5);
  $("#recent-expenses").innerHTML = recent.length ? recent.map(expenseRow).join("") : '<div class="empty-state">Nenhuma despesa registrada. Adicione um recibo para começar.</div>';
}

function expenseRow(item) {
  return `<div class="expense-row"><div><p class="expense-title">${escapeHtml(categoryLabel[item.category] || item.category)}</p><span class="expense-date">${dateLabel(item.expense_date)}</span></div><strong class="expense-amount">${money(item.amount, item.currency)}</strong><span class="status-badge ${item.status}">${statusLabel[item.status] || item.status}</span></div>`;
}

function renderExpenses() {
  const container = $("#all-expenses");
  if (!state.expenses.length) {
    container.innerHTML = '<div class="empty-state">Nenhuma despesa registrada.</div>';
    return;
  }
  container.innerHTML = `<table class="expenses-table"><thead><tr><th>DESPESA</th><th>DATA</th><th>VALOR</th><th>STATUS</th><th></th></tr></thead><tbody>${state.expenses.map((item) => `<tr><td><strong>${escapeHtml(categoryLabel[item.category] || item.category)}</strong><br /><span class="expense-date">${escapeHtml(item.description || "Sem descrição")}</span></td><td>${dateLabel(item.expense_date)}</td><td><strong>${money(item.amount, item.currency)}</strong></td><td><span class="status-badge ${item.status}">${statusLabel[item.status] || item.status}</span></td><td>${expenseActions(item)}</td></tr>`).join("")}</tbody></table>`;
}

function expenseActions(item) {
  const canSubmit = item.user_id === state.userId || state.role === "admin";
  const canApprove = ["approver", "admin"].includes(state.role);
  if (item.status === "draft" && canSubmit) return `<button class="table-action" data-expense-action="submit" data-expense-id="${item.id}" type="button">Enviar →</button>`;
  if (item.status === "submitted" && canApprove) return `<button class="table-action" data-expense-action="approve" data-expense-id="${item.id}" type="button">Aprovar →</button><button class="table-action danger" data-expense-action="reject" data-expense-id="${item.id}" type="button">Rejeitar</button>`;
  if (item.status === "approved" && canApprove) return `<button class="table-action" data-expense-action="reimburse" data-expense-id="${item.id}" type="button">Reembolsar →</button>`;
  return "";
}

function renderPolicies() {
  const container = $("#policies-list");
  container.innerHTML = state.policies.length ? state.policies.map((policy) => `<article class="policy-card"><div><strong>${escapeHtml(policy.category)}</strong><small>${policy.country_code} · ${policy.currency}</small></div><span class="policy-limit">${money(policy.max_amount, policy.currency)}</span></article>`).join("") : '<div class="empty-state">Nenhuma política cadastrada.</div>';
}

function renderUsers() {
  const container = $("#users-list");
  if (!container) return;
  container.innerHTML = state.users.length ? state.users.map((user) => `<article class="policy-card"><div><strong>${escapeHtml(user.full_name || user.email)}</strong><small>${escapeHtml(user.email)}</small></div><span class="status-badge ${user.role}">${roleLabel[user.role] || user.role}</span></article>`).join("") : '<div class="empty-state">Nenhum usuário cadastrado.</div>';
}

async function createPolicy(event) {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  try {
    const policy = await request("/policies", { method: "POST", body: JSON.stringify({ category: form.get("category"), country_code: "BR", currency: form.get("currency").toString().toUpperCase(), max_amount: Number(form.get("max_amount")) }) });
    state.policies.unshift(policy);
    renderPolicies();
    formElement.reset();
    setFeedback("#policy-feedback", "Política salva com sucesso.", true);
  } catch (error) {
    setFeedback("#policy-feedback", error.message);
  }
}

async function createUser(event) {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  try {
    const user = await request("/auth/users", { method: "POST", body: JSON.stringify({ full_name: form.get("full_name"), email: form.get("email"), password: form.get("password"), role: form.get("role") }) });
    state.users.push(user);
    state.users.sort((a, b) => (a.full_name || a.email).localeCompare(b.full_name || b.email));
    renderUsers();
    formElement.reset();
    setFeedback("#user-feedback", "Usuário criado com sucesso.", true);
  } catch (error) {
    setFeedback("#user-feedback", error.message);
  }
}

function openExpenseDialog() {
  const form = $("#expense-form");
  form.reset();
  $("#receipt-text").value = "";
  $("#receipt-preview").classList.add("hidden");
  $("#ocr-receipt-button").classList.add("hidden");
  setFeedback("#expense-feedback");
  $("#expense-dialog").showModal();
  const dateInput = form.elements.expense_date;
  if (!dateInput.value) dateInput.value = new Date().toISOString().slice(0, 10);
}

async function submitExpense(event) {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const payload = Object.fromEntries(form.entries());
  payload.amount = Number(payload.amount);
  ["merchant_tax_id", "merchant_city", "merchant_state", "invoice_key", "description"].forEach((key) => { if (!payload[key]) payload[key] = null; });
  try {
    const createdExpense = await request("/expenses", { method: "POST", body: JSON.stringify(payload) });
    state.expenses.unshift(createdExpense);
    renderOverview();
    renderExpenses();
    $("#expense-dialog").close();
    formElement.reset();
    setFeedback("#global-feedback", "Despesa registrada com sucesso.", true);
    await loadData();
    resetMainScroll();
  } catch (error) {
    setFeedback("#expense-feedback", error.message);
  }
}

async function parseReceipt() {
  const text = $("#receipt-text").value.trim();
  if (!text) return setFeedback("#expense-feedback", "Cole o texto do recibo antes de preencher os dados.");
  try {
    const parsed = await request("/expenses/parse-receipt", { method: "POST", body: JSON.stringify({ text }) });
    const form = $("#expense-form");
    if (parsed.amount) form.elements.amount.value = parsed.amount;
    if (parsed.expense_date) form.elements.expense_date.value = parsed.expense_date;
    if (parsed.merchant_tax_id) form.elements.merchant_tax_id.value = parsed.merchant_tax_id;
    if (parsed.merchant_city) form.elements.merchant_city.value = parsed.merchant_city;
    if (parsed.merchant_state) form.elements.merchant_state.value = parsed.merchant_state;
    if (parsed.invoice_key) form.elements.invoice_key.value = parsed.invoice_key;
    setFeedback("#expense-feedback", "Dados identificados e preenchidos com sucesso.", true);
  } catch (error) {
    setFeedback("#expense-feedback", error.message);
  }
}

async function readReceiptImage() {
  const file = $("#receipt-image").files[0];
  if (!file) return;
  const preview = $("#receipt-preview");
  preview.src = URL.createObjectURL(file);
  preview.classList.remove("hidden");
  $("#ocr-receipt-button").classList.remove("hidden");
  setFeedback("#expense-feedback", "Foto adicionada. Confira o enquadramento antes de ler os dados.", true);
}

async function ocrReceipt() {
  const file = $("#receipt-image").files[0];
  if (!file || !window.Tesseract) return setFeedback("#expense-feedback", "Não foi possível iniciar a leitura da foto.");
  const button = $("#ocr-receipt-button");
  button.disabled = true;
  button.firstChild.textContent = "Lendo foto... ";
  try {
    const result = await window.Tesseract.recognize(file, "por", { logger: (message) => { if (message.status === "recognizing text") setFeedback("#expense-feedback", `Lendo recibo: ${Math.round(message.progress * 100)}%`); } });
    $("#receipt-text").value = result.data.text;
    await parseReceipt();
  } catch (error) {
    setFeedback("#expense-feedback", "Não foi possível ler a foto. Confira os campos manualmente.");
  } finally {
    button.disabled = false;
    button.firstChild.textContent = "Ler dados da foto ";
  }
}

async function submitExpenseById(id) {
  try {
    await request(`/expenses/${id}/submit`, { method: "POST" });
    setFeedback("#global-feedback", "Despesa enviada para análise.", true);
    await loadData();
    resetMainScroll();
  } catch (error) {
    setFeedback("#global-feedback", error.message);
  }
}

async function transitionExpense(id, action) {
  try {
    await request(`/expenses/${id}/${action}`, { method: "POST" });
    setFeedback("#global-feedback", action === "approve" ? "Despesa aprovada." : action === "reimburse" ? "Despesa marcada como reembolsada." : "Despesa rejeitada.", true);
    await loadData();
    resetMainScroll();
  } catch (error) {
    setFeedback("#global-feedback", error.message);
  }
}

function setView(view) {
  const titles = { overview: "Visão geral", expenses: "Despesas", policies: "Políticas", team: "Equipe" };
  ["overview", "expenses", "policies", "team"].forEach((name) => $((`#${name}-view`)).classList.toggle("hidden", name !== view));
  $$(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  $("#page-title").textContent = titles[view];
  resetMainScroll();
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

$$('[data-auth-mode]').forEach((button) => button.addEventListener("click", () => switchAuthMode(button.dataset.authMode)));
$("#auth-form").addEventListener("submit", handleAuth);
$("#logout-button").addEventListener("click", logout);
$("#new-expense-button").addEventListener("click", openExpenseDialog);
$("#list-new-expense").addEventListener("click", openExpenseDialog);
$("#quick-new-expense").addEventListener("click", openExpenseDialog);
$("#close-dialog").addEventListener("click", () => $("#expense-dialog").close());
$("#expense-form").addEventListener("submit", submitExpense);
$("#parse-receipt-button").addEventListener("click", parseReceipt);
$("#receipt-image").addEventListener("change", readReceiptImage);
$("#ocr-receipt-button").addEventListener("click", ocrReceipt);
$("#policy-form").addEventListener("submit", createPolicy);
$("#user-form").addEventListener("submit", createUser);
$$('[data-view]').forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
$$('[data-view-target]').forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewTarget)));
$("#all-expenses").addEventListener("click", (event) => {
  const button = event.target.closest("[data-expense-action]");
  if (!button) return;
  if (button.dataset.expenseAction === "submit") submitExpenseById(button.dataset.expenseId);
  else transitionExpense(button.dataset.expenseId, button.dataset.expenseAction);
});

if (state.token) showDashboard();
else setDateLabels();
