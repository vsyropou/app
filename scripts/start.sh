#! /usr/bin/env sh
set -e

# Expect APP_NAME set so the ASGI module resolves to ${APP_NAME}.api:app
if [ -z "$APP_NAME" ]; then
    echo "Error: APP_NAME environment variable not set."
    exit 1
fi

MODULE="${APP_NAME}.api.main:app"

# Parse args: optional --reload flag, and a required log-config JSON path.
RELOAD=""
LOG_CONFIG=""
for arg in "$@"; do
    if [ "$arg" = "--reload" ]; then
        RELOAD="--reload"
    else
        LOG_CONFIG="$arg"
    fi
done

if [ -z "$LOG_CONFIG" ]; then
    echo "Error: log-config JSON path required as a positional argument."
    echo "Usage: start.sh [--reload] <path-to-logging.json>"
    exit 1
fi


# Configure hypercorn options. The 'json:' prefix tells hypercorn to use
# dictConfig on the file (see hypercorn/logging.py).
HYPERCORN_OPTIONS="--bind 0.0.0.0:8080 --access-logfile - --log-config json:${APP_NAME}/${LOG_CONFIG}"

# Start the app (module: variable)
exec hypercorn "$MODULE" $HYPERCORN_OPTIONS $RELOAD
