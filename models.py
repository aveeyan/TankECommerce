from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    # Add relationships
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class Nation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    flag_image_path = db.Column(db.String(255))
    tanks = db.relationship('Tank', backref='nation', lazy='dynamic')
    
    def __repr__(self):
        return f'<Nation {self.name}>'

class TankCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    image_path = db.Column(db.String(255))
    tanks = db.relationship('Tank', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Tank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
    image_path = db.Column(db.String(255))
    scale = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('tank_category.id'))
    nation_id = db.Column(db.Integer, db.ForeignKey('nation.id'))
    cart_items = db.relationship('CartItem', backref='tank', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='tank', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tank {self.name}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tank_id = db.Column(db.Integer, db.ForeignKey('tank.id'))
    quantity = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<CartItem User:{self.user_id} Tank:{self.tank_id}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    payment_id = db.Column(db.String(100))
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')
    
    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    tank_id = db.Column(db.Integer, db.ForeignKey('tank.id'), nullable=True)
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    
    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Tank:{self.tank_id}>'
