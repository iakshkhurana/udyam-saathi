import { expect, test } from "@playwright/test";

import { acceptAndConsent, apiOrder, esignAndTrack, kiranaConversation, loadSample, openQuote, startAdvisor, verifyKyc } from "./journey";

test("guided journey: landing → advisor → quote → consent → KYC → tracker, without an API key", async ({ page }) => {
  await startAdvisor(page, "en");
  await expect(page.getByText(/Guided mode/i).first()).toBeVisible();
  await kiranaConversation(page);
  await expect(page.getByText(/Dukaan Digital/).first()).toBeVisible();

  await openQuote(page);
  await expect(page.getByText(/2,495/).first()).toBeVisible();
  await page.getByRole("switch", { name: "Cloud CCTV" }).click();
  await expect(page.getByText(/2,893/).first()).toBeVisible();

  const orderId = await acceptAndConsent(page);
  await loadSample(page, "K03");
  await verifyKyc(page);
  await expect(page.getByText("All checks passed")).toBeVisible({ timeout: 30_000 });
  await esignAndTrack(page);
  await expect(page).toHaveURL(new RegExp(`/track/${orderId}`));
  await expect(page.getByText(/KYC verified/i).first()).toBeVisible();
});

test("KYC is refused before consent", async ({ request }) => {
  const quote = await (await request.post("http://localhost:8000/api/quotes", { data: { profile: { needs: ["cctv"] } } })).json();
  const order = await (await request.post(`http://localhost:8000/api/quotes/${quote.id}/accept`)).json();
  const res = await request.post(`http://localhost:8000/api/kyc/${order.id}/load-sample/K03`);
  expect(res.status()).toBe(403);
});

test("EN/HI toggle works on every screen", async ({ page }) => {
  const orderId = await apiOrder(page);
  const quote = await (await page.request.post("http://localhost:8000/api/quotes", { data: { profile: { needs: ["pos"] } } })).json();
  const routes = ["/", "/advisor", `/quote/${quote.id}`, `/consent/${orderId}`, `/kyc/${orderId}`, `/track/${orderId}`,
                  "/privacy", "/backoffice"];
  for (const path of routes) {
    await page.goto(path);
    const group = page.getByRole("group", { name: /Language|भाषा/ }).first();
    await group.getByRole("button", { name: "हिं" }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "hi");
    await expect(group.getByRole("button", { name: "हिं" })).toHaveAttribute("aria-pressed", "true");
    await group.getByRole("button", { name: "EN" }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  }
});
