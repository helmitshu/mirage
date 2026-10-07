/* Mirage content script: ambient ghost scoring on job pages.
 * Runs on LinkedIn Jobs and Indeed. Reads the posting from the page DOM
 * (your own browser, so no bot blocking), scores it via the Mirage API,
 * and stamps a small badge on the page. No clicks needed.
 *
 * Setup: replace API_BASE with the deployed scoring API URL, and put the
 * same origin in manifest.json host_permissions.
 */
"use strict";

const API_BASE = "https://blissful-imagination-production-ad37.up.railway.app"; // e.g. https://mirage-api-xxxx.up.railway.app
const MIN_TEXT = 50;
const DEBOUNCE_MS = 1200;

const SELECTORS = [
  // LinkedIn
  "#job-details",
  ".jobs-description__content",
  ".jobs-description-content__text",
  // Indeed
  "#jobDescriptionText",
  ".jobsearch-jobDescriptionText",
  "#jobsearch-JobComponent",
];

const VERDICT_COLORS = {
  "Legitimate": "#047857",
  "Caution": "#b45309",
  "Suspicious": "#c2410c",
  "Likely ghost": "#b91c1c",
};

const scoredUrls = new Set();
let debounceTimer = null;
let badgeEl = null;

function extractPostingText() {
  for (const sel of SELECTORS) {
    const el = document.querySelector(sel);
    if (el) {
      const text = (el.innerText || "").trim();
      if (text.length >= MIN_TEXT) return text;
    }
  }
  return "";
}

function verdictColor(verdict) {
  return VERDICT_COLORS[verdict] || "#374151";
}

function showBadge(score, verdict, topSignal) {
  removeBadge();
  badgeEl = document.createElement("div");
  badgeEl.id = "mirage-badge";
  const color = verdictColor(verdict);
  badgeEl.innerHTML =
    '<div style="display:flex;align-items:center;gap:10px;">' +
    '<div style="font-size:26px;font-weight:800;color:' + color + '">' + score + '</div>' +
    '<div>' +
    '<div style="font-weight:700;font-size:13px;color:#111827">Mirage: ' + verdict + '</div>' +
    (topSignal
      ? '<div style="font-size:12px;color:#6b7280;max-width:220px">' + topSignal + '</div>'
      : "") +
    "</div></div>";
  badgeEl.setAttribute(
    "style",
    "position:fixed;right:18px;bottom:18px;z-index:2147483647;" +
      "background:#fff;border:1px solid #e5e7eb;border-radius:14px;" +
      "padding:12px 16px;box-shadow:0 4px 16px rgba(16,24,40,.14);" +
      "font-family:system-ui,sans-serif;cursor:default;"
  );
  badgeEl.title = "Scored by Mirage. Click the Mirage demo for the full report.";
  document.documentElement.appendChild(badgeEl);
}

function showUnavailable() {
  removeBadge();
  badgeEl = document.createElement("div");
  badgeEl.id = "mirage-badge";
  badgeEl.textContent = "Mirage: scoring unavailable right now";
  badgeEl.setAttribute(
    "style",
    "position:fixed;right:18px;bottom:18px;z-index:2147483647;" +
      "background:#fff;border:1px solid #e5e7eb;border-radius:14px;" +
      "padding:10px 14px;box-shadow:0 4px 16px rgba(16,24,40,.14);" +
      "font-family:system-ui,sans-serif;font-size:12px;color:#6b7280;"
  );
  document.documentElement.appendChild(badgeEl);
}

function removeBadge() {
  if (badgeEl && badgeEl.parentNode) badgeEl.parentNode.removeChild(badgeEl);
  badgeEl = null;
}

async function scoreCurrentPage() {
  if (API_BASE.startsWith("__MIRAGE")) return; // not configured yet
  const url = location.href.split("?")[0];
  if (scoredUrls.has(url)) return;
  const text = extractPostingText();
  if (!text) return;
  scoredUrls.add(url);
  let resp;
  try {
    resp = await fetch(API_BASE + "/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.slice(0, 20000), url }),
    });
  } catch (e) {
    return; // API unreachable: stay silent, never break the page
  }
  if (resp.status === 429) {
    showUnavailable();
    return;
  }
  if (!resp.ok) return;
  let data;
  try {
    data = await resp.json();
  } catch (e) {
    return;
  }
  const top = data.signals && data.signals.length ? data.signals[0].title : "";
  showBadge(data.score, data.verdict, top);
}

function schedule() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(scoreCurrentPage, DEBOUNCE_MS);
}

const observer = new MutationObserver(schedule);
observer.observe(document.documentElement, {
  childList: true,
  subtree: true,
});
schedule();
