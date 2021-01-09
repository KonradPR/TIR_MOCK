import atexit
import random
from datetime import datetime, timedelta

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

states = {}


def initial_state():
    startTemperature = random.randrange(17, 25)
    startHumidity = random.randrange(20, 80)
    startStatus = random.randint(0, 3)
    return {'hvac_mode': getStatus(startStatus),
            'target_temp': 21,
            'target_temp_low': 18,
            'target_temp_high': 22,
            'ambient_temp': startTemperature,
            'humidity': startHumidity}


def job_function():
    # function will update temperature inside
    for x in states.keys():
        weatherOutside = weather
        actualTemperature = states[x]['ambient_temp']
        actualHumidity = states[x]['humidity']
        targetTemperature = states[x]['target_temp']
        actualStatus = states[x]['hvac_mode']
        temperatureDifference = abs(weatherOutside[0] - actualTemperature)
        humidityDifference = abs(weatherOutside[1] - actualHumidity)
        rand = random.uniform(0, 2.5)
        if actualStatus == status.heat:
            if abs(actualTemperature - targetTemperature) < 0.5:
                if actualTemperature - targetTemperature < 0:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 + 0.1) * (
                                                        temperatureDifference / 50) * (humidityDifference / 30) * rand
                else:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 - 0.1) * (
                                                        temperatureDifference / 50) * (humidityDifference / 30) * rand
            elif actualTemperature > targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 30) * (
                        temperatureDifference / 50) * (humidityDifference / 30) * rand
            elif actualTemperature < targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 7) * (
                        temperatureDifference / 50) * (humidityDifference / 30) * rand

        if actualStatus == status.cool:
            if abs(actualTemperature - targetTemperature) < 0.5:
                if actualTemperature - targetTemperature < 0:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 + 0.06) * (
                                                        temperatureDifference / 50) * (humidityDifference / 30) * rand
                else:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 - 0.2) * (
                                                        temperatureDifference / 50) * (humidityDifference / 30) * rand
            elif actualTemperature > targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 7) * (
                        temperatureDifference / 50) * (humidityDifference / 40) * rand
            elif actualTemperature < targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 30) * (
                        temperatureDifference / 50) * (humidityDifference / 50) * rand

        if actualStatus == status.hc:
            if abs(actualTemperature - targetTemperature) < 0.7:
                if actualTemperature - targetTemperature < 0:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 + 0.2) * (
                                                        temperatureDifference / 60) * (humidityDifference / 40) * rand
                else:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 - 0.2) * (
                                                        temperatureDifference / 60) * (humidityDifference / 40) * rand
            elif actualTemperature > targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 13) * (
                        temperatureDifference / 60) * (humidityDifference / 40) * rand
            elif actualTemperature < targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 13) * (
                        temperatureDifference / 60) * (humidityDifference / 40) * rand

        if actualStatus == status.eco:
            if abs(actualTemperature - targetTemperature) < 0.4:
                if actualTemperature - targetTemperature < 0:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 + 0.15) * (
                                                        temperatureDifference / 45) * (humidityDifference / 45) * (
                                                        rand * 1.5)
                else:
                    states[x]['ambient_temp'] = actualTemperature + (
                            (targetTemperature - actualTemperature) / 2 - 0.15) * (
                                                        temperatureDifference / 45) * (humidityDifference / 45) * (
                                                        rand * 1.5)
            elif actualTemperature > targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 16) * (
                        temperatureDifference / 45) * (humidityDifference / 45) * (rand * 1.5)
            elif actualTemperature < targetTemperature:
                states[x]['ambient_temp'] = actualTemperature + ((targetTemperature - actualTemperature) / 17) * (
                        temperatureDifference / 45) * (humidityDifference / 45) * (rand * 1.5)


def changeTemperature():
    # function will change temperature inside basing on the temperature outside
    for x in states.keys():
        actualTemperature = states[x]['ambient_temp']
        states[x]['ambient_temp'] = actualTemperature - ((actualTemperature - weather[0]) / 200)


def changeHumidity():
    for x in states.keys():
        actualHumidity = states[x]['humidity']
        outsideHumidity = weather[1]
        states[x]['humidity'] = (actualHumidity + (((outsideHumidity - actualHumidity) / 25) * random.uniform(-1, 1)))


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

states['default'] = initial_state()


@app.route('/', methods=['GET'])
def welcome():
    return 'Hello\n'


@app.route('/devices/thermostats/<int:id>/register', methods=['PUT'])
def register(id):
    if (id not in states):
        states[id] = initial_state()
        return jsonify({'id': id})
    return jsonify({'id': id})


@app.route('/devices/thermostats/<int:id>/target_temperature_c', methods=['GET'])
def get_target_temp(id):
    if (id in states):
        return jsonify({'target_temperature_c': states[id]['target_temp']})
    return jsonify({'target_temperature_c': states['default']['target_temp']})


@app.route('/devices/thermostats/<int:id>/target_temperature_c', methods=['PUT'])
def put_target_temp(id):
    if (id in states):
        if not request.json:
            abort(400)
        if not 'target_temperature_c' in request.json:
            abort(400)
        states[id]['target_temp'] = request.json.get('target_temperature_c')
        return jsonify({'target_temperature_c': states[id]['target_temp']})
    return jsonify({'target_temperature_c': states['default']['target_temp']})


@app.route('/devices/thermostats/<int:id>/target_temperature_low_c', methods=['GET'])
def get_target_temp_low(id):
    if (id in states):
        return jsonify({'target_temperature_low_c': states[id]['target_temp_low']})
    return jsonify({'target_temperature_low_c': states['default']['target_temp_low']})


@app.route('/devices/thermostats/<int:id>/target_temperature_low_c', methods=['PUT'])
def put_target_temp_low(id):
    if (id in states):
        if not request.json:
            abort(400)
        if not 'target_temperature_low_c' in request.json:
            abort(400)
        states[id]['target_temp_low'] = request.json.get('target_temperature_low_c')
        return jsonify({'target_temperature_low_c': states[id]['target_temp_low']})
    states['default']['target_temp_low'] = request.json.get('target_temperature_low_c')
    return jsonify({'target_temperature_low_c': states['default']['target_temp_low']})


@app.route('/devices/thermostats/<int:id>/target_temperature_high_c', methods=['GET'])
def get_target_temp_high(id):
    if (id in states):
        return jsonify({'target_temperature_high_c': states[id]['target_temp_high']})
    return jsonify({'target_temperature_high_c': states['default']['target_temp_high']})


@app.route('/devices/thermostats/<int:id>/target_temperature_high_c', methods=['PUT'])
def put_target_temp_high(id):
    if (id in states):
        if not request.json:
            abort(400)
        if not 'target_temperature_high_c' in request.json:
            abort(400)
        states[id]['target_temp_high'] = request.json.get('target_temperature_high_c')
        return jsonify({'target_temperature_high_c': states[id]['target_temp_high']})
    states['default']['target_temp_high'] = request.json.get('target_temperature_high_c')
    return jsonify({'target_temperature_high_c': states['default']['target_temp_high']})


@app.route('/devices/thermostats/<int:id>/hvac_mode', methods=['GET'])
def get_hvac(id):
    if (id in states):
        return jsonify({'hvac_mode': states[id]['hvac_mode'].name})
    return jsonify({'hvac_mode': states['default']['hvac_mode'].name})


@app.route('/devices/thermostats/<int:id>/hvac_mode', methods=['PUT'])
def put_hvac(id):
    if (id in states):
        if not request.json:
            abort(400)
        if not 'hvac_mode' in request.json:
            abort(400)
        states[id]['hvac_mode'] = request.json.get('hvac_mode')
        return jsonify({'hvac_mode': states[id]['hvac_mode'].name})
    states['default']['hvac_mode'] = request.json.get('hvac_mode')
    return jsonify({'hvac_mode': states['default']['hvac_mode'].name})


@app.route('/devices/thermostats/<int:id>/ambient_temperature_c', methods=['GET'])
def get_ambient_temp(id):
    if (id in states):
        return jsonify({'ambient_temperature_c': states[id]['ambient_temp']})
    return jsonify({'ambient_temperature_c': states['default']['ambient_temp']})


@app.route('/devices/thermostats/<int:id>/humidity', methods=['GET'])
def get_humidity(id):
    if (id in states):
        return jsonify({'humidity': states[id]['humidity']})
    return jsonify({'humidity': states['default']['humidity']})


@app.route('/devices/thermostats/simulate', methods=['GET'])
def simulation():
    response = jsonify(simluate_for_api(1, datetime.strptime(date_str2, '%m/%d/%y'), user_preferences))
    response.status_code = 200
    return response


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
    if (date_ref.hour in user_preferences[date_ref.date().weekday()]):
        for x in states.keys():
            states[x][user_preferences[date_ref.date().weekday()][date_ref.hour][0]] = \
                user_preferences[date_ref.date().weekday()][date_ref.hour][1]


def simluate_for_api(number_of_days, starting_date, user_preferences):
    result = []
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
            for x in states.keys():
                result.append({
                    'id': x,
                    'time': starting_date,
                    'target_temp': states[x]['target_temp'],
                    'target_temp_low': states[x]['target_temp_low'],
                    'target_temp_high': states[x]['target_temp_high'],
                    'humidity': states[x]['humidity'],
                    'ambient_temp': states[x]['ambient_temp'],
                    'hvac_mode': states[x]['hvac_mode'].name})

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
                writer.writerow([starting_date, states['default']['target_temp'], states['default']['target_temp_low'],
                                 states['default']['target_temp_high'], states['default']['humidity'],
                                 states['default']['ambient_temp'], states['default']['hvac_mode']])

            updateWeatherForSimulation(forecast, starting_date, start_ref)


date_str2 = '1/3/21'

# simluate(1,datetime.strptime(date_str2, '%m/%d/%y'),user_preferences)

if __name__ == '__main__':
    app.run(use_reloader=False)
