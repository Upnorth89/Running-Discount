"""Polite reading (Nov 1, 2026; Bastien: "We need to avoid triggering any bot detection in our scans", then "yes do 1-3").

Every store request goes through here (scrape.py's session S uses it, so hike.py and livecheck.py too):
  - our own name in the User-Agent (no browser disguise), so a store can see who we are and write a rule for us;
  - robots.txt read once per site: a Disallowed address is never fetched (raises RobotsNo), and its Crawl-delay is kept;
  - at least GAP seconds between two requests to one site (or its Crawl-delay if longer), counted across threads AND
    programs on this machine (the running and hiking reads run side by side); Shopify shops also share one platform pace;
  - a 429 / 503 "slow down" doubles that site's gap for the rest of the run (at least what Retry-After asks), and the
    caller's own retry waits as before.
robots.txt is matched the way Google reads it (most specific user-agent group, longest rule wins, * and $ wildcards, Allow
wins a tie), for our names TheGearFoxBot / ClaudeBot / anthropic-ai, else *.
"""
import contextlib
import fcntl
import os
import re
import threading
import time
from urllib.parse import urlsplit

import requests

UA = "Mozilla/5.0 (compatible; TheGearFoxBot/1.0; +https://thegearfox.com/about.html)"
AGENTS = ("thegearfoxbot", "claudebot", "anthropic-ai")
GAP = 1.0                    # seconds between two requests to the same site, when robots.txt asks nothing
MAX_GAP = 60.0
# Big shops on a CDN that ask for no Crawl-delay. Nov 1: at 1-2 pages a second the first polite read took 49 min and GitHub
# cancelled it (Altitude 44 min, shared with the hiking read). Still far gentler than before (10 pages at once, unpaced), and once a
# read has finished, only changed/on-sale products are re-read (Altitude: ~100 of 2,500).
HOST_GAP = {"www.altitude-sports.com": 0.25, "www.thelasthunt.com": 0.25,
            "www.sportinglife.ca": 0.4, "www.sportchek.ca": 0.4, "www.footlocker.ca": 0.4}
PLATFORM_GAP = {"shopify": 0.5}   # all Shopify shops together, from this machine
DIR = os.environ.get("POLITE_DIR", "/tmp/gf-polite")
STATS = {}                   # host -> {"n": requests, "slow": 429/503 answers, "no": refused by robots.txt, "delay": crawl-delay}


class RobotsNo(requests.RequestException):      # callers treat it like a failed request
    pass


def parse_robots(text):
    """-> {agent: {"rules": [(allow, pattern)], "delay": float|None}}; one group can name several agents."""
    groups, cur, last_was_agent = {}, [], False
    for line in (text or "").splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = (x.strip() for x in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if not last_was_agent:
                cur = []
            cur.append(v.lower())
            groups.setdefault(v.lower(), {"rules": [], "delay": None})
            last_was_agent = True
            continue
        last_was_agent = False
        for a in cur:
            g = groups[a]
            if k in ("allow", "disallow"):
                if v or k == "allow":
                    g["rules"].append((k == "allow", v))
            elif k == "crawl-delay":
                try:
                    g["delay"] = float(v)
                except ValueError:
                    pass
    return groups


def group_for(groups):
    for a in AGENTS:                                   # a group naming us (or the company behind the crawler we run)
        for name, g in groups.items():
            if name != "*" and a.startswith(name):
                return g
    return groups.get("*", {"rules": [], "delay": None})


def _rx(pat):
    end = pat.endswith("$")
    body = re.escape(pat[:-1] if end else pat).replace(r"\*", ".*")
    return re.compile(body + ("$" if end else ""))


def allowed(group, path):
    best, ok = -1, True
    for allow, pat in group["rules"]:
        if not pat:
            continue
        if _rx(pat).match(path):
            n = len(pat)
            if n > best or (n == best and allow):
                best, ok = n, allow
    return ok


_tl = threading.local()


@contextlib.contextmanager
def platform(name):
    """Requests made inside `with platform("shopify"):` are also paced as one stream for the whole platform: Shopify counts one
    machine's requests across all its shops, so the running read and the hiking read (two programs) share one pace."""
    old = getattr(_tl, "platform", None)
    _tl.platform = name
    try:
        yield
    finally:
        _tl.platform = old


def _pace(key, gap):
    """Wait until `key` may send again, across threads AND programs on this machine (a small file per key holds the next
    allowed time, under a file lock), then book the next slot `gap` seconds later. A slow-down stored there (after a 429/503)
    raises the gap for the rest of the day's run."""
    os.makedirs(DIR, exist_ok=True)
    path = os.path.join(DIR, re.sub(r"[^\w.-]", "_", key))
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            nxt, slow = (float(x) for x in (f.read().split() + ["0", "0"])[:2])
        except ValueError:
            nxt, slow = 0.0, 0.0
        if slow and time.time() - nxt > 6 * 3600:      # yesterday's slow-down doesn't carry over
            slow = 0.0
        wait = nxt - time.time()
        if wait > 0:
            time.sleep(wait)
        f.seek(0)
        f.truncate()
        f.write(f"{time.time() + max(gap, slow)} {slow}")
        fcntl.flock(f, fcntl.LOCK_UN)


def _slow(key, seconds):
    os.makedirs(DIR, exist_ok=True)
    path = os.path.join(DIR, re.sub(r"[^\w.-]", "_", key))
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            nxt, slow = (float(x) for x in (f.read().split() + ["0", "0"])[:2])
        except ValueError:
            nxt, slow = 0.0, 0.0
        slow = min(MAX_GAP, max(seconds, 2 * slow))
        f.seek(0)
        f.truncate()
        f.write(f"{max(nxt, time.time() + slow)} {slow}")
        fcntl.flock(f, fcntl.LOCK_UN)
    return slow


class PoliteSession(requests.Session):
    def __init__(self, gap=GAP, ua=UA):
        super().__init__()
        self.headers["User-Agent"] = ua
        self.gap = gap
        self._robots, self._locks = {}, {}
        self._guard = threading.Lock()

    def _lock(self, key):
        with self._guard:
            return self._locks.setdefault(key, threading.Lock())

    def robots(self, scheme, host):
        if host not in self._robots:
            with self._lock(host):
                if host not in self._robots:
                    g = {"rules": [], "delay": None}
                    try:
                        _pace(host, self.gap)
                        # Nov 1: its own cookie-less request, never through this session: Shopify answers robots.txt with geo
                        # cookies (localization=US from GitHub's location) that stuck in our jar and beat our Canadian cookies
                        # (13 stores read in the wrong currency on Nov 1).
                        r = requests.get(f"{scheme}://{host}/robots.txt", timeout=20, allow_redirects=True,
                                         headers={"User-Agent": self.headers.get("User-Agent", UA)})
                        if r.status_code == 200 and "html" not in r.headers.get("content-type", ""):
                            g = group_for(parse_robots(r.text))
                    except Exception:
                        pass                       # no robots.txt = no rules (the usual reading)
                    self._robots[host] = g
                    STATS.setdefault(host, {"n": 0, "slow": 0, "no": 0, "delay": None})["delay"] = g["delay"]
        return self._robots[host]

    def request(self, method, url, *a, **kw):
        u = urlsplit(url)
        host = u.netloc.lower()
        path = (u.path or "/") + (("?" + u.query) if u.query else "")
        st = STATS.setdefault(host, {"n": 0, "slow": 0, "no": 0, "delay": None})
        g = self.robots(u.scheme or "https", host) if u.path != "/robots.txt" else {"rules": [], "delay": None}
        if not allowed(g, path):
            st["no"] += 1
            raise RobotsNo(f"robots.txt says no: {host}{path[:80]}")
        gap = max(HOST_GAP.get(host, self.gap), g.get("delay") or 0)
        plat = getattr(_tl, "platform", None)
        if plat:
            _pace("platform-" + plat, PLATFORM_GAP.get(plat, 0.5))
        _pace(host, gap)
        r = super().request(method, url, *a, **kw)
        st["n"] += 1
        if r.status_code in (429, 503):                # "slow down": this site gets a longer gap for the rest of the run
            st["slow"] += 1
            ra = r.headers.get("Retry-After", "")
            _slow(host, max(2 * gap, float(ra) if ra.isdigit() else 0))
        return r


def report(top=25):
    """One line per site for the log: requests, slow-downs, robots refusals."""
    rows = sorted(STATS.items(), key=lambda kv: -kv[1]["n"])
    tot = sum(v["n"] for v in STATS.values())
    lines = [f"polite: {tot} requests to {len(STATS)} sites; "
             f"{sum(v['slow'] for v in STATS.values())} slow-downs (429/503), {sum(v['no'] for v in STATS.values())} refused by robots.txt"]
    for h, v in rows[:top]:
        lines.append(f"  {h}: {v['n']}" + (f", {v['slow']} slow-downs" if v["slow"] else "") + (f", {v['no']} robots no" if v["no"] else "")
                     + (f", crawl-delay {v['delay']:g}s" if v["delay"] else ""))
    for h, v in rows[top:]:
        if v["slow"] or v["no"]:
            lines.append(f"  {h}: {v['n']}, {v['slow']} slow-downs, {v['no']} robots no")
    return "\n".join(lines)
