from app import db

class User(db.Model):
    email = db.Column(db.String(80), primary_key=True, unique=True)
    password = db.Column(db.String(80))
    def __init__(self, email, password):
        self.email = email
        self.password = password
    def __repr__(self):
        return '<User %r>' % self.email
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return str(self.email)

class modbus_address(db.Model):
    __tablename__ = 'modbus_address'
    
    name = db.Column(db.String(80) , primary_key=True, unique= True)
    start_address = db.Column(db.String(80))
    qty = db.Column(db.String(80))
    function_code = db.Column(db.String(80))
    # publish_topic = db.Column(db.String(80))
    # def __init__(self, start_address, qty):
    #     self.start_address = start_address
    #     self.qty = qty

class ignition_parameter(db.Model):
    __tablename__ = "ignition_parameter"
    id = db.Column(db.Integer, primary_key = True)
    group_id = db.Column(db.String(80))
    node_name = db.Column(db.String(80))
    def __init__(self, group_id, node_name):
        self.group_id = group_id
        self.node_name = node_name
        
class mod_device(db.Model):
    __tablename__ = "mod_device"
    id = db.Column(db.Integer, primary_key = True)
    dev_name = db.Column(db.String(80) ,unique= True)
    mod_addresses = db.relationship('read_mod_registers', backref='device',lazy=True)
    def __init__(self, dev_name):
        self.dev_name = dev_name

class mqtt_parameters(db.Model):
    __tablename__ = 'mqtt_parameters'
    id = db.Column(db.Integer, primary_key = True)
    mqtt_ip = db.Column(db.String(80) ,unique= True)
    mqtt_port = db.Column(db.Integer)
    mqtt_user_name = db.Column(db.String(80))
    mqtt_password = db.Column(db.String(80))
    mqtt_access_token = db.Column(db.String(80))
    def __init__(self, mqtt_ip, mqtt_port,mqtt_user_name,mqtt_password,mqtt_access_token):
        self.mqtt_ip=mqtt_ip
        self.mqtt_port=mqtt_port
        self.mqtt_user_name=mqtt_user_name
        self.mqtt_password=mqtt_password
        self.mqtt_access_token=mqtt_access_token


class modbus_parameters(db.Model):
    __tablename__ = 'modbus_parameters'
    id = db.Column(db.Integer, primary_key = True)
    modbus_ip = db.Column(db.String(80),unique= True)
    modbus_port = db.Column(db.Integer)
    def __init__(self,modbus_ip,modbus_port):
        self.modbus_ip=modbus_ip
        self.modbus_port=modbus_port
    


class read_mod_registers(db.Model):
    __tablename__ = 'read_mod_registers'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80))
    address = db.Column(db.Integer)
    qty = db.Column(db.Integer)
    unit = db.Column(db.Integer)
    datatype = db.Column(db.String(80))
    byteorder = db.Column(db.String(80))
    wordorder = db.Column(db.String(80))
    pp = db.Column(db.Text)
    device_id = db.Column(db.Integer, db.ForeignKey('mod_device.id'))
    __table_args__ = (db.UniqueConstraint('name','address','device_id'),)
    def __init__(self,name, address, qty,unit,datatype,byteorder,wordorder, pp,device_id):
        self.name=name
        self.address = address
        self.qty = qty
        self.unit = unit
        self.datatype = datatype
        self.byteorder = byteorder
        self.wordorder = wordorder
        self.pp = pp
        self.device_id= device_id



class all_status(db.Model):
    __tablename__ = 'all_status'
    id = db.Column(db.Integer, primary_key = True)
    mqtt_status = db.Column(db.String(80))
    modbus_status= db.Column(db.String(80))
    last_sent_data = db.Column(db.String(80))
    last_sent_data_ts = db.Column(db.String(80))