import time as t
import json
import requests
import os.path


if os.path.exists('IconExtras.py'):
    import IconExtras as IconExtras
else:
    def IconExtra():
        return ''


class OpenWeatherMap:
    icon = str()
    unit = dict()
    direction = str()

    def __init__(self, settings):

        #GetIcon.__init__(self) 
        self.t_now = int(t.time())

        d = dict()
        s = str()

        with open(settings, 'r') as f:
            service = json.load(f)['station']

            self.city = service['city']
            self.t_timezone = service['timezone']
            self.t_locale = service['locale']
            self.encoding = service['encoding']
            self.font = service['font']
            self.sunrise_and_sunset = bool(eval(service['sunrise_and_sunset']))
            self.darkmode = service['darkmode']
            self.api_key = service['api_key']
            self.lat = service['lat']
            self.lon = service['lon']
            self.units = service['units']
            self.lang = service['lang']
            self.exclude = service['exclude']  
            self.alerts = bool(eval(service['alerts']))
            self.cloudconvert = bool(eval(service['cloudconvert']))
            self.converter = service['converter']
            self.graph = bool(eval(service['graph'])) if 'graph' in service else None
            self.graph_object = service['graph_object'] if 'graph_object' in service else None

            s += '&units=' + self.units if self.units != '' else ''
            s += '&lang=' + self.lang if self.lang != '' else ''
            s += '&exclude=' + self.exclude if self.exclude != '' else ''

            url = 'https://api.openweathermap.org/data/2.5/onecall?' + 'lat=' + self.lat + '&lon=' + self.lon + s + '&appid=' + self.api_key

        self.onecall = requests.get(url).json()

        # sanity check
        if 'cod' in self.onecall and self.onecall['cod'] == 401:
            print('OpenWeatherMap: Invalid API Key')
            exit(1)
       
        OpenWeatherMap.unit = self.set_unit(self.units)
        OpenWeatherMap.current_icons = dict()
        OpenWeatherMap.hourly_icons = dict()
        OpenWeatherMap.daily_icons = dict()
        OpenWeatherMap.header_icons = {'sunrise': get_Sunrise_icon(), 'sunset': get_Sunset_icon()}


    #def header_icons(self):
    #    return {'sunrise': get_Sunrise_icon(), 'sunset': get_Sunset_icon()}


    def weather_alerts(self):
        d = self.onecall
        dat = dict()
        dat['mode'] = self.alerts
        if 'alerts' in d and self.alerts == True:
            dat['alerts'] = d['alerts']
        else:
            dat['alerts'] = None

        return dat['alerts']


    def current_weather(self):

        # Current data format
        # list - 0:time  1:id  2:weather  3:description  4:icon  5:temp  6:pressure  7:humidity  8:wind_speed  9:wind_direction  10:clouds
        #        11:sunrise  12:sunsetb  13:gust  14:precipitation
        #
        c = self.onecall
        d = c['current']

        if not 'sunrise' in d:
            d['sunrise'] = 0

        if not 'sunset' in d:
            d['sunset'] = 0

       # wind_speed
        if 'gust' in d['weather'][0]:
            gust = float(d['gust'])
        else:
            gust = None

        # rain or snow past a hour
        precipitation = 0
        if 'rain' in d['weather'][0]:
            precipitation = float(d['rain'])
        elif 'snow' in d['weather'][0]:
            precipitation = float(d['snow'])

        dat = [int(d['dt']), int(d['weather'][0]['id']), str(d['weather'][0]['main']), str(d['weather'][0]['description']), \
                  str(d['weather'][0]['icon']), float(d['temp']), int(d['pressure']), int(d['humidity']), float(d['wind_speed']), \
                  self.cardinal(d['wind_deg']), float(d['clouds']), int(d['sunrise']), int(d['sunset']), \
                  gust, precipitation]

        # fix icon
        p = {'id': dat[1], 'weather': dat[2], 'description': dat[3], 'icon': dat[4]}
        dat[2] = self.fix_icon(**p)

        OpenWeatherMap.icons = self.add_icon(dat[2])
        OpenWeatherMap.current_icons[0] = self.add_icon(dat[2])
        OpenWeatherMap.current_icons['cardinal'] = self.add_icon(dat[9])

        return dat


    def hourly_forecast(self, hour):

        # Hourly forecast data format
        # list - 0:time  1:id  2:weather  3:description  4:icon  5:temp  6:clouds  7:pop  8:wind gust  9:wind_deg  10:precipitation 

        d = self.onecall
        h = d['hourly'][hour]

        wind_gust = float(h['wind_gust']) if 'wind_gust' in h else None
        wind_deg = float(h['wind_deg']) if 'wind_deg' in h else None

        precipitation = 0
        if ('rain' in h) or ('snow' in h):
            if 'rain' in h:
                precipitation = float(h['rain']['1h'])
            elif 'snow' in h:
                precipitation = float(h['snow']['1h'])

        dat = [int(h['dt']), int(h['weather'][0]['id']), str(h['weather'][0]['main']), str(h['weather'][0]['description']), \
                  str(h['weather'][0]['icon']), float(h['temp']), float(h['clouds']), float(h['pop']), \
                  wind_gust, self.cardinal(wind_deg), precipitation ]

        # fix icon
        p = {'id': dat[1], 'weather': dat[2], 'description': dat[3], 'icon': dat[4]}
        dat[2] = self.fix_icon(**p)

        OpenWeatherMap.icons = self.add_icon(dat[2])
        OpenWeatherMap.hourly_icons[hour] = self.add_icon(dat[2])

        return dat


    def daily_forecast(self, day):

        # Daily forecast data format
        # list - 0:time  1:id  2:weather  3:description  4:icon  5:temp day 6:temp min  7:temp max  8:clouds  9: pop
        #        10:precipitation  11:pressure  12:humidity  13:wind_speed  14:wind_deg  15:wind_gust
        #        13:sunrise  14:sunset  15:moonrise  16:moonset 17:moon_phase

        c = self.onecall
        d = c['daily'][day]

        wind_gust = float(d['wind_gust']) if 'wind_gust' in d else None
        wind_deg = float(d['wind_deg']) if 'wind_deg' in d else None

        precipitation = 0
        if ('rain' in d) or ('snow' in d):
            if 'rain' in d:
                precipitation = float(d['rain'])
            elif 'snow' in d:
                precipitation = float(d['snow'])

        dat = [int(d['dt']), int(d['weather'][0]['id']), str(d['weather'][0]['main']), str(d['weather'][0]['description']), \
                   str(d['weather'][0]['icon']), float(d['temp']['day']), float(d['temp']['min']), float(d['temp']['max']), \
                   float(d['clouds']), float(d['pop']), precipitation, float(d['pressure']), float(d['humidity']), \
                   float(d['wind_speed']), self.cardinal(wind_deg), wind_gust, float(d['sunrise']), \
                   float(d['sunset']), float(d['moonrise']), float(d['moonset']), float(d['moon_phase'])]

        # fix icon
        p = {'id': dat[1], 'weather': dat[2], 'description': dat[3], 'icon': dat[4]}
        dat[2] = self.fix_icon(**p)

        OpenWeatherMap.icons = self.add_icon(dat[2])
        OpenWeatherMap.daily_icons[day] = self.add_icon(dat[2])

        return dat


    def fix_icon(self, id, weather, description, icon):

        day_or_night = 'day' if icon[-1] == 'd' else 'night'

        if weather == 'Clear':
            dat = weather + '-' + day_or_night
        elif weather == 'Clouds' and description == 'few clouds':
            dat = 'Few-clouds' + '-' + day_or_night
        else:
            dat = weather

        if weather == 'Snow' and (int(id) == 611 or int(id) == 612 or int(id) == 613):
            dat = 'Sleet'
        elif weather == 'Snow' and (int(id) == 602 or int(id) == 622):
            dat = 'Snow2'

        return dat


    def cardinal(self, degree):

        if degree >= 348.75 or degree <= 33.75: return 'N'
        elif 33.75 <= degree <= 78.75: return 'NE'
        elif 78.75 <= degree <= 123.75: return 'E'
        elif 123.75 <= degree <= 168.75: return 'SE'
        elif 168.75 <= degree <= 213.75: return 'S'
        elif 213.75 <= degree <= 258.75: return 'SW'
        elif 258.75 <= degree <= 303.75: return 'W'
        elif 303.75 <= degree <= 348.75: return 'NW'
        else: return None

    def add_icon(self, s):
        if s == 'Clear-day':
            if ("get_ClearDay_icon" in dir(IconExtras)) == True: return IconExtras.get_ClearDay_icon()
            else: return get_ClearDay_icon()
        elif s == 'Clear-night':
            if ("get_ClearNight_icon" in dir(IconExtras)) == True: return IconExtras.get_ClearNight_icon()
            else: return get_ClearNight_icon()
        elif s == 'Rain':
            if ("get_Rain_icon" in dir(IconExtras)) == True: return IconExtras.get_Rain_icon()
            else: return get_Rain_icon()
        elif s == 'Drizzle':
            if ("get_Drizzle_icon" in dir(IconExtras)) == True: return IconExtras.get_Drizzle_icon()
            else: return get_Rain_icon()
        elif s == 'Thunderstorm':
            if ("get_Thunderstorm_icon" in dir(IconExtras)) == True: return IconExtras.get_Thunderstorm_icon()
            else: return get_Rain_icon()
        elif s == 'Snow':
            if ("get_Snow_icon" in dir(IconExtras)) == True: return IconExtras.get_Snow_icon()
            else: return get_Snow_icon()
        elif s == 'Sleet':
            if ("get_Sleet_icon" in dir(IconExtras)) == True: return IconExtras.get_Sleet_icon()
            else: return get_Rain_icon()
        elif s == 'Wind':
            if ("get_Wind_icon" in dir(IconExtras)) == True: return IconExtras.get_Wind_icon()
            else: return get_Wind_icon()
        elif s == 'Clouds':
            if ("get_Cloudy_icon" in dir(IconExtras)) == True: return IconExtras.get_Cloudy_icon()
            else: return get_Cloudy_icon()
        elif s == 'Few-clouds-day':
            if ("get_PartlyCloudyDay_icon" in dir(IconExtras)) == True: return IconExtras.get_PartlyCloudyDay_icon()
            else: return get_PartlyCloudyDay_icon()
        elif s == 'Few-clouds-night':
            if ("get_PartlyCloudyNight_icon" in dir(IconExtras)) == True: return IconExtras.get_PartlyCloudyNight_icon()
            else: return get_PartlyCloudyNight_icon()
        elif s == 'Mist':
            if ("get_Mist_icon" in dir(IconExtras)) == True: return IconExtras.get_Mist_icon()
            else: return get_Fog_icon()
        elif s == 'Smoke':
            if ("getS_moke_icon" in dir(IconExtras)) == True: return IconExtras.get_Smoke_icon()
            else: return get_Fog_icon()
        elif s == 'Haze':
            if ("get_Haze_icon" in dir(IconExtras)) == True: return IconExtras.get_Haze_icon()
            else: return get_Fog_icon()
        elif s == 'Dust':
            if ("get_Dust_icon" in dir(IconExtras)) == True: return IconExtras.get_Dust_icon()
            else: return get_Fog_icon()
        elif s == 'Fog':
            if ("get_Fog_icon" in dir(IconExtras)) == True: return IconExtras.get_Fog_icon()
            else: return get_Fog_icon()
        elif s == 'Sand':
            if ("get_Sand_icon" in dir(IconExtras)) == True: return IconExtras.get_Sand_icon()
            else: return get_Fog_icon()
        elif s == 'Dust':
            if ("get_Dust_icon" in dir(IconExtras)) == True: return IconExtras.get_Dust_icon()
            else: return get_Fog_icon()
        elif s == 'Ash':
            if ("get_Ash_icon" in dir(IconExtras)) == True: return IconExtras.get_Ash_icon()
            else: return get_Fog_icon()
        elif s == 'Squall':
            if ("get_Squall_icon" in dir(IconExtras)) == True: return IconExtras.get_Squall_icon()
            else: return get_Rain_icon()
        elif s == 'Tornado':
            if ("get_Tornado_icon" in dir(IconExtras)) == True: return IconExtras.get_Tornado_icon()
            else: return get_Wind_icon()
        elif s == 'Cyclone':
            if ("get_Cyclone_icon" in dir(IconExtras)) == True: return IconExtras.get_Cyclone_icon()
            else: return get_Wind_icon()
        elif s == 'Snow2':
            if ("get_Snow2_icon" in dir(IconExtras)) == True: return IconExtras.get_Snow2_icon()
            else: return get_Snow_icon()
        elif s == 'N':
            return get_DirectionDown_icon()
        elif s == 'NE':
            return get_DirectionDownLeft_icon()
        elif s == 'E':
            return get_DirectionLeft_icon()
        elif s == 'SE':
            return get_DirectionUpLeft_icon()
        elif s == 'S':
            return get_DirectionUp_icon()
        elif s == 'SW':
            return get_DirectionUpRight_icon()
        elif s == 'W':
            return get_DirectionRight_icon()
        elif s == 'NW':
            return get_DirectionDownRight_icon()
        else:
            return None

    def set_unit(self, s):
        if self.units == 'metric':
            dat = {'pressure': 'hPa', 'wind_speed': 'm/s', 'temp': 'C'}
        elif self.units == 'imperial':
            dat = {'pressure': 'hPa', 'wind_speed': 'mph', 'temp': 'F'}
        else:
            dat = {'pressure': 'hPa', 'wind_speed': 'm/s', 'temp': 'K'}

        return dat


# Published March 2015
# Author : Greg Fabre - http://www.iero.org
# Based on Noah Blon's work : http://codepen.io/noahblon/details/lxukH
# Public domain source code

def get_Home_icon():
    return '<g transform="matrix(6.070005,0,0,5.653153,292.99285,506.46284)"><path d="M 42,48 C 29.995672,48.017555 18.003366,48 6,48 L 6,27 c 0,-0.552 0.447,-1 1,-1 0.553,0 1,0.448 1,1 l 0,19 c 32.142331,0.03306 13.954169,0 32,0 l 0,-18 c 0,-0.552 0.447,-1 1,-1 0.553,0 1,0.448 1,1 z"/><path d="m 47,27 c -0.249,0 -0.497,-0.092 -0.691,-0.277 L 24,5.384 1.691,26.723 C 1.292,27.104 0.659,27.091 0.277,26.692 -0.105,26.293 -0.09,25.66 0.308,25.278 L 24,2.616 47.691,25.277 c 0.398,0.382 0.413,1.015 0.031,1.414 C 47.526,26.896 47.264,27 47,27 Z"/><path d="m 39,15 c -0.553,0 -1,-0.448 -1,-1 L 38,8 32,8 C 31.447,8 31,7.552 31,7 31,6.448 31.447,6 32,6 l 8,0 0,8 c 0,0.552 -0.447,1 -1,1 z" /></g>'

# Forecast.io icons
# clear-day, clear-night, rain, snow, sleet, wind, fog, cloudy, partly-cloudy-day, or partly-cloudy-night.

def get_ClearDay_icon():
    return '<path d="M71.997,51.999h-3.998c-1.105,0-2-0.895-2-1.999s0.895-2,2-2h3.998  c1.105,0,2,0.896,2,2S73.103,51.999,71.997,51.999z M64.142,38.688c-0.781,0.781-2.049,0.781-2.828,0  c-0.781-0.781-0.781-2.047,0-2.828l2.828-2.828c0.779-0.781,2.047-0.781,2.828,0c0.779,0.781,0.779,2.047,0,2.828L64.142,38.688z   M50.001,61.998c-6.627,0-12-5.372-12-11.998c0-6.627,5.372-11.999,12-11.999c6.627,0,11.998,5.372,11.998,11.999  C61.999,56.626,56.628,61.998,50.001,61.998z M50.001,42.001c-4.418,0-8,3.581-8,7.999c0,4.417,3.583,7.999,8,7.999  s7.998-3.582,7.998-7.999C57.999,45.582,54.419,42.001,50.001,42.001z M50.001,34.002c-1.105,0-2-0.896-2-2v-3.999  c0-1.104,0.895-2,2-2c1.104,0,2,0.896,2,2v3.999C52.001,33.106,51.104,34.002,50.001,34.002z M35.86,38.688l-2.828-2.828  c-0.781-0.781-0.781-2.047,0-2.828s2.047-0.781,2.828,0l2.828,2.828c0.781,0.781,0.781,2.047,0,2.828S36.641,39.469,35.86,38.688z   M34.002,50c0,1.104-0.896,1.999-2,1.999h-4c-1.104,0-1.999-0.895-1.999-1.999s0.896-2,1.999-2h4C33.107,48,34.002,48.896,34.002,50  z M35.86,61.312c0.781-0.78,2.047-0.78,2.828,0c0.781,0.781,0.781,2.048,0,2.828l-2.828,2.828c-0.781,0.781-2.047,0.781-2.828,0  c-0.781-0.78-0.781-2.047,0-2.828L35.86,61.312z M50.001,65.998c1.104,0,2,0.895,2,1.999v4c0,1.104-0.896,2-2,2  c-1.105,0-2-0.896-2-2v-4C48.001,66.893,48.896,65.998,50.001,65.998z M64.142,61.312l2.828,2.828c0.779,0.781,0.779,2.048,0,2.828  c-0.781,0.781-2.049,0.781-2.828,0l-2.828-2.828c-0.781-0.78-0.781-2.047,0-2.828C62.093,60.531,63.36,60.531,64.142,61.312z" />'

def get_ClearNight_icon():
    return '<path d="M50,61.998c-6.627,0-11.999-5.372-11.999-11.998  c0-6.627,5.372-11.999,11.999-11.999c0.755,0,1.491,0.078,2.207,0.212c-0.132,0.576-0.208,1.173-0.208,1.788  c0,4.418,3.582,7.999,8,7.999c0.615,0,1.212-0.076,1.788-0.208c0.133,0.717,0.211,1.452,0.211,2.208  C61.998,56.626,56.626,61.998,50,61.998z M48.212,42.208c-3.556,0.813-6.211,3.989-6.211,7.792c0,4.417,3.581,7.999,7.999,7.999  c3.802,0,6.978-2.655,7.791-6.211C52.937,50.884,49.115,47.062,48.212,42.208z" />'

def get_Rain_icon():
    return '<path d="m 59.999,65.64 c -0.266,0 -0.614,0 -1,0 0,-1.372 -0.319,-2.742 -0.943,-4 0.777,0 1.451,0 1.943,0 4.418,0 7.999,-3.58 7.999,-7.998 0,-4.418 -3.581,-7.999 -7.999,-7.999 -1.6,0 -3.083,0.481 -4.334,1.29 -1.231,-5.316 -5.973,-9.289 -11.664,-9.289 -6.627,0 -11.998,5.372 -11.998,11.998 0,5.953 4.339,10.879 10.023,11.822 -0.637,1.217 -0.969,2.549 -1.012,3.887 -7.406,-1.399 -13.012,-7.895 -13.012,-15.709 0,-8.835 7.162,-15.998 15.998,-15.998 6.004,0 11.229,3.312 13.965,8.204 0.664,-0.114 1.337,-0.205 2.033,-0.205 6.627,0 11.998,5.372 11.998,11.999 0,6.627 -5.37,11.998 -11.997,11.998 z m -9.998,-7.071 3.535,3.535 c 1.951,1.953 1.951,5.118 0,7.07 -1.953,1.953 -5.119,1.953 -7.07,0 -1.953,-1.952 -1.953,-5.117 0,-7.07 l 3.535,-3.535 z" />'

def get_Snow_icon():
    return '<path d="M63.999,64.943v-4.381c2.389-1.385,3.999-3.963,3.999-6.922  c0-4.416-3.581-7.998-7.999-7.998c-1.6,0-3.083,0.48-4.333,1.291c-1.231-5.317-5.974-9.291-11.665-9.291  c-6.627,0-11.998,5.373-11.998,12c0,3.549,1.55,6.729,4,8.924v4.916c-4.777-2.768-8-7.922-8-13.84  c0-8.836,7.163-15.999,15.998-15.999c6.004,0,11.229,3.312,13.965,8.204c0.664-0.113,1.337-0.205,2.033-0.205  c6.627,0,11.999,5.373,11.999,11.998C71.998,58.863,68.655,63.293,63.999,64.943z M42.001,57.641c1.105,0,2,0.896,2,2  c0,1.105-0.895,2-2,2c-1.104,0-1.999-0.895-1.999-2C40.002,58.537,40.897,57.641,42.001,57.641z M42.001,65.641c1.105,0,2,0.895,2,2  c0,1.104-0.895,1.998-2,1.998c-1.104,0-1.999-0.895-1.999-1.998C40.002,66.535,40.897,65.641,42.001,65.641z M50.001,61.641  c1.104,0,2,0.895,2,2c0,1.104-0.896,2-2,2c-1.105,0-2-0.896-2-2C48.001,62.535,48.896,61.641,50.001,61.641z M50.001,69.639  c1.104,0,2,0.896,2,2c0,1.105-0.896,2-2,2c-1.105,0-2-0.895-2-2C48.001,70.535,48.896,69.639,50.001,69.639z M57.999,57.641  c1.105,0,2,0.896,2,2c0,1.105-0.895,2-2,2c-1.104,0-1.999-0.895-1.999-2C56,58.537,56.896,57.641,57.999,57.641z M57.999,65.641  c1.105,0,2,0.895,2,2c0,1.104-0.895,1.998-2,1.998c-1.104,0-1.999-0.895-1.999-1.998C56,66.535,56.896,65.641,57.999,65.641z" />'

def get_Sleet_icon():
    return get_Snow_icon()

def get_Wind_icon():
    return '<path d="m 36.487886,31.712413 -7.4209,5.614747 -1.239742,0 0,-1.686046 -3.613959,0 0,32.148333 3.613959,0 0,-28.954574 1.286522,0 6.438465,4.155668 0.935655,0.04863 c 6.772487,-0.02017 8.174561,5.572594 20.993709,5.571513 4.65253,10e-4 6.520094,-1.29179 9.210331,-1.280746 4.597097,-0.01101 8.812682,2.102152 8.812682,2.102152 l 2.473633,-7.122458 c 0,0 -6.264433,-4.48985 -16.68386,-4.479907 -0.702187,-0.0099 -2.173664,0.189825 -3.070114,0.183735 -8.933613,0.006 -4.236867,-6.314021 -21.736381,-6.301051 z m -0.09357,1.048376 -0.742677,9.408344 -6.286419,-4.112434 7.029096,-5.29591 z" />'

def get_Fog_icon():
    return '<path d="M29.177,55.641c-0.262-0.646-0.473-1.315-0.648-2h43.47  c0,0.684-0.07,1.348-0.181,2H29.177z M36.263,35.643c2.294-1.271,4.93-1.999,7.738-1.999c2.806,0,5.436,0.73,7.727,1.999H36.263z   M28.142,47.642c0.085-0.682,0.218-1.347,0.387-1.999h40.396c0.551,0.613,1.039,1.281,1.455,1.999H28.142z M29.177,43.643  c0.281-0.693,0.613-1.359,0.984-2h27.682c0.04,0.068,0.084,0.135,0.123,0.205c0.664-0.114,1.338-0.205,2.033-0.205  c2.451,0,4.729,0.738,6.627,2H29.177z M31.524,39.643c0.58-0.723,1.225-1.388,1.92-2h21.122c0.69,0.61,1.326,1.28,1.903,2H31.524z   M71.817,51.641H28.142c-0.082-0.656-0.139-1.32-0.139-1.999h43.298C71.528,50.285,71.702,50.953,71.817,51.641z M71.301,57.641  c-0.247,0.699-0.555,1.367-0.921,2H31.524c-0.505-0.629-0.957-1.299-1.363-2H71.301z M33.444,61.641h35.48  c-0.68,0.758-1.447,1.434-2.299,1.999H36.263C35.247,63.078,34.309,62.4,33.444,61.641z" />'

def get_Cloudy_icon() :
    return '<path d="M43.945,65.639c-8.835,0-15.998-7.162-15.998-15.998  c0-8.836,7.163-15.998,15.998-15.998c6.004,0,11.229,3.312,13.965,8.203c0.664-0.113,1.338-0.205,2.033-0.205  c6.627,0,11.999,5.373,11.999,12c0,6.625-5.372,11.998-11.999,11.998C57.168,65.639,47.143,65.639,43.945,65.639z M59.943,61.639  c4.418,0,8-3.582,8-7.998c0-4.418-3.582-8-8-8c-1.6,0-3.082,0.481-4.333,1.291c-1.231-5.316-5.974-9.29-11.665-9.29  c-6.626,0-11.998,5.372-11.998,11.999c0,6.626,5.372,11.998,11.998,11.998C47.562,61.639,56.924,61.639,59.943,61.639z" />'

def get_PartlyCloudyDay_icon() :
    return '<path d="m 70.964271,47.439013 -3.309389,0 c -0.913392,0 -1.654695,-0.740476 -1.654695,-1.654695 0,-0.913391 0.741303,-1.65304 1.654695,-1.65304 l 3.309389,0 c 0.913392,0 1.654695,0.740476 1.654695,1.65304 0,0.914219 -0.741303,1.654695 -1.654695,1.654695 z M 64.463803,36.425365 c -0.646158,0.646158 -1.69358,0.646158 -2.339738,0 -0.646158,-0.645331 -0.646158,-1.69358 0,-2.338911 l 2.339738,-2.339739 c 0.646158,-0.646158 1.69358,-0.646158 2.339738,0 0.646159,0.645331 0.646159,1.69358 0,2.339739 l -2.339738,2.338911 z m -2.438193,12.91241 0,0 c 1.447031,1.725847 2.321537,3.946447 2.321537,6.374711 0,5.481177 -4.44451,9.926514 -9.927341,9.926514 -2.295889,0 -10.590873,0 -13.235903,0 -7.309614,0 -13.235903,-5.925462 -13.235903,-13.235903 0,-7.310441 5.926289,-13.235903 13.235903,-13.235903 1.30059,0 2.556503,0.191944 3.742092,0.541085 1.816028,-2.338911 4.648038,-3.850475 7.839116,-3.850475 5.482831,0 9.927341,4.445338 9.927341,9.926514 -8.27e-4,1.253431 -0.24324,2.449776 -0.666842,3.553457 z m -30.769048,3.065322 c 0,5.482831 4.443683,9.926514 9.926514,9.926514 2.991688,0 10.738141,0 13.235903,0 3.65522,0 6.617951,-2.963559 6.617951,-6.617125 0,-3.65522 -2.962731,-6.618779 -6.617951,-6.618779 -1.323756,0 -2.550712,0.398782 -3.584896,1.068106 -1.018465,-4.398179 -4.942573,-7.68523 -9.651007,-7.68523 -5.482831,0 -9.926514,4.443683 -9.926514,9.926514 z M 52.764284,39.167194 c -1.830092,0 -3.487269,0.742958 -4.684441,1.943439 1.935993,1.188071 3.545184,2.85683 4.657139,4.843291 0.549358,-0.09349 1.106163,-0.169606 1.681997,-0.169606 1.758113,0 3.407844,0.462487 4.839982,1.263359 l 0,0 c 0.07943,-0.408709 0.124102,-0.830656 0.124102,-1.263359 0,-3.653566 -2.963558,-6.617124 -6.618779,-6.617124 z m 0,-6.618779 c -0.913391,0 -1.653867,-0.740476 -1.653867,-1.653867 l 0,-3.308563 c 0,-0.914218 0.741303,-1.654694 1.653867,-1.654694 0.914219,0 1.654695,0.740476 1.654695,1.654694 l 0,3.308563 c 0,0.914218 -0.739649,1.653867 -1.654695,1.653867 z m -11.698692,3.87695 -2.338911,-2.338911 c -0.646158,-0.646159 -0.646158,-1.694408 0,-2.339739 0.645331,-0.646158 1.69358,-0.646158 2.338911,0 l 2.339739,2.339739 c 0.646158,0.645331 0.646158,1.69358 0,2.338911 -0.645331,0.646158 -1.69358,0.646158 -2.339739,0 z" />'

def get_PartlyCloudyNight_icon() :
    return '<path d="M69.763,46.758L69.763,46.758c1.368,1.949,2.179,4.318,2.179,6.883  c0,6.625-5.371,11.998-11.998,11.998c-2.775,0-12.801,0-15.998,0c-8.836,0-15.998-7.162-15.998-15.998s7.162-15.998,15.998-15.998  c2.002,0,3.914,0.375,5.68,1.047l0,0c1.635-4.682,6.078-8.047,11.318-8.047c0.755,0,1.491,0.078,2.207,0.212  c-0.131,0.575-0.207,1.173-0.207,1.788c0,4.418,3.581,7.999,7.998,7.999c0.616,0,1.213-0.076,1.789-0.208  c0.133,0.717,0.211,1.453,0.211,2.208C72.941,41.775,71.73,44.621,69.763,46.758z M31.947,49.641  c0,6.627,5.371,11.998,11.998,11.998c3.616,0,12.979,0,15.998,0c4.418,0,7.999-3.582,7.999-7.998c0-4.418-3.581-8-7.999-8  c-1.6,0-3.083,0.482-4.334,1.291c-1.231-5.316-5.973-9.29-11.664-9.29C37.318,37.642,31.947,43.014,31.947,49.641z M51.496,35.545  c0.001,0,0.002,0,0.002,0S51.497,35.545,51.496,35.545z M59.155,30.85c-2.9,0.664-5.175,2.91-5.925,5.775l0,0  c1.918,1.372,3.523,3.152,4.68,5.22c0.664-0.113,1.337-0.205,2.033-0.205c2.618,0,5.033,0.85,7.005,2.271l0,0  c0.858-0.979,1.485-2.168,1.786-3.482C63.881,39.525,60.059,35.706,59.155,30.85z" />'

#
#     https://erikflowers.github.io/weather-icons/
#     licensed under SIL OFL 1.1 (http://scripts.sil.org/OFL)
#
def get_WindDeg_icon():
    return '''<path d="M3.74,14.5c0-2.04,0.51-3.93,1.52-5.66s2.38-3.1,4.11-4.11s3.61-1.51,5.64-1.51c1.52,0,2.98,0.3,4.37,0.89
		s2.58,1.4,3.59,2.4s1.81,2.2,2.4,3.6s0.89,2.85,0.89,4.39c0,1.52-0.3,2.98-0.89,4.37s-1.4,2.59-2.4,3.59s-2.2,1.8-3.59,2.39
		s-2.84,0.89-4.37,0.89c-1.53,0-3-0.3-4.39-0.89s-2.59-1.4-3.6-2.4s-1.8-2.2-2.4-3.58S3.74,16.03,3.74,14.5z M6.22,14.5
		c0,2.37,0.86,4.43,2.59,6.18c1.73,1.73,3.79,2.59,6.2,2.59c1.58,0,3.05-0.39,4.39-1.18s2.42-1.85,3.21-3.2s1.19-2.81,1.19-4.39
		s-0.4-3.05-1.19-4.4s-1.86-2.42-3.21-3.21s-2.81-1.18-4.39-1.18s-3.05,0.39-4.39,1.18S8.2,8.75,7.4,10.1S6.22,12.92,6.22,14.5z
		 M11.11,20.35l3.75-13.11c0.01-0.1,0.06-0.15,0.15-0.15s0.14,0.05,0.15,0.15l3.74,13.11c0.04,0.11,0.03,0.19-0.02,0.25
		s-0.13,0.06-0.24,0l-3.47-1.3c-0.1-0.04-0.2-0.04-0.29,0l-3.5,1.3c-0.1,0.06-0.17,0.06-0.21,0S11.09,20.45,11.11,20.35z" />'''

def get_Sunrise_icon():
        return '''<path d="M2.75,15.36c0-0.25,0.1-0.48,0.3-0.69c0.22-0.19,0.46-0.29,0.7-0.29h2.33c0.27,0,0.49,0.1,0.67,0.29
		c0.18,0.19,0.27,0.43,0.27,0.69c0,0.29-0.09,0.53-0.27,0.72c-0.18,0.19-0.41,0.29-0.67,0.29H3.75c-0.27,0-0.5-0.1-0.7-0.3
		C2.85,15.86,2.75,15.62,2.75,15.36z M6.08,7.38c0-0.27,0.09-0.5,0.26-0.68C6.57,6.5,6.8,6.4,7.05,6.4c0.26,0,0.49,0.1,0.68,0.29
		l1.64,1.65c0.19,0.22,0.28,0.45,0.28,0.69c0,0.28-0.09,0.52-0.27,0.7s-0.4,0.28-0.66,0.28c-0.24,0-0.48-0.1-0.7-0.29L6.34,8.11
		C6.17,7.9,6.08,7.65,6.08,7.38z M8.08,20.88c0-0.28,0.1-0.51,0.29-0.68c0.18-0.17,0.4-0.26,0.68-0.26h2.63l3.11-2.92
		c0.1-0.08,0.21-0.08,0.34,0l3.16,2.92h2.77c0.27,0,0.5,0.09,0.69,0.28c0.19,0.18,0.29,0.41,0.29,0.67c0,0.27-0.1,0.5-0.29,0.69
		c-0.19,0.19-0.42,0.29-0.69,0.29h-3.38c-0.1,0-0.2-0.02-0.29-0.07l-2.41-2.27l-2.39,2.27c-0.08,0.05-0.17,0.07-0.28,0.07H9.05
		c-0.27,0-0.5-0.1-0.69-0.29C8.17,21.38,8.08,21.15,8.08,20.88z M9,15.36c0,0.97,0.21,1.85,0.62,2.64c0.02,0.12,0.11,0.18,0.25,0.18
		h1.88c0.07,0,0.12-0.03,0.15-0.08c0.03-0.06,0.02-0.12-0.02-0.19c-0.64-0.77-0.96-1.62-0.96-2.55c0-1.12,0.4-2.08,1.2-2.87
		c0.8-0.79,1.76-1.18,2.89-1.18c1.12,0,2.07,0.39,2.86,1.18c0.79,0.79,1.19,1.74,1.19,2.87c0,0.94-0.32,1.79-0.95,2.55
		c-0.04,0.07-0.05,0.13-0.03,0.19s0.07,0.08,0.15,0.08h1.9c0.13,0,0.21-0.06,0.23-0.18C20.8,17.23,21,16.35,21,15.36
		c0-0.81-0.16-1.59-0.48-2.32c-0.32-0.74-0.75-1.37-1.28-1.91c-0.53-0.53-1.17-0.96-1.91-1.28c-0.74-0.32-1.51-0.47-2.32-0.47
		c-0.81,0-1.59,0.16-2.33,0.47c-0.74,0.32-1.38,0.74-1.92,1.28c-0.54,0.53-0.97,1.17-1.29,1.91C9.16,13.77,9,14.54,9,15.36z
		 M14.03,6.4v-2.3c0-0.29,0.09-0.52,0.28-0.71s0.43-0.28,0.71-0.28c0.28,0,0.51,0.09,0.7,0.28S16,3.83,16,4.11v2.3
		c0,0.29-0.09,0.52-0.28,0.71c-0.18,0.18-0.42,0.28-0.7,0.28c-0.29,0-0.52-0.09-0.71-0.28C14.12,6.93,14.03,6.69,14.03,6.4z
		 M20.38,9.04c0-0.25,0.09-0.48,0.27-0.69l1.62-1.65c0.19-0.19,0.43-0.29,0.7-0.29c0.27,0,0.51,0.1,0.69,0.29
		c0.19,0.19,0.28,0.42,0.28,0.69c0,0.29-0.09,0.53-0.26,0.73L22,9.73c-0.21,0.19-0.45,0.29-0.7,0.29c-0.27,0-0.49-0.09-0.66-0.28
		S20.38,9.32,20.38,9.04z M22.99,15.36c0-0.27,0.09-0.5,0.27-0.69c0.18-0.19,0.4-0.29,0.66-0.29h2.35c0.27,0,0.5,0.1,0.69,0.29
		c0.19,0.19,0.29,0.43,0.29,0.69c0,0.28-0.1,0.51-0.29,0.71s-0.42,0.3-0.69,0.3h-2.35c-0.27,0-0.49-0.1-0.67-0.29
		C23.08,15.88,22.99,15.64,22.99,15.36z" />'''

def get_Sunset_icon():
    return '''<path d="M2.88,15.47c0-0.28,0.1-0.5,0.3-0.68c0.17-0.18,0.4-0.26,0.68-0.26h2.31c0.27,0,0.49,0.09,0.67,0.27
		c0.17,0.18,0.26,0.4,0.26,0.67c0,0.28-0.09,0.52-0.27,0.71c-0.18,0.19-0.4,0.29-0.66,0.29H3.87c-0.27,0-0.5-0.1-0.69-0.3
		C2.98,15.97,2.88,15.74,2.88,15.47z M6.17,7.61c0-0.28,0.08-0.51,0.25-0.68c0.2-0.2,0.43-0.3,0.7-0.3c0.29,0,0.51,0.1,0.68,0.3
		l1.62,1.63c0.46,0.44,0.46,0.89,0,1.35c-0.19,0.19-0.4,0.28-0.65,0.28c-0.22,0-0.44-0.09-0.68-0.28L6.43,8.29
		C6.26,8.11,6.17,7.88,6.17,7.61z M8.14,20.89c0-0.26,0.1-0.49,0.3-0.69c0.18-0.18,0.41-0.27,0.68-0.27h3.22
		c0.11,0,0.2,0.02,0.28,0.08l2.35,2.22L17.36,20c0.07-0.05,0.17-0.08,0.29-0.08h3.3c0.27,0,0.5,0.09,0.69,0.28
		c0.19,0.19,0.29,0.42,0.29,0.68c0,0.27-0.1,0.5-0.29,0.69c-0.19,0.19-0.42,0.29-0.69,0.29h-2.68l-3.14,2.84
		c-0.12,0.09-0.23,0.09-0.33,0l-3.08-2.84h-2.6c-0.27,0-0.5-0.1-0.69-0.29C8.24,21.39,8.14,21.16,8.14,20.89z M9.08,15.47
		c0,0.99,0.19,1.87,0.58,2.62c0.06,0.11,0.15,0.16,0.27,0.16h1.87c0.08,0,0.13-0.02,0.15-0.07c0.02-0.05-0.01-0.11-0.07-0.18
		c-0.59-0.74-0.89-1.59-0.89-2.53c0-1.1,0.39-2.04,1.18-2.81c0.79-0.77,1.74-1.16,2.85-1.16c1.1,0,2.04,0.39,2.83,1.16
		c0.78,0.78,1.18,1.71,1.18,2.8c0,0.94-0.3,1.79-0.89,2.53c-0.07,0.07-0.09,0.13-0.07,0.18c0.02,0.05,0.07,0.07,0.15,0.07h1.88
		c0.13,0,0.21-0.05,0.24-0.16c0.41-0.78,0.62-1.66,0.62-2.62c0-0.79-0.16-1.56-0.47-2.29s-0.74-1.37-1.27-1.9s-1.16-0.95-1.89-1.27
		c-0.73-0.32-1.5-0.47-2.3-0.47c-0.8,0-1.57,0.16-2.3,0.47c-0.73,0.32-1.36,0.74-1.89,1.27s-0.95,1.16-1.27,1.9
		S9.08,14.68,9.08,15.47z M14.04,6.66V4.33c0-0.27,0.1-0.5,0.29-0.69s0.42-0.29,0.69-0.29c0.27,0,0.5,0.1,0.69,0.29
		s0.29,0.42,0.29,0.69v2.32c0,0.27-0.1,0.5-0.29,0.69c-0.19,0.19-0.42,0.29-0.69,0.29c-0.27,0-0.5-0.1-0.69-0.29
		C14.13,7.15,14.04,6.93,14.04,6.66z M20.31,9.24c0-0.28,0.09-0.51,0.26-0.67l1.63-1.63c0.16-0.2,0.39-0.3,0.68-0.3
		c0.27,0,0.5,0.1,0.68,0.29c0.18,0.19,0.27,0.42,0.27,0.69c0,0.28-0.08,0.51-0.25,0.68l-1.66,1.63c-0.23,0.19-0.46,0.28-0.69,0.28
		c-0.26,0-0.48-0.09-0.66-0.28C20.4,9.74,20.31,9.51,20.31,9.24z M22.9,15.47c0-0.27,0.09-0.49,0.26-0.67
		c0.17-0.18,0.4-0.27,0.67-0.27h2.32c0.27,0,0.5,0.09,0.69,0.27c0.19,0.18,0.29,0.4,0.29,0.67c0,0.27-0.1,0.5-0.29,0.7
		c-0.19,0.2-0.42,0.3-0.69,0.3h-2.32c-0.26,0-0.48-0.1-0.66-0.29C22.99,15.99,22.9,15.75,22.9,15.47z" />'''

def get_DirectionUp_icon():
    return '''<path d="M9.95,10.87c-0.01,0.35,0.1,0.65,0.34,0.9s0.53,0.37,0.89,0.36c0.34,0.02,0.63-0.1,0.88-0.37l1.66-1.64v10.3
		c-0.01,0.35,0.11,0.64,0.36,0.88s0.55,0.35,0.92,0.34c0.34,0.02,0.64-0.09,0.89-0.32s0.39-0.53,0.4-0.88v-10.3l1.64,1.64
		c0.23,0.24,0.53,0.37,0.88,0.37c0.36,0,0.66-0.12,0.9-0.36s0.36-0.53,0.36-0.89c-0.02-0.36-0.15-0.64-0.4-0.85l-3.74-3.84
		c-0.24-0.23-0.55-0.37-0.92-0.4c-0.37,0.02-0.68,0.16-0.92,0.41l-3.75,3.81C10.08,10.25,9.95,10.53,9.95,10.87z" />'''

def get_DirectionUpRight_icon():
    return '''<path d="M10.05,17.55c0,0.3,0.09,0.55,0.26,0.73c0.2,0.19,0.46,0.28,0.79,0.28c0.3,0,0.55-0.09,0.73-0.28l6.04-6.05v1.95
		c0,0.3,0.1,0.55,0.3,0.75c0.2,0.2,0.45,0.3,0.75,0.3c0.29,0,0.54-0.1,0.74-0.31s0.3-0.45,0.3-0.75V9.7c0-0.3-0.1-0.55-0.3-0.75
		s-0.45-0.3-0.74-0.3h-4.5c-0.29,0-0.54,0.1-0.73,0.3S13.4,9.39,13.4,9.7c0,0.29,0.1,0.54,0.29,0.73s0.44,0.29,0.73,0.29h1.95
		l-6.06,6.06C10.14,16.99,10.05,17.25,10.05,17.55z" />'''

def get_DirectionRight_icon():
    return '''<path d="M9.94,14.36c0,0.22,0.08,0.42,0.23,0.57s0.34,0.22,0.56,0.2h6.58l-1.03,1.08c-0.16,0.16-0.24,0.35-0.24,0.55
		c0,0.22,0.08,0.42,0.24,0.57c0.16,0.16,0.35,0.23,0.58,0.23c0.21-0.01,0.39-0.1,0.53-0.27l2.45-2.41c0.16-0.16,0.23-0.35,0.23-0.58
		c-0.01-0.24-0.09-0.43-0.24-0.58l-2.47-2.39c-0.15-0.16-0.33-0.24-0.54-0.23c-0.23,0-0.42,0.07-0.57,0.22
		c-0.16,0.15-0.23,0.34-0.23,0.56c0,0.23,0.08,0.42,0.23,0.57l1.06,1.08h-6.59c-0.23,0.01-0.41,0.09-0.56,0.25
		C10.01,13.95,9.94,14.14,9.94,14.36z" />'''

def get_DirectionDownRight_icon():
    return '''<path d="M10.04,10.08c0-0.3,0.09-0.55,0.26-0.73c0.2-0.19,0.46-0.28,0.79-0.28c0.3,0,0.55,0.09,0.73,0.28l6.05,6.05v-1.95
		c0-0.3,0.1-0.55,0.3-0.75s0.45-0.3,0.75-0.3c0.29,0,0.54,0.1,0.74,0.31s0.3,0.45,0.3,0.75v4.48c0,0.3-0.1,0.55-0.3,0.75
		s-0.45,0.3-0.74,0.3h-4.48c-0.29,0-0.54-0.1-0.74-0.3s-0.3-0.45-0.3-0.75c0-0.29,0.1-0.54,0.3-0.73s0.45-0.29,0.74-0.29h1.93
		l-6.08-6.06C10.13,10.63,10.04,10.38,10.04,10.08z" />'''

def get_DirectionDown_icon():
    return '''<path d="M11.77,16.47c0,0.22,0.08,0.4,0.25,0.55l2.4,2.45c0.16,0.16,0.35,0.23,0.58,0.23c0.24,0,0.43-0.08,0.59-0.23l2.4-2.45
		c0.16-0.14,0.24-0.33,0.24-0.55c0-0.22-0.08-0.41-0.23-0.57s-0.34-0.23-0.56-0.23s-0.42,0.08-0.57,0.23l-1.06,1.05v-6.59
		c0-0.22-0.08-0.41-0.24-0.56C15.42,9.66,15.23,9.58,15,9.58s-0.42,0.07-0.58,0.22c-0.16,0.15-0.24,0.34-0.24,0.56v6.59l-1.06-1.05
		c-0.16-0.16-0.34-0.23-0.55-0.23c-0.22,0-0.42,0.08-0.57,0.23S11.77,16.25,11.77,16.47z" />'''

def get_DirectionDownLeft_icon():
    return '''<path d="M11.83,16.77c0,0.19,0.06,0.35,0.19,0.48c0.13,0.13,0.29,0.19,0.47,0.19h2.87c0.19,0,0.35-0.06,0.47-0.19
		c0.13-0.13,0.19-0.29,0.19-0.48c0-0.19-0.06-0.34-0.19-0.46c-0.13-0.12-0.29-0.18-0.47-0.18h-1.24L18,12.24
		c0.12-0.14,0.18-0.3,0.18-0.5c0-0.18-0.06-0.33-0.18-0.46c-0.12-0.12-0.29-0.18-0.5-0.18c-0.2,0-0.36,0.06-0.48,0.18l-3.86,3.87
		v-1.25c0-0.19-0.06-0.35-0.19-0.48c-0.13-0.13-0.29-0.19-0.48-0.19c-0.19,0-0.35,0.07-0.47,0.2c-0.13,0.13-0.19,0.29-0.19,0.48
		V16.77z" />'''

def get_DirectionLeft_icon():
    return '''<path d="M7.09,14.96c0,0.37,0.12,0.68,0.37,0.92l3.84,3.75c0.22,0.25,0.51,0.38,0.85,0.38c0.35,0,0.65-0.12,0.89-0.35
		s0.37-0.53,0.37-0.88s-0.12-0.65-0.37-0.89l-1.64-1.64h10.3c0.35,0,0.64-0.12,0.87-0.37s0.34-0.55,0.34-0.9s-0.11-0.65-0.34-0.9
		s-0.52-0.38-0.87-0.39H11.4l1.64-1.66c0.24-0.24,0.37-0.53,0.37-0.86c0-0.35-0.12-0.65-0.37-0.89S12.5,9.9,12.14,9.9
		c-0.32,0-0.61,0.14-0.85,0.41l-3.84,3.75C7.21,14.31,7.09,14.6,7.09,14.96z" />'''

def get_DirectionUpLeft_icon():
    return '''<path d="M10.03,14.31V9.84c0-0.3,0.1-0.55,0.3-0.75s0.45-0.3,0.74-0.3h4.48c0.29,0,0.54,0.1,0.74,0.3s0.3,0.45,0.3,0.75	
		c0,0.29-0.1,0.53-0.3,0.73s-0.45,0.29-0.74,0.29h-1.95l6.06,6.06c0.18,0.21,0.26,0.46,0.26,0.78c0,0.29-0.09,0.53-0.26,0.72
		c-0.2,0.19-0.46,0.28-0.79,0.28c-0.3,0-0.55-0.09-0.73-0.28l-6.02-6.05v1.95c0,0.3-0.1,0.55-0.3,0.75c-0.2,0.2-0.45,0.3-0.75,0.3
		c-0.29,0-0.54-0.1-0.74-0.31S10.03,14.6,10.03,14.31z" />'''

