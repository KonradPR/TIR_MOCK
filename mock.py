import atexit
import random

import flask
from apscheduler.schedulers.background import BackgroundScheduler
from flask import abort, request, jsonify
from pyowm import OWM
from enum import Enum


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


city = 'Krakow,PL'
ApiKey = '4526d487f12ef78b82b7a7d113faea64'
startTemperature = random.randrange(17, 25)
startHumidity = random.randrange(20, 80)
startStatus = random.randint(0, 3)


def getWeatherOutside():
    owm = OWM(ApiKey)
    observation = owm.weather_manager().weather_at_place(city)
    w = observation.weather
    temperature = w.temperature('celsius')['temp']
    humidity = w.humidity
    return temperature, humidity


def job_function():
    # function will update temperature inside
    print(state)
    weatherOutside = getWeatherOutside()
    actualTemperature = state['ambient_temp']
    actualHumidity = state['humidity']
    targetTemperature = state['target_temp']
    actualStatus = state['hvac_mode']
    temperatureDifference = abs(weatherOutside[0] - actualTemperature)
    humidityDifference = abs(weatherOutside[1] - actualHumidity)
    # print(actualStatus.name)
    if actualStatus == status.heat:
        if abs(actualTemperature - targetTemperature) < 0.5:
            if actualTemperature - targetTemperature < 0:
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 + 0.1) * (
                        temperatureDifference / 50) * (humidityDifference / 30)
            else:
                state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 2 - 0.1) * (
                        temperatureDifference / 50) * (humidityDifference / 30)
        elif actualTemperature > targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 30) * (
                    temperatureDifference / 50) * (humidityDifference / 30)
        elif actualTemperature < targetTemperature:
            state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 7) * (
                    temperatureDifference / 50) * (humidityDifference / 30)

    if actualStatus == status.cool:
        state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 20)

    if actualStatus == status.hc:
        state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 15)

    if actualStatus == status.eco:
        state['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 17)


def changeTemperature():
    # function will change temperature inside basing on the temperature outside
    actualTemperature = state['ambient_temp']
    state['ambient_temp'] = actualTemperature - ((actualTemperature - getWeatherOutside()[0]) / 200)


def changeHumidity():
    actualHumidity = state['humidity']
    outsideHumidity = getWeatherOutside()[1]
    state['humidity'] = actualHumidity + (outsideHumidity - actualHumidity) / 25


cron = BackgroundScheduler(daemon=True)
# for development purposes times are very short
cron.add_job(job_function, 'interval', minutes=0.01)
cron.add_job(changeTemperature, 'interval', minutes=0.03)
cron.add_job(changeHumidity, 'interval', minutes=0.08)
cron.start()

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))

app = flask.Flask(__name__)
app.config["DEBUG"] = True
state = {'hvac_mode': getStatus(0),
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


@app.route('/devices/thermostats/<int:id>/time_to_target', methods=['GET'])
def get_time(id):
    return jsonify({'time_to_target': get_time_to_target()})


def get_time_to_target():
    return 20


app.run(use_reloader=False)
