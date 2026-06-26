#!/usr/bin/env node
const path = require("node:path");
const { pathToFileURL } = require("node:url");

function fail(message) {
  console.error(message);
  process.exit(1);
}

const [htmlPath, outputPath, chromePath] = process.argv.slice(2);
if (!htmlPath || !outputPath) {
  fail("Usage: node render_pdf_node.cjs <input.html> <output.pdf> [chromePath]");
}

let playwright;
try {
  playwright = require("playwright");
} catch (error) {
  fail(`Unable to require playwright. Set NODE_PATH or install dependencies. ${error.message}`);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function headerTemplate(title, docType) {
  return `
<div style="width:100%; padding:0 17mm; font-family:Arial, sans-serif; font-size:8.5pt; color:#8a96a3; display:flex; justify-content:space-between;">
  <span>${escapeHtml(String(title || "md2pdf").slice(0, 72))}</span>
  <span>${escapeHtml(String(docType || "").slice(0, 40))}</span>
</div>`;
}

function footerTemplate() {
  return `
<div style="width:100%; padding:0 17mm; font-family:Arial, sans-serif; font-size:8.5pt; color:#8a96a3; display:flex; justify-content:flex-end;">
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>`;
}

(async () => {
  const launchOptions = { headless: true };
  if (chromePath) {
    launchOptions.executablePath = chromePath;
  }

  const browser = await playwright.chromium.launch(launchOptions);
  try {
    const page = await browser.newPage({ viewport: { width: 1240, height: 1754 } });
    page.setDefaultTimeout(60000);
    await page.goto(pathToFileURL(path.resolve(htmlPath)).href, { waitUntil: "networkidle" });
    await page.emulateMedia({ media: "print" });
    const title = await page.title();
    const docType = await page.locator(".print-header span").nth(1).textContent().catch(() => "");
    await page.addStyleTag({
      content: ".print-header,.print-footer{display:none!important;}",
    });
    await page.pdf({
      path: path.resolve(outputPath),
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: true,
      headerTemplate: headerTemplate(title, docType),
      footerTemplate: footerTemplate(),
    });
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({ method: "node-playwright" }));
})().catch((error) => {
  fail(error && error.stack ? error.stack : String(error));
});
