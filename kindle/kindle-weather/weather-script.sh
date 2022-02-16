#!/bin/sh

cd "$(dirname "$0")"

if [ -f /mnt/us/kindle-weather/enable ]; then

    [ -n "$(pidof powerd)" ] && (/etc/init.d/powerd stop; /etc/init.d/framework stop)

    rm -f /tmp/KindleStation_flatten.png
    scp -i /mnt/us/.ssh/id_rsa root@192.168.2.1:/tmp/KindleStation_flatten.png /tmp
    eips -c
    eips -g /tmp/KindleStation_flatten.png
fi
