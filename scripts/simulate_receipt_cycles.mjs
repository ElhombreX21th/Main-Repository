import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const baseUrl = process.env.BASE_URL || "http://127.0.0.1:8000";
const cycles = Number.parseInt(process.env.CYCLES || "75", 10);
const headless = process.env.HEADLESS === "1";
const slowMo = Number.parseInt(process.env.SLOW_MO_MS || "15", 10);
const password = "Senha-forte-123";
const runId = Date.now();
let browser;
let page;

function invoiceKey(index) {
  return `1234567890123456789012345678901234567890${String(index).padStart(4, "0")}`;
}

function amountText(index) {
  const reais = 50 + index;
  const cents = String(index % 100).padStart(2, "0");
  return `${reais},${cents}`;
}

function receiptText(index) {
  return [
    "CNPJ 12.345.678/0001-90",
    "Emissao 20/08/2026",
    "CIDADE: Sao Paulo UF: SP",
    `TOTAL R$ ${amountText(index)}`,
    `Chave ${invoiceKey(index)}`,
  ].join(" ");
}

async function humanClick(page, locator) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  if (!box) {
    throw new Error("Element is not visible for click");
  }
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
  await locator.click();
}

async function humanFill(page, locator, value) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 8 });
  }
  await locator.fill(String(value));
}

async function humanSelect(page, locator, value) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 8 });
  }
  await locator.selectOption(value);
}

async function clickFirstAction(page, action) {
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    const locator = page.locator(`[data-expense-action="${action}"]`).first();
    try {
      await locator.waitFor({ state: "visible", timeout: 5000 });
      const expenseId = await locator.getAttribute("data-expense-id");
      await humanClick(page, locator);
      return expenseId;
    } catch (error) {
      lastError = error;
      await page.waitForTimeout(150);
    }
  }
  throw lastError;
}

async function installVisibleCursor(page) {
  await page.evaluate(() => {
    if (document.querySelector("#simulation-cursor")) return;
    const cursor = document.createElement("div");
    cursor.id = "simulation-cursor";
    cursor.style.cssText = [
      "position: fixed",
      "left: 0",
      "top: 0",
      "width: 16px",
      "height: 16px",
      "border: 2px solid #ef5542",
      "border-radius: 50%",
      "background: rgba(239, 85, 66, 0.16)",
      "box-shadow: 0 0 0 6px rgba(239, 85, 66, 0.10)",
      "pointer-events: none",
      "z-index: 2147483647",
      "transform: translate(-30px, -30px)",
      "transition: transform 80ms linear",
    ].join(";");
    document.body.appendChild(cursor);
    document.addEventListener("mousemove", (event) => {
      cursor.style.transform = `translate(${event.clientX - 8}px, ${event.clientY - 8}px)`;
    });
  });
}

async function waitForDashboard(page) {
  await page.waitForFunction(() => {
    const dashboard = document.querySelector("#dashboard-screen:not(.hidden)");
    const feedback = document.querySelector("#auth-feedback")?.textContent?.trim();
    return dashboard || (feedback && feedback !== "Conectando...");
  });
  const dashboardVisible = await page.locator("#dashboard-screen:not(.hidden)").count();
  const feedback = await page.locator("#auth-feedback").innerText();
  if (!dashboardVisible && feedback.trim()) {
    throw new Error(`Authentication failed: ${feedback.trim()}`);
  }
  await page.waitForFunction(() => window.__reembolsabrReady === true);
}

async function login(page, email) {
  await humanClick(page, page.locator('[data-auth-mode="login"]'));
  await humanFill(page, page.locator('#auth-form input[name="email"]'), email);
  await humanFill(page, page.locator('#auth-form input[name="password"]'), password);
  await humanClick(page, page.locator('#auth-form button[type="submit"]'));
  await waitForDashboard(page);
}

async function logout(page) {
  await humanClick(page, page.locator("#logout-button"));
  await page.locator("#auth-screen:not(.hidden)").waitFor({ state: "visible" });
}

async function createPolicy(page) {
  console.log("creating policy");
  await humanClick(page, page.locator('[data-view="policies"]'));
  await humanFill(page, page.locator('#policy-form input[name="category"]'), "lunch");
  await humanFill(page, page.locator('#policy-form input[name="currency"]'), "BRL");
  await humanFill(page, page.locator('#policy-form input[name="max_amount"]'), "1000");
  await humanClick(page, page.locator('#policy-form button[type="submit"]'));
  await page.locator("#policies-list .policy-card").first().waitFor({ state: "visible" });
}

async function createUser(page, fullName, email, role) {
  console.log(`creating ${role}: ${email}`);
  await humanClick(page, page.locator("#team-nav"));
  await humanFill(page, page.locator('#user-form input[name="full_name"]'), fullName);
  await humanFill(page, page.locator('#user-form input[name="email"]'), email);
  await humanFill(page, page.locator('#user-form input[name="password"]'), password);
  await humanSelect(page, page.locator('#user-form select[name="role"]'), role);
  await humanClick(page, page.locator('#user-form button[type="submit"]'));
  await page.locator("#users-list .policy-card", { hasText: email }).waitFor({ state: "visible" });
}

async function createAndSubmitExpense(page, index) {
  await humanClick(page, page.locator("#list-new-expense"));
  await page.locator("#expense-dialog[open]").waitFor({ state: "visible" });
  await humanSelect(page, page.locator('#expense-form select[name="category"]'), "lunch");
  await humanFill(page, page.locator("#receipt-text"), receiptText(index));
  await humanClick(page, page.locator("#parse-receipt-button"));
  await page.waitForFunction(() => {
    const amount = document.querySelector('#expense-form input[name="amount"]');
    const date = document.querySelector('#expense-form input[name="expense_date"]');
    const invoice = document.querySelector('#expense-form input[name="invoice_key"]');
    return amount?.value && date?.value && invoice?.value;
  });
  await humanFill(page, page.locator('#expense-form textarea[name="description"]'), `Ciclo ${index}`);
  await humanClick(page, page.locator('#expense-form button[type="submit"]'));
  await page.waitForFunction(() => !document.querySelector("#expense-dialog")?.open);
  const expenseId = await clickFirstAction(page, "submit");
  await page.waitForFunction(
    (id) => !document.querySelector(`[data-expense-action="submit"][data-expense-id="${id}"]`),
    expenseId,
  );
}

async function reimburseOne(page) {
  const expenseId = await clickFirstAction(page, "approve");
  const reimburseButton = page.locator(`[data-expense-action="reimburse"][data-expense-id="${expenseId}"]`);
  await reimburseButton.waitFor({ state: "visible" });
  await humanClick(page, reimburseButton);
  await page.waitForFunction(
    (id) => !document.querySelector(`[data-expense-action="reimburse"][data-expense-id="${id}"]`),
    expenseId,
  );
}

async function main() {
  await mkdir("artifacts", { recursive: true });
  browser = await chromium.launch({ headless, slowMo });
  page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  page.setDefaultTimeout(15000);

  const adminEmail = `admin-${runId}@sim.example.com`;
  const employeeEmail = `employee-${runId}@sim.example.com`;
  const approverEmail = `approver-${runId}@sim.example.com`;
  const organization = `ReembolsaBR Sim ${runId}`;

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await installVisibleCursor(page);
  await humanClick(page, page.locator('[data-auth-mode="register"]'));
  await humanFill(page, page.locator('#auth-form input[name="full_name"]'), "Admin Simulacao");
  await humanFill(page, page.locator('#auth-form input[name="organization_name"]'), organization);
  await humanFill(page, page.locator('#auth-form input[name="email"]'), adminEmail);
  await humanFill(page, page.locator('#auth-form input[name="password"]'), password);
  await humanClick(page, page.locator('#auth-form button[type="submit"]'));
  await waitForDashboard(page);
  console.log(`registered admin: ${adminEmail}`);

  await createPolicy(page);
  await createUser(page, "Funcionario Simulacao", employeeEmail, "employee");
  await createUser(page, "Aprovador Simulacao", approverEmail, "approver");

  await logout(page);
  await login(page, employeeEmail);
  console.log(`logged as employee: ${employeeEmail}`);
  await humanClick(page, page.locator('[data-view="expenses"]'));
  for (let index = 1; index <= cycles; index += 1) {
    await createAndSubmitExpense(page, index);
    if (index % 10 === 0 || index === cycles) {
      console.log(`employee submitted ${index}/${cycles}`);
    }
  }

  await logout(page);
  await login(page, approverEmail);
  console.log(`logged as approver: ${approverEmail}`);
  await humanClick(page, page.locator('[data-view="expenses"]'));
  for (let index = 1; index <= cycles; index += 1) {
    await page.locator('[data-expense-action="approve"]').first().waitFor({ state: "visible" });
    await reimburseOne(page);
    if (index % 10 === 0 || index === cycles) {
      console.log(`approver reimbursed ${index}/${cycles}`);
    }
  }

  const reimbursedCount = await page.locator("#all-expenses .status-badge.reimbursed").count();
  const screenshotPath = `artifacts/simulation-${runId}.png`;
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await browser.close();
  browser = undefined;

  if (reimbursedCount !== cycles) {
    throw new Error(`Expected ${cycles} reimbursed expenses, found ${reimbursedCount}`);
  }

  console.log(
    JSON.stringify(
      {
        cycles,
        organization,
        employeeEmail,
        approverEmail,
        reimbursedCount,
        screenshotPath,
      },
      null,
      2,
    ),
  );
}

main().catch(async (error) => {
  if (page) {
    await page.screenshot({ path: `artifacts/simulation-error-${runId}.png`, fullPage: true }).catch(() => {});
  }
  if (browser) {
    await browser.close().catch(() => {});
  }
  console.error(error);
  process.exit(1);
});
