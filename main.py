from app import app,db,MqStatParent,ModStatParent,MqDataParent,MqStatChild , MqDataChild, ModStatChild,logger

from threading import Lock
from flask import Flask ,request , render_template, redirect
from models import User, modbus_address,mqtt_parameters,modbus_parameters, all_status,\
    pub_mqtt_topics, read_mod_registers, sub_mqtt_topics, write_mod_registers
from forms import SignupForm, MqttEditForm, ModbusEditForm, PubMqttTopicsForm, ReadModForm, pub_topics_choices
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from multiprocessing import Process, Pipe, Value, Manager
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
login_manager = LoginManager()
login_manager.init_app(app)
from process import on_connect,ModReadJson,ModWriteJson,is_connected,validate_ip,Mqtt_process,Mod_ReadWrite



async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

Mqtt_Stat = Value('d', 0)
Mqtt_bacProc = None
Mod_bacProc = None

def init_db():
    db.init_app(app)
    db.app = app
    db.create_all()



def background_thread(MqStatParent,MqDataParent,ModStatParent):
    status_data = all_status.query.get(1)
    while True:  
        if MqStatParent.poll():
            msg = MqStatParent.recv()
            socketio.emit('Status', {'data': msg, }, namespace='/Gate')
            if hasattr(status_data, "mqtt_status"):
                status_data.mqtt_status = msg
                db.session.commit()
        if ModStatParent.poll():
            msg = ModStatParent.recv()
            socketio.emit('Status', {'data': msg, }, namespace='/Gate')
            if hasattr(status_data, "modbus_status"):
                status_data.modbus_status = msg
                db.session.commit()
        if MqDataParent.poll():
            msg = MqDataParent.recv()
            socketio.emit('Data_Sent', {'data': "sent at- " + str(datetime.now()) + "  | Topic- " + msg[0].topic + "  | Payload- " +  msg[1]}, namespace='/Gate')
            if hasattr(status_data, "last_sent_data") and hasattr(status_data, "last_sent_data_ts") :
                status_data.last_sent_data = msg[0].topic + msg[1]
                status_data.last_sent_data_ts = str(datetime.now())
                db.session.commit()

@app.route('/')
def index():
    # print(current_user)
    form = SignupForm()
    mqtt_view = mqtt_parameters.query.get(1)
    modbus_view = modbus_parameters.query.get(1)
    last_status = all_status.query.get(1)
    return render_template('index.html', form = form, mqtt_view=mqtt_view,modbus_view=modbus_view,last_status=last_status,current_user= current_user)


@app.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('signup.html', form = form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                return "Email address already exists" 
            else:
                newuser = User(form.email.data, form.password.data)
                db.session.add(newuser)
                db.session.commit()
                # login_user(newuser)
                return "User created!!!"        
        else:
             return "Form didn't validate"


@app.route('/login', methods=['GET','POST'])
def login():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user=User.query.filter_by(email=form.email.data).first()
            if user:
                if user.password == form.password.data:
                    login_user(user)
                    return redirect('/')
             
                else:
                    return "Wrong password"            
            else:
                return "user doesn't exist"        
    else:
        return "form not validated"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')



@login_manager.user_loader
def load_user(email):
    return User.query.filter_by(email = email).first()

@app.route('/protected')
@login_required
def protected():
    return "protected area"

# @app.route('/view')
# def view_test():
#     qry = User.query.filter_by(email='arvindh91').first()
#     print(qry)
#     return redirect('/')
    
@app.route('/settings/view')
def settings_view():
    form = SignupForm()
    mqtt_view = mqtt_parameters.query.get(1)
    modbus_view = modbus_parameters.query.get(1)
    return render_template('view.html',form =form, mqtt_view = mqtt_view , modbus_view=modbus_view , current_user= current_user)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def setting_edit():
    form = SignupForm()
    mqtt_view = mqtt_parameters.query.get(1)
    modbus_view = modbus_parameters.query.get(1)
    mqttform = MqttEditForm(obj=mqtt_view)
    modbusform = ModbusEditForm(obj=modbus_view)
    if request.method == 'GET':
        return render_template('edit.html', form=form, mqtt_edit= mqttform, modbus_edit=modbusform)
    elif request.method == 'POST':
        pass      
    else:
        return "Form didn't validate"

@app.route('/mqtt/edit', methods=['GET', 'POST'])
@login_required
def mqtt_edit():
    mqttform = MqttEditForm()
    if request.method == 'POST':
        if mqttform.validate_on_submit():
                mqtt_data = mqtt_parameters.query.get(1)
                if not mqtt_data == None :
                    mqtt_data.mqtt_ip = mqttform.mqtt_ip.data
                    mqtt_data.mqtt_port = mqttform.mqtt_port.data
                    mqtt_data.mqtt_user_name =mqttform.mqtt_user_name.data
                    mqtt_data.mqtt_password = mqttform.mqtt_password.data
                    mqtt_data.mqtt_access_token = mqttform.mqtt_access_token.data
                    db.session.commit()
                elif mqtt_data == None:
                    mqtt_data = mqtt_parameters(mqttform.mqtt_ip.data,mqttform.mqtt_port.data,mqttform.mqtt_user_name.data,mqttform.mqtt_password.data,mqttform.mqtt_access_token.data)
                    db.session.add(mqtt_data)
                    db.session.commit()
                return redirect('/settings/view') 

@app.route('/modbus/edit', methods=['GET', 'POST'])
@login_required
def modbus_edit():
    form = SignupForm()
    modbusform = ModbusEditForm()
    if request.method == 'POST':
        if modbusform.validate_on_submit():
                modbus_data = modbus_parameters.query.get(1)
                if not modbus_data == None :
                    modbus_data.modbus_ip = modbusform.modbus_ip.data
                    modbus_data.modbus_port = modbusform.modbus_port.data
                    db.session.commit()
                elif modbus_data == None:
                    modbus_data = modbus_parameters(modbusform.modbus_ip.data, modbusform.modbus_port.data)
                    db.session.add(modbus_data)
                    db.session.commit()
                return redirect('/settings/view') 

@app.route('/pub/view')
def pub_view():
    form = SignupForm()
    pubview = pub_mqtt_topics.query.all()
    # pubview  = pub_mqtt_topics.query.filter(pub_mqtt_topics.mod_addresses.any(read_mod_registers.address >= 0)).all()
    # for p in pubview:
    #     print(p.mod_addresses)
    return  render_template('pubView.html', pubview=pubview,form=form  )


@app.route('/pub/create', methods=['GET', 'POST'])
def pub_create():
    pubform = PubMqttTopicsForm()
    form = SignupForm()
    if request.method == 'GET':
        return render_template('pubCreate.html', form=form, pubform= pubform )
    elif request.method == 'POST':
        if pubform.validate_on_submit():
            newPubTopic = pub_mqtt_topics(pubform.topic.data, pubform.qos.data, pubform.retain.data)
            db.session.add(newPubTopic)
            db.session.commit()
            return redirect('/pub/view')
        else:
            return "Invalid Data Filed in Form"
    else:
            return "Invalid Form"

@app.route('/pub/delete/<int:id>')
def pub_edit(id):
    pubdel = pub_mqtt_topics.query.get(id)
    if pubdel:
        db.session.delete(pubdel)
        db.session.commit()
    return redirect('/pub/view')
      

@app.route('/modRead/view')
def modRead_view():
    form = SignupForm()
    modreadview = read_mod_registers.query.all()
    return  render_template('modReadView.html', modreadview=modreadview,form=form  )


@app.route('/modRead/create', methods=['GET', 'POST'])
def modRead_create():
    # from forms import ReadModForm
    modReadform = ReadModForm()
    form = SignupForm()
    if request.method == 'GET':
        return render_template('modReadCreate.html', form=form, modReadform= modReadform )
    elif request.method == 'POST':
        if modReadform.validate_on_submit():
            newmodRead = read_mod_registers(modReadform.name.data,modReadform.address.data, modReadform.qty.data, modReadform.unit.data, modReadform.pp.data, modReadform.pub_topic_id.data[0])
            db.session.add(newmodRead)
            db.session.commit()
            return redirect('/modRead/view')
        else:
            return "Invalid Data Filed in Form"
    else:
            return "Invalid Form"


@app.route('/modRead/delete/<int:id>')
def modRead_del(id):
    modReaddel = read_mod_registers.query.get(id)
    if modReaddel:
        db.session.delete(modReaddel)
        db.session.commit()
    return redirect('/modRead/view')   

# @app.route('/start')
def start():
    global thread
    global Mqtt_bacProc
    global Mod_bacProc
    loos = None
    with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(background_thread, MqStatParent, MqDataParent,ModStatParent)
    ModConn, MqConn = Pipe()

    if Mod_bacProc == None:
        Mod_bacProc  = Process(target=Mod_ReadWrite, args=(ModConn,ModStatChild), daemon=True)
        Mod_bacProc.start()
        loos = 1
    elif hasattr(Mod_bacProc, "is_alive"):
        if not Mod_bacProc.is_alive():
            Mod_bacProc  = Process(target=Mod_ReadWrite, args=(ModConn,ModStatChild), daemon=True)
            Mod_bacProc.start()
            loos = 1

    
        
    if Mqtt_bacProc == None :
        Mqtt_bacProc = Process(target=Mqtt_process, args=(Mqtt_Stat,MqConn,MqStatChild,MqDataChild), daemon=True)
        Mqtt_bacProc.start()
        loos = 11
    elif hasattr(Mqtt_bacProc, "is_alive"): 
        if not Mqtt_bacProc.is_alive():
            Mqtt_bacProc = Process(target=Mqtt_process, args=(Mqtt_Stat,MqConn,MqStatChild,MqDataChild), daemon=True)
            Mqtt_bacProc.start()
            loos = 11
    

    
    # Mod_bacProc.join() 
    # Mqtt_bacProc.join()
    if loos == 1:
        socketio.emit('Status', {'data': "Mqtt Process Started", }, namespace='/Gate') 
        loos = None
    elif loos == 11:
        socketio.emit('Status', {'data': "Mqtt & Modbus Process Started ", }, namespace='/Gate')     
    elif loos == None: 
        socketio.emit('Status', {'data': "Mqtt & Modbus already running", }, namespace='/Gate')  
    # return redirect('/')
    return None

# @app.route('/stop')
def stop():
    Mqtt_bacProc.terminate()
    Mod_bacProc.terminate()
    socketio.emit('Status', {'data': "Mqtt & Modbus Process Stopped ", }, namespace='/Gate') 
    # return redirect('/')
    return None

@socketio.on('Mqtt_Cmd', namespace='/Gate')
def Mqtt_Cmd_sock_fn(message):
    if message['data'] == "start":
        start()
        print("Finished processing the - {} -  command recevied in WS" .format(message['data']))
    if message['data'] == "stop":
        stop()
        print("Finished processing the - {} -  command recevied in WS" .format(message['data']))

@socketio.on('Mod_Cmd', namespace='/Gate')
def Mod_Cmd_sock_fn(message):
    msg = message['data']
    if msg == "start":
        ModStatParent.send(1)
    if msg == "stop":
        ModStatParent.send(3)
    # print(message['data'] )


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
# @app.route('/edit/mqtt', methods=['GET', 'POST'])
# def edit_mqtt():
#     post = db.session.query(Post).filter(Post.id==1).first()

#     if request.method == 'POST':
#         title = request.form['title']
#         text = request.form['content']

#         post.title = title
#         post.body = content

#         db.session.commit()

#         return redirect(url_for('post', id=id))
#     else:
#         return render_template('something.html', post=post)


if __name__ == '__main__':
    init_db()   
    app.run(port=5000, host="0.0.0.0", debug=True)