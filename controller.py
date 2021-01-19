import json

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

ENDPOINT = "a24ojhzjcj6a8j-ats.iot.us-east-1.amazonaws.com"
# CLIENT_ID = "testDevice"
PATH_TO_CERT = "certificates/9edb23887d-certificate.pem.crt"
PATH_TO_KEY = "certificates/9edb23887d-private.pem.key"
PATH_TO_ROOT = "certificates/root.pem"

ID = "controller"
CLIENT = AWSIoTMQTTClient(str(ID))
QOS = 0


def configure_mqtt():
    CLIENT.configureEndpoint(ENDPOINT, 8883)
    CLIENT.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)
    CLIENT.connect()
    on_connect()
    # on_message()


def printMessage(client, userdata, message):
    # print(f"Received from topic: {message.topic} : {message.payload}")
    topic = message.topic
    payload = message.payload
    mess = json.loads(payload)
    if len(message.topic.split("/")) < 4:
        print(f"Received from topic: {message.topic} : {message.payload}")
    else:
        mockID = message.topic.split("/")[3]
        mess = list(json.loads(message.payload).values())
        print(f"Thermostat {mockID} " + str(message.topic.split('/')[4]) + ": " + str(mess[1]))


def on_connect():
    # CLIENT.subscribe('/', 1, welcome)
    CLIENT.subscribe(f'/devices/thermostats/+/get_target_temperature_return', QOS, printMessage)
    CLIENT.subscribe(f'/devices/thermostats/+/get_target_temperature_low_return', QOS, printMessage)
    CLIENT.subscribe(f'/devices/thermostats/+/get_target_temperature_high_return', QOS, printMessage)
    CLIENT.subscribe(f'/devices/thermostats/+/get_hvac_mode_return', QOS, printMessage)
    CLIENT.subscribe(f'/devices/thermostats/+/get_ambient_temperature_return', QOS, printMessage)
    CLIENT.subscribe(f'/devices/thermostats/+/get_humidity_return', QOS, printMessage)
    CLIENT.subscribe(f'/devices/info', QOS, printMessage)
    print("connect")


def on_message(client, userdata, message):
    print(message.payload.decode('utf8'))


def executeCommand(command):
    split = command.split(" ")
    if len(split) < 2:
        print("Command is too short")
        return
    comm, mockID = split[0], split[1]
    value = ''
    print(value)
    if len(split) == 3:
        value = split[2]
    if comm == 'help':
        print("pomoc:")
    elif comm == 'ambient_temp':
        CLIENT.publish(f'/devices/thermostats/{mockID}/get_ambient_temperature', '0', QOS)
    elif comm == 'get_target_temp':
        CLIENT.publish(f'/devices/thermostats/{mockID}/get_target_temperature', '0', QOS)
    elif comm == 'get_target_temp_low':
        CLIENT.publish(f'/devices/thermostats/{mockID}/get_target_temperature_low', '0', QOS)
    elif comm == 'get_target_temp_high':
        CLIENT.publish(f'/devices/thermostats/{mockID}/get_target_temperature_high', '0', QOS)
    elif comm == 'get_hvac_mode':
        CLIENT.publish(f'/devices/thermostats/{mockID}/get_hvac_mode', '0', QOS)
    elif comm == 'get_humidity':
        CLIENT.publish(f'/devices/thermostats/{mockID}/get_humidity', '0', QOS)
    elif comm == 'put_hvac_mode':
        CLIENT.publish(f'/devices/thermostats/{mockID}/put_hvac_mode', value, QOS)
    elif comm == 'put_target_temp':
        CLIENT.publish(f'/devices/thermostats/{mockID}/put_target_temperature', value, QOS)
    elif comm == 'put_target_temp_high':
        CLIENT.publish(f'/devices/thermostats/{mockID}/put_target_temperature_high', value, QOS)
    elif comm == 'put_target_temp_low':
        CLIENT.publish(f'/devices/thermostats/{mockID}/put_target_temperature_low', value, QOS)
    else:
        print("Command not recognized")


if __name__ == '__main__':
    configure_mqtt()
    while True:
        command = input()
        executeCommand(command)
