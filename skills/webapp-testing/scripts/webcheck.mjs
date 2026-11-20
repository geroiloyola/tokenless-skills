#!/usr/bin/env node
/**
 * webcheck.mjs — verificacion de UI en navegador real para agentes.
 *
 * Uso:
 *   node webcheck.mjs <url> [--out dir] [--width 1440] [--wait 800] [--full]
 *
 * Salida: JSON por stdout + screenshot PNG en <out>/.
 * Exit: 0 limpio · 1 defectos · 2 sin Playwright.
 *
 * Requiere Playwright accesible desde el cwd:
 *   npm i -D playwright && npx playwright install chromium
 * a11y avanzada via axe-core (CDN); si no hay red o el sitio bloquea CDN,
 * cae a los checks basicos integrados (report.axe = false).
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const argv = process.argv.slice(2);
const url = argv.find((a) => !a.startsWith("--"));
if (!url) {
  console.error("usage: webcheck.mjs <url> [--out dir] [--width 1440] [--wait 800] [--full]");
  process.exit(2);
}
const flag = (name, def) => {
  const i = argv.indexOf(name);
  return i > -1 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : def;
};
const outDir = flag("--out", ".vibe/artifacts");
const width = Number(flag("--width", 1440));
const waitMs = Number(flag("--wait", 800));
const fullPage = argv.includes("--full");

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch {
  try {
    ({ chromium } = await import("playwright-core"));
  } catch {
    console.error("Playwright no disponible. Instala: npm i -D playwright && npx playwright install chromium");
    process.exit(2);
  }
}

mkdirSync(outDir, { recursive: true });
const report = { url, viewport: width, console: [], warnings: [], network: [], a11y: [], axe: null, layout: [], screenshot: null };
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height: 900 } });

const basicA11y = (p) =>
  p.evaluate(() => {
    const issues = [];
    document.querySelectorAll("img:not([alt])").forEach((el) =>
      issues.push(`img sin alt: ${el.getAttribute("src")?.slice(0, 120) ?? "?"}`));
    document.querySelectorAll("button, a[href], [role=button]").forEach((el) => {
      const name = (el.getAttribute("aria-label") || el.textContent || "").trim();
      if (!name && !el.querySelector("img[alt]:not([alt=''])"))
        issues.push(`control sin nombre accesible: <${el.tagName.toLowerCase()}> ${el.outerHTML.slice(0, 120)}`);
    });
    document.querySelectorAll("input:not([type=hidden]), select, textarea").forEach((el) => {
      const id = el.getAttribute("id");
      const strongLabel =
        el.getAttribute("aria-label") ||
        el.getAttribute("aria-labelledby") ||
        (id && document.querySelector(`label[for="${id}"]`));
      const placeholder = el.getAttribute("placeholder");
      if (!strongLabel) {
        issues.push(
          placeholder
            ? `campo sin label real (solo placeholder): <${el.tagName.toLowerCase()} name="${el.getAttribute("name") ?? ""}">`
            : `campo sin label: <${el.tagName.toLowerCase()} name="${el.getAttribute("name") ?? ""}">`,
        );
      }
    });
    return [...new Set(issues)].slice(0, 25);
  });

page.on("console", (m) => {
  if (m.type() === "error") report.console.push(`[error] ${m.text().slice(0, 300)}`);
  else if (m.type() === "warning") report.warnings.push(`[warning] ${m.text().slice(0, 300)}`);
});
page.on("pageerror", (e) => report.console.push(`[pageerror] ${String(e.message).slice(0, 300)}`));
page.on("requestfailed", (r) => report.network.push(`[failed] ${r.url().slice(0, 200)} — ${r.failure()?.errorText ?? ""}`));
page.on("response", (r) => {
  if (r.status() >= 400) report.network.push(`[${r.status()}] ${r.url().slice(0, 200)}`);
});

try {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(waitMs);

  // axe-core se inyecta DESPUES de navegar (addScriptTag), nunca antes:
  // un script cargado en about:blank muere con la navegacion.
  const axeLoaded = await page
    .addScriptTag({ url: "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js" })
    .then(() => page.evaluate(() => typeof window.axe === "object"))
    .catch(() => false);

  if (axeLoaded) {
    report.axe = true;
    report.a11y = await page
      .evaluate(async () => {
        const r = await window.axe.run();
        return r.violations.map((v) => `axe:${v.id} ${v.help} (${v.nodes.length} nodes)`);
      })
      .catch(async () => {
        report.axe = false;
        return basicA11y(page);
      });
  } else {
    report.axe = false;
    report.a11y = await basicA11y(page);
  }

  report.layout = await page.evaluate(() => {
    const issues = [];
    if (document.documentElement.scrollWidth > window.innerWidth + 1)
      issues.push(`overflow horizontal: ${document.documentElement.scrollWidth}px > ${window.innerWidth}px`);
    const h1 = document.querySelectorAll("h1").length;
    if (h1 === 0) issues.push("sin <h1>");
    if (h1 > 1) issues.push(`${h1} elementos <h1>`);
    const empty = document.body.innerText.replace(/\s+/g, " ").trim();
    if (empty.length < 20) issues.push("pagina practicamente vacia (posible crash de render)");
    return issues;
  });

  const name = `webcheck-${width}${fullPage ? "-full" : ""}-${Date.now()}.png`;
  const file = join(outDir, name);
  await page.screenshot({ path: file, fullPage });

  const mobile = await browser.newPage({ viewport: { width: 375, height: 812 } });
  await mobile.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
  const overflow375 = await mobile.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  if (overflow375) report.layout.push("overflow horizontal a 375px (movil)");
  await mobile.close();

  report.screenshot = file;
} catch (e) {
  report.network.push(`[fatal] ${String(e.message).slice(0, 300)}`);
} finally {
  await browser.close();
}

const defects =
  report.console.length + report.network.length + report.a11y.length + report.layout.length;
writeFileSync(join(outDir, "webcheck.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ ...report, defects, verdict: defects ? "FAIL" : "PASS" }, null, 2));
process.exit(defects ? 1 : 0);
