const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const state = { expenses: [], user: null, page: "dashboard" };
const demoMode = location.hostname.endsWith(".vercel.app") || (location.pathname === "/demo" || location.pathname.endsWith("/demo.html")) || new URLSearchParams(location.search).has("demo");
const labels = { meals: "Alimentação", travel: "Viagem", transport: "Transporte", lodging: "Hospedagem", supplies: "Materiais" };
const statusLabels = { draft: "Rascunho", submitted: "Em aprovação", approved: "Aprovada", rejected: "Rejeitada", reimbursed: "Reembolsada" };

function h(value) {
  const element = document.createElement("span");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function toast(message, error = false) {
  const element = $("#toast");
  element.textContent = message;
  element.className = `toast show${error ? " error" : ""}`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (element.className = "toast"), 3200);
}

function money(value, currency = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value || 0));
}

async function api(path, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = { ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`/api/v1${path}`, { ...options, headers });
  if (response.status === 401 && token) {
    const refreshed = await refreshSession();
    if (refreshed) return api(path, options);
    logout();
  }
  if (!response.ok) {
    let message = "Não foi possível concluir a operação.";
    try { message = (await response.json()).detail || message; } catch (_) { /* resposta sem JSON */ }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

async function refreshSession() {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return false;
  try {
    const response = await fetch("/api/v1/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: refresh }) });
    if (!response.ok) return false;
    saveTokens(await response.json());
    return true;
  } catch (_) { return false; }
}

function saveTokens(data) {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  state.user = null;
  $("#app-screen").classList.add("hidden");
  $("#auth-screen").classList.remove("hidden");
}

async function enterApp() {
  try {
    state.user = demoMode ? { email: "admin@acme.com.br", role: "admin", is_active: true } : await api("/users/me");
    localStorage.setItem("user_email", state.user.email);
    $("#user-name").textContent = state.user.email.split("@")[0];
    $("#user-role").textContent = { admin: "Administrador", approver: "Aprovador", employee: "Colaborador" }[state.user.role];
    $("#avatar").textContent = state.user.email.slice(0, 2).toUpperCase();
    if (state.user.role === "employee") $$('[data-page="approvals"], [data-page="policies"], [data-page="users"]').forEach((el) => el.classList.add("hidden"));
    $("#auth-screen").classList.add("hidden");
    $("#app-screen").classList.remove("hidden");
    await loadExpenses();
    navigate("dashboard");
  } catch (_) { logout(); }
}

async function loadExpenses() {
  if (demoMode) {
    state.expenses = [
      { id:"a1", user_id:"carlos.silva", category:"travel", amount:"2650.00", currency:"BRL", expense_date:"2026-08-14", description:"Passagem para visita ao cliente", cost_center:"COM-01", status:"submitted", policy_violation:null },
      { id:"a2", user_id:"marina.costa", category:"meals", amount:"148.70", currency:"BRL", expense_date:"2026-08-13", description:"Almoço com cliente", cost_center:"COM-01", status:"approved", policy_violation:null },
      { id:"a3", user_id:"joao.santos", category:"lodging", amount:"890.00", currency:"BRL", expense_date:"2026-08-12", description:"Hotel — conferência anual", cost_center:"MKT-02", status:"reimbursed", policy_violation:null },
      { id:"a4", user_id:"ana.lima", category:"transport", amount:"76.40", currency:"BRL", expense_date:"2026-08-11", description:"Transporte por aplicativo", cost_center:"OPS-03", status:"draft", policy_violation:null },
      { id:"a5", user_id:"pedro.alves", category:"meals", amount:"238.90", currency:"BRL", expense_date:"2026-08-10", description:"Jantar durante viagem", cost_center:"COM-01", status:"submitted", policy_violation:"Limite: BRL 150.00" },
    ];
    $("#approval-badge").textContent = "2";
    return;
  }
  try { state.expenses = await api("/expenses"); }
  catch (error) { toast(error.message, true); state.expenses = []; }
  $("#approval-badge").textContent = state.expenses.filter((e) => e.status === "submitted").length;
}

function expenseRow(expense) {
  return `<div class="expense-row">
    <div class="merchant"><span class="merchant-icon">${h((labels[expense.category] || expense.category)[0])}</span><div><strong>${h(labels[expense.category] || expense.category)}</strong><small>${h(expense.description || "Despesa corporativa")}</small></div></div>
    <small>${new Date(`${expense.expense_date}T12:00:00`).toLocaleDateString("pt-BR")}</small>
    <span class="amount">${money(expense.amount, expense.currency)}</span>
    <span class="status ${expense.status}">${statusLabels[expense.status]}</span>
  </div>`;
}

function pageHead(title, subtitle, action = "") {
  return `<div class="page-head"><div><span class="eyebrow">REEMBOLSABR</span><h1>${title}</h1><p>${subtitle}</p></div>${action}</div>`;
}

function renderDashboard() {
  const total = state.expenses.reduce((sum, item) => sum + Number(item.amount), 0);
  const pending = state.expenses.filter((item) => item.status === "submitted");
  const approved = state.expenses.filter((item) => ["approved", "reimbursed"].includes(item.status));
  const violation = state.expenses.filter((item) => item.policy_violation);
  $("#page").innerHTML = `${pageHead(`Olá, ${h(state.user.email.split("@")[0])}!`, "Aqui está o resumo das despesas da sua empresa.", '<button class="btn primary new-expense">＋ Nova despesa</button>')}
    <section class="stats">
      <div class="stat-card"><span class="stat-icon">▤</span><div><small>TOTAL REGISTRADO</small><strong>${money(total)}</strong></div></div>
      <div class="stat-card"><span class="stat-icon orange">◷</span><div><small>AGUARDANDO APROVAÇÃO</small><strong>${pending.length}</strong></div></div>
      <div class="stat-card"><span class="stat-icon blue">✓</span><div><small>APROVADAS</small><strong>${approved.length}</strong></div></div>
      <div class="stat-card"><span class="stat-icon red">!</span><div><small>FORA DA POLÍTICA</small><strong>${violation.length}</strong></div></div>
    </section>
    <section class="dashboard-grid">
      <div class="card"><div class="card-head"><h3>Despesas recentes</h3><button class="text-btn" data-go="expenses">Ver todas →</button></div>${state.expenses.length ? state.expenses.slice(0, 5).map(expenseRow).join("") : '<div class="empty">◎<strong>Nenhuma despesa ainda</strong>Comece adicionando seu primeiro comprovante.</div>'}</div>
      <div><div class="card quick-card"><h3>Registre em segundos</h3><p>Adicione uma despesa, anexe seu comprovante e acompanhe a aprovação.</p><button class="btn new-expense">＋ Adicionar despesa</button></div><div class="card policy-note"><h3>Lembretes rápidos</h3><div class="policy-line">✓ Guarde sempre o comprovante fiscal</div><div class="policy-line">✓ Informe o centro de custo correto</div><div class="policy-line">✓ Envie até o fechamento do mês</div></div></div>
    </section>`;
  bindCommon();
}

function renderExpenses() {
  $("#page").innerHTML = `${pageHead("Minhas despesas", "Consulte e acompanhe todas as solicitações.", '<button class="btn primary new-expense">＋ Nova despesa</button>')}
    <div class="table-card"><table class="data-table"><thead><tr><th>DESPESA</th><th>DATA</th><th>VALOR</th><th>STATUS</th><th>AÇÕES</th></tr></thead><tbody>${state.expenses.map((e) => `<tr><td><strong>${h(labels[e.category] || e.category)}</strong><br><small>${h(e.cost_center || "Sem centro de custo")}</small></td><td>${new Date(`${e.expense_date}T12:00`).toLocaleDateString("pt-BR")}</td><td><strong>${money(e.amount, e.currency)}</strong></td><td><span class="status ${e.status}">${statusLabels[e.status]}</span></td><td class="actions">${["draft", "rejected"].includes(e.status) ? `<button class="action-btn submit-expense" data-id="${e.id}">Enviar</button>` : "—"}</td></tr>`).join("") || '<tr><td colspan="5" class="empty">Nenhuma despesa registrada.</td></tr>'}</tbody></table></div>`;
  bindCommon();
  $$(".submit-expense").forEach((button) => button.onclick = () => expenseAction(button.dataset.id, "submit"));
}

function renderApprovals() {
  const pending = state.expenses.filter((item) => item.status === "submitted");
  $("#page").innerHTML = `${pageHead("Aprovações", "Revise solicitações pendentes da sua equipe.")}
    <div class="table-card"><table class="data-table"><thead><tr><th>COLABORADOR</th><th>CATEGORIA</th><th>DATA</th><th>VALOR</th><th>DECISÃO</th></tr></thead><tbody>${pending.map((e) => `<tr><td>${e.user_id.slice(0, 8)}</td><td>${h(labels[e.category] || e.category)}${e.policy_violation ? '<br><small style="color:#c45454">⚠ Fora da política</small>' : ""}</td><td>${new Date(`${e.expense_date}T12:00`).toLocaleDateString("pt-BR")}</td><td><strong>${money(e.amount, e.currency)}</strong></td><td class="actions"><button class="action-btn approve" data-action="approve" data-id="${e.id}">✓ Aprovar</button><button class="action-btn reject" data-action="reject" data-id="${e.id}">× Rejeitar</button></td></tr>`).join("") || '<tr><td colspan="5" class="empty">Tudo certo! Não há aprovações pendentes.</td></tr>'}</tbody></table></div>`;
  $$('[data-action]').forEach((button) => button.onclick = () => expenseAction(button.dataset.id, button.dataset.action));
}

async function renderReports() {
  $("#page").innerHTML = `${pageHead("Relatórios", "Visualize para onde estão indo os recursos.")}<div class="card"><div class="skeleton"></div><div class="skeleton"></div></div>`;
  try {
    const reports = demoMode ? [
      { category:"travel", currency:"BRL", count:1, total:"2650.00" },
      { category:"lodging", currency:"BRL", count:1, total:"890.00" },
      { category:"meals", currency:"BRL", count:2, total:"387.60" },
      { category:"transport", currency:"BRL", count:1, total:"76.40" },
    ] : await api("/reports/expenses");
    const max = Math.max(...reports.map((r) => Number(r.total)), 1);
    $("#page").innerHTML = `${pageHead("Relatórios", "Visualize para onde estão indo os recursos.")}<div class="card"><div class="card-head"><h3>Despesas por categoria</h3><span class="eyebrow">TOTAL ${money(reports.reduce((s, r) => s + Number(r.total), 0))}</span></div><div class="chart">${reports.map((r) => `<div class="bar-wrap"><div class="bar" style="height:${Math.max(5, Number(r.total) / max * 100)}%" title="${money(r.total, r.currency)}"></div><small>${h(labels[r.category] || r.category)}</small></div>`).join("") || '<div class="empty">Sem dados para exibir.</div>'}</div></div>`;
  } catch (error) { $("#page").innerHTML = pageHead("Relatórios", error.message); }
}

async function renderPolicies() {
  $("#page").innerHTML = `${pageHead("Políticas", "Limites aplicados às despesas da empresa.")}<div class="card"><div class="skeleton"></div></div>`;
  try {
    const policies = demoMode ? [
      { category:"meals", country_code:"BR", currency:"BRL", max_amount:"150.00" },
      { category:"lodging", country_code:"BR", currency:"BRL", max_amount:"900.00" },
      { category:"transport", country_code:"BR", currency:"BRL", max_amount:"200.00" },
    ] : await api("/policies");
    $("#page").innerHTML = `${pageHead("Políticas", "Limites aplicados às despesas da empresa.")}<div class="table-card"><table class="data-table"><thead><tr><th>CATEGORIA</th><th>PAÍS</th><th>MOEDA</th><th>LIMITE</th></tr></thead><tbody>${policies.map((p) => `<tr><td><strong>${h(labels[p.category] || p.category)}</strong></td><td>${p.country_code}</td><td>${p.currency}</td><td>${money(p.max_amount, p.currency)}</td></tr>`).join("") || '<tr><td colspan="4" class="empty">Nenhuma política configurada.</td></tr>'}</tbody></table></div>`;
  } catch (error) { toast(error.message, true); }
}

async function renderUsers() {
  $("#page").innerHTML = `${pageHead("Equipe", "Gerencie colaboradores e aprovadores.")}<div class="card"><div class="skeleton"></div></div>`;
  try {
    const users = demoMode ? [
      { email:"admin@acme.com.br", role:"admin", is_active:true },
      { email:"marina@acme.com.br", role:"approver", is_active:true },
      { email:"carlos@acme.com.br", role:"employee", is_active:true },
      { email:"ana@acme.com.br", role:"employee", is_active:true },
    ] : await api("/users");
    $("#page").innerHTML = `${pageHead("Equipe", "Gerencie colaboradores e aprovadores.")}<div class="table-card"><table class="data-table"><thead><tr><th>USUÁRIO</th><th>FUNÇÃO</th><th>STATUS</th></tr></thead><tbody>${users.map((u) => `<tr><td><strong>${h(u.email)}</strong></td><td>${{admin:"Administrador",approver:"Aprovador",employee:"Colaborador"}[u.role]}</td><td><span class="status ${u.is_active ? "approved" : "rejected"}">${u.is_active ? "Ativo" : "Inativo"}</span></td></tr>`).join("")}</tbody></table></div>`;
  } catch (error) { toast(error.message, true); }
}

async function expenseAction(id, action) {
  if (demoMode) {
    const expense = state.expenses.find((item) => item.id === id);
    if (expense) expense.status = action === "approve" ? "approved" : action === "reject" ? "rejected" : "submitted";
    toast("Demonstração atualizada — nenhum dado real foi alterado.");
    loadExpenses(); navigate(state.page); return;
  }
  try { await api(`/expenses/${id}/${action}`, { method: "POST", body: action === "submit" ? undefined : JSON.stringify({ comment: action === "approve" ? "Aprovado pela interface" : "Rejeitado pela interface" }) }); toast(action === "approve" ? "Despesa aprovada!" : action === "reject" ? "Despesa rejeitada." : "Despesa enviada para aprovação!"); await loadExpenses(); navigate(state.page); }
  catch (error) { toast(error.message, true); }
}

function bindCommon() {
  $$(".new-expense").forEach((button) => button.onclick = () => { $("#exp-date").valueAsDate = new Date(); $("#expense-modal").showModal(); });
  $$('[data-go]').forEach((button) => button.onclick = () => navigate(button.dataset.go));
}

function navigate(page) {
  state.page = page;
  $$("#nav button").forEach((button) => button.classList.toggle("active", button.dataset.page === page));
  $(".sidebar").classList.remove("open");
  ({ dashboard: renderDashboard, expenses: renderExpenses, approvals: renderApprovals, reports: renderReports, policies: renderPolicies, users: renderUsers }[page] || renderDashboard)();
}

$("#login-form").onsubmit = async (event) => {
  event.preventDefault();
  const body = new URLSearchParams({ username: $("#login-email").value, password: $("#login-password").value });
  try {
    const response = await fetch("/api/v1/auth/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
    if (!response.ok) throw new Error("E-mail ou senha incorretos.");
    saveTokens(await response.json()); await enterApp();
  } catch (error) { toast(error.message, true); }
};

$("#register-form").onsubmit = async (event) => {
  event.preventDefault();
  try {
    const data = await api("/auth/register", { method: "POST", body: JSON.stringify({ organization_name: $("#register-company").value, email: $("#register-email").value, password: $("#register-password").value, country_code: "BR" }) });
    saveTokens(data); toast("Ambiente criado com sucesso!"); await enterApp();
  } catch (error) { toast(error.message, true); }
};

$("#expense-form").onsubmit = async (event) => {
  event.preventDefault();
  const payload = { category: $("#exp-category").value, amount: $("#exp-amount").value, currency: "BRL", expense_date: $("#exp-date").value, merchant_tax_id: $("#exp-cnpj").value || null, invoice_key: $("#exp-key").value || null, country_code: "BR", cost_center: $("#exp-cost").value || null, description: $("#exp-description").value || null };
  try { await api("/expenses", { method: "POST", body: JSON.stringify(payload) }); $("#expense-modal").close(); event.target.reset(); toast("Despesa salva com sucesso!"); await loadExpenses(); navigate("expenses"); }
  catch (error) { toast(error.message, true); }
};

$("#show-register").onclick = () => { $("#login-form").classList.add("hidden"); $("#show-register").classList.add("hidden"); $(".divider").classList.add("hidden"); $("#register-form").classList.remove("hidden"); $(".auth-heading h2").textContent = "Crie seu ambiente"; };
$("#back-login").onclick = () => { $("#login-form").classList.remove("hidden"); $("#show-register").classList.remove("hidden"); $(".divider").classList.remove("hidden"); $("#register-form").classList.add("hidden"); $(".auth-heading h2").textContent = "Acesse sua conta"; };
$$('.close-modal').forEach((button) => button.onclick = () => $("#expense-modal").close());
$("#logout").onclick = logout;
$("#menu-toggle").onclick = () => $(".sidebar").classList.toggle("open");
$$("#nav button[data-page]").forEach((button) => button.onclick = () => navigate(button.dataset.page));
$("#global-search").oninput = (event) => { if (state.page !== "expenses") navigate("expenses"); const value = event.target.value.toLowerCase(); $$(".data-table tbody tr").forEach((row) => row.style.display = row.textContent.toLowerCase().includes(value) ? "" : "none"); };

if (demoMode || localStorage.getItem("access_token")) enterApp();
