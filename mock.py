import flask
from flask import request, jsonify
from flask import abort
import time
import atexit
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler



def job_function():
    #update_data_perdioclay
    print("update ran")

cron = BackgroundScheduler(daemon=True)
cron.add_job(job_function,'interval',minutes=1)
cron.start()


# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))


app = flask.Flask(__name__)
app.config["DEBUG"] = True
state = {'hvac_mode': 'heat',
         'target_temp': 21,
         'target_temp_low': 18,
         'target_temp_high': 22,
         'ambient_temp': 20,
         'humidity': 60}


@app.route('/devices/thermostats/<int:id>/target_temperature_c', methods=['GET'])
def get_target_temp(id):
    return jsonify({'target_temperature_c':state['target_temp']})

@app.route('/devices/thermostats/<int:id>/target_temperature_c', methods=['PUT'])
def put_target_temp(id):
    if not request.json:
        abort(400)
    if not 'target_temperature_c' in request.json:
        abort(400)
    state['target_temp'] = request.json.get('target_temperature_c')
    return jsonify({'target_temperature_c':state['target_temp']})


@app.route('/devices/thermostats/<int:id>/target_temperature_low_c', methods=['GET'])
def get_target_temp_low(id):
    return jsonify({'target_temperature_low_c':state['target_temp_low']})

@app.route('/devices/thermostats/<int:id>/target_temperature_low_c', methods=['PUT'])
def put_target_temp_low(id):
    if not request.json:
        abort(400)
    if not 'target_temperature_low_c' in request.json:
        abort(400)
    state['target_temp_low'] = request.json.get('target_temperature_low_c')
    return jsonify({'target_temperature_low_c':state['target_temp_low']})

@app.route('/devices/thermostats/<int:id>/target_temperature_high_c', methods=['GET'])
def get_target_temp_high(id):
    return jsonify({'target_temperature_high_c':state['target_temp_high']})

@app.route('/devices/thermostats/<int:id>/target_temperature_high_c', methods=['PUT'])
def put_target_temp_high(id):
    if not request.json:
        abort(400)
    if not 'target_temperature_high_c' in request.json:
        abort(400)
    state['target_temp_high'] = request.json.get('target_temperature_high_c')
    return jsonify({'target_temperature_high_c':state['target_temp_high']})

@app.route('/devices/thermostats/<int:id>/hvac_mode', methods=['GET'])
def get_hvac(id):
    return jsonify({'hvac_mode':state['hvac_mode']})

@app.route('/devices/thermostats/<int:id>/hvac_mode', methods=['PUT'])
def put_hvac(id):
    if not request.json:
        abort(400)
    if not 'hvac_mode' in request.json:
        abort(400)
    state['hvac_mode'] = request.json.get('hvac_mode')
    return jsonify({'hvac_mode':state['hvac_mode']})


@app.route('/devices/thermostats/<int:id>/ambient_temperature_c', methods=['GET'])
def get_ambient_temp(id):
    return jsonify({'ambient_temperature_c':state['ambient_temp']})

@app.route('/devices/thermostats/<int:id>/humidity', methods=['GET'])
def get_humidity(id):
    return jsonify({'humidity':state['humidity']})

@app.route('/devices/thermostats/<int:id>/time_to_target', methods=['GET'])
def get_time(id):
    return jsonify({'time_to_target':get_time_to_target()})


def get_time_to_target():
    return 20


app.run()