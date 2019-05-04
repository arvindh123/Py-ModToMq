from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField,TextAreaField, SubmitField, RadioField,SelectField, BooleanField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import pub_mqtt_topics
from app import db, init_db


def pub_topics_choices():
    topics = pub_mqtt_topics.query.with_entities(pub_mqtt_topics.id,pub_mqtt_topics.topic).all()
#     ret_list = list()
#     for topic in topics:
#         ret_list.append(("%s" %topic.id, topic.topic))
    # return ret_list
    return topics

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
    submit = SubmitField("save")

class PubMqttTopicsForm(FlaskForm):
    topic = StringField('Topic')
    qos = SelectField('Qos' ,choices = [('0', '0'),('1', '1'), ('2','2')])
    retain = BooleanField('Retain')


class ReadModForm(FlaskForm):
    name =  StringField('Name')
    address =  IntegerField('Register')
    qty = IntegerField('Qty')
    unit = IntegerField('Unit')
    pp = TextAreaField('Post Porcess')
    pub_topic_id = QuerySelectField(query_factory=pub_topics_choices,get_label="topic", allow_blank=False, get_pk=lambda a: a.id)
    # pub_topic_id = SelectField('Publish Topic' ,choices = pub_topics_choices())
class SubMqttTopicsForm(FlaskForm):
    pass


class WriteModForm(FlaskForm):
    pass



