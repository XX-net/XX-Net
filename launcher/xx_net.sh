#!/bin/sh
#
# xx_net init script
#

### BEGIN INIT INFO
# Provides:          xx_net
# Required-Start:    $syslog
# Required-Stop:     $syslog
# Should-Start:      $local_fs
# Should-Stop:       $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Monitor for xx_net activity
### END INIT INFO

# **NOTE** bash will exit immediately if any command exits with non-zero.
set -e

PACKAGE_NAME=xx_net
PACKAGE_DESC="xx_net proxy server"
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:${PATH}

start() {
    echo -n "Starting ${PACKAGE_DESC}: "
    if hash python2 2>/dev/null; then
        nohup python2 launcher/start.py 2>&1 | /usr/bin/logger -t ${PACKAGE_NAME} &
    else
        nohup python launcher/start.py 2>&1 | /usr/bin/logger -t ${PACKAGE_NAME} &
    fi
    echo "${PACKAGE_NAME}."
}

stop() {
    echo -n "Stopping ${PACKAGE_DESC}: "
    if hash python2 2>/dev/null; then
        kill -9 `ps aux | grep 'python2 launcher/start.py' | grep -v grep | awk '{print $2}'` || true
    else
        kill -9 `ps aux | grep 'python launcher/start.py' | grep -v grep | awk '{print $2}'` || true
    fi
    echo "${PACKAGE_NAME}."
}

restart() {
    stop
    sleep 1
    start
}

usage() {
    N=$(basename "$0")
    echo "Usage: [sudo] $N {start|stop|restart}" >&2
    exit 1
}

if [ "$(id -u)" != "0" ]; then
    echo "please use sudo to run ${PACKAGE_NAME}"
    exit 0
fi

# `readlink -f` won't work on Mac, this hack should work on all systems.
cd $(python -c "import os; print os.path.dirname(os.path.realpath('$0'))")

case "$1" in
    # If no arg is given, start the goagent.
    # If arg `start` is given, also start goagent.
    '' | start)
        start
        ;;
    stop)
        stop
        ;;
    #reload)
    restart | force-reload)
        restart
        ;;
    *)
        usage
        ;;
esac

exit 0
}
