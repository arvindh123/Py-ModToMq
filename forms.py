from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField,TextAreaField, SubmitField, RadioField,SelectField, BooleanField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import mod_device
from app import db, init_db


def mod_device_choices():
    mod_devices = mod_device.query.with_entities(mod_device.id,mod_device.dev_name).all()
#     ret_list = list()
#     for topic in topics:
#         ret_list.append(("%s" %topic.id, topic.topic))
    # return ret_list
    return mod_devices

class SignupForm(FlaskForm):
    email = StringField('email',validators=[DataRequired()])
    password = PasswordField('password',validators=[DataRequired()])
    submit = SubmitField("Sign In")

class MqttEditForm(FlaskForm):
    mqtt_ip = StringField('mqtt_ip',validators=[DataRequired()])
    mqtt_port = StringField('mqtt_port',validators=[DataRequired()])
    mqtt_user_name = StringField('mqtt_user_name')
    mqtt_password =PasswordField('mqtt_password')
    mqtt_access_token = StringField('mqtt_access_token')
    submit = SubmitField("save")

class ModbusEditForm(FlaskForm):
    modbus_ip = StringField('modbus_ip',validators=[DataRequired()])
    modbus_port = StringField('modbus_port',validators=[DataRequired()])
    # submit = SubmitField("save")

class ModDevicesForm(FlaskForm):
    dev_name = StringField('Modbus Device Name')

class IgnitionParaForm(FlaskForm):
    group_id = StringField('Group ID',validators=[DataRequired()])
    node_name = StringField('Node Name',validators=[DataRequired()])

class ReadModForm(FlaskForm):
    name =  StringField('Name')
    address =  IntegerField('Register')
    qty = IntegerField('Qty')
    unit = IntegerField('Unit')
    datatype = SelectField('Data Type' ,choices = [("Int8","Int8"),("Int16","Int16"),("Int32","Int32"),("Int64","Int64"),("UInt8","UInt8"),("UInt16","UInt16"),("UInt32","UInt32"),("UInt64","UInt64"),("Float","Float"),("Double","Double"),("Boolean","Boolean"),("String","String"),("Post Process","Post Process")])
    byteorder = SelectField('Byte Order' ,choices = [("Big Endian","Big Endian"),("Little Endian","Little Endian")])
    wordorder = SelectField('Word Order' ,choices = [("Big Endian","Big Endian"),("ittle Endian","ittle Endian")])
    pp = TextAreaField('Post Porcess')
    mod_device_id = QuerySelectField('Modbus Device Name' ,query_factory=mod_device_choices,get_label="dev_name", allow_blank=False, get_pk=lambda a: a.id)
    # pub_topic_id = SelectField('Publish Topic' ,choices = pub_topics_choices())

    