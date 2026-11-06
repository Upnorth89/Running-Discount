// Stripe webhook for Fox Pro (Nov 5, 2026: first version).
// Stripe calls https://krwymmkauwqqxjxbvkyq.supabase.co/functions/v1/stripe-webhook (deployed with --no-verify-jwt: Stripe sends no
// Supabase login, so every request is checked against Stripe's own signature instead, with STRIPE_WEBHOOK_SECRET).
// Nov 7 (piece 1): a paid checkout records the member (pro_join: next Founding Fox number while #001-#100 last); subscription changes
// keep status / renewal date / "cancels at the end" current. Each event id once (pro_events). Next: the purchase email with the terms.
const SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";
const KEY = Deno.env.get("STRIPE_SECRET_KEY") ?? "";
const SB = Deno.env.get("SUPABASE_URL") ?? "";
const SR = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

async function db(path: string, body?: unknown, method?: string) {
  const r = await fetch(`${SB}/rest/v1/${path}`, {
    method: method || (body ? "POST" : "GET"),
    headers: { apikey: SR, Authorization: `Bearer ${SR}`, "Content-Type": "application/json", ...(path.startsWith("rpc/") ? {} : { Prefer: "return=minimal" }) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: r.status, j: await r.json().catch(() => null) };
}

async function stripeGet(path: string) {
  const r = await fetch("https://api.stripe.com/v1" + path, { headers: { Authorization: `Bearer ${KEY}` } });
  return r.status === 200 ? await r.json() : null;
}

const iso = (t?: number | null) => (t ? new Date(t * 1000).toISOString() : null);
// Stripe moved current_period_end from the subscription onto its items (2025 API): read either
const periodEnd = (sub: any) => sub?.current_period_end ?? sub?.items?.data?.[0]?.current_period_end ?? null;

async function handle(ev: any): Promise<string> {
  const o = ev.data?.object || {};
  if (ev.type === "checkout.session.completed" && o.mode === "subscription" && o.payment_status === "paid") {
    const sub = await stripeGet(`/subscriptions/${o.subscription}`);
    const item = sub?.items?.data?.[0]?.price;
    const r = await db("rpc/pro_join", {
      p_sub: o.client_reference_id, p_plan: o.metadata?.plan === "founding" ? "founding" : "regular",
      p_currency: (item?.currency || o.currency || "cad").toLowerCase(), p_amount: item?.unit_amount ?? o.amount_total ?? 0,
      p_customer: o.customer, p_stripe_sub: o.subscription, p_period_end: iso(periodEnd(sub)), p_live: !!ev.livemode,
    });
    if (r.status >= 300) throw new Error(`pro_join http ${r.status}`);
    if (o.metadata?.plan === "founding" && r.j === 0) console.log("FOUNDING FULL: a founding checkout paid after #100 (price to fix by hand)");
    return `joined #${r.j}`;
  }
  if (ev.type === "customer.subscription.updated" || ev.type === "customer.subscription.deleted") {
    const r = await db(`pro_members?stripe_sub=eq.${o.id}`, {
      status: ev.type.endsWith("deleted") ? "canceled" : o.status, cancel_at_end: !!o.cancel_at_period_end,
      current_period_end: iso(periodEnd(o)), updated_at: new Date().toISOString(),
    }, "PATCH");
    if (r.status >= 300) throw new Error(`update http ${r.status}`);
    return "updated";
  }
  return "ignored";
}
const TOLERANCE = 300; // seconds, Stripe's own default

const hex = (b: ArrayBuffer) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");

function same(a: string, b: string) {          // constant-time compare
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

async function verified(body: string, header: string | null): Promise<boolean> {
  if (!SECRET || !header) return false;
  const parts = header.split(",").map((p) => p.split("=") as [string, string]);
  const t = parts.find(([k]) => k === "t")?.[1];
  const sigs = parts.filter(([k]) => k === "v1").map(([, v]) => v);
  if (!t || !sigs.length || Math.abs(Date.now() / 1000 - Number(t)) > TOLERANCE) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(SECRET), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const want = hex(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${t}.${body}`)));
  return sigs.some((s) => same(s, want));
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  if (!SECRET) return new Response("webhook secret not set yet", { status: 503 });
  const body = await req.text();
  if (!(await verified(body, req.headers.get("stripe-signature")))) return new Response("bad signature", { status: 400 });
  let ev: any = {};
  try { ev = JSON.parse(body); } catch { return new Response("bad json", { status: 400 }); }
  const seen = await db("pro_events", { id: ev.id, type: ev.type });
  if (seen.status === 409) return new Response(JSON.stringify({ received: true, duplicate: true }), { headers: { "Content-Type": "application/json" } });
  let what = "";
  try {
    what = await handle(ev);
  } catch (e) {
    await db(`pro_events?id=eq.${ev.id}`, undefined, "DELETE");     // let Stripe's retry try again
    console.log(`stripe event ${ev.type} ${ev.id} FAILED: ${(e as Error).message}`);
    return new Response("failed", { status: 500 });
  }
  console.log(`stripe event ${ev.type} ${ev.id} live=${ev.livemode}: ${what}`);   // ids and types only, nothing personal
  return new Response(JSON.stringify({ received: true }), { headers: { "Content-Type": "application/json" } });
});
