import atexit
import random
import datetime

import flask
from apscheduler.schedulers.background import BackgroundScheduler
from flask import abort, request, jsonify
from pyowm import OWM
from enum import Enum
import csv


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
    historian = owm.weather_manager().station_hour_history(station_id)
    return historian.temperature_series(unit='celsius'),historian.humidity_series()

def updateWeatherForSimulation(temps,hums,datetime):
    return null
    

city = 'Krakow,PL'
station_id = 39276
ApiKey = '4526d487f12ef78b82b7a7d113faea64'
startTemperature = random.randrange(17, 25)
startHumidity = random.randrange(20, 80)
startStatus = random.randint(0, 3)
weather = getWeatherOutside()


def job_function():
    # function will update temperature inside
    print(state)
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
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 + 0.1) * (
                        temperatureDifference / 50) * (humidityDifference / 30) * rand
            else:
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 - 0.1) * (
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
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 + 0.06) * (
                        temperatureDifference / 50) * (humidityDifference / 30) * rand
            else:
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 - 0.2) * (
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
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 + 0.2) * (
                        temperatureDifference / 60) * (humidityDifference / 40) * rand
            else:
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 - 0.2) * (
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
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 + 0.15) * (
                        temperatureDifference / 45) * (humidityDifference / 45) * (rand * 1.5)
            else:
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 - 0.15) * (
                        temperatureDifference / 45) * (humidityDifference / 45) * (rand * 1.5)
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
    print(weather)


cron = BackgroundScheduler(daemon=True)
# for development purposes times are very short
cron.add_job(job_function, 'interval', seconds=100)
cron.add_job(changeTemperature, 'interval', seconds=300)
cron.add_job(changeHumidity, 'interval', seconds=100)
cron.add_job(updateWeather, 'interval', minutes=10)
cron.start()

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))

app = flask.Flask(__name__)
app.config["DEBUG"] = True
state = {'hvac_mode': getStatus(startStatus),
         'target_temp': 21,
         'target_temp_low': 18,
         'target_temp_high': 22,
         'ambient_temp': startTemperature,
         'humidity': startHumidity}


@app.route('/devices/thermostats/<int:id>/target_temperature_c', methods=['GET'])
def get_target_temp(id):
    return jsonify({'target_temperature_c': state['target_temp']})


@app.route('/devices/thermostats/<int:id>/target_temperature_c', methods=['PUT'])
def put_target_temp(id):
    if not request.json:
        abort(400)
    if not 'target_temperature_c' in request.json:
        abort(400)
    state['target_temp'] = request.json.get('target_temperature_c')
    return jsonify({'target_temperature_c': state['target_temp']})


@app.route('/devices/thermostats/<int:id>/target_temperature_low_c', methods=['GET'])
def get_target_temp_low(id):
    return jsonify({'target_temperature_low_c': state['target_temp_low']})


@app.route('/devices/thermostats/<int:id>/target_temperature_low_c', methods=['PUT'])
def put_target_temp_low(id):
    if not request.json:
        abort(400)
    if not 'target_temperature_low_c' in request.json:
        abort(400)
    state['target_temp_low'] = request.json.get('target_temperature_low_c')
    return jsonify({'target_temperature_low_c': state['target_temp_low']})


@app.route('/devices/thermostats/<int:id>/target_temperature_high_c', methods=['GET'])
def get_target_temp_high(id):
    return jsonify({'target_temperature_high_c': state['target_temp_high']})


@app.route('/devices/thermostats/<int:id>/target_temperature_high_c', methods=['PUT'])
def put_target_temp_high(id):
    if not request.json:
        abort(400)
    if not 'target_temperature_high_c' in request.json:
        abort(400)
    state['target_temp_high'] = request.json.get('target_temperature_high_c')
    return jsonify({'target_temperature_high_c': state['target_temp_high']})


@app.route('/devices/thermostats/<int:id>/hvac_mode', methods=['GET'])
def get_hvac(id):
    return jsonify({'hvac_mode': state['hvac_mode'].name})


@app.route('/devices/thermostats/<int:id>/hvac_mode', methods=['PUT'])
def put_hvac(id):
    if not request.json:
        abort(400)
    if not 'hvac_mode' in request.json:
        abort(400)
    state['hvac_mode'] = request.json.get('hvac_mode')
    return jsonify({'hvac_mode': state['hvac_mode'].name})


@app.route('/devices/thermostats/<int:id>/ambient_temperature_c', methods=['GET'])
def get_ambient_temp(id):
    return jsonify({'ambient_temperature_c': state['ambient_temp']})


@app.route('/devices/thermostats/<int:id>/humidity', methods=['GET'])
def get_humidity(id):
    return jsonify({'humidity': state['humidity']})

user_preferences = {
    1:{
        6:20,
        9:17,
        16:22
    },
    2:{
        6:20,
        9:17,
        16:22
    },
    3:{
        6:20,
        9:17,
        16:22
    },
    4:{
        6:20,
        9:17,
        16:22
    },
    5:{
        6:20,
        9:17,
        16:22
    },
    6:{
        8:22
    },
    7:{
        8:22
    }
}

def simluate(number_of_days,starting_date,user_preferences):
    with open('csv_file.csv', "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        end_date = starting_date + datetime.timedelta(days=number_of_days)
        temps,hums = getHistoricalWeather()
        while(starting_date<=end_date):
            if(starting_date.hour() in user_preferences[starting_date.date().weekday()]):
                state['target_temp'] =  user_preferences[starting_date.date().weekday()][starting_date.hour()]
            for x in range(6):
                job_function()
                job_function()
                job_function()
                changeTemperature()
                changeHumidity()
               
                writer.writerow([starting_date,state['target_temp'],state['target_temp_low'],state['target_temp_high'],state['humidity'],state['ambient_temp'],state['hvac_mode']])

            updateWeatherForSimulation(temps,hums,starting_date)
            starting_date+=datetime.timedelta(hours=1)

        




#app.run(use_reloader=False)
