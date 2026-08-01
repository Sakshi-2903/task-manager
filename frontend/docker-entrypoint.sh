#!/bin/sh
set -eu

envsubst '${BACKEND_HOST} ${BACKEND_PORT} ${DNS_RESOLVER}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
