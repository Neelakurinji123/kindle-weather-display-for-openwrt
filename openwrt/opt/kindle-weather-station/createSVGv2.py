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
import math
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


class Header:
    def __init__(self, p):
        self.p = p

    def text(self):
        tz = timezone(self.p.t_timezone)
        p = self.p
        curt_weather = self.p.current_weather()
        t_now = self.p.t_now
        tz = timezone(self.p.t_timezone)
        sunrise_and_sunset = self.p.sunrise_and_sunset
        svg_text = str()

        svg_text += '''<?xml version="1.0" encoding="{}"?>
<svg xmlns="http://www.w3.org/2000/svg" height="800" width="600" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink">\n'''.format(p.encoding)
        svg_text += '<g font-family="{}">\n'.format(p.font)
        #svg_text += '<g font-family="{}">\n'.format("Chalkboard")
        #svg_text += '<g font-family="{}">\n'.format("Arial")

        return svg_text


class Maintenant:
    def __init__(self, p, base_x, base_y):
        self.p = p
        self.base_x = base_x
        self.base_y = base_y

    def text(self):
        p = self.p
        curt_weather = p.current_weather()
        tz = timezone(p.t_timezone)
        t_now = p.t_now
        x = self.base_x
        y = self.base_y
        sunrise_and_sunset = p.sunrise_and_sunset
        svg_text = str()

        if sunrise_and_sunset == True:
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

            svg_text += SVGtext("start", "30px", (x + 20), (y + 40), ' '.join(w)).svg()
            svg_text += SVGtext("end", "30px", (x + 445), (y + 40), t_sunrise).svg()
            svg_text += SVGtext("end", "30px", (x + 580),(y + 40),t_sunset).svg()
        else:
            maintenant = str.lower(datetime.fromtimestamp(t_now, tz).strftime("%a %Y/%m/%d %H:%M"))
            w = maintenant.split()
            d = read_i18n(p)
            w[0] = d["abbreviated_weekday"][w[0]] if not d == dict() else w[0]
            svg_text += SVGtext("start", "30px", (x + 20), (y + 40), p.city).svg()
            svg_text += SVGtext("end", "30px", (x + 580), (y + 40), ' '.join(w)).svg()

        return svg_text


    def icon(self):
        p = self.p
        tz = timezone(p.t_timezone)
        curt_weather = p.current_weather()
        sunrise_and_sunset = self.p.sunrise_and_sunset
        x = self.base_x
        y = self.base_y
        svg_icon = str()

        if p.sunrise_and_sunset == True:
            svg_icon += SVGtransform("(1.1,0,0,1.1," + str(x + 332) + "," + str(y + 14) + ")", p.header_icons['sunrise']).svg() 
            svg_icon += SVGtransform("(1.1,0,0,1.1," + str(x + 467) + "," + str(y + 14) + ")", p.header_icons['sunset']).svg()

        return svg_icon


class CurrentWeather:

    def add_curt_weather_prec(self):
        p = self.p
        curt_weather = p.current_weather()
        x = self.base_x
        y = self.base_y
        svg_text = str()

        # probability of precipitation
        if (curt_weather[2] == 'Rain' or curt_weather[2] == 'Drizzle' or
                curt_weather[2] == 'Snow' or curt_weather[2] == 'Sleet' or curt_weather[2] == 'Clouds'):

#            r = Decimal(curt_weather[14]).quantize(Decimal('0.1'), rounding=ROUND_HALF_EVEN)
            r = Decimal(curt_weather[15]).quantize(Decimal('0.1'), rounding=ROUND_HALF_EVEN)

            if r == 0:
                svg_text += SVGtext("end", "45px", (x + 200 - int(s_padding(r) * 0.64)), (y + 135), "n/a").svg()

            else:
                svg_text += SVGtext("end", "45px", (x + 195 - int(s_padding(r) * 0.64)), (y + 135), \
                          Decimal(float(r)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)).svg()

        return svg_text

    def add_curt_weather_temp(self):
        p = self.p
        curt_weather = p.current_weather()
        today_forecast = p.daily_forecast(0)
        x = self.base_x
        y = self.base_y
        disc_offset = self.disc_offset
        wordwrap= self.wordwrap
        svg_text = str()

        # Temperature
        tempEntier = math.floor(curt_weather[5])
        tempDecimale = 10 * (curt_weather[5] - tempEntier)

        svg_text += SVGtext("end", "100px", (x + 155), (y + 315), int(tempEntier)).svg()
        svg_text += SVGtext("start", "50px", (x + 150), (y + 310), "." + str(int(tempDecimale))).svg()
        svg_text += SVGcircle((x + 170), (y + 245), 7, "black", 3, "none").svg()
        svg_text += SVGtext("start", "35px", (x + 180), (y + 265), p.unit['temp']).svg()

        # Max temp
        svg_text += SVGtext("end", "35px", (x + 280), (y + 275), int(math.ceil(today_forecast[7]))).svg()
        svg_text += SVGcircle((x + 285), (y + 255), 4, "black", 3, "none").svg()
        svg_text += SVGtext("start", "25px", (x + 290), (y + 267), p.unit['temp']).svg()

        # Line
        svg_text += SVGline((x + 220), (x + 320), (y + 282), (y + 282), "fill:none;stroke:black;stroke-width:1px;").svg()

        # Min temp
        svg_text += SVGtext("end", "35px", (x + 280), (y + 315), int(math.ceil(today_forecast[6]))).svg()
        svg_text += SVGcircle((x + 285), (y + 295), 4, "black", 3, "none").svg()
        svg_text += SVGtext("start", "25px", (x + 290), (y + 307), p.unit['temp']).svg()
        return svg_text

    def add_curt_weather_pres(self):
        p = self.p
        curt_weather = p.current_weather()
        x = self.base_x
        y = self.base_y

        # Pressure
        svg_text = SVGtext("end", "30px", (x + 280 + self.disc_offset),(y + 370), str(round(curt_weather[6])) + p.unit['pressure']).svg()
        return svg_text

    def add_curt_weather_humi(self):
        p = self.p
        curt_weather = p.current_weather()
        x = self.base_x
        y = self.base_y

        # Humidity
        svg_text = SVGtext("end", "30px", (x + 155 + self.disc_offset), (y + 370), str(round(curt_weather[7])) + "%").svg()
        return svg_text

    def add_curt_weather_wind(self):
        p = self.p
        curt_weather = p.current_weather()
        x = self.base_x
        y = self.base_y

        # Wind
        svg_text = SVGtext("end", "30px", (x + 85 + self.disc_offset),(y + 370), str(int(curt_weather[8])) + p.unit['wind_speed']).svg()
        return svg_text

    def add_curt_weather_disc(self):
        curt_weather = self.p.current_weather()
        x = self.base_x
        y = self.base_y
        svg_text = str()

        # Description
        disc = text_split(length=self.wordwrap, text=curt_weather[3])
        for w in disc:
            svg_text += SVGtext("end", "30px", (x + 280 + self.disc_offset), (y + 410), w).svg()
            y += 35

        return svg_text

    def add_curt_weather_icon(self):
        x = self.base_x
        y = self.base_y
        svg_icon = SVGtransform("(4,0,0,4," + str(x - 30) + "," + str(y - 80) + ")", self.p.current_icons[0]).svg()
        return svg_icon

    def add_curt_weather_wind_icon(self):
        p = self.p
        curt_weather = p.current_weather()
        x = self.base_x
        y = self.base_y
        r = p.current_icons['cardinal']
        _x = x - 10 - len(str(int(curt_weather[8]))) * 17 + self.disc_offset
        svg_icon = SVGtransform("(1.6,0,0,1.6," + str(_x) + "," + str(y + 336) + ")", r).svg()

        return svg_icon


class CurrentWeatherNoAlerts(CurrentWeather):
    def __init__(self, p, base_x, base_y, disc_offset, wordwrap):
        self.p = p
        self.base_x = base_x
        self.base_y = base_y
        self.disc_offset = disc_offset
        self.wordwrap = wordwrap

    def text(self):
        prec = super(CurrentWeatherNoAlerts, self).add_curt_weather_prec() 
        temp = super(CurrentWeatherNoAlerts, self).add_curt_weather_temp() 
        pres = super(CurrentWeatherNoAlerts, self).add_curt_weather_pres() 
        humi = super(CurrentWeatherNoAlerts, self).add_curt_weather_humi() 
        wind = super(CurrentWeatherNoAlerts, self).add_curt_weather_wind() 
        disc = super(CurrentWeatherNoAlerts, self).add_curt_weather_disc()
        svg_text = prec + temp + pres + humi + wind + disc

        return svg_text

    def icon(self):
        p = self.p
        curt_weather = p.current_weather()
        disc_offset = 0
        svg_icon = str()

        svg_icon += super(CurrentWeatherNoAlerts, self).add_curt_weather_icon()

        if int(curt_weather[8]) != 0:        
            svg_icon += super(CurrentWeatherNoAlerts, self).add_curt_weather_wind_icon() 

        return svg_icon


class CurrentWeatherAlerts(CurrentWeather):
    def __init__(self, p, base_x, base_y, disc_offset, wordwrap):
        self.p = p
        self.base_x = base_x
        self.base_y = base_y
        self.disc_offset = disc_offset
        self.wordwrap = wordwrap

    def text(self):
        base_x = self.base_x
        base_y = self.base_y
        svg_text = str()

        svg_text += super(CurrentWeatherAlerts, self).add_curt_weather_prec()

        self.base_x = 270
        self.base_y = -160
        svg_text += super(CurrentWeatherAlerts, self).add_curt_weather_temp()

        self.base_x = 270
        self.base_y = -165
        svg_text += super(CurrentWeatherAlerts, self).add_curt_weather_pres()

        self.base_x = 270
        self.base_y = -165
        svg_text += super(CurrentWeatherAlerts, self).add_curt_weather_humi()

        self.base_x = 465
        self.base_y = -125
        svg_text += super(CurrentWeatherAlerts, self).add_curt_weather_wind()

        self.base_x = 270
        self.base_y = -165
        svg_text += super(CurrentWeatherAlerts, self).add_curt_weather_disc()

        return svg_text

    def icon(self):
        p = self.p
        svg_icon = str()
        curt_weather = p.current_weather()
        self.base_x = -5
        self.base_y = 45
        svg_icon += super(CurrentWeatherAlerts, self).add_curt_weather_icon()

        if int(curt_weather[8]) != 0:
            self.base_x = 450
            self.base_y = -125
            svg_icon += super(CurrentWeatherAlerts, self).add_curt_weather_wind_icon()

        return svg_icon


class HourlyWeather:
    def __init__(self, p, base_x, base_y, h_hour, h_range, h_step, pitch):
        self.p = p
        self.base_x = base_x
        self.base_y = base_y
        self.h_hour = h_hour
        self.h_range = h_range
        self.h_step = h_step
        self.pitch = pitch

    # Hourly weather document area (base_x=370 ,base_y=40)
    def text(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        curt_weather = p.current_weather()
        today_forecast = p.daily_forecast(0)
        disc_offset = 0
        wordwrap = 0
        h_hour = self.h_hour
        h_range = self.h_range
        h_step = self.h_step
        pitch = self.pitch
        svg_text = str()
   
        # 3h forecast
        for i in range(h_hour, h_range, h_step):
            hourly = p.hourly_forecast(i)

            hrs = {3: "three hours later", 6: "six hours later", 9: "nine hours later"}

            d = read_i18n(p)
            if not d == dict():
                for k in hrs.keys():
                    hrs[k] = d["hours"][hours[k]]

            svg_text += SVGtext("start", "25px", (x - 0), (y + 165), hrs[i]).svg()
            svg_text += temp_unit(x=(x + 30), y=(y + 96), text=round(hourly[5]), unit=p.unit['temp'])


            # probability of precipitation
            w = hourly[2]
            if w == 'Rain' or w == 'Drizzle' or w == 'Snow' or w == 'Sleet' or w == 'Clouds':
                r = Decimal(hourly[7]).quantize(Decimal('0.1'), rounding=ROUND_HALF_EVEN)
                if r == 0:
                    s1 = SVGtext("end", "25px", int(x + 140 - s_padding(r) * 0.357), (y + 92), 'n/a')
                    svg_text += s1.svg()
                else:
                    s1 = SVGtext("end", "25px", int(x + 137 - s_padding(r) * 0.357), (y + 92), r)
                    svg_text += s1.svg()

            y += pitch

        return svg_text


    def icon(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        h_hour = self.h_hour
        h_range = self.h_range
        h_step = self.h_step
        pitch = self.pitch
        svg_icon = str()

        for i in range(h_hour, h_range, h_step):
            svg_icon += SVGtransform("(2.3,0,0,2.3," + str(x + 8) + "," + str(y - 32) + ")", p.hourly_icons[i]).svg()
            y += pitch

        return svg_icon


class DailyWeather:
    def __init__(self, p, base_x, base_y, d_range, pitch):
        self.p = p
        self.base_x = 0
        self.base_y = 500
        self.pitch = 90
        self.d_range = 4

    def text(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        daily = p.daily_forecast
        pitch = self.pitch
        d_range = self.d_range        
        disc_offset = 0
        wordwrap = 0
        svg_text = str()

        minTemp = math.floor(min([daily(1)[6], daily(2)[6] , daily(3)[6]]))
        maxTemp = math.ceil(max([daily(1)[7], daily(2)[7] , daily(3)[7]]))
        pasTemp = 120 / (maxTemp-minTemp)

        d = read_i18n(p)

        # Drawing temp bars
        for i in range(1, d_range):
            forecast = p.daily_forecast(i)
            tLow = math.floor(forecast[6])
            tHigh = math.ceil(forecast[7])
            jour = datetime.fromtimestamp(forecast[0], tz)
            tMin = (int)(x + 355 + pasTemp * (tLow - minTemp))
            tMax = (int)(x + 440 + pasTemp * (tHigh - minTemp))

            w = str.lower(jour.strftime("%A"))
            w = d["full_weekday"][w] if not d == dict() else w

            svg_text += SVGtext("end", "35px", (x + 185), (y + 75), w).svg()
            svg_text += temp_unit(x=tMin, y=(y + 75), text=int(tLow), unit=p.unit['temp'])
            svg_text += temp_unit(x=int(tMax - s_padding(tHigh)), y=(y + 75), text=int(tHigh), unit=p.unit['temp'])
            svg_text += SVGline(int(tMin + 40), int(tMax - 65), (y + 75 - 10), (y + 75 - 10), "fill:none;stroke:black;stroke-linecap:round;stroke-width:10px;").svg()
            y += pitch

        return svg_text


    def icon(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        pitch = self.pitch
        d_range = self.d_range        
        disc_offset = 0
        svg_icon = str()

        for i in range(1, d_range):
            svg_icon += SVGtransform("(1.9,0,0,1.9,{},{})".format((x + 160), (y -30)), p.daily_icons[i]).svg()
            y += pitch

        return svg_icon


class Alerts:
    def __init__(self, p, base_x, base_y, max_y):
        self.p = p
        self.base_x = base_x
        self.base_y = base_y
        self.max_y = max_y

    def text(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        max_y = self.max_y
        alerts = p.weather_alerts()
        svg_text = str()

        _c = text_split(length=35, text=alerts[0]['event'], start_text="ALERT: ")

        for v in _c:
            svg_text += SVGtext2("start", "bold", "30px", "20", y, str(v)).svg()
            y += 40

        x += 30
        svg_text += SVGtext("start", "20px", x, y, "Description:").svg()

        x += 10
        length = 60
        #length = 57
        _c = alerts[0]['description']
        _c = re.sub(r'\n', ' ', _c, flags=re.MULTILINE)
        flag = True
        _list = text_split(length=length, text=_c, match='\*')
        for v in _list:
            y += 30
            if y > max_y:
                v = v[:-2]
                v += "..."
                _text = SVGtext("start", "18px", x, y, str(v))
                svg_text += _text.svg()
                flag = False
                break
            else:
                _text = SVGtext("start", "18px", x, y, str(v))
                svg_text += _text.svg()

        return svg_text


class DrawGraph:
    def __init__(self, p, base_x, base_y, canvas, object):
        self.p = p
        self.base_x = base_x
        self.base_y = base_y
        self.canvas = canvas
        self.object = object

    def draw(self):
        if self.object['type'] == "line":
            res = DrawGraph.line_graph(self)
        elif self.object['type'] == "bar":
            res = DrawGraph.bar_graph(self)
        elif self.object['type'] == "tile":
            res = DrawGraph.tile(self)

        return res

    def line_graph(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        w = self.canvas["width"]
        h = self.canvas["height"]
        bgcolor = self.canvas["bgcolor"]
        axis = self.canvas["axis"]
        axis_color = self.canvas["axis_color"]
        grid = self.canvas["grid"]
        grid_color = self.canvas["grid_color"]
        stroke = self.object["stroke"]
        stroke_color = self.object["stroke-color"]
        fill = self.object["fill"]
        stroke_linecap = self.object["stroke-linecap"]
        label = bool(eval(self.object["label"]))
        label_adjust = bool(eval(self.object["label_adjust"]))
        name = self.object["name"]
        start = self.object["start"]
        end = self.object["end"]
        step = self.object["step"]
        basis = self.object["basis"]
        svg = '<g font-family="{}">\n'.format(p.font)

        # Canvas
        style = "fill:{};stroke:{};stroke-width:{}px;".format(bgcolor, bgcolor, (0))
        svg += SVGrect(x=(x - 10), y=(y - h + 10), width=(w + 10), height=(h - 45), style=style).svg()
        style = "fill:none;stroke:{};stroke-width:{}px;".format(axis_color, axis)

        # Graph
        points = str()
        _text = str()

        if basis == "hour":
            t_min = min([p.hourly_forecast(n)[5] for n in range(start, end, step)])
            t_max = max([p.hourly_forecast(n)[5] for n in range(start, end, step)])
            t_step = 45 / (t_max - t_min) if (t_max - t_min) != 0 else 1
        elif basis == "day":
            t_min = min([p.daily_forecast(n)[5] for n in range(start, end, step)])
            t_max = max([p.daily_forecast(n)[5] for n in range(start, end, step)])
            t_step = 45 / (t_max - t_min) if (t_max - t_min) != 0 else 1

        for n in range(start, end, step):
            if basis == "hour":
                hourly = p.hourly_forecast(n)
                heure = datetime.fromtimestamp(hourly[0], tz).strftime('%H')
                _x = x + 10 + int((w - 22) / (end - start - 1)) * n
                _y = y - (hourly[5] - t_min) * t_step - 45
                points += "{},{} ".format(_x, _y)
                points2 = points + "{},{} {},{}".format(_x, (y - 35), (x + 10), (y - 35))

                if int(heure) % 3 == 0:
                    svg += SVGtext("end", "16px", (_x + 14), (_y - 9), "{} {}".format(round(int(hourly[5])), p.unit['temp'])).svg()
                    svg += SVGcircle((_x + 3), (_y - 20), 2, "black", 1, "none").svg()

                    if label == True and label_adjust == True:
                        svg += SVGtext("middle", "16px", _x, (y - 9), "{}:00".format(heure)).svg()
                    elif label == True and label_adjust == False:
                        svg += SVGtext("middle", "16px", _x, (y - 15), "{}:00".format(heure)).svg()

            elif basis == "day":
                daily = p.daily_forecast(n)
                jour = str.lower(datetime.fromtimestamp(daily[0], tz).strftime('%a'))
                _x = x + 25 + int((w - 50)  / (end - start - 1)) * n
                _y = y - (daily[5] - t_min) * t_step - 45
                points += "{},{} ".format(_x, _y)
                points2 = points + "{},{} {},{}".format(_x, (y - 35), (x + 25), (y - 35))
                svg += SVGtext("end", "16px", (_x + 14), (_y - 9), "{} {}".format(int(daily[5]), p.unit['temp'])).svg()
                svg += SVGcircle((_x + 3), (_y - 20), 2, "black", 1, "none").svg()

                if label == True and label_adjust == True:
                    svg += SVGtext("middle", "16px", _x, (y - 9), "{}".format(jour)).svg()
                elif label == True and label_adjust == False:
                    svg += SVGtext("middle", "16px", _x, (y - 15), "{}".format(jour)).svg()

        style2 = "fill:{};stroke:{};stroke-width:{}px;stroke-linecap:{};".format(fill, fill, "0", stroke_linecap)
        svg += SVGpolyline(points2, style2).svg()
        style = "fill:none;stroke:{};stroke-width:{}px;stroke-linecap:{};".format(stroke_color, stroke, stroke_linecap)
        svg += SVGpolyline(points, style).svg()

        # Text
        svg += SVGtext("start", "16px", x, (y - h + 27), name).svg()
        svg += '</g>'

        return svg


    def bar_graph(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        w = self.canvas["width"]
        h = self.canvas["height"]
        bgcolor = self.canvas["bgcolor"]
        axis = self.canvas["axis"]
        axis_color = self.canvas["axis_color"]
        grid = self.canvas["grid"]
        grid_color = self.canvas["grid_color"]
        stroke = self.object["stroke"]
        stroke_color = self.object["stroke-color"]
        graph_fill = self.object["fill"]
        stroke_linecap = self.object["stroke-linecap"]
        label = bool(eval(self.object["label"]))
        label_adjust = bool(eval(self.object["label_adjust"]))
        name = self.object["name"]
        start = self.object["start"]
        end = self.object["end"]
        step = self.object["step"]
        basis = self.object["basis"]
        l_sum = float()

        svg = '<g font-family="{}">\n'.format(p.font)
        #data = p.daily_forecast(0)
        #hourly  = p.hourly_forecast(5)

        # Canvas
        style = "fill:{};stroke:{};stroke-width:{}px;".format(bgcolor, bgcolor, (0))
        svg += SVGrect(x=(x - 10), y=(y - h + 10), width=(w + 10), height=(h - 45), style=style).svg()

        if basis == "hour" and name == "precipitation":
            # Graph
            l_min = min([p.hourly_forecast(n)[10] if not p.hourly_forecast(n)[10] is None else 0 for n in range(start, end, step)])
            l_max = max([p.hourly_forecast(n)[10] if not p.hourly_forecast(n)[10] is None else 0 for n in range(start, end, step)])
            l_sum = round(sum([p.hourly_forecast(n)[10] if not p.hourly_forecast(n)[10] is None else 0 for n in range(start, end, step)]), 2)

            if l_max >= 100:
                l_step = 60 / (l_max - l_min) if (l_max - l_min) != 0 else 1
            elif 100 > l_max >= 50:
                l_step = 55 / (l_max - l_min) if (l_max - l_min) != 0 else 1
            elif 50 > l_max >= 10:
                l_step = 50 / (l_max - l_min) if (l_max - l_min) != 0 else 1
            elif 10 > l_max >= 1:
                l_step = 40 / 10
            else:
                l_step = 30 

            style = "fill:{};stroke:{};stroke-linecap:{};stroke-width:{}px;".format(graph_fill, stroke_color, stroke_linecap, stroke)
            for n in range(start, end, step):
                hourly = p.hourly_forecast(n)
                heure = datetime.fromtimestamp(hourly[0], tz).strftime('%H')
                _x = x + 10 + int((w - 22) / (end - start - 1)) * n
                _y = y - (hourly[10] - l_min) * l_step - 35
                svg += SVGline(_x, _x, (y - 35), _y, style).svg()

                if l_max == hourly[10] and l_max != 0:
                    svg += SVGtext("middle", "16px", _x, (_y - 5), "max:{}".format(round(hourly[10],2))).svg()
                    style2 = "fill:{};stroke:{};stroke-linecap:{};stroke-width:{}px;".format(axis_color, axis_color, stroke_linecap, "1")
                    svg += SVGline(_x, _x, _y, (_y - 3), style2).svg()
                if int(heure) % 3 == 0:
                    if label == True and label_adjust == True:
                        svg += SVGtext("middle", "16px", _x, (y - 9), "{}:00".format(heure)).svg()
                    elif label == True and label_adjust == False:
                        svg += SVGtext("middle", "16px", _x, (y - 15), "{}:00".format(heure)).svg()

        elif basis == "day" and name == "precipitation":
            # Graph
            l_min = min([p.daily_forecast(n)[10] if not p.daily_forecast(n)[10] is None else 0 for n in range(start, end, step)])
            l_max = max([p.daily_forecast(n)[10] if not p.daily_forecast(n)[10] is None else 0 for n in range(start, end, step)])
            l_sum = round(sum([p.daily_forecast(n)[10] if not p.daily_forecast(n)[10] is None else 0 for n in range(start, end, step)]), 2)

            if l_max >= 100:
                l_step = 60 / (l_max - l_min) if (l_max - l_min) != 0 else 1
            elif 100 > l_max >= 50:
                l_step = 55 / (l_max - l_min) if (l_max - l_min) != 0 else 1
            elif 50 > l_max >= 10:
                l_step = 50 / (l_max - l_min) if (l_max - l_min) != 0 else 1
            elif 10 > l_max >= 1:
                l_step = 40 / 10
            else:
                l_step = 30

            style = "fill:{};stroke:{};stroke-linecap:{};stroke-width:{}px;".format(graph_fill, stroke_color, stroke_linecap, stroke)
            for n in range(start, end, step):
                daily = p.daily_forecast(n)
                jour = str.lower(datetime.fromtimestamp(daily[0], tz).strftime('%a'))
                _x = x + 25 + int((w  - 50) / (end - start - 1)) * n
                _y = y - (daily[10] - l_min) * l_step - 35
                svg += SVGline(_x, _x, (y - 35), _y, style).svg()

                if l_max == daily[10] and l_max != 0:
                    svg += SVGtext("middle", "16px", _x, (_y - 5), "max:{}".format(round(daily[10],2))).svg()
                    style2 = "fill:{};stroke:{};stroke-linecap:{};stroke-width:{}px;".format(axis_color, axis_color, stroke_linecap, "1")
                    svg += SVGline(_x, _x, _y, (_y - 3), style2).svg()

                if label == True and label_adjust == True:
                    svg += SVGtext("middle", "16px", _x, (y - 9), "{}".format(jour)).svg()
                elif label == True and label_adjust == False:
                    svg += SVGtext("middle", "16px", _x, (y - 15), "{}".format(jour)).svg()

        style = "fill:none;stroke:{};stroke-width:{}px;".format(axis_color, 1)
        svg += SVGline(x1=(x - 10), x2=(x + w), y1=(y - 35), y2=(y - 35), style=style).svg()

        # Text
        svg += SVGtext("start", "16px", x, (y - h + 27), "{} (total: {} mm)".format(name, l_sum)).svg()
        svg += '</g>'

        return svg

    def tile(self):
        p = self.p
        x = self.base_x
        y = self.base_y
        w = self.canvas["width"]
        h = self.canvas["height"]
        bgcolor = self.canvas["bgcolor"]
        axis = self.canvas["axis"]
        axis_color = self.canvas["axis_color"]
        grid_y = self.canvas["grid"]
        grid_y_color = self.canvas["grid_color"]
        stroke = self.object["stroke"] if "stroke" in self.object else None
        stroke_color = self.object["stroke-color"] if "stroke-color" in self.object else None
        fill = self.object["fill"] if "fill" in self.object else None
        stroke_linecap = self.object["stroke-linecap"] if "stroke-linecap" in self.object else None
        label = bool(eval(self.object["label"]))
        label_adjust = bool(eval(self.object["label_adjust"]))
        name = self.object["name"]
        start = self.object["start"]
        end = self.object["end"]
        step = self.object["step"]
        basis = self.object["basis"]
        svg = svg = '<g font-family="{}">\n'.format(p.font)
        icons = str()

        tz = timezone(p.t_timezone)
        t_now = p.t_now
        
        # Canvas
        style = "fill:{};stroke:{};stroke-width:{}px;".format(bgcolor, bgcolor, (0))
        svg += SVGrect(x=(x - 10), y=(y - h + 10), width=(w + 10), height=(h - 45), style=style).svg()
        style = "fill:none;stroke:{};stroke-width:{}px;".format(axis_color, axis)

        # Graph
        points = str()
        _text = str()

        for n in range(start, end, step):
            if basis == "day" and name == "weather":
                daily = p.daily_forecast(n)
                jour = str.lower(datetime.fromtimestamp(daily[0], tz).strftime('%a'))
                _x = x + 25 + int((w - 50)  / (end - start - 1)) * n
                _y = y - 45

                icons += SVGtransform("(1.0,0,0,1.0,{},{})".format((_x - 53), (_y - 105)), p.daily_icons[n]).svg()
                svg += SVGtext("start", "16px", (_x - 32), (_y - 10), "hi:").svg()
                svg += SVGtext("end", "16px", (_x + 26), (_y - 10), "{} {}".format(round(daily[7]), p.unit['temp'])).svg()
                svg += SVGcircle((_x + 15), (_y - 21), 2, "black", 1, "none").svg()
                svg += SVGtext("start", "16px", (_x - 32), (_y + 7), "lo:").svg()
                svg += SVGtext("end", "16px", (_x + 26), (_y + 7), "{} {}".format(round(daily[6]), p.unit['temp'])).svg()
                svg += SVGcircle((_x + 15), (_y - 4), 2, "black", 1, "none").svg()

                if n < (end - 1):
                    style = "fill:none;stroke:{};stroke-linecap:{};stroke-width:{}px;".format(grid_y_color, stroke_linecap, grid_y)
                    icons += SVGline((_x + 30), (_x + 30), (_y - h + 55), (_y + 10), style).svg()

                if label == True and label_adjust == True:
                    svg += SVGtext("middle", "16px", _x, (y - 9), "{}".format(jour)).svg()
                elif label == True and label_adjust == False:
                    svg += SVGtext("middle", "16px", _x, (y - 15), "{}".format(jour)).svg()

            elif basis == "day" and name == "moon phase":
                daily = p.daily_forecast(n)
                jour = str.lower(datetime.fromtimestamp(daily[0], tz).strftime('%a'))
                day = int(datetime.fromtimestamp(daily[0], tz).strftime('%-d'))
                mon = int(datetime.fromtimestamp(daily[0], tz).strftime('%-m'))
                yrs = int(datetime.fromtimestamp(daily[0], tz).strftime('%Y'))
                lat = float(p.lat)
                _x = x + 25 + int((w - 50)  / (end - start - 1)) * n
                _y = y - 45
                r =14

                # icon
                style = "fill:{};stroke:{};stroke-width:{}px;".format(fill, stroke_color, 1)
                icons += SVGcircle((_x - 3), (_y - 53), (r + 2), stroke_color, stroke, "none").svg()

                # moon phase:  360d = 2pi(rad)
                #lat = -1  # test
                pi = math.pi
                rad = daily[20] * pi * 2  # One call API: 0,1=new moon, 0.25=1st qurater moon, 0.5=full moon, 0.75=lst quarter moon 
                c = 0.025
                m = rad * c * math.cos(rad)
                rx = _x - 3
                ry = _y - 53
                rp = r + 2
                #rp = r - 2 # test
                ra1 = 1 * rp
                ra2 = (math.cos(rad) * rp)
                ra3 = 1 * rp

                def phase(rad):
                    if (2 * pi / 60) > rad >= 0 or (2 * pi / 60) > (pi * 2 - rad) >= 0:
                        res = 'n'
                    elif (2 * pi / 60) > abs(rad - pi * 0.5) >= 0:
                        res = '1'
                    elif (2 * pi / 60) > abs(rad - pi) >= 0:
                        res = 'f'
                    elif (2 * pi / 60) > abs(rad - pi * 1.5) >= 0:
                        res = '3'
                    else:
                        res = str()

                    return res

                def ramadhan(day, mon, yrs):
                    ra = Gregorian(yrs, mon, day).to_hijri()
                    if ra.month_name() == "Ramadhan":
                        res = "r"
                    else:
                        res = str()

                    return res

                if lat >= 0:
                    if phase(rad) == "n":
                        px1 = math.cos(pi * 0.5 - m) * rp + rx
                        py1 = math.sin(pi * 0.5 - m ) * rp + ry
                        px2 = math.cos(pi * 0.5 - m) * rp + rx
                        py2 = -math.sin(pi * 0.5 - m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 1 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    elif rad < pi * 0.5:
                        px1 = math.cos(pi * 0.5 - m) * rp + rx
                        py1 = math.sin(pi * 0.5 - m) * rp + ry
                        px2 = math.cos(pi * 0.5 - m) * rp + rx
                        py2 = -math.sin(pi * 0.5 - m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 1 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3+1, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    elif pi > rad >= pi * 0.5:
                        px1 = math.cos(pi * 0.5 + m) * rp + rx
                        py1 = math.sin(pi * 0.5 + m) * rp + ry
                        px2 = math.cos(pi * 0.5 + m) * rp + rx
                        py2 = -math.sin(pi * 0.5 + m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 0 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    elif pi * 1.5 > rad >= pi:
                        px1 = math.cos(pi * 1.5 + m) * rp + rx
                        py1 = math.sin(pi * 1.5 + m) * rp + ry
                        px2 = math.cos(pi * 1.5 + m) * rp + rx
                        py2 = -math.sin(pi * 1.5 + m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 0 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    else:
                        px1 = math.cos(pi * 1.5 - m) * rp + rx
                        py1 = math.sin(pi * 1.5 - m) * rp + ry
                        px2 = math.cos(pi * 1.5 - m) * rp + rx
                        py2 = -math.sin(pi * 1.5 - m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 1 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3+1.75, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                else:
                    if phase(rad) == "n":
                        px1 = math.cos(pi * 0.5 + m) * rp + rx
                        py1 = math.sin(pi * 0.5 + m) * rp + ry
                        px2 = math.cos(pi * 0.5 + m) * rp + rx
                        py2 = -math.sin(pi * 0.5 + m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 1 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    elif rad < pi * 0.5:
                        px1 = math.cos(pi * 1.5 - m) * rp + rx
                        py1 = math.sin(pi * 1.5 - m) * rp + ry
                        px2 = math.cos(pi * 1.5 - m) * rp + rx
                        py2 = -math.sin(pi * 1.5 - m) * rp +ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 1 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3+1, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    elif pi > rad >= pi * 0.5:
                        px1 = math.cos(pi * 1.5 + m) * rp + rx
                        py1 = math.sin(pi * 1.5 + m) * rp + ry
                        px2 = math.cos(pi * 1.5 + m) * rp + rx
                        py2 = -math.sin(pi * 1.5 + m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 0 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    elif pi * 1.5 > rad >= pi:
                        px1 = math.cos(pi * 0.5 + m) * rp + rx
                        py1 = math.sin(pi * 0.5 + m) * rp + ry
                        px2 = math.cos(pi * 0.5 + m) * rp + rx
                        py2 = -math.sin(pi * 0.5 + m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 0 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()
                    else:
                        px1 = math.cos(pi * 0.5 - m) * rp + rx
                        py1 = math.sin(pi * 0.5 - m) * rp + ry
                        px2 = math.cos(pi * 0.5 - m) * rp + rx
                        py2 = -math.sin(pi * 0.5 - m) * rp + ry
                        d = "M{} {} A{} {} 0 1 1 {} {} {} {} 0 0 1 {} {}z".format(px1, py1, ra1, ra1, px2, py2, ra2, ra3+1.75, px1, py1)
                        ps = phase(rad)
                        ra = ramadhan(day, mon, yrs) if p.ramadhan == True else str()

                icons += SVGpath(d, style).svg() if ps != 'f' else ''

                # moonrise and moonset time
                #t_moonrise = str(daily[20])  # test
                t_moonrise = "00:00" if daily[18] == 0 else str(datetime.fromtimestamp(daily[18], tz).strftime("%H:%M"))
                t_moonset = "00:00" if daily[19] == 0 else str(datetime.fromtimestamp(daily[19], tz).strftime("%H:%M"))

                svg += SVGtext("start", "16px", (_x - 32), (_y - 10), "r:").svg()
                svg += SVGtext("end", "16px", (_x + 24), (_y - 10), "{}".format(t_moonrise)).svg()
                svg += SVGtext("start", "16px", (_x - 32), (_y + 7), "s:").svg()
                svg += SVGtext("end", "16px", (_x + 24), (_y + 7), "{}".format(t_moonset)).svg()

                # moon phase and ramadhan 
                svg += SVGtext("start", "16px", (_x - 32), (_y - 68), "{}".format(ps)).svg()
                svg += SVGtext("end", "16px", (_x + 24), (_y - 68), "{}".format(ra)).svg()

                # grid
                if n < (end - 1):
                    style = "fill:none;stroke:{};stroke-linecap:{};stroke-width:{}px;".format(grid_y_color, stroke_linecap, grid_y)
                    icons += SVGline((_x + 30), (_x + 30), (_y - h + 55), (_y + 10), style).svg()

                # label
                if label == True and label_adjust == True:
                    svg += SVGtext("middle", "16px", _x, (y - 9), "{}".format(jour)).svg()
                elif label == True and label_adjust == False:
                    svg += SVGtext("middle", "16px", _x, (y - 15), "{}".format(jour)).svg()

        # Text
        #svg += SVGtext("start", "16px", x, (y - h + 27), "{}".format(name)).svg()
        svg += '</g>'
        svg += icons
        return svg


# Reguler font
class SVGtext:
    def __init__(self, anchor, fontsize, x, y, v):
        self.anchor = anchor
        self.fontsize = fontsize
        self.x = x
        self.y = y
        self.v = v

    def svg(self):
        res = '<text style="text-anchor:{};" font-size="{}" x="{}" y="{}">{}</text>\n'.\
               format(self.anchor, self.fontsize, self.x, self.y, self.v)

        return res 

# Bold font
class SVGtext2:
    def __init__(self, anchor, fontweight, fontsize, x, y, v):
        self.anchor = anchor
        self.fontweight = fontweight
        self.fontsize = fontsize
        self.x = x
        self.y = y
        self.v = v

    def svg(self):
        res = '<text style="text-anchor:{};" font-weight="{}" font-size="{}" x="{}" y="{}">{}</text>\n'.\
               format(self.anchor, self.fontweight, self.fontsize, self.x, self.y, self.v)

        return res


class SVGcircle:
    def __init__(self, cx, cy, r, stroke, width, fill):
        self.cx = cx
        self.cy = cy
        self.r = r
        self.stroke = stroke
        self.width = width
        self.fill = fill

    def svg(self):
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

    def svg(self):
        res = '<line x1="{}" x2="{}" y1="{}" y2="{}" style="{}"/>\n'.\
                format(self.x1, self.x2, self.y1, self.y2, self.style)

        return res


class SVGtransform:
    def __init__(self, matrix, obj):
        self.matrix = matrix
        self.obj = obj

    def svg(self):
        res  = '<g transform="matrix{}">{}</g>\n'.format(self.matrix, self.obj)

        return res

class SVGpolyline:
    def __init__(self, points, style):
        self.points = points
        self.style = style

    def svg(self):
        res = '<polyline points="{}" style="{}"/>\n'.format(self.points, self.style)
        return res

class SVGrect:
    def __init__(self, x, y, width, height, style):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.style = style

    def svg(self):
        res = '<rect x="{}" y="{}" width="{}" height="{}" style="{}"/>\n'.format(self.x, self.y, self.width, self.height, self.style)
        return res

class SVGpath:
    def __init__(self, d, style):
        self.d = d
        self.style = style

    def svg(self):
        res = '<path d="{}" style="{}"/>\n'.format(self.d, self.style)
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


def temp_unit(x, y, text, unit):
    svg = str()
    svg += SVGtext("end", "35px", x, y, text).svg()
    svg += SVGcircle((x + 5), (y - 25), 4, "black", 2, "none").svg()
    svg += SVGtext("start", "25px", (x + 10), (y  - 10), unit).svg()
    return svg


def read_i18n(p):
    with open(i18nfile, 'r') as f:
        try:
            res = json.load(f)["locale"][p.t_locale]
        except:
            res = dict()
    return res


def create_svg(p, t_now, tz, utc, svgfile, pngfile):
    svg_header = str()
    svg_text = str()
    svg_draw = str()
    svg_footer = str()

    f_svg = open(svgfile,"w", encoding=p.encoding)

    header = Header(p=p)
    svg_header += header.text()

    maintenant = Maintenant(p=p, base_x=0, base_y=0)
    svg_text += maintenant.text()
    svg_draw += maintenant.icon()

    if p.graph == True and len(p.graph_object) > 2:

        # Current weather
        base_x = -5
        base_y = 45
        disc_offset = 0
        wordwrap = 0
        current = CurrentWeatherAlerts(p=p, base_x=base_x, base_y=base_y, disc_offset=disc_offset, wordwrap=wordwrap)
        svg_text += current.text()
        svg_draw += current.icon()

        # Graph area x=0,600 y=240,800(240+140+140+140+140)
        base_x = 40
        #base_y = 380
        base_y = 420
        canvas = {"width": 530, "height": 140, "bgcolor": "rgb(220,220,220)", "axis": 0, \
                      "axis_color": "rgb(0,0,0)", "grid": 3, "grid_color": "rgb(255,255,255)"}

        for obj in p.graph_object:
            svg_draw += DrawGraph(p=p, base_x=base_x, base_y=base_y, canvas=canvas, object=obj).draw()
            base_y += 130

    else:
       # Current weather
        base_x = 5
        base_y = 40
        disc_offset = 35
        wordwrap = 20

        current = CurrentWeatherNoAlerts(p=p, base_x=base_x, base_y=base_y, disc_offset=disc_offset, wordwrap=wordwrap)
        svg_text += current.text()
        svg_draw += current.icon()

        # Hourly weather
        base_x = 370
        base_y = 40
        h_hour = 3
        h_range = 12
        h_step = 3
        pitch = 155

        hourly = HourlyWeather(p, base_x=base_x, base_y=base_y, h_hour=h_hour, h_range=h_range, h_step=h_step, pitch=pitch)
        svg_text += hourly.text()
        svg_draw += hourly.icon()

        # Daily weather

        # area x=0,600 y=520,800(520+140+140)
        if p.graph == True and len(p.graph_object) <= 2:
            base_x = 40
            base_y = 660
            canvas = {"width": 530, "height": 140, "bgcolor": "rgb(220,220,220)", "axis": 0, \
                          "axis_color": "rgb(0,0,0)", "grid": 3, "grid_color": "rgb(255,255,255)"}

            for obj in p.graph_object:
                svg_draw += DrawGraph(p=p, base_x=base_x, base_y=base_y, canvas=canvas, object=obj).draw()
                base_y += 140
        else:
            base_x = 0
            base_y = 500
            d_range = 4
            pitch = 90
            daily= DailyWeather(p=p, base_x=base_x, base_y=base_y, d_range=d_range, pitch=pitch)
            svg_text += daily.text()
            svg_draw += daily.icon()

    svg_text += '</g>\n'
    svg_footer += '</svg>' 
    f_svg.write(svg_header + svg_text + svg_draw + svg_footer)
    f_svg.close()


def create_alerts_svg(p, t_now, tz, utc, svgfile, pngfile):
    svg_header = str()
    svg_text = str()
    svg_draw = str()
    svg_footer = str()

    f_svg = open(svgfile,"w", encoding=p.encoding)

    header = Header(p=p)
    svg_header += header.text()

    maintenant = Maintenant(p=p, base_x=0, base_y=0)
    svg_text += maintenant.text()
    svg_draw += maintenant.icon()

    # Current weather
    base_x = -5
    base_y = 45
    disc_offset = 0
    wordwrap = 0
    current = CurrentWeatherAlerts(p=p, base_x=base_x, base_y=base_y, disc_offset=disc_offset, wordwrap=wordwrap)
    svg_text += current.text()
    svg_draw += current.icon()

    base_x = 0
    base_y = 340
    max_y = 800
    alerts =  Alerts(p, base_x, base_y, max_y)
    svg_text += alerts.text()

    svg_text += '</g>\n'
    svg_footer += '</svg>'

    f_svg.write(svg_header + svg_text + svg_draw + svg_footer) 

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

    if p.ramadhan == True:
        from hijri_converter import Hijri, Gregorian

    # locale setting
    #locale.setlocale(locale.LC_TIME, p.t_locale)
    locale.setlocale(locale.LC_TIME, "en_US.utf-8")

    if p.alerts == True and not (p.weather_alerts() is None):
        create_alerts_svg(p=p, t_now=t_now, tz=tz, utc=utc, svgfile=svgfile, pngfile=pngfile)
    else:
        create_svg(p=p, t_now=t_now, tz=tz, utc=utc, svgfile=svgfile, pngfile=pngfile)

    t.sleep(1)
    try:
        img_processing(p=p, svgfile=svgfile, pngfile=pngfile, pngtmpfile=pngtmpfile, mode=mode)
    except Exception as e:
        shutil.copyfile(error_image, flatten_pngfile)
        print(e)
        exit(1)
