#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <redirect interface dev>"
    echo "       $0 -clear"
    exit 0
fi


iptables -t nat -F
iptables -t nat -X REDSOCKS

if [ "$1" = "-clear" ]; then
    exit 0
fi



iptables -t nat -N REDSOCKS
iptables -t nat -A REDSOCKS -d 0.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 10.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 127.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 169.254.0.0/16 -j RETURN
iptables -t nat -A REDSOCKS -d 172.16.0.0/12 -j RETURN
iptables -t nat -A REDSOCKS -d 192.168.0.0/16 -j RETURN
iptables -t nat -A REDSOCKS -d 224.0.0.0/4 -j RETURN
iptables -t nat -A REDSOCKS -d 240.0.0.0/4 -j RETURN
iptables -t nat -A REDSOCKS -p tcp -j REDIRECT --to-ports 8086
iptables -t nat -A PREROUTING --in-interface $1 -p tcp -j REDSOCKS


