# syntax=docker/dockerfile:1

# ---- runtime ----------------------------------------------------------------
# The unprivileged variant listens on 8080 and runs as uid 101 already, so no
# root-owned master process and no capability to bind port 80.
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

COPY dist/ /usr/share/nginx/html/
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

ENV BACKEND_HOST=backend \
    BACKEND_PORT=5001 \
    DNS_RESOLVER=127.0.0.11

EXPOSE 8080

ENTRYPOINT ["/bin/sh", "/docker-entrypoint.sh"]

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/nginx-health || exit 1