const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto("http://localhost:8080/home", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  if (errors.length) {
    console.error("❌ Errors found:\n" + errors.join("\n---\n"));
    process.exit(1);
  } else {
    console.log("✅ Home loaded without JS errors");
  }

  await browser.close();
})();
