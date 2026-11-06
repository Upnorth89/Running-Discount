// Fox Pro checkout (Nov 7, 2026, piece 1). The site's lead-in screen posts {k, side, lang}; we answer {url} = a Stripe Checkout page.
// k = the member's own key (subscribers.token, the ?k= of their links): only members can pay (Pro is an upgrade of a member).
// Price: Founding ($36/year CAD) while fewer than 100 founding spots are paid, else regular ($45/year). Looked up by Stripe lookup_key,
// so no price id lives in the code. USD: the same numbers (US$36 / US$45, Bastien Oct 31).
// OFF switch: PRO_CHECKOUT secret must be "test" (sandbox key only) or "live"; anything else answers "closed".
const KEY = Deno.env.get("STRIPE_SECRET_KEY") ?? "";
const OPEN = Deno.env.get("PRO_CHECKOUT") ?? "";
const SB = Deno.env.get("SUPABASE_URL") ?? "";
const SR = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const SITE = "https://thegearfox.com";
const API = "https://api.stripe.com/v1";
const FOUNDING = 100;

const live = /^(sk|rk)_live_/.test(KEY);
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, apikey, authorization",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const out = (o: unknown, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

async function stripe(path: string, body?: URLSearchParams) {
  const r = await fetch(API + path, {
    method: body ? "POST" : "GET",
    headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  return { status: r.status, j: await r.json().catch(() => ({})) };
}

async function db(path: string, body?: unknown) {
  const r = await fetch(`${SB}/rest/v1/${path}`, {
    method: body ? "POST" : "GET",
    headers: { apikey: SR, Authorization: `Bearer ${SR}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: r.status, j: await r.json().catch(() => null) };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });
  if (req.method !== "POST") return out({ error: "method" }, 405);
  if (!(OPEN === "live" && live) && !(OPEN === "test" && /^(sk|rk)_test_/.test(KEY))) return out({ error: "closed" }, 403);
  let b: { k?: string; side?: string; lang?: string } = {};
  try { b = await req.json(); } catch { return out({ error: "bad_json" }, 400); }
  const k = String(b.k || "");
  if (!/^[0-9a-f-]{36}$/i.test(k)) return out({ error: "not_member" }, 400);
  const side = b.side === "us" ? "us" : "ca";
  const cur = side === "us" ? "usd" : "cad";
  const lang = b.lang === "fr" ? "fr" : "en";

  const s = await db(`subscribers?token=eq.${k}&unsubscribed_at=is.null&select=id,email`);
  const sub = Array.isArray(s.j) && s.j[0];
  if (!sub) return out({ error: "not_member" }, 404);
  const m = await db(`pro_members?subscriber_id=eq.${sub.id}&select=status,refunded_at,stripe_customer`);
  const mem = Array.isArray(m.j) && m.j[0];
  if (mem && !mem.refunded_at && ["active", "trialing", "past_due"].includes(mem.status)) return out({ error: "already_pro" }, 409);

  const t = await db("rpc/pro_founding_taken", { p_live: live });
  const founding = typeof t.j === "number" && t.j < FOUNDING;
  const look = `fox_pro_${founding ? "founding" : "regular"}_${cur}`;
  const p = await stripe(`/prices?active=true&lookup_keys[]=${look}&limit=1`);
  const price = p.j?.data?.[0];
  if (!price) return out({ error: side === "us" ? "not_yet" : "no_price" }, 503);

  const q = new URLSearchParams({
    mode: "subscription",
    "line_items[0][price]": price.id,
    "line_items[0][quantity]": "1",
    client_reference_id: sub.id,
    "metadata[plan]": founding ? "founding" : "regular",
    "metadata[side]": side,
    "subscription_data[metadata][subscriber]": sub.id,
    "subscription_data[metadata][plan]": founding ? "founding" : "regular",
    locale: lang === "fr" ? "fr-CA" : "en",
    allow_promotion_codes: "false",
    billing_address_collection: "auto",
    success_url: `${SITE}/?k=${k}&pro=welcome&session={CHECKOUT_SESSION_ID}`,
    cancel_url: `${SITE}/?k=${k}&pro=checkout`,
  });
  if (mem?.stripe_customer) q.set("customer", mem.stripe_customer);
  else q.set("customer_email", sub.email);
  const c = await stripe("/checkout/sessions", q);
  if (c.status !== 200) return out({ error: "stripe", code: c.j?.error?.code || `http ${c.status}` }, 502);
  console.log(`checkout ${look} test=${!live}`);              // no address, no id
  return out({ url: c.j.url, plan: founding ? "founding" : "regular", amount: price.unit_amount, currency: cur });
});
