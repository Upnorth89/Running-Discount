// One-off setup helper (Nov 5, 2026). The stripe-setup workflow deploys it, calls it once, then deletes it.
// It never returns or logs the key: only "test"/"live" mode, "ok" or Stripe's error code.
// Actions: ?do=check   -> asks Stripe for the account balance (proves STRIPE_SECRET_KEY works)
//          ?do=portal  -> sets the customer portal (cancel at period end, no reason asked, no retention offer)
// Guard: the caller must send the SETUP_NONCE secret the workflow set a moment before (random per run).
const KEY = Deno.env.get("STRIPE_SECRET_KEY") ?? "";
const NONCE = Deno.env.get("SETUP_NONCE") ?? "";
const API = "https://api.stripe.com/v1";

function mode(): string {
  if (/^(sk|rk)_test_/.test(KEY)) return "test";
  if (/^(sk|rk)_live_/.test(KEY)) return "live";
  return KEY ? "unknown" : "missing";
}

async function stripe(path: string, body?: URLSearchParams) {
  const r = await fetch(API + path, {
    method: body ? "POST" : "GET",
    headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const j = await r.json().catch(() => ({}));
  return { status: r.status, j };
}

const PORTAL: Record<string, string> = {
  "business_profile[headline]": "The Gear Fox: manage your Fox Pro membership",
  "business_profile[privacy_policy_url]": "https://thegearfox.com/privacy.html",
  "business_profile[terms_of_service_url]": "https://thegearfox.com/terms.html",
  "default_return_url": "https://thegearfox.com/",
  "features[subscription_cancel][enabled]": "true",
  "features[subscription_cancel][mode]": "at_period_end",
  "features[subscription_cancel][proration_behavior]": "none",
  "features[subscription_cancel][cancellation_reason][enabled]": "false",
  // Stripe requires the reason list even when the question is switched off (it is never shown)
  "features[subscription_cancel][cancellation_reason][options][0]": "too_expensive",
  "features[subscription_cancel][cancellation_reason][options][1]": "unused",
  "features[subscription_cancel][cancellation_reason][options][2]": "missing_features",
  "features[subscription_cancel][cancellation_reason][options][3]": "other",
  "features[payment_method_update][enabled]": "true",
  "features[invoice_history][enabled]": "true",
};

Deno.serve(async (req) => {
  const out = (o: unknown, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "Content-Type": "application/json" } });
  if (!NONCE || req.headers.get("x-setup-nonce") !== NONCE) return out({ error: "forbidden" }, 403);
  const m = mode();
  if (m !== "test") return out({ mode: m, error: m === "live" ? "refusing: this helper only runs on the test (sandbox) key" : "no usable key" }, 400);
  const what = new URL(req.url).searchParams.get("do");
  if (what === "check") {
    const r = await stripe("/balance");
    return out({ mode: m, result: r.status === 200 ? "ok" : (r.j?.error?.code || r.j?.error?.type || `http ${r.status}`) });
  }
  if (what === "portal") {
    const list = await stripe("/billing_portal/configurations?is_default=true&limit=1");
    if (list.status !== 200) return out({ mode: m, step: "list", result: list.j?.error?.code || `http ${list.status}`, param: list.j?.error?.param, why: list.j?.error?.message });
    const cur = list.j?.data?.[0];
    const r = await stripe(cur ? `/billing_portal/configurations/${cur.id}` : "/billing_portal/configurations", new URLSearchParams(PORTAL));
    const c = r.j || {};
    return out({
      mode: m, result: r.status === 200 ? "ok" : (c?.error?.code || `http ${r.status}`), param: c?.error?.param, why: c?.error?.message,
      config: r.status === 200 ? {
        id: c.id, is_default: c.is_default, cancel: c.features?.subscription_cancel?.enabled,
        cancel_mode: c.features?.subscription_cancel?.mode, reason_asked: c.features?.subscription_cancel?.cancellation_reason?.enabled,
        card_update: c.features?.payment_method_update?.enabled, invoices: c.features?.invoice_history?.enabled,
      } : undefined,
    });
  }
  return out({ error: "unknown action" }, 400);
});
