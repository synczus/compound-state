#!/bin/bash
# IBKR Gateway systemd wrapper
# Infrastructure, not agent. Agents come and go; the gateway persists.

GATEWAY_DIR="/opt/ibkr/gateway"
LOG_FILE="/var/log/ibkr/gateway.log"
PID_FILE="/var/run/ibkr-gateway.pid"

case "$1" in
  start)
    echo "Starting IBKR Gateway..."
    mkdir -p /opt/ibkr /var/log/ibkr
    # TWS/Gateway startup command placeholder
    # java -jar $GATEWAY_DIR/ibgateway.jar ... &
    echo $! > $PID_FILE
    echo "Gateway PID: $(cat $PID_FILE)"
    ;;
  stop)
    echo "Stopping IBKR Gateway..."
    if [ -f $PID_FILE ]; then
      kill $(cat $PID_FILE) 2>/dev/null
      rm -f $PID_FILE
    fi
    ;;
  status)
    if [ -f $PID_FILE ] && kill -0 $(cat $PID_FILE) 2>/dev/null; then
      echo "Running"
    else
      echo "Stopped"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
esac