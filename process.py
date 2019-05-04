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
from models import User, ignition_parameter,mod_device,mqtt_parameters, modbus_parameters,read_mod_registers, all_status
from datetime import datetime
from sparkplug_b import *
import sparkplug_b as sparkplug
import string
############------------------------------------------------------################

def on_connect(client, userdata, flag,rc):
    print("Connected with result code "+str(rc))   
    logger.info("Connected with result code "+str(rc)) 
    # client.subsrcibe("Modbus\Received")
    client.subscribe("spBv1.0/" )
    Mqtt_Stat.value =  rc





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

#################------------Pulish Node Birth -------------------#################
def publishNodeBirth():
    print ("Publishing Node Birth")

    # Create the node birth payload
    payload = sparkplug.getNodeBirthPayload()
    

    # Set up the Node Controls
    addMetric(payload, "Node Control/Next Server", None, MetricDataType.Boolean, False)
    addMetric(payload, "Node Control/Rebirth", None, MetricDataType.Boolean, False)
    addMetric(payload, "Node Control/Reboot", None, MetricDataType.Boolean, False)

    byteArray = bytearray(payload.SerializeToString())
    return byteArray
######################################################################
def on_message(client, userdata, msg):
    print("Message arrived: " + msg.topic)
    tokens = msg.topic.split("/")
    igni= ignition_parameter.query.get(1)
    if tokens[0] == "spBv1.0" and tokens[1] == igni.group_id and (tokens[2] == "NCMD" or tokens[2] == "DCMD") and tokens[3] == igni.node_name:
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        for metric in inboundPayload.metrics:
            if metric.name == "Node Control/Next Server":
                # 'Node Control/Next Server' is an NCMD used to tell the device/client application to
                # disconnect from the current MQTT server and connect to the next MQTT server in the
                # list of available servers.  This is used for clients that have a pool of MQTT servers
                # to connect to.
                print(" Node Control/Next Server is not implemented in this example")
                # pass
            elif metric.name == "Node Control/Rebirth" :
                # 'Node Control/Rebirth' is an NCMD used to tell the device/client application to resend
                # its full NBIRTH and DBIRTH again.  MQTT Engine will send this NCMD to a device/client
                # application if it receives an NDATA or DDATA with a metric that was not published in the
                # original NBIRTH or DBIRTH.  This is why the application must send all known metrics in
                # its original NBIRTH and DBIRTH messages.
                # publishBirth()
                print(metric.name)
            elif metric.name == "Node Control/Reboot" :
                # 'Node Control/Reboot' is an NCMD used to tell a device/client application to reboot
                # This can be used for devices that need a full application reset via a sft reboot.
                # In this case, we fake a full reboot with a republishing of the NBIRTH and DBIRTH
                # messages.
                print(metric.name)
            else:
                print ("Unknown command: " + metric.name)
    else:
        print ("Unknown command...")

    print ("Done publishing")
#################------------Get Endian  -------------------#################
def getEndian(endianType):
    if endianType == None:
        return Endian.Big
    elif endianType == "Big Endian":
        return Endian.Big
    elif endianType == "Little Endian":
        return Endian.Little

#################------------Get Meteric Datatype -------------------#################
def getMetricDatatype(dttype):
    if dttype == None:
        return MetricDataType.String
    elif dttype == "Int8":
        return MetricDataType.Int8
    elif dttype == "Int16":
        return MetricDataType.Int16
    elif dttype == "Int32":
        return MetricDataType.Int32
    elif dttype == "Int64":
        return MetricDataType.Int64
    elif dttype == "UInt8":
        return MetricDataType.UInt8
    elif dttype == "UInt16":
        return MetricDataType.UInt16
    elif dttype == "UInt32":
        return MetricDataType.UInt32
    elif dttype == "UInt64":
        return MetricDataType.UInt64
    elif dttype == "Float":
        return MetricDataType.Float
    elif dttype == "Double":
        return MetricDataType.Double
    elif dttype == "Boolean":
        return MetricDataType.Boolean
    elif dttype == "String":
        return MetricDataType.String
    else:
        return MetricDataType.String     
#################------------Get Meteric Datatype -------------------#################
def getMetricDatatypeInit(dttype):
    if dttype == None:
        return (MetricDataType.String, "")
    elif dttype == "Int8":
        return (MetricDataType.Int8, 0)
    elif dttype == "Int16":
        return (MetricDataType.Int16, 0)
    elif dttype == "Int32":
        return (MetricDataType.Int32, 0)
    elif dttype == "Int64":
        return (MetricDataType.Int64, 0)
    elif dttype == "UInt8":
        return (MetricDataType.UInt8, 0)
    elif dttype == "UInt16":
        return (MetricDataType.UInt16, 0)
    elif dttype == "UInt32":
        return (MetricDataType.UInt32, 0)
    elif dttype == "UInt64":
        return (MetricDataType.UInt64, 0)
    elif dttype == "Float":
        return (MetricDataType.Float, 0)
    elif dttype == "Double":
        return (MetricDataType.Double, 0)
    elif dttype == "Boolean":
        return (MetricDataType.Boolean, 0)
    elif dttype == "String":
        return (MetricDataType.String, "")
    else:
        return (MetricDataType.String, "")

#################------------Pulish Node Birth -------------------#################

def publishDeviceBirth(regis):
    print ("Publishing Device Birth")
    payload = sparkplug.getDeviceBirthPayload()
    for reg in regis:
        retValue = getMetricDatatypeInit(reg.datatype)
        addMetric(payload, 'input/%s' %reg.name, reg.id, retValue[0], retValue[1])
    addMetric(payload, 'input/ts' ,None, MetricDataType.String,"")
    totalByteArray = bytearray(payload.SerializeToString())

    return totalByteArray

#################---------------Modbuss Return as dict-----------------################
def ModReadDict(client,Device):
    value_dict = {} 
    # ret_dict =  {}
    for regis in Device.mod_addresses:
        response = client.read_holding_registers(regis.address,regis.qty,unit = regis.unit)
        
        if regis.datatype == "Post Process":
            value_dict[regis.name] = exec(regis.pp)
        elif regis.datatype == "Int8":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_8bit_int(), regis.datatype)
        elif regis.datatype == "Int16":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_16bit_int(), regis.datatype)
        elif regis.datatype == "Int32":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_int(), regis.datatype)
        elif regis.datatype == "Int64":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_64bit_int(), regis.datatype)
        elif regis.datatype == "UInt8":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "UInt16":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "UInt32":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "UInt64":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "Float":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "Double":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "Boolean":
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers,byteorder=getEndian(regis.byteorder),wordorder=getEndian(regis.wordorder))
            value_dict[regis.name] = (decoder.decode_32bit_float(), regis.datatype)
        elif regis.datatype == "String":
            value_dict[regis.name] = ("{}" .format("".join(chr(i) for i in response.registers)), regis.datatype)
        else:
            value_dict[regis.name] = response.registers
        # print(json.dumps(value_dict))     
    value_dict["ts"] = (str(datetime.now()), "String")
    return (Device.dev_name, value_dict)
#################---------------Modbuss Return as palyload--------------################
def ModReadReg(client,Device):
    payload = sparkplug.getDdataPayload()
    for regis in Device.mod_addresses:
        response = client.read_holding_registers(regis.address,regis.qty,unit = regis.unit)
        if hasattr(response, "registers"):
                if isinstance(response.registers, list):
                    if regis.pp:
                        exec(regis.pp)
                        value = exec(regis.pp)
                        addMetric(payload, 'input/%s' %regis.name, regis.id, MetricDataType.String, "%s" %str(value))
                    else:
                        value = ''.join(str(e) for e in response.registers)
                        addMetric(payload, 'input/%s' %regis.name, regis.id, MetricDataType.String, ''.join(random.choice(string.ascii_lowercase) for i in range(12)))
    
    byteArray = bytearray(payload.SerializeToString())
    return (Device.dev_name, byteArray)
#################---------------mqtt function ---------------------################  
def genPayload(val_dict):
    payload = sparkplug.getDdataPayload()
    for key , value in val_dict.items():
        # addMetric(payload, 'input/%s' %key, None, MetricDataType.String, "%s" %str(value))
        addMetric(payload,'input/%s' %key, None, getMetricDatatype(value[1]), value[0])
    byteArray = bytearray(payload.SerializeToString())
    return byteArray
#################---------------mqtt function ---------------------################

def Mqtt_process(Stat, MqConn,MqStatChild , MqDataChild,):
    mq = mqtt_parameters.query.get(1)
    igni= ignition_parameter.query.get(1)
    ModDevices = mod_device.query.filter(mod_device.mod_addresses.any(read_mod_registers.address >= 0)).all()
    try:
        client = mqtt.Client(client_id = "Proj_%s" %(random.getrandbits(8)))
        client.on_connect = on_connect
        client.on_message = on_message
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
        ## --- Node Birth ----####
        client.publish("spBv1.0/" + igni.group_id + "/NBIRTH/" + igni.node_name, publishNodeBirth(), 0, False)
        ### --- Device Birth ----####
        for device in ModDevices:
            client.publish("spBv1.0/" + igni.group_id  + "/DBIRTH/" + igni.node_name + "/" + device.dev_name, publishDeviceBirth(device.mod_addresses), 0, False)
           

        while True:
            if MqConn.poll():
                msg = MqConn.recv()
                client.publish("spBv1.0/" + igni.group_id + "/DDATA/" + igni.node_name + "/" + msg[0], genPayload(msg[1]), 0, False)
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
    
    ModDevices = mod_device.query.filter(mod_device.mod_addresses.any(read_mod_registers.address >= 0)).all()

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
                for Device in ModDevices:
                    GetModValues = ModReadDict(Modclient,Device) 
                    #########################
                    ModConn.send(GetModValues)
                    #########################

                time.sleep(1)
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
                
    except Exception as e:
        ModStatChild.send("Modbus Disconnected, Modbus process Stopped")
        ModStatChild.send(str(e))
        print(e)
############------------------------------------------------------################