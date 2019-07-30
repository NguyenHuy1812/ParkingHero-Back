from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import types
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.fields.html5 import DateTimeLocalField
import datetime
from sqlalchemy import desc

db = SQLAlchemy()
ma = Marshmallow()

class ProfileUser(db.Model):
    __tablename__="profile"
    id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    avatar_url = db.Column(db.String, default = 'https://pbs.twimg.com/profile_images/787106179482869760/CwwG2e2M_400x400.jpg')
    phone = db.Column(db.Integer)
    address = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())


class Price(db.Model):
    __tablename__='price'
    id = db.Column(db.Integer, primary_key= True)
    pricetype = db.Column(db.String)
    price = db.Column(db.Integer)
class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key= True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    building = db.Column(db.Integer, db.ForeignKey('building.id'))
    parking =db.Column(db.Integer, db.ForeignKey('parking.id'))
    price = db.Column(db.Integer)
    status = db.Column(db.String, default = 'Checkin')
    ticket_qrcode = db.Column(db.String)
    time_check_in = db.Column(
        db.DateTime , default = None)
    time_check_out = db.Column(
        db.DateTime, default = None)

    time_lot = db.Column(db.String)
    totalbill = db.Column(db.Integer)

class Parking(db.Model):
    __tablename__="parking"
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String, default = 'No.')
    building_id = db.Column(db.Integer, db.ForeignKey('building.id'))
    transaction = db.relationship('Transaction', backref = 'parkingtrans' ,order_by = 'desc(Transaction.id)')
    status = db.Column(db.String, default = 'Available')
    status_color = db.Column(db.String, default = 'green')
    book_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    time_booking = db.Column(db.DateTime)
    price = db.Column(db.Integer)
    in_use_status = db.Column(db.String, default = 'not_use')
    
class Building(db.Model):
    __tablename__="building"
    id = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    buildingname = db.Column(db.String, unique = True)
    buildingcontact = db.Column(db.String)
    image_url = db.Column(db.String , default = 'http://images.adsttc.com/media/images/51d4/84a8/b3fc/4bea/e100/01d6/medium_jpg/Portada.jpg?1372882078')
    location = db.Column(db.String)
    description = db.Column(db.String)
    totalparkingslot = db.Column(db.Integer)
    parkings = db.relationship('Parking', backref = 'parkinglot', order_by = 'Parking.id')
    totaltransaction = db.relationship('Transaction', backref= 'totaltrans', order_by ='desc(Transaction.id)')
    street_location = db.Column(db.String)

class User(UserMixin, db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(255) , unique= True)
    password = db.Column(db.String(255))
    profiles = db.relationship('ProfileUser', backref= 'owneruser')
    building = db.relationship('Building', backref= 'owneruser')
    transactions = db.relationship('Transaction', backref='owneruser', order_by = 'desc(Transaction.id)')
    parkings = db.relationship('Parking', backref = 'owneruser' )

    def __repr__(self):
        return "{}".format(self.name)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref = 'token_user')



class UserSchema(ma.ModelSchema):

    class Meta:
        model = User
        ordered = True
    building = ma.Nested('BuildingSchema', many = True, ordered= True)
    profiles = ma.Nested('ProfileSchema', many=True)
    transactions = ma.Nested('TransactionSchema', many =True,ordered= True)
    parkings = ma.Nested('ParkingSchema', many = True , ordered = True)

class BuildingSchema(ma.ModelSchema):
    
    class Meta:
        model = Building
        ordered = True
    parkings = ma.Nested('ParkingSchema', many = True,ordered= True)
    totaltransaction = ma.Nested('TransactionSchema', many =True,ordered= True)
class ParkingSchema(ma.ModelSchema):
    
    class Meta:
        ordered = True
        model = Parking
    transaction = ma.Nested('TransactionSchema', many =True,ordered= True)
    owneruser = ma.Nested('UserSchema', exclude=('building', 'parkings','transaction'))
    parkinglot = ma.Nested('BuildingSchema', exclude = ('parkings' , 'transaction'))
class TransactionSchema(ma.ModelSchema):
    class Meta:
        model = Transaction
        ordered = True

class ProfileSchema(ma.ModelSchema):
    class Meta:
        model = ProfileUser
        ordered = True

# setup login manager
login_manager = LoginManager()
login_manager.login_view = "facebook.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.request_loader
def load_user_from_request(request):
    # Login Using our Custom Header
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        if token:
            return token.user

    return None
