from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from ctypes import c_short
import socket
import json
import time


from multiprocessing import Process, Pipe, Value, Manager
import random
from ctypes import c_char_p
from check import is_connected
import logging 
logger = logging.getLogger(__name__)
logging.basicConfig(filename='exceptionnss.log',format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
random.seed(time.time())


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option gased on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

FlMqParent, FlMqChild = Pipe()
FlModParent, FlModChild  = Pipe()

############--------------Variables-------Save all as ini file ----#############
Proj = "Test"
UNIT = 0x1
Remote_Server = "localhost"
Remote_Server_Port = 1883 
mqUsername = None
mqPassword = None
mqAccessToken = None
Controller_address = "localhost"
Controller_port = 502
Mqtt_Stat = Value('d', 0)


Mqtt_Cmd = Value('d', 0)
Mod_Cmd = Value('d', 0)


############------------------------------------------------------################

def on_connect(client, userdata, flag,rc):

    print("Connected with result code "+str(rc))   
    logger.info("Connected with result code "+str(rc)) 
    client.subsrcibe("Modbus\Received")
    Mqtt_Stat.value =  rc


def ModReadJson(client,start,qty):
    result = client.read_holding_registers(start,qty,unit=UNIT)
    return_dict = {}
    if hasattr(result ,"registers"):
        for i in range(len(result.registers)):
            return_dict["%s" %str(start+i)] = "%s" %str(result.registers[i])
    return json.dumps(return_dict)

def ModWriteJson(client,json_data):
    print(json_data)
    pass

#################---------------mqtt function ---------------------################

def Mqtt_process(Stat, MqConn,FlMqChild):
    # global Mqtt_Stat
    try:
        client = mqtt.Client(client_id = "Proj_%s" %(random.getrandbits(8)))
        client.on_connect = on_connect
        Mqtt_Stat = client._handle_connack()
        if mqUsername and mqPassword :
            client.username_pw_set(mqUsername,mqPassword)
        elif mqAccessToken:
            client.username_pw_set(mqAccessToken)

        client.connect(Remote_Server,Remote_Server_Port,60)
        FlMqChild.send("Setted Client parameters")
        logger.info("Setted Client parameters")

        client.loop_start()
        FlMqChild.send("Loop Started & Connected to Server")
        logger.info("Loop Started & Connected to Server")
        Mqtt_Stat = Stat.value
        while (Mqtt_Stat > 0):
            time.sleep(1)

            if Mqtt_Stat == 0:
                pass

            elif Mqtt_Stat == 1: #---Connection refused - incorrect protocol version ---#
                client.loop_stop()
                FlMqChild.send("Connection refused - invalid client identifier")    
                logger.error("Connection refused - invalid client identifier")  

            elif Mqtt_Stat == 2 : #---Connection refused - invalid client identifier---#
                FlMqChild.send("Connection refused - invalid client identifier")
                logger.error("Connection refused - invalid client identifier")
                client.loop_stop()
                time.sleep(1)
                client = mqtt.Client(client_id = "Proj_%s" %random.getrandbits(8))
                FlMqChild.send("Changed another Client identifier")
                logger.info("Changed another Client identifier")
                client.loop_start()
                FlMqChild.send("Loop Started")
                logger.info("Loop Started")

            elif Mqtt_Stat == 3: #-- Connection refused - server unavailable ---#
                client.loop_stop()
                FlMqChild.send("Connection Unaviable Checck Internet")
                logger.error("Connection Unaviable Checck Internet")

            elif Mqtt_Stat == 4: #---Connection refused - bad username or password---#
                client.loop_stop()
                FlMqChild.send(" Connection refused - bad username or password")
                logger.error(" Connection refused - bad username or password")
            elif Mqtt_Stat == 5 : #---Connection refused - not authorised---#
                client.loop_stop()
                FlMqChild.send("Connection refused - not authorised")
                logger.error("Connection refused - not authorised")

            else :
                FlMqChild.send("Waiting for Connection or Not Connected or -->Mqtt_Stat - %s" %Mqtt_Stat)
                logger.info("Waiting for Connection or Not Connected or -->Mqtt_Stat - %s" %Mqtt_Stat)

        while True:
            if MqConn.poll():
                msg = MqConn.recv()
                
                client.publish("Modbus/Received", msg)
                FlMqChild.send(msg)
    except Exception as e :
        print("Mqtt error - {}".format(e))
        logger.exception("Got Exception")


####################------------------Modbus function -------------------#####################
def Mod_ReadWrite(ModConn, FlModChild):
    try:
        while True:
            if is_connected(Controller_address,Controller_port):
                FlModChild.send("Controller Connection is UP")
                logger.info("Controller Connection is UP")
                break
            else:
                FlModChild.send("Controller connection is  DOWN")
                logger.error("Controller connection is  DOWN")
                time.sleep(10)
        Modclient = ModbusClient(Controller_address, port=Controller_port)
        msg = 0        
        while True :
            
            if FlModChild.poll():
                msg = FlModChild.recv()

            if msg == 1:
                Modclient.connect()
                FlModChild.send("Connected to Controller")
                logger.info("Connected to Controller")
                msg = 2
            while msg  == 2:
                GetModValues = ModReadJson(Modclient, 0 , 10) 
                if hasattr(GetModValues ,"registers"):
                    ModConn.send(GetModValues)
                print(GetModValues)
                if FlModChild.poll():
                    msg = FlModChild.recv()
            if Modclient :
                Modclient.close()
            # FlModChild.send("Disconnected from Controller")
        # FlModChild.send(GetModValues)
        # if ModConn.poll():
        #     msg = ModConn.recv()
        #     if isinstance(msg, dict):
        #         if "ModWrite" in msg:
        #             if msg["ModWrite"] == True:
        #                 ModWriteJson(ModbusClient,msg)
    except Exception as e:
        print(e)

############------------------------------------------------------################


def background_thread(FlMqParent,FlModParent):
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        if FlMqParent.poll():
            msg = FlMqParent.recv()
            socketio.emit('Status', {'data': msg, }, namespace='/Gate')
        if FlModParent.poll():
            msg = FlModParent.recv()
            socketio.emit('Status', {'data': msg, }, namespace='/Gate')


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/start')
def start():
    global thread
    with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(background_thread, FlMqParent, FlModParent)
    
    Mqtt_bacProc = None
    Mod_bacProc = None
    ModConn, MqConn = Pipe()
    if Mod_bacProc == None:
        Mod_bacProc  = Process(target=Mod_ReadWrite, args=(ModConn,FlModChild), daemon=True)
        Mod_bacProc.start()
    if Mqtt_bacProc == None:
        Mqtt_bacProc = Process(target=Mqtt_process, args=(Mqtt_Stat,MqConn,FlMqChild), daemon=True)
        Mqtt_bacProc.start()   
    print(Mqtt_bacProc.is_alive())
    if Mqtt_bacProc.is_alive():
        Mqtt_bacProc.join()
    if Mod_bacProc.is_alive():
        Mod_bacProc.join()
    


@socketio.on('Mqtt_Cmd', namespace='/Gate')
def Mqtt_Cmd_sock_fn(message):
    if message['data'] == "start":
        Mqtt_Cmd = 1

@socketio.on('Mod_Cmd', namespace='/Gate')
def Mod_Cmd_sock_fn(message):
    if message['data'] == "start":
        FlModParent.send(1)
    if message['data'] == "stop":
        FlModParent.send(0)
    print(message['data'] )

@socketio.on('SaveSettings', namespace='/Gate')
def Gate_SaveSettings(message):
    Recivied_Settings = message['data']

@socketio.on('disconnect_request', namespace='/Gate')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/Gate')
def ping_pong():
    emit('my_pong') 

@socketio.on('my_event', namespace='/Gate')
def my_event(message):
    # print(message['data'])
    emit('my_event',
         {'data': message['data']})


@socketio.on('connect', namespace='/Gate')
def Gate_connect():
    emit('Status', {'data': 'Connected to Socket', 'count': 0})


@socketio.on('disconnect', namespace='/Gate')
def Gate_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    
    socketio.run(app, debug=True)
    

    