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


city = 'Krakow,PL'
ApiKey = '4526d487f12ef78b82b7a7d113faea64'
startTemperature = random.randrange(17, 25)
startHumidity = random.randrange(20, 80)


def getWeatherOutside():
    owm = OWM(ApiKey)
    observation = owm.weather_manager().weather_at_place(city)
    w = observation.weather
    temperature = w.temperature('celsius')['temp']
    humidity = w.humidity
    return temperature, humidity


def job_function():
    # function will update temperature inside
    print(getWeatherOutside())
    print(state)
    actualTemperature = state['ambient_temp']
    actualHumidity = state['humidity']
    targetTemperature = state['target_temp']
    if actualTemperature < targetTemperature:
        state['ambient_temp'] = actualTemperature + 0.1
        return
    elif actualTemperature > targetTemperature:
        state['ambient_temp'] = actualTemperature - 0.1
        return
    else:
        return


def changeTemperature():
    # function will change temperature inside basing on the temperature outside
    actualTemperature = state['ambient_temp']
    state['ambient_temp'] = actualTemperature - ((actualTemperature - getWeatherOutside()[0]) / 100)
    return


cron = BackgroundScheduler(daemon=True)
cron.add_job(job_function, 'interval', minutes=0.1)
cron.add_job(changeTemperature, 'interval', minutes=0.15)
cron.start()

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))

app = flask.Flask(__name__)
app.config["DEBUG"] = True
state = {'hvac_mode': status.heat,
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
