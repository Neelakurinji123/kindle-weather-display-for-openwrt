# Kindle Weather Display for OpenWrt
This program is for a weather display on old Kindle 3 based on the original work by [Kindle-weather-station](https://gitlab.com/iero/Kindle-weather-station)

## Features
- Weather data is from [OpenWeatherMap API](https://openweathermap.org/)
- Converting SVG to PNG is [CloudConvert API](https://cloudconvert.com/)
- The weather information is current weather, 3 hour forecast and 3 day forecast
- Almost any locales, languages and units are enabled

## Screenshots
<img src="/sample_screenshots/KindleStation.png" height="400" alt="Kindle 3 Screenshot" /><img src="https://user-images.githubusercontent.com/70471447/154597426-2da949ff-90e9-4416-af16-47f2413bda54.jpg" height="400">

## Requirements
- Minimum 256M/100M OpenWrt router
- USB port x1
- LAN port x1
- API key for OpenWeatherMap
- One Call API subscription
- API key for CloudConvert
- Jailbroken Kindle 3

## OpenWrt setup

### Python 3 installation
```
# opkg install python3 python3-pytz python3-pip python3-requests imagemagickpip install --upgrade pip
# pip install wheel
# pip install --upgrade pip
# pip install --upgrade setuptools
# pip install cloudconvert
```

### Network interface `usb` and firewall zone `usb` setup
- Netwok > Interfaces: Add interface `usb`
- IP address is `192.168.2.1/24`
- Netwok > Interfaces - Firewall settings: Add `usb` zone
- Input, Output and Forward set `reject`
- Add foreward `usb` zone to `lan`
- Network > Firewall - Traffic Rules: `22/tcp`, `123/udp`, `53/udp` and `icmp` set open both incoming and outgoing
- Setup `123/udp`, `53/udp` and `icmp` for snat

### USB network installation
```
# opkg install kmod-usb-net kmod-usb-net-rndis kmod-usb-net-cdc-ether usbutils
```
### uci output
```
firewall.@zone[2]=zone
firewall.@zone[2].name='usb'
firewall.@zone[2].network='usb'
firewall.@zone[2].forward='REJECT'
firewall.@zone[2].input='REJECT'
firewall.@zone[2].output='REJECT'
firewall.@rule[11]=rule
firewall.@rule[11].name='Allow-USB-ssh'
firewall.@rule[11].proto='tcp'
firewall.@rule[11].src='usb'
firewall.@rule[11].dest_port='22'
firewall.@rule[11].target='ACCEPT'
firewall.@rule[12]=rule
firewall.@rule[12].name='Allow-USB-NTP'
firewall.@rule[12].proto='udp'
firewall.@rule[12].src='usb'
firewall.@rule[12].dest_port='123'
firewall.@rule[12].target='ACCEPT'
firewall.@rule[13]=rule
firewall.@rule[13].name='Allow-USB-HTTP'
firewall.@rule[13].proto='tcp'
firewall.@rule[13].src='usb'
firewall.@rule[13].dest_port='80'
firewall.@rule[13].target='ACCEPT'
firewall.@rule[14]=rule
firewall.@rule[14].name='Allow-LAN-NTP'
firewall.@rule[14].proto='udp'
firewall.@rule[14].src='lan'
firewall.@rule[14].dest_port='123'
firewall.@rule[14].target='ACCEPT'
firewall.@nat[0]=nat
firewall.@nat[0].proto='udp'
firewall.@nat[0].src='lan'
firewall.@nat[0].dest_port='123'
firewall.@nat[0].target='SNAT'
firewall.@nat[0].name='SNAT-NTP'
firewall.@nat[0].src_ip='192.168.2.0/24'
firewall.@nat[0].snat_ip='<br-lan IP>'
firewall.@nat[0].device='br-lan'
firewall.@nat[1]=nat
firewall.@nat[1].name='SNAT-DNS'
firewall.@nat[1].proto='udp'
firewall.@nat[1].dest_port='53'
firewall.@nat[1].target='SNAT'
firewall.@nat[1].src='lan'
firewall.@nat[1].src_ip='192.168.2.0/24'
firewall.@nat[1].snat_ip='<br-lan IP>'
firewall.@nat[1].device='br-lan'
firewall.@nat[2]=nat
firewall.@nat[2].name='SNAT-PING'
firewall.@nat[2].target='SNAT'
firewall.@nat[2].src='lan'
firewall.@nat[2].src_ip='192.168.2.0/24'
firewall.@nat[2].snat_ip='<br-lan IP>'
firewall.@nat[2].device='br-lan'
firewall.@nat[2].proto='icmp'
firewall.@rule[15]=rule
firewall.@rule[15].name='Allow-USB-OUT-SSH'
firewall.@rule[15].proto='tcp'
firewall.@rule[15].dest='usb'
firewall.@rule[15].dest_port='22'
firewall.@rule[15].target='ACCEPT'
firewall.@rule[16]=rule
firewall.@rule[16].name='Allow-USB-OUT-NTP'
firewall.@rule[16].proto='udp'
firewall.@rule[16].dest='usb'
firewall.@rule[16].dest_port='123'
firewall.@rule[16].target='ACCEPT'
firewall.@rule[17]=rule
firewall.@rule[17].name='Alow-USB-OUT-PING'
firewall.@rule[17].proto='icmp'
firewall.@rule[17].dest='usb'
firewall.@rule[17].target='ACCEPT'
firewall.@rule[18]=rule
firewall.@rule[18].name='Allow-USB-PING'
firewall.@rule[18].proto='icmp'
firewall.@rule[18].target='ACCEPT'
firewall.@rule[18].src='usb'
firewall.@rule[19]=rule
firewall.@rule[19].name='Allow-USB-DNS'
firewall.@rule[19].proto='udp'
firewall.@rule[19].dest_port='53'
firewall.@rule[19].target='ACCEPT'
firewall.@rule[19].src='usb'
firewall.@rule[20]=rule
firewall.@rule[20].name='Allow-USB-OUT-DNS'
firewall.@rule[20].proto='udp'
firewall.@rule[20].dest_port='53'
firewall.@rule[20].target='ACCEPT'
firewall.@rule[20].src='usb'
firewall.@forwarding[1]=forwarding
firewall.@forwarding[1].src='usb'
firewall.@forwarding[1].dest='lan'
network.usb=interface
network.usb.proto='static'
network.usb.netmask='255.255.255.0'
network.usb.device='usb0'
network.usb.ipaddr='192.168.2.1'
system.@system[0].zonename='<Zone Name>'
system.@system[0].timezone='<Time Zone>'
```

### Kindle Weather Display server setup
Copy kindle-weather-display-for-openwrt to OpenWrt
```
# opkg install unzip
# unzip kindle-weather-display-for-openwrt.zip
# mkdir /opt
# mv kindle-weather-display-for-openwrt/opt/kindle-weather-station /opt/
# cd /opt/kindle-weather-station
```

Edit API keys for OpenWeatherMap and cloudconvert in settings.json and cloudconvert.json

Edit crontab and restart cron
```
# crontab -e

0 * * * * sh -c "/opt/kindle-weather-station/kindle-weather.sh"
```
```
# /etc/init.d/cron stop
# /etc/init.d/cron start
```

`createSVGv2.py` runs at hourly intervals and create these files: `KindleStation.svg`, `KindleStation.png` and `KindleStation_flatten.png`

## Kindle setup
Copy kindle-weather-display-for-openwrt to Kindle
```
# scp kindle-weather-display-for-openwrt.zip root@192.168.2.2:/tmp
```
Login to Kindle and copy these files
```
# ssh root@192.168.2.2
# cd /tmp
# unzip kindle-weather-display-for-openwrt.zip
# mv kindle-weather-display-for-openwrt/kindle/kindle-weather /mnt/us
# mv kindle-weather-display-for-openwrt/kindle/launchpad /mnt/us
# cd /mnt/us/kindle-weather
# mv disable enable
```
Edit crontab and restart cron
```
# mntroot rw
# nano /etc/crontab/root

2 * * * * sh -c "/mnt/us/kindle-weather/weather-script.sh"
0 * * * * sh -c "/usr/bin/ntpdate 0.jp.pool.ntp.org"

# mntroot ro
# /etc/init.d/cron stop
# kill $(pidof crond)
# /etc/init.d/cron start
# pidof crond
```
`cron` starts to run to download `KindleStation_flatten.png` from OpenWrt server and synchronize the clock at hourly intervals

Create ssh rsa key
```
# mkdir /mnt/us/.ssh
# cd /mnt/us/.ssh
# ssh-keygen -t rsa
Generating public/private rsa key pair.
Enter file in which to save the key (/tmp/root/../../../../../../mnt/us/usbnet/etc/dot.ssh/id_rsa): /mnt/us/.ssh/id_rsa
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /mnt/us/.ssh/id_rsa.
Your public key has been saved in /mnt/us/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:PoCOk8QP8ZqA0n/c+ON8IBPpBZ6SPba6cpCS7ru89Vc root@kindle
The key's randomart image is:
+---[RSA 2048]----+
|                 |
|      .          |
|  .  + +         |
|.o oo.O .        |
|+.=.o+.=S        |
|+ooX .==.E       |
|..*o+.+o=.       |
|..o.+. +...      |
|.*+o.o..+o       |
+----[SHA256]-----+ 
# scp -i /mnt/us/.ssh/id_rsa id_rsa.pub root@192.168.2.1:/tmp
```
Add pub key to OpenWrt
```
# cat /tmp/id_rsa.pub >> /etc/dropbear/authorized_keys
```
## How to terminate a running Kindle Weather Display
```
# ssh root@192.168.2.2

# cd /mnt/us/kindle-weather
# mv enable disable
```
Comment out cronjobs
```
# nano /etc/crontab/root

#2 * * * * sh -c "/mnt/us/kindle-weather/weather-script.sh"
#0 * * * * sh -c "/usr/bin/ntpdate 0.jp.pool.ntp.org"
```
Type `Shift`, `q` and `q` keys quickly and soon start rebooting
