#!/usr/bin/env python3
# encoding=utf-8
# -*- coding: utf-8 -*-

# Written by : krishna@hottunalabs.net
# Date       : 16 February 2022 
#
# This script was modified from:

# Author : Greg Fabre - http://www.iero.org
# Public domain source code
# Published March 2015
# Update October 2016

# This code creates an SVG image, ready for Kindle 600x800 screen.
# With weather information from Netatmo weather station and
# forecast from forecast.io.

# Please fill settings.json file

import time as t
import math
import sys
import json
import re
from datetime import datetime, timedelta, date
from pytz import timezone
import pytz
import locale
import shutil
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from subprocess import Popen
from OpenWeatherMapAPIv2 import OpenWeatherMap

settings = "settings.json"
svgfile = "/tmp/KindleStation.svg"
pngfile = "/tmp/KindleStation.png"
pngtmpfile = "/tmp/.KindleStation.png"
flatten_pngfile = "/tmp/KindleStation_flatten.png"
error_image = "./img/error_service_unavailable.png"
i18nfile = "i18n.json"
coverter = 'convert'


class SVGtext:
    def __init__(self, anchor, fontsize, x, y, va):
        self.anchor = anchor
        self.fontsize = fontsize
        self.x = x
        self.y = y
        self.va = va

    def code(self):
        res = '<text style="text-anchor:{};" font-size="{}" x="{}" y="{}">{}</text>\n'.\
               format(self.anchor, self.fontsize, self.x, self.y, self.va)

        return res 


class SVGtext2:
    def __init__(self, anchor, fontweight, fontsize, x, y, va):
        self.anchor = anchor
        self.fontweight = fontweight
        self.fontsize = fontsize
        self.x = x
        self.y = y
        self.va = va

    def code(self):
        res = '<text style="text-anchor:{};" font-weight="{}" font-size="{}" x="{}" y="{}">{}</text>\n'.\
               format(self.anchor, self.fontweight, self.fontsize, self.x, self.y, self.va)

        return res


class SVGcircle:
    def __init__(self, cx, cy, r, stroke, width, fill):
        self.cx = cx
        self.cy = cy
        self.r = r
        self.stroke = stroke
        self.width = width
        self.fill = fill

    def code(self):
        res = '<circle cx="{}" cy="{}" r="{}" stroke="{}" stroke-width="{}" fill="{}"/>\n'.\
               format(self.cx, self.cy, self.r, self.stroke, self.width, self.fill)

        return res


class SVGline:
    def __init__(self, x1, x2, y1, y2, style):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.style = style

    def code(self):
        res = '<line x1="{}" x2="{}" y1="{}" y2="{}" style="{}"/>\n'.\
                format(self.x1, self.x2, self.y1, self.y2, self.style)

        return res


class SVGtransform:
    def __init__(self, matrix, obj):
        self.matrix = matrix
        self.obj = obj

    def code(self):
        res  = '<g transform="matrix{}">{}</g>\n'.format(self.matrix, self.obj)

        return res


def s_padding(x):
    if x >= 100 : return -5
    elif 100 > x >= 10 : return 10
    elif 10 > x >= 0 : return 30
    elif -10 < x < 0 : return 20
    elif x <= -10 : return 0


def text_split(length, text, start_text="" , match=""):
    text_list = text.split()
    b1 = start_text
    s = list()
    n = int(0)
    for v in text_list:
        n += 1
        b2 = b1
        b1 += v + " "
        if len(text_list) == n:
            s += [b1 + "\n"]
        elif re.match(r'{}'.format(match), v) and not match == '':
            s += [b2 + "\n"]
            b1 = v + " "
        elif re.match(r'^\*$', v) and not match == '':
            s += [b2 + "\n"]
            b1 = v + " "
        elif len(b1) < length:
            continue
        elif len(b1) >= length:
            s += [b2 + "\n"]
            b1 = v + " "

    return s


def add_header(p, t_now, tz):
    curt_weather = p.current_weather()
    base_x = int(0)
    base_y = int(40)
    if p.sunrise_and_sunset == True:
        if curt_weather[11] == 0:
            t_sunrise = "n/a"
        else:
            t_sunrise = str(datetime.fromtimestamp(curt_weather[11], tz).strftime("%H:%M"))

        if curt_weather[12] == 0:
            t_sunset = "n/a"
        else:
            t_sunset = str(datetime.fromtimestamp(curt_weather[12], tz).strftime("%H:%M"))

        # localtime
        maintenant = (str.lower(datetime.fromtimestamp(t_now, tz).strftime("%a, %d %b %H:%M")))
        w = maintenant.split()
        d = read_i18n(p)
        w[0] = d["abbreviated_weekday"][w[0][:-1]] + ',' if not d == dict() else w[0]
        w[2] = d["abbreviated_month"][w[2]] if not d == dict() else w[2]
        s_text1 = SVGtext("start", "30px", (base_x + 20), (base_y + 0), ' '.join(w))
        s_text2 = SVGtext("end", "30px", (base_x + 445), (base_y + 0), t_sunrise)
        s_text3 = SVGtext("end", "30px", (base_x + 580),(base_y + 0),t_sunset)

        s = s_text1.code() + s_text2.code() + s_text3.code()

    else:
        maintenant = str.lower(datetime.fromtimestamp(t_now, tz).strftime("%a %Y/%m/%d %H:%M"))
        w = maintenant.split()
        d = read_i18n(p)
        w[0] = d["abbreviated_weekday"][w[0]] if not d == dict() else w[0]
        s_text1 = SVGtext("start", "30px", (base_x + 20), (base_y + 0), p.city)
        s_text2 = SVGtext("end", "30px", (base_x + 580), (base_y + 0), ' '.join(w))
        s = s_text1.code() + s_text2.code()

    return s


def add_alerts(p, base_y, max_y):
    alerts = p.weather_alerts()
    s = str()
    c = text_split(length=35, text=alerts[0]['event'], start_text="ALERT: ")

    for v in c:
        s_text = SVGtext2("start", "bold", "30px", "20", base_y, str(v))
        s += s_text.code()
        base_y += 40

    s_text = SVGtext("start", "20px", "30", base_y, "Description:")
    s += s_text.code()
    base_y += 30

    v1 = alerts[0]['description']
    v1 = re.sub(r'\n', ' ', v1, flags=re.MULTILINE)
    base_x = 40
    length = 60
    #length = 57
    flag = True
    v1_list = text_split(length=length, text=v1, match='\*')
    for v2 in v1_list:
        if base_y > max_y -35:
            v2 = v2[:-2]
            v2 += "..."
            s_text = SVGtext("start", "18px", base_x, base_y, str(v2))
            s += s_text.code()
            flag = False
            break
        else:
            s_text = SVGtext("start", "18px", base_x, base_y, str(v2))
            s += s_text.code()

        base_y += 30

    return s


def add_curt_weather_disc(p, base_x, base_y, disc_offset=0, wordwrap=0):
    curt_weather = p.current_weather()
    today_forecast = p.daily_forecast(0)
    s = str()

    # Temperature
    tempEntier = math.floor(curt_weather[5])
    tempDecimale = 10 * (curt_weather[5] - tempEntier)

    s1_temp1 = SVGtext("end", "100px", (base_x + 25), (base_y - 130), int(tempEntier))
    s1_temp2 = SVGtext("start", "50px", (base_x + 20), (base_y - 135), "." + str(int(tempDecimale)))
    s1_temp3 = SVGcircle((base_x + 40), (base_y - 200), 7, "black", 3, "none")
    s1_temp4 = SVGtext("start", "35px", (base_x + 50), (base_y - 180), p.unit['temp'])
    s1_temp_text = s1_temp1.code() + s1_temp2.code() + s1_temp3.code() + s1_temp4.code()

    # Max
    s3_max1 = SVGtext("end", "35px", (base_x + 150), (base_y - 170), int(math.ceil(today_forecast[7])))
    s3_max2 = SVGcircle((base_x + 155), (base_y - 190), 4, "black", 3, "none")
    s3_max3 = SVGtext("start", "25px", (base_x + 160), (base_y - 178), p.unit['temp'])

    # line
    s3_line = SVGline((base_x + 90), (base_x + 190), (base_y - 163), (base_y - 163), "fill:none;stroke:black;stroke-width:1px;")

    # Min
    s3_min1 = SVGtext("end", "35px", (base_x + 150), (base_y - 130), int(math.ceil(today_forecast[6])))
    s3_min2 = SVGcircle((base_x + 155), (base_y - 150), 4, "black", 3, "none")
    s3_min3 = SVGtext("start", "25px", (base_x + 160), (base_y - 138), p.unit['temp'])
    s3_minmax_text = s3_max1.code() + s3_max2.code() + s3_max3.code() + s3_line.code() + s3_min1.code() + s3_min2.code() + s3_min3.code()

    if p.alerts == True and not p.weather_alerts() is None:
        # Pressure
        s2_pres = SVGtext("end", "30px", (base_x + 150 + disc_offset),(base_y - 80), str(round(curt_weather[6])) + p.unit['pressure'])

        # Humidity
        s2_humi = SVGtext("end", "30px", (base_x + 0 + disc_offset), (base_y - 80), str(round(curt_weather[7])) + "%")

        # Wind
        s2_wind = SVGtext("end", "30px", (base_x + 150 + disc_offset),(base_y - 40), str(int(curt_weather[8])) + " " + p.unit['wind_speed'])

        # description
        disc = [curt_weather[3]]
        s2_desc_text = str()
        n = 0
        for w in disc:
            s2_desc_text += SVGtext("end", "30px", (base_x + 150 + disc_offset), (base_y + n), w).code()
            n += 35
    else:
        base_y += 5
        # Pressure
        s2_pres = SVGtext("end", "30px", (base_x + 150 + disc_offset),(base_y - 80), str(round(curt_weather[6])) + p.unit['pressure'])

        # Humidity
        s2_humi = SVGtext("end", "30px", (base_x + 25 + disc_offset), (base_y - 80), str(round(curt_weather[7])) + "%")

        # Wind
        s2_wind = SVGtext("end", "30px", (base_x - 45 + disc_offset),(base_y - 80), str(int(curt_weather[8])) + p.unit['wind_speed'])

        # description
        disc = text_split(length=wordwrap, text=curt_weather[3])
        s2_desc_text = str()
        n = 0
        for w in disc:
            s2_desc_text += SVGtext("end", "30px", (base_x + 150 + disc_offset), (base_y - 40 + n), w).code()
            n += 35

    s2_text = s2_pres.code() + s2_humi.code() + s2_wind.code() + s2_desc_text

    s = s1_temp_text + s2_text + s3_minmax_text

    return s


def add_curt_weather_precipitation(p, base_x, base_y):
    curt_weather = p.current_weather()
    s = str()

    # probability of precipitation
    if (curt_weather[2] == 'Rain' or curt_weather[2] == 'Drizzle' or
            curt_weather[2] == 'Snow' or curt_weather[2] == 'Sleet' or curt_weather[2] == 'Clouds'):

        r = Decimal(curt_weather[14]).quantize(Decimal('0.1'), rounding=ROUND_HALF_EVEN)

        if r == 0:
            s1_prob = SVGtext("end", "45px", (base_x - 205 - int(s_padding(r) * 0.64)), (base_y - 105), "n/a")
            s += s1_prob.code()

        else:
            s1_prob = SVGtext("end", "45px", (base_x - 210 - int(s_padding(r) * 0.64)), (base_y - 105), \
                      Decimal(float(r)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
            s += s1_prob.code()

    return s


def add_curt_weather(p, base_x, base_y, disc_offset, wordwrap):
    curt_weather = p.current_weather()
    s = str()

    if p.alerts == True and not (p.weather_alerts() is None):
        s += add_curt_weather_precipitation(p=p, base_x=400, base_y=280)
    else:
        s += add_curt_weather_precipitation(p=p, base_x=405, base_y=280)
    s += add_curt_weather_disc(p=p, base_x=base_x, base_y=base_y, disc_offset=disc_offset, wordwrap=wordwrap)
    return s


def add_curt_weather_alerts(p, base_x, base_y):
    curt_weather = p.current_weather()
    s = str()

    s += add_curt_weather_precipitation(p=p, base_x=base_x, base_y=base_y)
    s += add_curt_weather_disc(p=p, base_x=base_x, base_y=base_y)

    return s


def text_temp_unit(base_x, base_y, text, unit):
    s1_text1 = SVGtext("end", "35px", (base_x), (base_y), text)
    s1_circle2 = SVGcircle((base_x + 5), (base_y - 25), 4, "black", 2, "none")
    s1_text3 = SVGtext("start", "25px", (base_x + 10), (base_y  - 10), unit)

    s = s1_text1.code() + s1_circle2.code() + s1_text3.code()

    return s


def add_hourly_forecast_precipitation(hourly_forecast, base_x, base_y):
    s = str()

    # probability of precipitation
    w = hourly_forecast[2]
    if w == 'Rain' or w == 'Drizzle' or w == 'Snow' or w == 'Sleet' or w == 'Clouds':
        r = Decimal(hourly_forecast[7]).quantize(Decimal('0.1'), rounding=ROUND_HALF_EVEN)
        if r == 0:
            s1 = SVGtext("end", "25px", int(base_x + 10 - s_padding(r) * 0.357), (base_y - 78), 'n/a')
            s += s1.code()
        else:
            s1 = SVGtext("end", "25px", int(base_x + 7 - s_padding(r) * 0.357), (base_y - 78), r)
            s += s1.code()

    return s


def add_hourly_forecast(p, tz, base_x, base_y, pitch):
    hourly_icon = list()
    s = str()
 
    # 3h forecast
    for i in range(3, 12, 3):
        hourly_forecast = p.hourly_forecast(i)
        jour = datetime.fromtimestamp(hourly_forecast[0], tz)

        hours = {3: "three hours later", 6: "six hours later", 9: "nine hours later"}

        d = read_i18n(p)
        if not d == dict():
            for k in hours.keys():
                hours[k] = d["hours"][hours[k]]

        s1 = SVGtext("start", "25px", (base_x - 130), (base_y - 5), hours[i])
        #s1 = SVGtext("end", "25px", (base_x + 80), (base_y - 5), hours[i])
        s1_text1 = text_temp_unit(base_x=(base_x - 100), base_y=(base_y - 74), text=round(hourly_forecast[5]), unit=p.unit['temp'])
        s1_text2 = add_hourly_forecast_precipitation(hourly_forecast=hourly_forecast, base_x=base_x, base_y=base_y)

        s += s1.code() + s1_text1 + s1_text2

        base_y += pitch

    return s


def add_daily_forecast(p, base_x, base_y, pitch):
    minTemp = math.floor(min([p.daily_forecast(1)[6], p.daily_forecast(2)[6] , p.daily_forecast(3)[6]]))
    maxTemp = math.ceil(max([p.daily_forecast(1)[7], p.daily_forecast(2)[7] , p.daily_forecast(3)[7]]))
    pasTemp = 120 / (maxTemp-minTemp)

    s = str()
    n = 0
    d = read_i18n(p)
    for i in range(1, 4):
        forecast = p.daily_forecast(i)
        tLow = math.floor(forecast[6])
        tHigh = math.ceil(forecast[7])
        jour = datetime.fromtimestamp(forecast[0], tz)
        tMin = (int)(base_x + 355 + pasTemp * (tLow - minTemp))
        tMax = (int)(base_x + 440 + pasTemp * (tHigh - minTemp))

        w = str.lower(jour.strftime("%A"))
        w = d["full_weekday"][w] if not d == dict() else w

        s1 = SVGtext("end", "35px", (base_x + 185), (base_y + n), w)
        s1_text1 = text_temp_unit(base_x=tMin, base_y=(base_y + n), text=int(tLow), unit=p.unit['temp'])
        s1_text2 = text_temp_unit(base_x=int(tMax - s_padding(tHigh)), base_y=(base_y + n), text=int(tHigh), unit=p.unit['temp'])
        s1_line = SVGline(int(tMin + 40), int(tMax - 65), (base_y + n - 10), (base_y + n - 10), "fill:none;stroke:black;stroke-linecap:round;stroke-width:10px;")

        s += s1.code() + s1_text1 + s1_text2 + s1_line.code()
        n += pitch

    return s


def add_sunrise_and_sunset_icons(p):
    r = p.header()
    s = str()
    s1 = SVGtransform("(1.1,0,0,1.1,332,14)", p.header.icons['sunrise']) 
    s2 = SVGtransform("(1.1,0,0,1.1,467,14)", p.header.icons['sunset'])

    return s1.code() + s2.code()


def add_today_icon(p):
    curt_weather = p.current_weather()
    s = str()
    if p.alerts == True and not (p.weather_alerts() is None):
        s1 = SVGtransform("(4,0,0,4,-35,-40)", p.current_weather.icons[0])
    else:
        s1 = SVGtransform("(4,0,0,4,-30,-40)", p.current_weather.icons[0])
    s = s1.code()

    return s

def add_wind_direction_icon(p, base_x, base_y, disc_offset=0):
    curt_weather = p.current_weather()
    s = str()
    r = p.current_weather.icons['cardinal']
    w = base_x + 40 - len(str(int(curt_weather[8]))) * 17 + disc_offset
    s1 = SVGtransform("(1.6,0,0,1.6," + str(w) + "," + str(base_y - 74) + ")", r)
    s += s1.code()

    return s


def add_next_hours_icons(p, base_x, base_y, pitch):
    n = 0
    s = str()
    for i in range(3, 12, 3):
        s1 = SVGtransform("(2.3,0,0,2.3," + str(base_x - 122) + "," + str(base_y - 202 + n) + ")", p.hourly_forecast.icons[i])
        s += s1.code()
        n += pitch

    return s


def add_next_days_icons(p, base_x, base_y, pitch):
    n = 0
    base_x = 160
    base_y = 470
    pitch = 90
    s = str()
    for i in range(1, 4):
        s1 = SVGtransform("(1.9,0,0,1.9," + str(base_x) + "," + str(base_y + n) + ")", p.daily_forecast.icons[i])
        s += s1.code()
        n += pitch

    return s


def create_svg(p, t_now, tz, utc, svgfile, pngfile):

    svg_header = str()
    svg_text = str()
    svg_icons = str()
    svg_footer = str()

    f_svg = open(svgfile,"w", encoding=p.encoding)

    # Header
    svg_header += '''<?xml version="1.0" encoding="{}"?>
<svg xmlns="http://www.w3.org/2000/svg" height="800" width="600" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink">\n'''.format(p.encoding)
    svg_header += '<g font-family="{}">\n'.format(p.font)
    #svg_header += '<g font-family="{}">\n'.format("Chalkboard")
    #svg_header += '<g font-family="{}">\n'.format("Arial")

    # Document area
    svg_text += add_header(p=p, t_now=t_now, tz=tz)

    base_x = 130
#    base_y = 480
    base_y = 485
    disc_offset = 35
    wordwrap = 20
    svg_text += add_curt_weather(p=p, base_x=base_x, base_y=base_y, disc_offset=disc_offset, wordwrap=wordwrap)

    if p.sunrise_and_sunset == True:
        svg_icons += add_sunrise_and_sunset_icons(p) 

    svg_icons += add_today_icon(p)

    curt_weather = p.current_weather()
    if int(curt_weather[8]) != 0:
       base_y += 5 
       svg_icons += add_wind_direction_icon(p=p, base_x=(base_x - 180), base_y=(base_y - 40), disc_offset=disc_offset)

    base_x = 500
    base_y = 210
    #base_y = 200
    pitch = 155
    #pitch = 150
    svg_text += add_hourly_forecast(p=p, tz=tz, base_x=base_x, base_y=base_y, pitch=pitch)
    svg_icons += add_next_hours_icons(p=p, base_x=base_x, base_y=base_y, pitch=pitch)

    base_x = 0
    base_y = 575
    pitch = 90
    svg_text += add_daily_forecast(p, base_x, base_y, pitch)
    svg_text += '</g>\n'

    base_x = 160
    base_y = 470
    pitch = 90
    svg_icons += add_next_days_icons(p=p, base_x=base_x, base_y=base_y, pitch=pitch)

    svg_footer += '</svg>' 

    f_svg.write(svg_header + svg_text + svg_icons + svg_footer)

    # close file
    f_svg.close()


def create_alerts_svg(p, t_now, tz, utc, svgfile, pngfile):

    svg_header = str()
    svg_text = str()
    svg_icons = str()
    svg_footer = str()

    f_svg = open(svgfile,"w", encoding=p.encoding)

    # Header
    svg_header += '''<?xml version="1.0" encoding="{}"?>
<svg xmlns="http://www.w3.org/2000/svg" height="800" width="600" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink">\n'''.format(p.encoding)
    svg_header += '<g font-family="{}">\n'.format(p.font)
    #svg_header += '<g font-family="{}">\n'.format("Chalkboard")
    #svg_header += '<g font-family="{}">\n'.format("Arial")

    # Document area
    svg_text += add_header(p=p, t_now=t_now, tz=tz)

    if p.sunrise_and_sunset == True:
        svg_icons += add_sunrise_and_sunset_icons(p)

    svg_icons += add_today_icon(p)

    base_x = 400
    base_y = 280
    disc_offset = 0
    svg_text += add_curt_weather_alerts(p=p, base_x=base_x, base_y=base_y)

    curt_weather = p.current_weather()
    if int(curt_weather[8]) != 0:
         svg_icons += add_wind_direction_icon(p=p, base_x=base_x, base_y=base_y, disc_offset=disc_offset)

    base_y = 340
    max_y = 800
    svg_text += add_alerts(p=p, base_y=base_y, max_y=max_y)
    svg_text += '</g>\n'

    svg_footer += '</svg>'

    f_svg.write(svg_header + svg_text + svg_icons + svg_footer) 
    # close file
    f_svg.close()


# image processing
def img_processing(p, svgfile, pngfile, pngtmpfile, mode):

    if p.cloudconvert == False and (p.encoding == 'iso-8859-1' or p.encoding == 'iso-8859-5'):
        if converter == 'convert':
            args = ['convert', '-size', '600x800', '-background', 'white', '-depth', '8', svgfile, pngfile]
        elif covnerter == 'gm':
            args = ['gm', 'convert', '-size', '600x800', '-background', 'white', '-depth', '8', \
                    '-resize', '600x800', '-colorspace', 'gray', '-type', 'palette', '-geometry', '600x800', \
                    svgfile, pngfile]

        output = Popen(args)
    elif p.cloudconvert == True:
        # cloudconvert API
        import cloudconvert
        import json

        with open('cloudconvert.json') as f:
            data = json.load(f)

#        print(data['api_key'])
        cloudconvert.configure(api_key=data['api_key'], sandbox=False)

        try:
            # upload
            job = cloudconvert.Job.create(payload={
                'tasks': {
                    'upload-my-file': {
                        'operation': 'import/upload'
                    }
                }
            })

            upload_task_id = job['tasks'][0]['id']

            upload_task = cloudconvert.Task.find(id=upload_task_id)
            res = cloudconvert.Task.upload(file_name=svgfile, task=upload_task)

            res = cloudconvert.Task.find(id=upload_task_id)

            # convert
            job = cloudconvert.Job.create(payload={
                 "tasks": {
                     'convert-my-file': {
                         'operation': 'convert',
                         'input': res['id'],
                         'output_format': 'png',
                         'some_other_option': 'value'
                     },
                     'export-my-file': {
                         'operation': 'export/url',
                         'input': 'convert-my-file'
                     }
                 }
            })

            # download
            exported_url_task_id = job['tasks'][1]['id']
            res = cloudconvert.Task.wait(id=exported_url_task_id) # Wait for job completion
            file = res.get("result").get("files")[0]
            res = cloudconvert.download(filename=pngfile, url=file['url'])  # download and return filename

        except Exception as e:
            print(e)

    if mode == 'darkmode':
        args = ['convert', '-flatten', pngfile, pngtmpfile]
        output = Popen(args)
        t.sleep(3)
        args = ['convert', '-negate', pngtmpfile, flatten_pngfile]
        output = Popen(args)
    elif mode == 'lightmode':
        args = ['convert', '-flatten', pngfile, flatten_pngfile]
        output = Popen(args)
    else:
        args = ['convert', '-flatten', pngfile, flatten_pngfile]
        output = Popen(args)

    #t.sleep(3)


def read_i18n(p):
    with open(i18nfile, 'r') as f:
        try:
            d = json.load(f)["locale"][p.t_locale]
        except:
            d = dict()
    return d


if __name__ == "__main__":

    # Using custom settings.xml
    if len(sys.argv) > 1:
        settings = sys.argv[1]

    try:
        p = OpenWeatherMap(settings)
    except Exception as e:
        shutil.copyfile(error_image, flatten_pngfile)
        print(e)
        exit(1)

    curt_weather = p.current_weather()

    # timezone setting
    t_now = p.t_now
    tz = timezone(p.t_timezone)
    utc = pytz.utc

    if p.darkmode == 'True':
        mode = 'darkmode'
    elif p.darkmode == 'Auto':
        if curt_weather[11] > t_now or curt_weather[12] < t_now:
            mode = 'darkmode'
        else:
            mode = 'lightmode'
    elif p.darkmode == 'False':
        mode = 'lightmode'
    else:
        mode = 'lightmode'

    # locale setting
    #locale.setlocale(locale.LC_TIME, p.t_locale)
    locale.setlocale(locale.LC_TIME, "en_US.utf-8")

    if p.alerts == True and not (p.weather_alerts() is None):
        create_alerts_svg(p=p, t_now=t_now, tz=tz, utc=utc, svgfile=svgfile, pngfile=pngfile)
    else:
        create_svg(p=p, t_now=t_now, tz=tz, utc=utc, svgfile=svgfile, pngfile=pngfile)

    t.sleep(1)
    img_processing(p=p, svgfile=svgfile, pngfile=pngfile, pngtmpfile=pngtmpfile, mode=mode)
