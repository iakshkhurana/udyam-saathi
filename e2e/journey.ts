import { expect, type Page } from "@playwright/test";

const API = "http://localhost:8000/api";
const OCR_TIMEOUT = 90_000;

export async function chip(page: Page, label: string) {
  const button = page.getByRole("button", { name: label, exact: true }).last();
  await expect(button).toBeEnabled();
  await button.click();
}

export async function startAdvisor(page: Page, language: "en" | "hi") {
  await page.goto("/");
  await page.getByRole("button", { name: language === "en" ? "Start in English" : "हिंदी में शुरू करें" }).first().click();
  await expect(page).toHaveURL(/\/advisor/);
}

export async function kiranaConversation(page: Page, hindi = false) {
  const L = hindi
    ? ["किराना / दुकान", "1–2", "1", "लखनऊ", "मोबाइल हॉटस्पॉट", "छोड़ें", "आप ही सुझाइए", "GSTIN नहीं है"]
    : ["Kirana / shop", "1–2", "1", "Lucknow", "Mobile hotspot", "Skip", "Suggest for me", "No GSTIN"];
  await chip(page, L[0]);
  await chip(page, L[1]);
  await chip(page, L[2]);
  await page.locator("#msg").fill("Lucknow");
  await page.getByRole("button", { name: hindi ? "भेजें" : "Send" }).click();
  for (const label of L.slice(4)) await chip(page, label);
}

export async function openQuote(page: Page) {
  await page.getByRole("button", { name: /See quote|कोटेशन देखें/ }).first().click();
  await expect(page).toHaveURL(/\/quote\//);
  await expect(page.getByRole("switch").first()).toBeVisible();
}

export async function acceptAndConsent(page: Page): Promise<string> {
  await page.getByRole("button", { name: "Accept & continue" }).click();
  await expect(page).toHaveURL(/\/consent\//);
  const orderId = page.url().split("/consent/")[1].split(/[?#]/)[0];
  await page.getByText("I agree to KYC verification").click();
  await page.getByRole("button", { name: "I agree & continue" }).click();
  await expect(page).toHaveURL(/\/kyc\//);
  return orderId;
}

export async function loadSample(page: Page, applicant: string) {
  const select = page.locator("#sample");
  await expect(select).toBeEnabled({ timeout: OCR_TIMEOUT });
  await select.selectOption(applicant);
  await expect(page.locator("#sample:not([disabled])")).toBeVisible({ timeout: OCR_TIMEOUT });
}

export async function verifyKyc(page: Page) {
  await page.getByRole("button", { name: "Check all documents" }).click();
}

export async function esignAndTrack(page: Page) {
  await page.getByRole("button", { name: "e-Sign with Aadhaar OTP" }).click();
  await page.locator("#otp").fill("123456");
  await page.getByRole("button", { name: "Confirm" }).click();
  await expect(page).toHaveURL(/\/track\//, { timeout: 30_000 });
}

export async function apiOrder(page: Page, sample?: string): Promise<string> {
  const quote = await (await page.request.post(`${API}/quotes`, {
    data: { profile: { segment: "micro", employees: 3, needs: ["cctv", "pos"], current_spend: 1500, city: "Lucknow" } },
  })).json();
  const order = await (await page.request.post(`${API}/quotes/${quote.id}/accept`)).json();
  await page.request.post(`${API}/consents`, { data: { order_id: order.id, kyc: true, language: "en" } });
  if (sample) {
    await page.request.post(`${API}/kyc/${order.id}/load-sample/${sample}`, { timeout: OCR_TIMEOUT });
    await page.request.post(`${API}/kyc/${order.id}/verify`);
  }
  return order.id;
}
