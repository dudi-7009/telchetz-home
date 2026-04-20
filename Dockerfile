# ============================================================================
# Tel-Chetz marketing homepage — static site served by nginx.
# Multi-stage: stage 1 renders og-image.svg → og-image.png (1200x630)
# with Hebrew-capable fonts so social preview previews look good.
# ============================================================================

# --- Stage 1: render the SVG to PNG -----------------------------------------
# Debian slim instead of Alpine — librsvg2-bin is a known-good CLI package
# and fonts-noto-hebrew ships reliable Hebrew glyph coverage for rendering.
FROM debian:12-slim AS svgrender
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        librsvg2-bin \
        fonts-noto-core \
        fonts-liberation \
        fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /render
COPY assets/og-image.svg ./og-image.svg
RUN rsvg-convert -w 1200 -h 630 og-image.svg -o og-image.png \
  && ls -la og-image.png

# --- Stage 2: nginx serving ------------------------------------------------
FROM nginx:1.27-alpine

RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
COPY robots.txt /usr/share/nginx/html/robots.txt
COPY sitemap.xml /usr/share/nginx/html/sitemap.xml
COPY assets/ /usr/share/nginx/html/assets/
COPY --from=svgrender /render/og-image.png /usr/share/nginx/html/assets/og-image.png

# Landing pages — each in its own directory so /slug/ serves /slug/index.html
COPY nihul-nochichut/   /usr/share/nginx/html/nihul-nochichut/
COPY ciunim-mivchanim/  /usr/share/nginx/html/ciunim-mivchanim/
COPY chiyuv-horim/      /usr/share/nginx/html/chiyuv-horim/
COPY talmud-torah/      /usr/share/nginx/html/talmud-torah/
COPY yeshiva-ktana/     /usr/share/nginx/html/yeshiva-ktana/
COPY seminar/           /usr/share/nginx/html/seminar/
COPY merkaz-siyua/      /usr/share/nginx/html/merkaz-siyua/

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
