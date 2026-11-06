import { expect, test, type Page } from "@playwright/test";

import { chip, esignAndTrack, loadSample, openQuote, startAdvisor, verifyKyc } from "./journey";

const OUT = "../docs/screenshots";

async function shot(page: Page, name: string, fullPage = true) {
  if (fullPage) await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage, animations: "disabled" });
}

test.describe.configure({ mode: "serial" });

test("capture the demo journey", async ({ page }) => {
  test.setTimeout(300_000);

  await page.goto("/");
  await expect(page.getByRole("button", { name: "Start in English" }).first()).toBeVisible();
  await shot(page, "01_landing", false);

  await startAdvisor(page, "hi");
  await chip(page, "किराना / दुकान");
  await chip(page, "1–2");
  await expect(page.getByRole("button", { name: "1", exact: true }).last()).toBeVisible();
  await shot(page, "02_advisor_hindi", false);

  await chip(page, "1");
  await page.locator("#msg").fill("Lucknow");
  await page.getByRole("button", { name: "भेजें" }).click();
  for (const label of ["मोबाइल हॉटस्पॉट", "छोड़ें", "आप ही सुझाइए", "GSTIN नहीं है"]) await chip(page, label);
  await expect(page.getByText(/Dukaan Digital/).first()).toBeVisible();
  await shot(page, "03_bundle_why", false);

  await openQuote(page);
  await page.getByRole("group", { name: /Language|भाषा/ }).first().getByRole("button", { name: "EN" }).click();
  await page.getByRole("switch", { name: "Cloud CCTV" }).click();
  await expect(page.getByText(/2,893/).first()).toBeVisible();
  await shot(page, "04_quote_toggles");

  await page.getByRole("button", { name: "Accept & continue" }).click();
  await expect(page).toHaveURL(/\/consent\//);
  await page.getByText("I agree to KYC verification").click();
  await shot(page, "05_consent");
  await page.getByRole("button", { name: "I agree & continue" }).click();
  await expect(page).toHaveURL(/\/kyc\//);
  const orderId = page.url().split("/kyc/")[1];

  await loadSample(page, "K01");
  await verifyKyc(page);
  await expect(page.getByText(/Cancelled/).first()).toBeVisible({ timeout: 30_000 });
  await shot(page, "06_kyc_error_K01");

  await loadSample(page, "K03");
  await verifyKyc(page);
  await expect(page.getByText("All checks passed")).toBeVisible({ timeout: 30_000 });
  await shot(page, "07_kyc_pass_K03");

  await esignAndTrack(page);
  await expect(page.getByText(/KYC verified/i).first()).toBeVisible();
  await shot(page, "08_tracker");

  await page.goto(`/track/${orderId}?demo=1`);
  await page.getByRole("button", { name: /Advance to next stage/ }).click();
  await page.getByRole("button", { name: /Simulate delay/ }).click();
  await expect(page.getByText(/credit/i).first()).toBeVisible();
  await shot(page, "09_tracker_delay");

  await startAdvisor(page, "en");
  await chip(page, "Restaurant chain");
  await page.locator("#msg").fill("Please call me back");
  await page.getByRole("button", { name: "Send" }).click();
  await page.goto("/backoffice");
  await page.locator("#pin").fill("2026");
  await page.getByRole("button", { name: "Unlock" }).click();
  await page.getByRole("button", { name: "Advisor leads" }).click();
  await expect(page.getByText(/callback/i).first()).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 800 });
  await shot(page, "10_backoffice", false);
});
