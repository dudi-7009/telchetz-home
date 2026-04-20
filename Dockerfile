# Tel-Chetz marketing homepage — static site served by nginx
FROM nginx:1.27-alpine

# Drop default site + config
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy site + nginx config
COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
COPY robots.txt /usr/share/nginx/html/robots.txt
COPY sitemap.xml /usr/share/nginx/html/sitemap.xml
COPY assets/ /usr/share/nginx/html/assets/

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
