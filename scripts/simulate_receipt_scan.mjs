import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";

const baseUrl = process.env.BASE_URL || "http://localhost:8000";
const email = process.env.SIM_EMAIL || "admin.teste@reembolsabr.com";
const password = process.env.SIM_PASSWORD || "Senha-forte-123";
const slowMo = Number(process.env.SLOW_MO_MS || 400);
const headless = process.env.HEADLESS === "1";
const imagePath = "artifacts/recibo-nfce.png";

const receiptHtml = `<body style="margin:0;background:#fff"><div style="width:420px;padding:24px;font:15px 'Courier New',monospace;color:#000;line-height:1.35">
<div style="text-align:center;font-weight:bold;font-size:18px">RESTAURANTE SABOR DA SERRA LTDA</div>
<div style="text-align:center">CNPJ: 12.345.678/0001-95</div>
<div style="text-align:center">Av Paulista, 1000 - Sao Paulo - SP</div>
<hr>
<div style="text-align:center;font-weight:bold">DANFE NFC-e - Documento Auxiliar da Nota Fiscal de Consumidor Eletronica</div>
<hr>
<div>1 Prato executivo almoco ..... 48,90</div>
<div>1 Suco natural .............. 12,00</div>
<div>1 Cafe expresso .............  6,50</div>
<hr>
<div style="font-weight:bold;font-size:17px">VALOR TOTAL R$ 67,40</div>
<div>Forma de pagamento: Cartao de credito</div>
<hr>
<div>Data de emissao: 15/05/2026 12:30:45</div>
<div>Chave de acesso:</div>
<div>3526 0512 3456 7800 0195 6500 1000 0012 3410 0000 1234</div>
</div></body>`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const say = (m) => console.log(`>> ${m}`);

const browser = await chromium.launch({ headless, slowMo });
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
page.setDefaultTimeout(20000);
await mkdir("artifacts", { recursive: true });

say("Gerando imagem de um recibo NFC-e (como uma foto de recibo real)");
const shot = await browser.newPage({ viewport: { width: 480, height: 600 }, deviceScaleFactor: 2 });
await shot.setContent(receiptHtml);
await shot.screenshot({ path: imagePath, fullPage: true });
await shot.close();

say("Abrindo o sistema e fazendo login");
await page.goto(baseUrl, { waitUntil: "networkidle" });
await page.locator('[data-auth-mode="login"]').click();
await page.locator('#auth-form input[name="email"]').fill(email);
await page.locator('#auth-form input[name="password"]').fill(password);
await page.locator('#auth-form button[type="submit"]').click();
await page.waitForFunction(() => window.__reembolsabrReady === true);

say("Abrindo 'Nova despesa' e anexando a foto do recibo (sem digitar nada)");
await page.locator("#quick-new-expense").click();
await page.locator("#expense-dialog[open]").waitFor();
await page.locator("#receipt-gallery").setInputFiles(imagePath);

say("Aguardando o OCR ler o recibo e preencher o formulario...");
await page.waitForFunction(
  () => {
    const f = (n) => document.querySelector(`#expense-form [name="${n}"]`)?.value;
    return f("amount") && f("expense_date") && f("merchant_tax_id") && f("invoice_key");
  },
  null,
  { timeout: 180000 },
);
await sleep(2500);

const values = await page.evaluate(() =>
  Object.fromEntries(
    ["category", "amount", "expense_date", "expense_time", "merchant_city", "merchant_state", "merchant_tax_id", "invoice_key", "description"].map((n) => [
      n,
      document.querySelector(`#expense-form [name="${n}"]`)?.value,
    ]),
  ),
);
console.log("Campos preenchidos automaticamente:", values);

const checks = {
  valor: Number(String(values.amount).replace(",", ".")) === 67.4,
  data: values.expense_date === "2026-05-15",
  cnpj: String(values.merchant_tax_id).replace(/\D/g, "") === "12345678000195",
  chave: String(values.invoice_key).replace(/\D/g, "").length === 44,
};
console.log("Conferencia:", checks);
await page.screenshot({ path: "artifacts/scan-preenchido.png" });

say("Salvando a despesa");
await page.locator('#expense-form button[type="submit"]').click();
await page.waitForFunction(() => !document.querySelector("#expense-dialog")?.open);
await sleep(2000);
await page.screenshot({ path: "artifacts/scan-final.png" });
await browser.close();

if (!Object.values(checks).every(Boolean)) {
  console.error("FALHA: algum campo nao foi extraido corretamente");
  process.exit(1);
}
console.log("SUCESSO: recibo escaneado e despesa criada sem digitacao");
