# W5100S-EVB-Pico Home Assistant IO Board
# Copyright (C) 2022 David Dietrich
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
import board
import busio
import digitalio
import time
import config

from adafruit_debouncer import Debouncer
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

import adafruit_minimqtt.adafruit_minimqtt as MQTT

IOs = dict()
led = None
now = time.monotonic()
lastBlink = time.monotonic()
timesToBlink = 0

# Set up a MQTT Client
# NOTE: We'll need to connect insecurely for ethernet configurations.
mqtt_client = MQTT.MQTT(
    broker=config.broker['broker'],  #PC IP address
    username=config.broker['username'],
    password=config.broker['password'],
    is_ssl=config.broker['is_ssl'],
    socket_pool=config.broker['socket_pool'],
    ssl_context=config.broker['ssl_context'],
)
### Code ###
def read_switches():
    for _i in IOs:
        if IOs[_i]['type'] == 'OUTPUT':
            continue
        switch = IOs[_i]['switch']
        switch.update()
        longpTime = IOs[_i]['longpTime'] if 'longpTime' in IOs[_i] else 1
        if IOs[_i]['switchType'] == 'toggle' or IOs[_i]['switchType'] == 'momentary':
            if IOs[_i]['state'] == 'off':
                if switch.fell:
                    IOs[_i]['state'] = 'on'
                    IOs[_i]['stateChanged'] = True
                    print("State changed: " + IOs[_i]['id'] + "on")
                    if IOs[_i]['switchType'] == 'momentary':
                        IOs[_i]['pressedAt'] = time.monotonic()
            if IOs[_i]['state'] == 'on':                
                if switch.rose:
                    IOs[_i]['state'] = 'off'
                    IOs[_i]['stateChanged'] = True
                    print("State changed: " + IOs[_i]['id'] + "off")                    
                    IOs[_i]['pressedAt'] = -1
                if switch.value == False and time.monotonic() - IOs[_i]['pressedAt'] > longpTime and IOs[_i]['pressedAt'] != -1:
                    print("longpress: " + str(longpTime))
                    IOs[_i]['longPressed'] = True
                    IOs[_i]['pressedAt'] = -1
                    IOs[_i]['stateChanged'] = True
        elif IOs[_i]['switchType'] == 'edge':
            if switch.rose:
                if IOs[_i]['state'] == 'off':
                    IOs[_i]['state'] = 'on'
                    IOs[_i]['stateChanged'] = True
                    print("State changed: " + IOs[_i]['id'] + "on")
                else:
                    IOs[_i]['state'] = 'off'
                    IOs[_i]['stateChanged'] = True
                    print("State changed: " + IOs[_i]['id'] + "off")

def blink_led(times = 0, delay = 0.1):
    global lastBlink, timesToBlink
    if times != 0:
        timesToBlink = times * 2
    if timesToBlink == 0:
        led.value = False
        return
    if time.monotonic() - lastBlink > delay:
        led.value = not led.value
        lastBlink = time.monotonic()
        timesToBlink -= 1

def publish_states():
    for _i in IOs:
        if IOs[_i]['type'] == 'OUTPUT':
            continue
        if IOs[_i]['stateChanged']:
            if IOs[_i]['switchType'] == 'momentary':
                print('momentary')
                if IOs[_i]['longPressed'] == True:
                    print("Publish Longpressed")
                    mqtt_client.publish(get_state_topic(_i, True), 'ON')
                    IOs[_i]['longPressed'] = False
                else:
                    mqtt_client.publish(get_state_topic(_i), IOs[_i]['state'].upper())
                    if IOs[_i]['state'] == 'off':
                        mqtt_client.publish(get_state_topic(_i, True), 'OFF')
                    # Publish longpress off
                IOs[_i]['stateChanged'] = False
            else:
                mqtt_client.publish(get_state_topic(_i), IOs[_i]['state'].upper())
                IOs[_i]['stateChanged'] = False

def init_io():
    global led
    global switch
    led = digitalio.DigitalInOut(board.GP25)
    led.direction = digitalio.Direction.OUTPUT

    for _io in config.IOs:
        _p = make_pin(getattr(board, _io['pin']), _io)
        IOs[_io['id']] = dict(
                pin = _p,
                type = _io['type'],
                id = _io['pin']
            )
        if _io['type'] == "INPUT":
            IOs[_io['id']]['switch'] = Debouncer(IOs[_io['id']]['pin'])
            IOs[_io['id']]['state'] = 'off'
            IOs[_io['id']]['switchType'] = _io['switchType']
            IOs[_io['id']]['stateChanged'] = False
            IOs[_io['id']]['longPressed'] = False
            IOs[_io['id']]['pressedAt'] = -1
            if 'longpTime' in _io:            
                IOs[_io['id']]['longpTime'] = _io['longpTime']
    print(IOs)

def init_ethernet():
    #SPI0
    SPI0_SCK = board.GP18
    SPI0_TX = board.GP19
    SPI0_RX = board.GP16
    SPI0_CSn = board.GP17
    #Reset
    W5x00_RSTn = board.GP20
    print("W5100S-EVB-Pico HomeAssistant board")
    MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, config.device['mac'])
    ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
    ethernetRst.direction = digitalio.Direction.OUTPUT
    cs = digitalio.DigitalInOut(SPI0_CSn)
    spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)
    # Reset W5500 first
    ethernetRst.value = False
    time.sleep(1)
    ethernetRst.value = True
    _eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)
    return _eth

def init_mqtt(eth):
    print()

def make_pin(pin, _config):
    io = digitalio.DigitalInOut(pin)
    if _config['type'] == 'OUTPUT':
        io.direction = digitalio.Direction.OUTPUT
        io.value = _config['defState']
    else:
        io.direction = digitalio.Direction.INPUT
        io.pull = digitalio.Pull.UP
    return io
#callbacks
def message(client, topic, message):
    # Method callled when a client's subscribed feed has a new value.
    print("New message on topic {0}: {1}".format(topic, message))
    for i in IOs:
        if IOs[i]['type'] == 'INPUT':
            continue        
        _tp = get_set_topic(i)
        if topic == _tp:
            blink_led(4, 0.4)
            #print("Found: " + topic);
            if message.lower() == "on":
                IOs[i]['pin'].value = False
                mqtt_client.publish(get_state_topic(i), message)                
            else:
                IOs[i]['pin'].value = True
                mqtt_client.publish(get_state_topic(i), message)
    if topic == 'homeassistant/{0}/clear'.format(config.device['id']):
        mqtt_discovery(True)
    

#Subscribe to topics
def subscribe_to_topics():
    for _io in IOs:
        if IOs[_io]['type'] == 'INPUT':
            continue
        mqtt_client.subscribe(get_set_topic(_io))
        print("Subscribed to:" + get_set_topic(_io))

    mqtt_client.subscribe('homeassistant/{0}/clear'.format(config.device['id']))

#Get set topic
def get_set_topic(_io):
    return "homeassistant/switch/{0}/{1}".format(config.device['id'], _io) + "/set"

#Get state topic
def get_state_topic(_io, longPress = False):
    if IOs[_io]['type'] == 'INPUT':
        if longPress:
            return "homeassistant/binary_sensor/{0}/{1}_longp".format(config.device['id'], _io) + "/state"
        else:
            return "homeassistant/binary_sensor/{0}/{1}".format(config.device['id'], _io) + "/state"
    else:
        return "homeassistant/switch/{0}/{1}".format(config.device['id'], _io) + "/state"
def get_base_topic(_io, longPress = False):
    if IOs[_io]['type'] == 'INPUT':
        if longPress:
            return "homeassistant/binary_sensor/{0}/{1}_longp".format(config.device['id'], _io)
        else:
            return "homeassistant/binary_sensor/{0}/{1}".format(config.device['id'], _io)
    else:
        return "homeassistant/switch/{0}/{1}".format(config.device['id'], _io)

#Homeassistant MQTT discovery
def mqtt_discovery(clear = False):
    for _io in IOs:
        _base_topic = get_base_topic(_io)

        _topic = _base_topic + "/config"
        _payload = '"~": "' + _base_topic + '", "name": "{0}_{1}"'.format(config.device['id'], _io) + ', "stat_t": "~/state", "ret": true'
        if IOs[_io]['type'] == 'OUTPUT':
            _payload += ', "cmd_t": "~/set"'
        _payload = "{" + _payload + "}"
        if not clear:
            mqtt_client.publish(_topic, _payload)
        else:
            mqtt_client.publish(_topic, '')
        if 'switchType' in IOs[_io] and IOs[_io]['switchType'] == 'momentary':
            _base_topic = get_base_topic(_io, True)
            _topic = _base_topic + "/config"
            _payload = '"~": "' + _base_topic + '", "name": "{0}_{1}_longp"'.format(config.device['id'], _io) + ', "stat_t": "~/state"'            
            _payload = "{" + _payload + "}"
            if not clear:
                mqtt_client.publish(_topic, _payload)
            else:
                mqtt_client.publish(_topic, '')
            print(_topic)
            print(_payload)


    _stopic = "homeassistant/sensor/{0}/uptime_n/config".format(config.device['id'])
    _spayload = '"~": "' + "homeassistant/sensor/{0}/uptime_n".format(config.device['id']) + '", "name": "{0}_uptime_n"'.format(config.device['id']) + ', "stat_t": "~/state"'
    _spayload = "{" + _spayload + "}"
    print(_stopic)
    print(_spayload)
    mqtt_client.publish(_stopic, _spayload)

#Init ios
init_io()
#Init ethernet
eth = init_ethernet()

init_mqtt(eth)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize MQTT interface with the ethernet interface
MQTT.set_socket(socket, eth)
# Setup the callback methods above
mqtt_client.on_message = message
# Connect the client to the MQTT broker.
print("Connecting to Broker...")
mqtt_client.connect()
print("Connected to Broker...")
blink_led(5)
mqtt_discovery()
mqtt_client.publish("homeassistant/sensor/{0}/uptime_n/state".format(config.device['id']), round(time.monotonic() / 60, 1))

#subscribe a new message
subscribe_to_topics()
#MQTT Subscriber Run
uptime = time.monotonic()
while True:
    #start = time.monotonic()
    mqtt_client.loop(0.0001)
    read_switches()
    publish_states()
    if time.monotonic() - uptime > 60:
        now = time.monotonic()
        mqtt_client.publish("homeassistant/sensor/{0}/uptime_n/state".format(config.device['id']), round(time.monotonic() / 60, 1))
    if time.monotonic() - now > 10:
        blink_led(2)
        now = time.monotonic()
    blink_led()
    
#Disconnected
print("Disconnecting from %s" % mqtt_client.broker)
mqtt_client.disconnect()
