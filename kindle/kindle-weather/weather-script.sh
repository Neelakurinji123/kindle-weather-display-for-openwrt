#!/bin/sh

cd "$(dirname "$0")"

if [ -f /mnt/us/kindle-weather/enable ]; then

    if [ "$(pidof powerd)" != '' ]; then
        /etc/init.d/powerd stop
        /etc/init.d/framework stop
    fi

    if ! $(mount -l | grep -q 'tmpfs on /tmp_data'); then
        mount -a
        sleep 3
    fi

    rm -f /www/KindleStation_flatten.png
    scp -i /mnt/us/.ssh/id_rsa root@192.168.2.1:/tmp/KindleStation_flatten.png /tmp_data/
    eips -c
    eips -g /tmp_data/KindleStation_flatten.png
fi
