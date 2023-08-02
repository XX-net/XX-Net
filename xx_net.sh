#!/bin/bash
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
PACKAGE_DESC="XX-Net proxy server"
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:${PATH}


if [ -L $0 ];then
       PACKAGE_PATH="$(dirname $(readlink -n $0))/"                                         
else
    PACKAGE_PATH=`dirname $0`
fi
cd $PACKAGE_PATH
PACKAGE_PATH="`pwd `/"
PACKAGE_START="${PACKAGE_PATH}start"


start() {
    echo -n "Starting ${PACKAGE_DESC}: "
    nohup ${PACKAGE_START} >/dev/null 2>&1 &
    echo "${PACKAGE_NAME}."
}

stop() {
    echo -n "Stopping ${PACKAGE_DESC}: "
    kill -9 `ps aux | grep "${PACKAGE_START}" | grep -v grep | awk '{print $2}'` || true
    kill -9 `ps aux | grep "launcher/start.py" | grep -v grep | awk '{print $2}'` || true
    echo "${PACKAGE_NAME}."
}

status() {
    pid="PID`ps aux | grep "${PACKAGE_START}" | grep -v grep | awk '{print $2}'`"
    if [[ "$pid" == "PID" ]];then
        echo "xx-net stopped"
    else
        echo "xx-net running,pid: ${pid##"PID"}"
    fi
}   

restart() {
    stop
    sleep 1
    start
}

usage() {
    N=$(basename "$0")
    echo "Usage: [sudo] $N {start|stop|restart|status}" >&2
    exit 1
}

if [ "$(id -u)" != "0" ]; then
    echo "please use sudo to run ${PACKAGE_NAME}"
    exit 0
fi


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
       status)
        status
        ;;
    *)
        usage
        ;;
esac

exit 0
