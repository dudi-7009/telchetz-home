"""
Tel-Chetz lead capture service.

Receives POST /lead from the homepage CTA form, validates the payload, and
sends the lead to office@telchetz.com via Stalwart SMTP (STARTTLS on 587).

Env vars:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM
    LEAD_TO           — recipient (default: office@telchetz.com)
    LEAD_BIND_HOST    — default 0.0.0.0
    LEAD_BIND_PORT    — default 8000
"""
from __future__ import annotations

import html
import json
import logging
import os
import re
import smtplib
import ssl
import time
from collections import defaultdict, deque
from email.message import EmailMessage
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lead-service")

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
EMAIL_FROM = os.environ.get("EMAIL_FROM") or f"Tel-Chetz <{SMTP_USER}>"
LEAD_TO = os.environ.get("LEAD_TO", "office@telchetz.com")

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# Simple per-IP rate limit: max 5 submissions / hour
RATE_LIMIT_WINDOW = 3600
RATE_LIMIT_MAX = 5
_rate_store: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(ip: str) -> bool:
    now = time.time()
    q = _rate_store[ip]
    while q and q[0] < now - RATE_LIMIT_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT_MAX:
        return True
    q.append(now)
    return False


def _build_email(email: str, message: str | None, ip: str, ua: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"ליד חדש מ-telchetz.com · {email}"
    msg["From"] = EMAIL_FROM
    msg["To"] = LEAD_TO
    msg["Reply-To"] = email
    body_lines = [
        "ליד חדש מהדף הראשי של telchetz.com",
        "",
        f"אימייל הלקוח: {email}",
    ]
    if message:
        body_lines += ["", "הודעה:", message]
    body_lines += [
        "",
        "---",
        f"IP: {ip}",
        f"User-Agent: {ua}",
        f"מקור: https://telchetz.com/#contact",
    ]
    text_body = "\n".join(body_lines)
    msg.set_content(text_body)

    html_body = f"""
<!doctype html><html lang="he" dir="rtl"><body style="font-family:system-ui,sans-serif;line-height:1.6;color:#1C1917">
  <h2 style="color:#0F2847;margin:0 0 8px">ליד חדש מ-telchetz.com</h2>
  <p style="color:#64748b;font-size:13px;margin:0 0 24px">דרך הטופס בדף הראשי</p>
  <table style="border-collapse:collapse;width:100%;max-width:520px">
    <tr><td style="padding:8px 12px;background:#F5F1E8;font-weight:600;width:140px">אימייל</td>
        <td style="padding:8px 12px;background:#fff;border-bottom:1px solid #e2e8f0">
          <a href="mailto:{html.escape(email)}">{html.escape(email)}</a></td></tr>
    {f'<tr><td style="padding:8px 12px;background:#F5F1E8;font-weight:600;vertical-align:top">הודעה</td><td style="padding:8px 12px;background:#fff;border-bottom:1px solid #e2e8f0;white-space:pre-wrap">{html.escape(message)}</td></tr>' if message else ''}
    <tr><td style="padding:8px 12px;background:#F5F1E8;font-weight:600">IP</td>
        <td style="padding:8px 12px;background:#fff;border-bottom:1px solid #e2e8f0;font-family:monospace">{html.escape(ip)}</td></tr>
    <tr><td style="padding:8px 12px;background:#F5F1E8;font-weight:600">User-Agent</td>
        <td style="padding:8px 12px;background:#fff;font-family:monospace;font-size:11px">{html.escape(ua)}</td></tr>
  </table>
  <p style="color:#94a3b8;font-size:12px;margin-top:24px">
    מקור: <a href="https://telchetz.com/#contact" style="color:#C4922A">telchetz.com/#contact</a>
  </p>
</body></html>
"""
    msg.add_alternative(html_body, subtype="html")
    return msg


def _send(msg: EmailMessage) -> None:
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.ehlo()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


app = Flask(__name__)


@app.get("/healthz")
def healthz():
    return "ok", 200, {"Content-Type": "text/plain"}


@app.post("/lead")
def lead():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    ua = request.headers.get("User-Agent", "-")

    if _rate_limited(ip):
        log.warning("rate limited ip=%s", ip)
        return jsonify(ok=False, error="rate_limited"), 429

    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()

    email = (data.get("email") or "").strip().lower()
    message = (data.get("message") or "").strip() or None

    if not email or not EMAIL_RE.match(email) or len(email) > 254:
        return jsonify(ok=False, error="invalid_email"), 400
    if message and len(message) > 4000:
        return jsonify(ok=False, error="message_too_long"), 400

    try:
        _send(_build_email(email, message, ip, ua))
    except Exception:
        log.exception("smtp send failed")
        return jsonify(ok=False, error="smtp_failed"), 502

    log.info("lead sent email=%s ip=%s", email, ip)
    return jsonify(ok=True), 200


if __name__ == "__main__":
    host = os.environ.get("LEAD_BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("LEAD_BIND_PORT", "8000"))
    app.run(host=host, port=port)
