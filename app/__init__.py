from flask import Flask, redirect, url_for, flash, render_template, jsonify,request
from flask_login import login_required, logout_user,current_user, login_user
from .config import Config
from .oauth import blueprint
from .cli import create_db
from sqlalchemy.orm.exc import NoResultFound
from .models import db, User, OAuth, Token
import requests
from .models import db,User, login_manager,User,UserMixin ,ProfileUser, Building ,ma , UserSchema, Price, Transaction, Parking,BuildingSchema ,TransactionSchema   
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_cors import CORS , cross_origin
from flask_dance.contrib.facebook import make_facebook_blueprint
from flask_migrate import Migrate
from app.form import SignupForm, SigninForm, EditProfileForm
import wtforms_json
import uuid
from sqlalchemy import func
import datetime
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from flask_qrcode import QRcode
import random
wtforms_json.init()

app = Flask(__name__)



cors = CORS(app)
migrate = Migrate(app, db, compare_type = True)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.app = app
db.init_app(app)
qrcode =QRcode(app)
login_manager.init_app(app)

POSTGRES = {
    'user': 'mac',
    'pw': None,
    'db': 'finalcarparking',
    'host': 'localhost',
    'port': 5432,
}


# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:%(pw)s@%(host)s:\%(port)s/%(db)s' % POSTGRES
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://bbcmobyfqhjjpx:7fdd1b70c6ff1897b86ef9c3fa66bb35a89bcf49d30510f5fcf732b504eb3ac0@ec2-54-204-35-248.compute-1.amazonaws.com:5432/dobjk8f2invuc' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = '_5#y2L"F4Q8z\n\xec]/'

scheduler = APScheduler()

scheduler.init_app(app)

scheduler.start()



@app.route("/logout", methods = ['POST', 'GET'])
@login_required
def logout():
    if request.method =="POST":
        cur_token = Token.query.filter_by(user_id = current_user.id).first()
        print(cur_token)
        db.session.delete(cur_token)
        db.session.commit()
        print('currrrrr', cur_token.uuid)
        logout_user()
        flash("You have logged out")
    return redirect(url_for("index"))


@app.route("/")
def index():
    print('alolalalala')
    # cur_building = Building.query.filter_by(id = 1). first()
    # cur_user = User.query.filter_by(id = 1).first()
    # print('currrr', cur_user.parkings , cur_building)
    return render_template("home.html")


@app.route("/booking", methods = ['POST', 'GET'])
def booking():
    if request.method == 'POST':
        data = request.get_json()
        print(data['idx'], type(data['idx']))
        cur_parking = Parking.query.filter_by(id = data['idx']).first()
        print( cur_parking.book_by, current_user.id)
        if cur_parking.status =='Booked':
            # if current_user.id == cur_parking.book_by:
            cur_parking.status = 'Available'
            cur_parking.status_color = 'green'
            cur_parking.owneruser = None
            cur_parking.time_booking = None
            cur_parking.in_use_status = 'not_use'
            db.session.commit()
        else:
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur_parking.status = "Booked"
            cur_parking.status_color = "red"
            cur_parking.book_by = current_user.id
            cur_parking.time_booking = time
            cur_parking.in_use_status = 'booking'
            db.session.commit()
        return jsonify ("You are booking this lot")
@app.route("/parking/checkin/<idx>", methods = ['POST', 'GET'])
@login_required
def checkin(idx):
    data = request.get_json()
    cur_parking = Parking.query.filter_by(id = data['idx']).first()
    cur_building= cur_parking.building_id
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur_parking.in_use_status = 'using'
    new_transaction = Transaction(user = current_user.id, building = cur_building,
            parking = cur_parking.id , time_check_in = time , price = cur_parking.price,
    ticket_qrcode = qrcode((str(current_user.id)+str(cur_building) + str(random.randint(1,101)) + str(cur_parking.id)), icon_img='https://www.agner.io/icon.jpg', fill_color='blue' ))
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify("Success Checkin!")
@app.route("/parking/<park_id>/checkout/<trans_id>", methods = ['POST', 'GET'])
@login_required
def checkout(park_id , trans_id):
    data = request.get_json()
    cur_parking = Parking.query.filter_by(id = data['park_id']).first()
    cur_transaction = Transaction.query.filter_by(id = data['trans_id']).first()
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur_transaction.time_check_out = time
    cur_transaction.status = 'success'
    db.session.commit()
    time_lot = int((cur_transaction.time_check_out - cur_transaction.time_check_in).total_seconds())/60
    cur_transaction.totalbill = int(time_lot * cur_transaction.price/60)
    if cur_transaction.totalbill == 0:
        cur_transaction.totalbill = cur_transaction.price
    cur_transaction.time_lot = str(time_lot)
    cur_parking.status = 'Available'
    cur_parking.in_use_status = 'not_use'
    cur_parking.status_color = 'green'
    cur_parking.time_booking = None
    cur_parking.book_by = None
    print('########################', time , cur_transaction.time_check_in , cur_transaction.time_lot)
    db.session.commit()

    return jsonify("Success Checkout!")

@app.route("/parking/order", methods = ['POST', 'GET'])
@login_required
def list_order():
    if request.method == "GET": 
        trans_schema = TransactionSchema()
        print(current_user)
        out_put = trans_schema.dump(current_user).data
        return jsonify({'data': out_put} ) 


    


@app.route("/addparking", methods = ['POST', 'GET'])
@login_required
def addParking():
    if request.method == 'POST':
        data = request.get_json()
        if data['nums'] == 0:
            new_parking = Parking(name =data['name'], building_id = data['building_id'], status ='Available', price =data['price'])
            db.session.add(new_parking)
            db.session.commit()
            return jsonify('Success adding')
        else:
            for i in range (0,data['nums']):
                new_parking = Parking(name =data['name'], building_id = data['building_id'], status ='Available', price =data['price'])
                db.session.add(new_parking)
                db.session.commit()
    return jsonify('Success adding!')


        
@app.route("/parking/edit/<idx>", methods = ['POST', 'GET'])
def edit_parking(idx):
    data = request.get_json()
    cur_parking = Parking.query.filter_by(id = idx).first()
    cur_parking.name = data['parkingname']
    cur_parking.price = data['parkingprice']
    db.session.commit()
    return jsonify("Updated...")

@app.route("/deleteparking",methods = ['POST','GET'])
def deleteParking():
    data = request.get_json()
    delete_park = Parking.query.filter_by(id = int(data['parking_id'])).first()
    db.session.delete(delete_park)
    db.session.commit()
    return jsonify('hello deleteddddd')


@app.route("/user/signup", methods = ['POST', ' GET'])
def signup():
    if request.method == 'POST':
        form = SignupForm.from_json(request.json)
        # data = request.get_json()
        print('suifhawduihasiudhasiud', form)
        if form.validate():
            new_user = User(name = form.sname.data, email =form.semail.data)
            new_user.set_password(form.spassword.data)
            db.session.add(new_user)
            db.session.commit()
            new_add_user = User.query.filter_by(name = form.sname.data).first()
            new_profile = ProfileUser(user_id = new_add_user.id, address = form.saddress.data)
            db.session.add(new_profile)
            db.session.commit()
            return jsonify("success!")
            # return redirect("http://localhost:3000/sign-in")
        else:
            print('checkcekcekcekeckcekce!!!!!!')
            return jsonify(form.errors)
        return jsonify("success!")
@app.route("/facebooklogin")
def log():
    return render_template("home.html")

@app.route("/user/signin", methods =['POST', 'GET'])
def signin():
    if request.method == 'POST':
        form = SigninForm.from_json(request.json)
        if form.validate():
            log_user = User.query.filter_by(name=form.username.data).first()
            if log_user is None:
                error = "Wrong username"
                form.username.errors.append(error)
                return jsonify({'error': "wrong username"})
            elif  not log_user.check_password(form.password.data):
                error = "Wrong password"
                form.password.errors.append(error)
                print('efhuiqehiuwefhwiuefhwieufwueifweiufhweiufhwiuefweuhif')
                return jsonify({'error': "wrong password"})
            else:
                login_user(log_user)
                token_query = Token.query.filter_by(user_id=current_user.id)
                try:
                    token = token_query.one()
                except NoResultFound:  
                    token = Token(user_id=current_user.id, uuid=str(uuid.uuid4().hex))    
                    db.session.add(token)
                    db.session.commit()
                return jsonify({ 'status': 'ok' , 'token': token.uuid})
        else:
            return jsonify("form.errors")
        return 'login Please'
        



@app.route("/user/data", methods = ['POST', 'GET'])
@login_required
def data_user():
    if request.method == "GET": 
        user_schema = UserSchema() 
        cur_buidling = Building.query.filter_by(user = current_user.id). first()
        cur_time = datetime.now()
        total_trans = Transaction.query.filter(Transaction.building == cur_buidling.id, Transaction.time_check_out < (cur_time - timedelta(days = 1)) ).with_entities( Transaction.building, func.sum(Transaction.totalbill)).group_by(Transaction.building).all()
        out_put = user_schema.dump(current_user).data
        return jsonify({'data': out_put, 'total': total_trans} ) 
    else:
        form = EditProfileForm.from_json(request.json)
        data = request.get_json()
        print('datataatatfiatatatat', data)
        if form.validate():
            cur_profile = ProfileUser.query.filter_by(user_id = current_user.id).first()
            cur_profile.first_name = form.firstname.data
            cur_profile.last_name = form.lastname.data
            current_user.email = data['email']
            cur_profile.address = data['address']
            cur_profile.phone = data['phone']
            cur_profile.avatar_url = data['avatar']
            db.session.commit()
            return jsonify("success!")
        else:
            return jsonify(form.errors)
        return jsonify({'data': data})


    # datastore = json.loads(data)


@app.route("/addbuilding", methods = ['POST', 'GET'])
def addbuilding():
    if request.method == 'POST':
        data = request.get_json()
        print('datattatatatat', data['buildingname'], current_user)
        newbuilding = Building(user = current_user.id, buildingname = data['buildingname'], buildingcontact = data['buildingcontact'], location = data['location'], description = data['description'], totalparkingslot = data['totalparkingslot'])
        db.session.add(newbuilding)
        db.session.commit()
        return jsonify(data)
    else:
        pass
@app.route("/updatebuilding", methods = ['POST', 'GET'])
def updatebuilding():
    if request.method == 'POST':
        data = request.get_json()
        print('datattatatatat', data['buildingname'], current_user)
        cur_building = Building.query.filter_by(user = current_user.id).first()
        cur_building.buildingname = data['buildingname']
        cur_building.buildingcontact = data['buildingcontact']
        cur_building.location = data['location']
        cur_building.description = data['description']
        cur_building.totalparkingslot = data['totalparkingslot']
        cur_building.image_url = data['image_url']
        db.session.commit()
        return jsonify(data)
    else:
        pass



@app.route("/data/building", methods = ['POST', 'GET'])
def data_user_building():
    if request.method == "GET" :
        building_available = Building.query.all()
        total_lot = Parking.query.with_entities(Parking.building_id, func.count(Parking.status)).group_by(Parking.building_id).all()
        avaivale_lot = Parking.query.with_entities(Parking.building_id, func.count(Parking.status)).group_by(Parking.building_id).filter_by(status = 'Available').all()
        print (total_lot, avaivale_lot)
        building_schema = BuildingSchema(many = True) 
        out_put = building_schema.dump(building_available).data
        return jsonify({'data': out_put, 'total_lot': total_lot , 'avaivale_lot': avaivale_lot } ) 
    else:
        data = request.get_json() 
        print('datattatatatat', data)
    # datastore = json.loads(data)
@app.route("/data/building/<idx>", methods = ['POST', 'GET'])
def data_user_building_parking(idx):
    if request.method == "GET" : 
        current_building = Building.query.filter_by(id = idx).first()
        building_schema = BuildingSchema() 
        out_put = building_schema.dump(current_building).data
        return jsonify({'data': out_put} ) 
  
@app.route("/manage/building", methods = ['POST', 'GET'])
def manage_building():
    if request.method == 'GET':
        current_building = Building.query.filter_by(user = current_user.id).first()
        building_schema = BuildingSchema() 
        out_put = building_schema.dump(current_building).data
        return jsonify({'data': out_put } ) 
    else:
        return jsonify('helo')


@scheduler.task('interval', id='do_job_1', minutes= 5, misfire_grace_time=900)
def job1():
    with db.app.app_context():
        check_parking = Parking.query.filter_by( in_use_status = 'booking' ).all()
        # # cur_parking = Parking.query.filter_by(id =37).first()
        time_now = datetime.now()
        print('is running?')
        # time_check =  time_now - cur_parking.time_booking
        # print('timechecking', time_check)
        for cur_parking in check_parking:
            if ((time_now - cur_parking.time_booking).total_seconds() > 900):
                print(((time_now - cur_parking.time_booking)))
                cur_parking.status = 'Available'
                cur_parking.status_color = 'green'
                cur_parking.owneruser = None
                cur_parking.time_booking = None
                cur_parking.in_use_status = 'not_use'
                db.session.commit()


                          

