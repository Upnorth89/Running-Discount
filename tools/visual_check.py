"""Letters touching things (Oct 28, 2026; Bastien: "I shouldn't have to see the y bleeding over. These details matter and should be
caught in our scan").

The site test checked buttons sitting on buttons, not the letters of a headline hanging into the search box. This looks at a page the
way a person does, in the browser that drew it:
  - text touching a box it doesn't belong to: each visible line of text (its letters' own height, descenders included) against every
    form box, button, picture and bordered/filled box that isn't its own parent or child;
  - text cut off: a button, link, label or heading whose words are wider or taller than the box that clips them;
  - nothing wider than the screen.
Fixed, sticky and absolutely placed things (bars, toasts, dialogs, the heart and badges sitting on a card or photo) are left out:
they float over the page on purpose. A page whose stylesheet didn't load answers ["STYLES-MISSING <url>"] (callers retry or skip).

  from visual_check import collisions; collisions(page) -> ["headline 'Find running…' touches the search box (form#rdSearch) by 4px", ...]
"""

JS = r"""() => {
// a stylesheet that didn't load (a network blip) draws everything unstyled: say so instead of listing a hundred "collisions"
for (const l of document.querySelectorAll('link[rel=stylesheet]')) {
  if (!l.href.startsWith(location.origin)) continue;   // web fonts: a fallback font still draws the page
  if (!l.sheet) return ['STYLES-MISSING ' + l.href];
  try { if (!l.sheet.cssRules.length) return ['STYLES-MISSING ' + l.href] } catch (e) {}   // an error page served as CSS: empty; fonts (other site) can't be read
}
// every page of ours sets its own font: the browser's default serif means the page's styles never arrived
if (/times|serif$/i.test(getComputedStyle(document.body).fontFamily.split(',')[0].replace(/["']/g, '').trim())) return ['STYLES-MISSING (default font)'];
const vis = e => { if (!e || !e.getClientRects().length) return false; const s = getComputedStyle(e);
  return s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05 };
const floating = e => { for (let x = e; x && x !== document.body; x = x.parentElement) { const p = getComputedStyle(x).position;
  if (p === 'fixed' || p === 'sticky' || p === 'absolute' || x.matches('dialog,[role=dialog],.sheet,.toast,.lostamp,.offtag,.disc,.badge,.pic,.tile .off,header.top,.topbar,.rdtop'))
  return true } return false };
const name = e => { const id = e.id ? '#' + e.id : ''; const c = typeof e.className === 'string' && e.className.trim() ? '.' + e.className.trim().split(/\s+/)[0] : '';
  return e.tagName.toLowerCase() + id + c };
const said = e => (e.innerText || e.value || e.getAttribute('aria-label') || e.alt || '').trim().replace(/\s+/g, ' ').slice(0, 40);
// solid boxes: things a line of text must never touch
const solids = [...document.querySelectorAll('input,select,textarea,button,img,form,[role=button],a.btn,.btn,.chip,.pill')]
  .concat([...document.querySelectorAll('div,section,aside,a,span,label,nav,ul,li,p')].filter(e => { const s = getComputedStyle(e);
    const filled = s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent';
    const bordered = parseFloat(s.borderTopWidth) > 0 && parseFloat(s.borderBottomWidth) > 0 && s.borderTopStyle !== 'none';
    return (filled || bordered) }))
  .filter(e => vis(e) && !floating(e));
const sb = solids.map(e => [e, e.getBoundingClientRect()]).filter(([e, r]) => r.width > 6 && r.height > 6 && !e.matches('main,.wrap'));
// lines of text: every visible text node, measured by its letters (Range rects use the font's full height, descenders included)
const out = [], seen = new Set();
const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: n => n.nodeValue.trim().length > 1 ? 1 : 3 });
let n, count = 0;
while ((n = tw.nextNode()) && count < 6000) {
  const el = n.parentElement; count++;
  if (!el || !vis(el) || floating(el) || el.closest('script,style,noscript,option,select,svg')) continue;
  const rg = document.createRange(); rg.selectNodeContents(n);
  // words clipped on purpose ("…", a box with overflow hidden) are measured only where they're drawn: inside the clipping box
  let clip = null;
  for (let x = el; x && x !== document.body; x = x.parentElement) { const cs = getComputedStyle(x);
    if (/hidden|clip|auto|scroll/.test(cs.overflowX + cs.overflowY)) { clip = x.getBoundingClientRect(); break } }
  for (const r0 of rg.getClientRects()) {
    const r = clip ? { left: Math.max(r0.left, clip.left), right: Math.min(r0.right, clip.right), top: Math.max(r0.top, clip.top),
                       bottom: Math.min(r0.bottom, clip.bottom), width: 0, height: 0 } : r0;
    if (clip) { r.width = r.right - r.left; r.height = r.bottom - r.top }
    if (r.width < 2 || r.height < 4 || r.bottom < 0 || r.top > document.documentElement.scrollHeight) continue;
    for (const [s, b] of sb) {
      if (s === el || s.contains(el) || el.contains(s)) continue;
      const x = Math.min(r.right, b.right) - Math.max(r.left, b.left), y = Math.min(r.bottom, b.bottom) - Math.max(r.top, b.top);
      if (x > 2 && y > 1.5) {
        const k = name(el) + '|' + name(s);
        if (seen.has(k)) continue; seen.add(k);
        out.push(`text “${n.nodeValue.trim().replace(/\s+/g, ' ').slice(0, 40)}” (${name(el)}) touches ${name(s)}${said(s) ? ' “' + said(s) + '”' : ''} by ${Math.round(y)}px`);
      }
    }
  }
}
// words cut off by the box that clips them
for (const e of document.querySelectorAll('button,a,label,h1,h2,h3,.chip,.pill,summary')) {
  if (!vis(e) || floating(e) || !said(e)) continue;
  const s = getComputedStyle(e);
  if (s.textOverflow === 'ellipsis' || (s.webkitLineClamp && s.webkitLineClamp !== 'none')) continue;   // shortened on purpose, with "…"
  const clips = /hidden|clip/.test(s.overflowX + s.overflowY);
  if (clips && (e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 3))
    out.push(`words cut off in ${name(e)} “${said(e)}” (${e.scrollWidth}×${e.scrollHeight} in ${e.clientWidth}×${e.clientHeight})`);
}
if (document.documentElement.scrollWidth > innerWidth + 1) out.push(`page is ${document.documentElement.scrollWidth - innerWidth}px wider than the screen`);
return out.slice(0, 12);
}"""


def collisions(page):
    """What looks broken on the page as drawn right now (empty list = clean). A page that moves on while we look (a redirect, a
    script changing the address) is measured again once it settles."""
    for i in range(3):
        try:
            return page.evaluate(JS)
        except Exception as e:
            if "context was destroyed" not in str(e) or i == 2:
                raise
            page.wait_for_load_state("load")
            page.wait_for_timeout(1500)
