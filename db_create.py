from app import app
from models import db, User, Tank, TankCategory, Nation, CartItem, Order

with app.app_context():
    db.create_all()
    print("✅ All tables created successfully.")
