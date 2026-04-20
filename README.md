# Tel-Chetz Homepage (telchetz.com)

Static marketing homepage for Tel-Chetz — served at the root domain `telchetz.com`.
Separate project from the app at `app.telchetz.com` (`telchetz-app` container) and from the management UI at `manage.telchetz.com` (`telchetz-manage`).

## Stack

- Plain HTML + CSS + JS (no build step, no framework).
- Fonts: Suez One · Miriam Libre · Assistant · Fraunces · JetBrains Mono (all Google Fonts).
- Icons: lucide via CDN.
- Served by nginx:1.27-alpine. Aggressive cache for `/assets/*`, no-cache for HTML.
- SEO: `<title>` + meta + Open Graph + Twitter Card + canonical + hreflang + JSON-LD (`Organization + LocalBusiness + SoftwareApplication + WebSite + FAQPage`).
- Accessibility: RTL, `prefers-reduced-motion` respected.

## Layout

```
index.html            ← single-page site
robots.txt
sitemap.xml
assets/
  logo-full.png       ← hero / footer lockup
  logo-wordmark.svg
  mark.svg            ← favicon + peek header
  telchetz.css        ← shared design tokens (inherited from the app)
Dockerfile
nginx.conf
.dockerignore
README.md             ← this file
_design_pkg/          ← source design bundle from claude.ai/design (git-ignored; not shipped)
```

## Build locally

```bash
docker build -t telchetz-home:latest .
docker run --rm -p 8080:80 telchetz-home:latest
# then open http://localhost:8080/
```

## Deploy to production (Hetzner VPS)

Target: `/opt/apps/telchetz-home/` on the production server.
Container name: `telchetz-home`. Network: `coolify` (so Traefik can reach it).

First-time setup:

```bash
# on the VPS
mkdir -p /opt/apps/telchetz-home
# copy project files here (via MCP file_write, scp, or git pull)
cd /opt/apps/telchetz-home
docker build -t telchetz-home:latest .
docker run -d \
  --name telchetz-home \
  --network coolify \
  --restart unless-stopped \
  --health-cmd "wget -qO- http://127.0.0.1/healthz || exit 1" \
  --health-interval 30s \
  telchetz-home:latest
```

Traefik already has a route for `Host(\`telchetz.com\`)`. The route currently points to `telchetz-app:3000` — we flip it to `telchetz-home:80` in `/opt/traefik/dynamic/telchetz.yml` to put the new homepage live on the root domain.

### Updating the site

```bash
cd /opt/apps/telchetz-home
# pull updated files, then:
docker build -t telchetz-home:latest .
docker stop telchetz-home && docker rm telchetz-home
docker run -d --name telchetz-home --network coolify --restart unless-stopped telchetz-home:latest
```

### Rollback

`telchetz.com` → homepage was previously routed to `telchetz-app:3000`. If the new homepage misbehaves, flip the Traefik rule back:

```yaml
services:
  telchetz-app:
    loadBalancer:
      servers:
        - url: http://telchetz-app:3000
```

Traefik reloads dynamic config within seconds — no restart needed.

## SEO checklist (Wave 1 — done here)

- [x] `<title>` targets primary query: "תוכנה לניהול מוסד חינוכי"
- [x] `meta description` ≤ 160 chars, contains keywords + value prop
- [x] `meta keywords` (low weight but harmless)
- [x] Canonical URL + hreflang `he-IL`
- [x] Open Graph + Twitter Card
- [x] JSON-LD structured data (Organization / LocalBusiness / SoftwareApplication / WebSite / FAQPage)
- [x] Real NAP (Name, Address, Phone) — consistent on page + schema
- [x] `robots.txt` + `sitemap.xml`
- [x] Aggressive gzip + cache headers
- [x] `font-display: swap` (via Google Fonts `&display=swap`)
- [x] `defer` on lucide icon script
- [x] HSTS + CSP + X-Frame-Options
- [x] Client list pulled from real subscribed institutions (6 networks with written consent)

## SEO gaps (Wave 2)

- [ ] Dedicated landing pages per query: `/nihul-nochichut`, `/ciunim-mivchanim`, `/chiyuv-horim`, `/yeshiva-ktana`, `/talmud-torah`, `/seminar`, `/merkaz-siyua` (800-1200 words each)
- [ ] Blog (2 posts/month): content marketing for long-tail queries
- [ ] Real customer logos (once written consent allows visual marks)
- [ ] Real quoted testimonial (currently generic placeholder)
- [ ] Case studies page
- [ ] Backlinks / press mentions
- [ ] Google Business Profile (local SEO)
- [ ] Google Search Console + Bing Webmaster setup

## Open TODOs in the page

- `form.cta-form` currently does not POST anywhere — handler is front-end only. Wire to a real endpoint (e.g. `/api/lead` on the app, or Stalwart Mail + GoTrue magic-link).
- Quote section uses a generic placeholder — replace with real testimonial once consent is in hand.
- Credibility strip shows text-only network names with initial mark. Once real logos (PNG/SVG) are provided, swap in `<img>` elements.

## Subscribed institutions (source of truth)

Pulled live from `public.institutions` (via `mcp__Server__db_read`) on 2026-04-21 — `is_subscribed=true AND is_active=true`:

1. **רשת באיאן** — 4 קמפוסים (קרית גת · ירושלים ×2 · ביתר עילית) + באיאן גנים (ביתר עילית)
2. **רשת בעלזא** — 8 קמפוסים (גבעת זאב · רובע ז · קדושת אהרן · רובע ג · חיפה · קרית גת · נתיבות התורה · פרשת מרדכי)
3. **רשת מתיקות התורה** — 3 קמפוסים (בני ברק · ביתר עילית · בית שמש)
4. **מתיקות החינוך** — בית ספר בנות, ביתר עילית
5. **מרכז הרב וובר**
6. **מרכז שלהבת**

Excluded from display: `דמה` and `בדיקה` (test / dummy data).
