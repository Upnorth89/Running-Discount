// Stripe webhook for Fox Pro (Nov 5, 2026: first version).
// Stripe calls https://krwymmkauwqqxjxbvkyq.supabase.co/functions/v1/stripe-webhook (deployed with --no-verify-jwt: Stripe sends no
// Supabase login, so every request is checked against Stripe's own signature instead, with STRIPE_WEBHOOK_SECRET).
// For now it only proves the endpoint works end to end: a correctly signed event is acknowledged (200), anything else is refused.
// Next (Fox Pro build, behind the switch): record checkout.session.completed / subscription / invoice events in the database,
// hand out the Founding Fox number after payment, send the purchase email with the terms.
const SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";
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
  let ev: { id?: string; type?: string; livemode?: boolean } = {};
  try { ev = JSON.parse(body); } catch { return new Response("bad json", { status: 400 }); }
  console.log(`stripe event ${ev.type} ${ev.id} live=${ev.livemode}`);   // ids and types only, nothing personal
  return new Response(JSON.stringify({ received: true }), { headers: { "Content-Type": "application/json" } });
});
