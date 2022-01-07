# config file
# device
#   id: id of the device, this will appear in homeassistant
#   mac: the last character of the MAC address
device = dict(
    id = 'rd3',
    mac = 0x04,    
)

broker = dict(
    broker="192.168.1.11",  #MQTT broker IP address
    username="username",
    password="password",
    is_ssl=False,
    socket_pool=None,
    ssl_context=None,
)
# IO Config
#   id: id of the io, this will appear in homeassistant
#   pin: the GPxx of the board
#   type: IO direction INPUT or OUTPUT
#   defState: default state of the IO#   
#   sitchType: Only with type='INPUT' options: toggle | momentary | edge
#       toggle: standard switch, short to ground -> on, else -> off
#       momentary: short to ground -> on, else -> off
#           longpress sends mqtt state: binary_sensor.DEVICEID_IOID_longp           
#       edge: changes on/off state on button release
IOs = [dict(
    id = '3',
    pin = 'GP2',
    type = 'OUTPUT',
    defState = True,
), dict(
    id = '4',
    pin = 'GP3',
    type = 'OUTPUT',
    defState = True,
), dict(
    id = '5',
    pin = 'GP4',
    type = 'INPUT',
    switchType = 'momentary',
    longpTime = 1
), dict(
    id = '6',
    pin = 'GP5',
    type = 'INPUT',
    switchType = 'edge'
)]
