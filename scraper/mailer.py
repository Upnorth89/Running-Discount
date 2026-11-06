"""One way to send our emails through Resend (Nov 6, 2026; growth's night-shift job before the Black Friday sends).

Resend takes 2 requests a second on every plan (Oct 29: 41 of 54 welcome emails sent at once got 429). Every bulk sender
(Friday email, alerts, confirm reminders, race reminders, the Dec 2 founding-link send) goes through send():
  - at least GAP (0.6 s) between two sends from this program;
  - on 429 or a 5xx / network error: wait Retry-After (else 2 s, 4 s, 8 s) and try again, up to TRIES times;
  - still not sent: one log line with a short hash of the address (never the address: the repo and its logs are public),
    and the caller carries on. Callers only stamp weekly_sent_at / last_mail_at / reminded_at when the result is ok.
"""
import hashlib
import os
import time

import requests

URL = "https://api.resend.com/emails"
GAP = 0.6
TRIES = 4
_last = [0.0]


class Failed:
    ok = False

    def __init__(self, status, text):
        self.status_code, self.text = status, text


def tag(addr):
    return hashlib.sha256(str(addr or "").strip().lower().encode()).hexdigest()[:10]


def send(payload, key=None, log=print, sleep=time.sleep):
    """POST one email. Returns the last response (r.ok True = sent) or a Failed with ok False."""
    key = key or os.environ.get("RESEND_API_KEY", "")
    last = None
    for i in range(TRIES):
        wait = _last[0] + GAP - time.time()
        if wait > 0:
            sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.post(URL, timeout=60, headers={"Authorization": f"Bearer {key}"}, json=payload)
        except requests.RequestException as e:
            last = Failed(0, f"{type(e).__name__}")
        else:
            if r.ok:
                return r
            last = r
            if r.status_code != 429 and r.status_code < 500:
                break                     # 4xx other than 429 (bad address, bad key): trying again won't help
        if i < TRIES - 1:
            ra = getattr(last, "headers", None) and last.headers.get("Retry-After")
            try:
                delay = min(float(ra), 30.0) if ra else 2.0 * 2 ** i
            except ValueError:
                delay = 2.0 * 2 ** i
            sleep(delay)
    to = (payload.get("to") or [""])[0]
    log(f"mail #{tag(to)} NOT sent after {i + 1} tries: HTTP {last.status_code}")
    return last
