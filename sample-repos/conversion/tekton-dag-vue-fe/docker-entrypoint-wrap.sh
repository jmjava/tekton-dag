#!/bin/sh
python3 /usr/local/bin/propagation_proxy.py &
exec /docker-entrypoint.sh "$@"
