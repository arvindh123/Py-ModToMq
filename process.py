from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import paho.mqtt.client as mqtt
import socket
from multiprocessing import Process, Pipe, Value, Manager
import random
import json
import time
from app import logger,db
from models import User, modbus_address,mqtt_parameters,modbus_parameters,pub_mqtt_topics,read_mod_registers
from datetime import datetime

############------------------------------------------------------################

def on_connect(client, userdata, flag,rc):
    print("Connected with result code "+str(rc))   
    logger.info("Connected with result code "+str(rc)) 
    client.subsrcibe("Modbus\Received")
    Mqtt_Stat.value =  rc


def ModReadJson(client,start,qty):
    response = client.read_holding_registers(start,qty,unit=0x1)
    return_dict = {}
    for i in range(qty):
        return_dict["%s" %str(start+i)] = "%s" %str(response.registers[i])
    return json.dumps(return_dict)

def ModReadTopic(client,topic):
    value_dict = {} 
    # ret_dict =  {}
    for regis in topic.mod_addresses:
        response = client.read_holding_registers(regis.address,regis.qty,unit = regis.unit)
        
        if regis.pp:
            exec(regis.pp)
            # value = exec(regis.pp)
            # value_dict[regis.name] = value
        else:
            value_dict[regis.name] = "%s" %response.registers
        # print(json.dumps(value_dict))     
    # value_dict["ts"] = str(datetime.now())
    return (topic, json.dumps(value_dict))
    

def ModWriteJson(client,json_data):
    print(json_data)
    pass

def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

def is_connected(hostname,port):
   try:
      # see if we can resolve the host name -- tells us if there is
      # a DNS listening
      if validate_ip(hostname):
         host = hostname
      else:
         host = socket.gethostbyname(hostname)
      # connect to the host -- tells us if the host is actually
      # reachable
      s = socket.create_connection((host, port), 2)
      s.close()
      del s
      return True
   except:
      return False
      pass
   return False
#################---------------mqtt function ---------------------################

def Mqtt_process(Stat, MqConn,MqStatChild , MqDataChild,):
    mq = mqtt_parameters.query.get(1)
    try:
        client = mqtt.Client(client_id = "Proj_%s" %(random.getrandbits(8)))
        client.on_connect = on_connect
        # Mqtt_Stat = client._handle_connack()
        if mq.mqtt_user_name and mq.mqtt_password :
            client.username_pw_set(mq.mqtt_user_name,mq.mqtt_password)
        elif mq.mqtt_access_token:
            client.username_pw_set(mq.mqtt_access_token)

        client.connect(mq.mqtt_ip,mq.mqtt_port,60)
        MqStatChild.send("Setted Client parameters")
        logger.info("Setted Client parameters")

        client.loop_start()
        MqStatChild.send("Loop Started & Connected to Server")
        logger.info("Loop Started & Connected to Server")
        Mqtt_Stat = Stat.value
        while (Mqtt_Stat > 0):
            time.sleep(1)

            if Mqtt_Stat == 0:
                pass

            elif Mqtt_Stat == 1: #---Connection refused - incorrect protocol version ---#
                client.loop_stop()
                MqStatChild.send("Connection refused - invalid client identifier")    
                logger.error("Connection refused - invalid client identifier")  

            elif Mqtt_Stat == 2 : #---Connection refused - invalid client identifier---#
                MqStatChild.send("Connection refused - invalid client identifier")
                logger.error("Connection refused - invalid client identifier")
                client.loop_stop()
                time.sleep(1)
                client = mqtt.Client(client_id = "Proj_%s" %random.getrandbits(8))
                MqStatChild.send("Changed another Client identifier")
                logger.info("Changed another Client identifier")
                client.loop_start()
                MqStatChild.send("Loop Started")
                logger.info("Loop Started")

            elif Mqtt_Stat == 3: #-- Connection refused - server unavailable ---#
                client.loop_stop()
                MqStatChild.send("Connection Unaviable Checck Internet")
                logger.error("Connection Unaviable Checck Internet")

            elif Mqtt_Stat == 4: #---Connection refused - bad username or password---#
                client.loop_stop()
                MqStatChild.send(" Connection refused - bad username or password")
                logger.error(" Connection refused - bad username or password")
            elif Mqtt_Stat == 5 : #---Connection refused - not authorised---#
                client.loop_stop()
                MqStatChild.send("Connection refused - not authorised")
                logger.error("Connection refused - not authorised")

            else :
                MqStatChild.send("Waiting for Connection or Not Connected or -->Mqtt_Stat - %s" %Mqtt_Stat)
                logger.info("Waiting for Connection or Not Connected or -->Mqtt_Stat - %s" %Mqtt_Stat)

        while True:
            if MqConn.poll():
                msg = MqConn.recv()
                client.publish(msg[0].topic, payload= msg[1], qos=msg[0].qos, retain=msg[0].retain)
                # client.publish(msg["topic"], msg["value"])
                MqDataChild.send(msg)

    except Exception as e :
        client.loop_stop()
        print("Mqtt error - {}".format(e))
        MqStatChild.send("Mqtt Disconnected, mqtt Process Stopped")
        MqStatChild.send(str(e))
        logger.exception("Got Exception")


####################------------------Modbus function -------------------#####################
def Mod_ReadWrite(ModConn, ModStatChild):
    mod = modbus_parameters.query.get(1)
    
    PubTopics = pub_mqtt_topics.query.filter(pub_mqtt_topics.mod_addresses.any(read_mod_registers.address >= 0)).all()

    try:
        while True:
            if is_connected(mod.modbus_ip,mod.modbus_port):
                ModStatChild.send("Modbus device Connection is UP")
                logger.info("Modbus device Connection is UP")
                break
            else:
                ModStatChild.send("Modbus device connection is  DOWN")
                logger.error("Modbus device connection is  DOWN")
                time.sleep(10)
        Modclient = ModbusClient(mod.modbus_ip, port = mod.modbus_port)
        msg = 0        
        while True :
            
            if ModStatChild.poll():
                msg = ModStatChild.recv()
                print("received Msg in modbus outer while loop {}".format(msg))
                logger.info("received Msg in modbus outer while loop {}".format(msg))
            if msg == 1:
                Modclient.connect()
                ModStatChild.send("Connected to Modbus device")
                logger.info("Connected to Modbus device")
                msg = 2
            while msg  == 2:
                # GetModValues = ModReadJson(Modclient, 0 , 10) 
                for topic in PubTopics:
                    GetModValues = ModReadTopic(Modclient,topic)
                    #########################
                    ModConn.send(GetModValues)
                    #########################
                    # print(GetModValues)
                time.sleep(0.5)
                if ModStatChild.poll():
                    msg = ModStatChild.recv()
                    if msg == 1 :
                        print("received Msg in modbus inner while loop {}".format(msg))
                        logger.info("received Msg in modbus inner while loop {}".format(msg))
                        msg = 2
                        ModStatChild.send("Modbus device data Acquisition already running")
                    
            while msg == 3 :
                Modclient.close()
                msg = 0
                ModStatChild.send("Modbus device connection Closed")
                
            # FlModChild.send("Disconnected from Controller")
        # FlModChild.send(GetModValues)
        # if ModConn.poll():
        #     msg = ModConn.recv()
        #     if isinstance(msg, dict):
        #         if "ModWrite" in msg:
        #             if msg["ModWrite"] == True:
        #                 ModWriteJson(ModbusClient,msg)
    except Exception as e:
        ModStatChild.send("Modbus Disconnected, Modbus process Stopped")
        ModStatChild.send(str(e))
        print(e)
############------------------------------------------------------################