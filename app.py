# from models import User
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from multiprocessing import Process, Pipe, Value, Manager

import logging 
logger = logging.getLogger(__name__)
logging.basicConfig(filename='exceptionnss.log',format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/database.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MqStatParent, MqStatChild = Pipe()
MqDataParent, MqDataChild = Pipe()
ModStatParent, ModStatChild = Pipe()
def init_db():
    db.init_app(app)
    db.app = app
    db.create_all()