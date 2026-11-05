// Running Free relay (Nov 5, 2026; Bastien, in the backend chat: "okay push running free"). runningfree.com shows visitors outside Canada a page saying it is
// "only available to visitors in Canada"; GitHub's night computers are in the US. We are a Canadian business, so the night read asks
// THIS function, run in Supabase's Canadian region (the caller sends x-region: ca-central-1), to fetch ONE runningfree.com page with our
// honest bot name and hand the page back. The night job keeps the pacing (one page every 30 s = its robots.txt Crawl-delay), checks
// robots.txt itself and stops on any 403/429/captcha. Same line as every store: never a disguise, never another site, no cookies.
// Guard: the caller must send x-rf-key = the RF_KEY secret (set by the rf-relay workflow); only runningfree.com, only GET, no /myaccount.
const KEY = Deno.env.get("RF_KEY") ?? "";
const UA = "Mozilla/5.0 (compatible; TheGearFox/1.0; +https://thegearfox.com/about.html)";
const BASE = "https://www.runningfree.com";

Deno.serve(async (req) => {
  const out = (body: string, status: number, extra: Record<string, string> = {}) =>
    new Response(body, { status, headers: { "content-type": "text/plain; charset=utf-8", ...extra } });
  if (!KEY || req.headers.get("x-rf-key") !== KEY) return out("forbidden", 403);
  const path = new URL(req.url).searchParams.get("path") ?? "";
  if (!path.startsWith("/") || path.startsWith("//") || /^\/myaccount|cmd=/i.test(path) || path.length > 400) return out("bad path", 400);
  try {
    const r = await fetch(BASE + path, {
      headers: { "User-Agent": UA, "Accept": "text/html,text/plain,*/*", "Accept-Encoding": "identity" },
      redirect: "follow",
      signal: AbortSignal.timeout(50000),
    });
    const final = new URL(r.url);
    if (final.hostname.replace(/^www\./, "") !== "runningfree.com") return out("left runningfree.com", 502);
    const text = await r.text();
    // the store's answer, unchanged: its status code in x-rf-status, the page as the body
    return out(text, 200, { "x-rf-status": String(r.status), "x-rf-region": Deno.env.get("SB_REGION") ?? "" });
  } catch (e) {
    return out("fetch failed: " + String(e).slice(0, 120), 504);
  }
});
