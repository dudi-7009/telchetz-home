# ============================================================================
# Tel-Chetz marketing homepage — static site served by nginx.
# Multi-stage: stage 1 renders og-image.svg → og-image.png (1200x630)
# with Hebrew-capable fonts so social preview previews look good.
# ============================================================================

# --- Stage 1: render the SVG to PNG -----------------------------------------
FROM alpine:3.20 AS svgrender
RUN apk add --no-cache librsvg font-noto-hebrew font-noto ttf-liberation
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

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
