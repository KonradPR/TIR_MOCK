import atexit
import csv
import os
import random
import sys
from datetime import datetime, timedelta
from enum import Enum
from json import dumps

import AWSIoTPythonSDK
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from apscheduler.schedulers.background import BackgroundScheduler
from pyowm import OWM

sys.path.insert(0, os.path.dirname(AWSIoTPythonSDK.__file__))
# Now the import statement should work


# dir_path = os.path.dirname(os.path.realpath(__file__))
ENDPOINT = "a24ojhzjcj6a8j-ats.iot.us-east-1.amazonaws.com"
# CLIENT_ID = "testDevice"
PATH_TO_CERT = "certificates/9edb23887d-certificate.pem.crt"
PATH_TO_KEY = "certificates/9edb23887d-private.pem.key"
PATH_TO_ROOT = "certificates/root.pem"

ID = 4
CLIENT = AWSIoTMQTTClient(str(ID))
QOS = 0
connected = False


def configure_mqtt():
    CLIENT.configureEndpoint(ENDPOINT, 8883)
    CLIENT.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)
    # CLIENT.configureIAMCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)
    CLIENT.connect()
    on_connect()
    # on_message()


class status(Enum):
    heat = 0,
    cool = 1,
    hc = 2,
    eco = 3


def getStatus(num: int):
    if num == 0:
        return status.heat
    elif num == 1:
        return status.cool
    elif num == 2:
        return status.hc
    elif num == 3:
        return status.eco


def getWeatherOutside():
    owm = OWM(ApiKey)
    observation = owm.weather_manager().weather_at_place(city)
    w = observation.weather
    temperature = w.temperature('celsius')['temp']
    humidity = w.humidity
    return temperature, humidity


def getHistoricalWeather():
    owm = OWM(ApiKey)
    return owm.weather_manager().forecast_at_place('Krakow,PL', '3h')


def updateWeatherForSimulation(forecast, timepoint, start_ref):
    global weather
    start = datetime.strptime(forecast.when_starts('iso')[0:19], "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(forecast.when_ends('iso')[0:19], "%Y-%m-%d %H:%M:%S")
    delta = timepoint - start_ref
    day = delta.days % 5
    if (start + timedelta(days=day) + timedelta(hours=2)) > end:
        weatherO = forecast.get_weather_at(start + timedelta(days=day) - timedelta(hours=2))
        weather = weatherO.temperature(unit='celsius')['temp'], weatherO.humidity
    weatherO = forecast.get_weather_at(start + timedelta(days=day) + timedelta(hours=2))
    weather = weatherO.temperature(unit='celsius')['temp'], weatherO.humidity


city = 'Krakow,PL'
station_id = 39276
ApiKey = '4526d487f12ef78b82b7a7d113faea64'
startTemperature = random.randrange(17, 25)
startHumidity = random.randrange(20, 80)
startStatus = random.randint(0, 3)
weather = getWeatherOutside()

state = {
    'hvac_mode': getStatus(startStatus),
    'target_temp': 21,
    'target_temp_low': 18,
    'targetz_temp_high': 22,
    'ambient_temp': startTemperature,
    'humidity': startHumidity}


def job_function():
    weatherOutside = weather
    actualTemperature = state['ambient_temp']
    actualHumidity = state['humidity']
    targetTemperature = state['target_temp']
    actualStatus = state['hvac_mode']
    temperatureDifference = abs(weatherOutside[0] - actualTemperature)
    humidityDifference = abs(weatherOutside[1] - actualHumidity)
    rand = random.uniform(0, 2.5)
    if actualStatus == status.heat:
        if abs(actualTemperature - targetTemperature) < 0.5:
            if actualTemperature - targetTemperature < 0:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 + 0.1) * (
                                                temperatureDifference / 50) * (humidityDifference / 30) * rand
            else:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 - 0.1) * (
                                                temperatureDifference / 50) * (humidityDifference / 30) * rand
        elif actualTemperature > targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 30) * (
                    temperatureDifference / 50) * (humidityDifference / 30) * rand
        elif actualTemperature < targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 7) * (
                    temperatureDifference / 50) * (humidityDifference / 30) * rand

    if actualStatus == status.cool:
        if abs(actualTemperature - targetTemperature) < 0.5:
            if actualTemperature - targetTemperature < 0:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 + 0.06) * (
                                                temperatureDifference / 50) * (humidityDifference / 30) * rand
            else:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 - 0.2) * (
                                                temperatureDifference / 50) * (humidityDifference / 30) * rand
        elif actualTemperature > targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 7) * (
                    temperatureDifference / 50) * (humidityDifference / 40) * rand
        elif actualTemperature < targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 30) * (
                    temperatureDifference / 50) * (humidityDifference / 50) * rand

    if actualStatus == status.hc:
        if abs(actualTemperature - targetTemperature) < 0.7:
            if actualTemperature - targetTemperature < 0:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 + 0.2) * (
                                                temperatureDifference / 60) * (humidityDifference / 40) * rand
            else:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 - 0.2) * (
                                                temperatureDifference / 60) * (humidityDifference / 40) * rand
        elif actualTemperature > targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 13) * (
                    temperatureDifference / 60) * (humidityDifference / 40) * rand
        elif actualTemperature < targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 13) * (
                    temperatureDifference / 60) * (humidityDifference / 40) * rand

    if actualStatus == status.eco:
        if abs(actualTemperature - targetTemperature) < 0.4:
            if actualTemperature - targetTemperature < 0:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 + 0.15) * (
                                                temperatureDifference / 45) * (humidityDifference / 45) * (
                                                rand * 1.5)
            else:
                state['ambient_temp'] = actualTemperature + (
                        (targetTemperature - actualTemperature) / 2 - 0.15) * (
                                                temperatureDifference / 45) * (humidityDifference / 45) * (
                                                rand * 1.5)
        elif actualTemperature > targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 16) * (
                    temperatureDifference / 45) * (humidityDifference / 45) * (rand * 1.5)
        elif actualTemperature < targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 17) * (
                    temperatureDifference / 45) * (humidityDifference / 45) * (rand * 1.5)


def changeTemperature():
    # function will change temperature inside basing on the temperature outside
    actualTemperature = state['ambient_temp']
    state['ambient_temp'] = actualTemperature - ((actualTemperature - weather[0]) / 200)


def changeHumidity():
    actualHumidity = state['humidity']
    outsideHumidity = weather[1]
    state['humidity'] = (actualHumidity + (((outsideHumidity - actualHumidity) / 25) * random.uniform(-1, 1)))


def updateWeather():
    global weather
    weather = getWeatherOutside()
    print(f"Temperature outside: {weather}")


def sendTemperatureToController():
    print(state['ambient_temp'])
    # CLIENT.publish(f'/devices/thermostats/{ID}/get_ambient_temperature_return',
    #                dumps({'ambient_temperature_c': state['ambient_temp']}), 0)


cron = BackgroundScheduler(daemon=True)
# for development purposes times are very short
cron.add_job(job_function, 'interval', seconds=100)
cron.add_job(changeTemperature, 'interval', seconds=400)
cron.add_job(changeHumidity, 'interval', seconds=100)
cron.add_job(updateWeather, 'interval', minutes=10)
cron.add_job(sendTemperatureToController, 'interval', minutes=1)
cron.start()

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))


def get_target_temp(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    CLIENT.publish(f'/devices/thermostats/{ID}/get_target_temperature_return',
                   dumps({'target_temperature_c': state['target_temp']}), QOS)


def put_target_temp(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    state['target_temp'] = message.payload.decode('utf8')


def get_target_temp_low(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    CLIENT.publish(f'/devices/thermostats/{ID}/get_target_temperature_low_return',
                   dumps({'target_temperature_low_c': state['target_temp_low']}), QOS)


def put_target_temp_low(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    state['target_temp_low'] = message.payload.decode('utf8')


def get_target_temp_high(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    CLIENT.publish(f'/devices/thermostats/{ID}/get_target_temperature_high_return',
                   dumps({'target_temperature_high_c': state['target_temp_high']}), QOS)


def put_target_temp_high(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    state['target_temp_high'] = message.payload.decode('utf8')


def get_hvac(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    CLIENT.publish(f'/devices/thermostats/{ID}/get_hvac_mode_return', dumps({'hvac_mode': state['hvac_mode'].name}),
                   QOS)


def put_hvac(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    state['hvac_mode'] = message.payload.decode('utf8')


def get_ambient_temp(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    CLIENT.publish(f'/devices/thermostats/{ID}/get_ambient_temperature_return',
                   dumps({'ambient_temperature_c': state['ambient_temp']}), QOS)


def get_humidity(client, userdata, message):
    print(f"Received from topic: {message.topic} : {message.payload}")
    CLIENT.publish(f'/devices/thermostats/{ID}/get_humidity_return', dumps({'humidity': state['humidity']}), QOS)


def on_connect():
    CLIENT.subscribe(f'/devices/thermostats/{ID}/get_target_temperature', QOS, get_target_temp)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/get_target_temperature_low', QOS, get_target_temp_low)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/get_target_temperature_high', QOS, get_target_temp_high)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/get_hvac_mode', QOS, get_hvac)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/get_ambient_temperature', QOS, get_ambient_temp)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/get_humidity', QOS, get_humidity)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/put_target_temperature', QOS, put_target_temp)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/put_target_temperature_low', QOS, put_target_temp_low)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/put_target_temperature_high', QOS, put_target_temp_high)
    CLIENT.subscribe(f'/devices/thermostats/{ID}/put_hvac_mode', QOS, put_hvac)
    print("connect")
    CLIENT.publish('/devices/info', f"Thermostat {ID} connected", QOS)
    global connected
    connected = True


def on_message(client, userdata, message):
    print(message.payload.decode('utf8'))


user_preferences = {
    0: {
        6: ['target_temp', 20],
        9: ['target_temp', 17],
        16: ['target_temp', 22],
        22: ['target_temp', 18]
    },
    1: {
        6: ['target_temp', 20],
        9: ['target_temp', 17],
        16: ['target_temp', 22],
        22: ['target_temp', 18]
    },
    2: {
        6: ['target_temp', 20],
        9: ['target_temp', 17],
        16: ['target_temp', 22],
        22: ['target_temp', 18]
    },
    3: {
        6: ['target_temp', 20],
        9: ['target_temp', 17],
        16: ['target_temp', 22],
        22: ['target_temp', 18]
    },
    4: {
        6: ['target_temp', 20],
        9: ['target_temp', 17],
        16: ['target_temp', 22],
        22: ['target_temp', 18]
    },
    5: {
        5: ['target_temp', 20],
        8: ['target_temp', 22],
        22: ['target_temp', 18]
    },
    6: {
        6: ['target_temp', 20],
        8: ['target_temp', 22],
        22: ['target_temp', 18]
    }
}


def simulate_preferences(user_preferences, date_ref):
    if date_ref.hour in user_preferences[date_ref.date().weekday()]:
        state[user_preferences[date_ref.date().weekday()][date_ref.hour][0]] = \
            user_preferences[date_ref.date().weekday()][date_ref.hour][1]


def simluate_for_api(number_of_days, starting_date, user_preferences):
    result = []
    end_date = starting_date + timedelta(days=number_of_days)
    forecast = getHistoricalWeather()
    start_ref = starting_date
    while starting_date <= end_date:
        simulate_preferences(user_preferences, starting_date)
        for x in range(6):
            job_function()
            job_function()
            job_function()
            changeTemperature()
            changeHumidity()
            starting_date += timedelta(minutes=10)
            result.append({
                'id': x,
                'time': starting_date,
                'target_temp': state['target_temp'],
                'target_temp_low': state['target_temp_low'],
                'target_temp_high': state['target_temp_high'],
                'humidity': state['humidity'],
                'ambient_temp': state['ambient_temp'],
                'hvac_mode': state['hvac_mode'].name})

        updateWeatherForSimulation(forecast, starting_date, start_ref)
    return result


def simluate(number_of_days, starting_date, user_preferences):
    with open('csv_file.csv', "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        end_date = starting_date + timedelta(days=number_of_days)
        forecast = getHistoricalWeather()
        start_ref = starting_date
        while (starting_date <= end_date):
            simulate_preferences(user_preferences, starting_date)
            for x in range(6):
                job_function()
                job_function()
                job_function()
                changeTemperature()
                changeHumidity()
                starting_date += timedelta(minutes=10)
                writer.writerow([starting_date, state['target_temp'], state['target_temp_low'],
                                 state['target_temp_high'], state['humidity'],
                                 state['ambient_temp'], state['hvac_mode']])

            updateWeatherForSimulation(forecast, starting_date, start_ref)


date_str2 = '1/3/21'

# simluate(1,datetime.strptime(date_str2, '%m/%d/%y'),user_preferences)

if __name__ == '__main__':
    configure_mqtt()

    # app.run(use_reloader=False, host='0.0.0.0', port=84)

    while True:
        pass
