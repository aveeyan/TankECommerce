import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from models import db, User, Tank, TankCategory, Nation, CartItem, Order, OrderItem
from config import Config
from datetime import datetime
import json
import stripe

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models_tanks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['jpg', 'png', 'jpeg', 'gif']

@app.before_request
def create_tables():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Categories with image paths
    categories = [
        {'name': 'Light', 'image_path': 'images/weight_light.png'},
        {'name': 'Medium', 'image_path': 'images/weight_medium.png'},
        {'name': 'Heavy', 'image_path': 'images/weight_heavy.png'},
        {'name': 'Tank Destroyer', 'image_path': 'images/weight_td.png'}
    ]
    
    for cat_data in categories:
        cat = TankCategory.query.filter_by(name=cat_data['name']).first()
        if not cat:
            cat = TankCategory(name=cat_data['name'], image_path=cat_data['image_path'])
            db.session.add(cat)
        else:
            # Update image path for existing categories
            cat.image_path = cat_data['image_path']
    
    # Nations with flag image paths
    nations = [
        {'name': 'Germany', 'flag_image_path': 'images/flag_germany.png'},
        {'name': 'USA', 'flag_image_path': 'images/flag_us.png'},
        {'name': 'Soviet Union', 'flag_image_path': 'images/flag_soviet.png'},
        {'name': 'Britain', 'flag_image_path': 'images/flag_uk.png'},
        {'name': 'France', 'flag_image_path': 'images/flag_france.png'},
        {'name': 'Japan', 'flag_image_path': 'images/flag_japan.png'}
    ]
    
    for nation_data in nations:
        nation = Nation.query.filter_by(name=nation_data['name']).first()
        if not nation:
            nation = Nation(name=nation_data['name'], flag_image_path=nation_data['flag_image_path'])
            db.session.add(nation)
        else:
            # Update flag image path for existing nations
            nation.flag_image_path = nation_data['flag_image_path']
    
    db.session.commit()

@app.route('/')
def index():
    categories = TankCategory.query.all()
    nations = Nation.query.all()
    
    # Start with all tanks query
    tanks_query = Tank.query
    
    # Get filter parameters
    category_ids = request.args.getlist('category')
    nation_id = request.args.get('nation')
    search = request.args.get('search')
    
    # Apply category filter - modified to handle multiple selections
    if category_ids:
        # Convert string IDs to integers
        category_ids = [int(cat_id) for cat_id in category_ids if cat_id.isdigit()]
        if category_ids:
            # Filter tanks that belong to ANY of the selected categories (OR logic)
            tanks_query = tanks_query.filter(Tank.category_id.in_(category_ids))
    
    # Apply nation filter
    if nation_id:
        tanks_query = tanks_query.filter_by(nation_id=nation_id)
    
    # Apply search filter
    if search:
        tanks_query = tanks_query.filter(Tank.name.contains(search))
    
    # Final ordering and execution
    tanks = tanks_query.order_by(Tank.created_at.desc()).all()
    
    return render_template('index.html', tanks=tanks, categories=categories, nations=nations, now=datetime.now())

# Admin routes
@app.route('/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for('index'))
    tanks = Tank.query.all()
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/dashboard.html', tanks=tanks, orders=orders, now=datetime.now())

# Ensure admin route is protected
@app.route('/admin/add_tank', methods=['GET', 'POST'])
@login_required
def add_tank():
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for('index'))
    categories = TankCategory.query.all()
    nations = Nation.query.all()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category_id = int(request.form['category_id'])
        nation_id = int(request.form['nation_id'])
        scale = request.form['scale']
        image_path = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(app.root_path, filepath))
                image_path = filepath
        tank = Tank(name=name, description=description, price=price, stock=stock,
                    category_id=category_id, nation_id=nation_id, scale=scale, image_path=image_path)
        db.session.add(tank)
        db.session.commit()
        flash(f"Tank {name} added successfully!")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_tank.html', categories=categories, nations=nations, now=datetime.now())


@app.route('/tank/<int:id>')
def tank_detail(id):
    tank = Tank.query.get_or_404(id)
    return render_template('product.html', tank=tank, now=datetime.now())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        flash('Login successful!')
        return redirect(next_page)
    return render_template('login.html', now=datetime.now())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', now=datetime.now())

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.tank.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total, now=datetime.now())

@app.route('/add_to_cart/<int:tank_id>', methods=['POST'])
@login_required
def add_to_cart(tank_id):
    tank = Tank.query.get_or_404(tank_id)
    quantity = int(request.form.get('quantity', 1))
    cart_item = CartItem.query.filter_by(user_id=current_user.id, tank_id=tank_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=current_user.id, tank_id=tank_id, quantity=quantity)
        db.session.add(cart_item)
    db.session.commit()
    flash(f"{tank.name} added to your cart!")
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash("You cannot remove this item.")
        return redirect(url_for('cart'))
    db.session.delete(cart_item)
    db.session.commit()
    flash("Item removed from cart.")
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty!")
        return redirect(url_for('cart'))
    total = sum(item.tank.price * item.quantity for item in cart_items)
    if request.method == 'POST':
        order = Order(user_id=current_user.id, total_amount=total, status='pending')
        db.session.add(order)
        db.session.flush()
        for item in cart_items:
            order_item = OrderItem(order_id=order.id, tank_id=item.tank.id, quantity=item.quantity, price=item.tank.price)
            db.session.add(order_item)
            item.tank.stock -= item.quantity
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
        payment_data = {'amount': total, 'order_id': order.id}
        session['payment_data'] = payment_data
        return redirect(url_for('payment_process'))
    return render_template('checkout.html', cart_items=cart_items, total=total, now=datetime.now())

@app.route('/payment/process')
@login_required
def payment_process():
    payment_data = session.get('payment_data')
    if not payment_data:
        flash("Payment data not found.")
        return redirect(url_for('cart'))
    
    # Pass the Stripe public key to the template
    return render_template(
        'payment_process.html', 
        payment_data=payment_data, 
        stripe_public_key=app.config['STRIPE_PUBLIC_KEY'],
        now=datetime.now()
    )

# New route to create a payment intent
@app.route('/create_payment_intent', methods=['POST'])
@login_required
def create_payment_intent():
    try:
        data = request.json
        order_id = data.get('order_id')
        amount = float(data.get('amount'))
        
        # Verify the order belongs to the current user
        order = Order.query.get(order_id)
        if not order or order.user_id != current_user.id:
            return jsonify({'error': 'Invalid order'}), 400
        
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe expects amounts in cents
            currency='usd',
            metadata={'order_id': order_id},
            description=f'Order #{order_id} from TankECommerce'
        )
        
        return jsonify({
            'clientSecret': intent.client_secret
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/payment/success')
@login_required
def payment_success():
    payment_data = session.get('payment_data')
    if not payment_data:
        flash("Payment data not found.")
        return redirect(url_for('cart'))
    
    order = Order.query.get(payment_data['order_id'])
    if order and order.user_id == current_user.id:
        order.status = 'paid'
        order.payment_id = f"STRIPE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db.session.commit()
        session.pop('payment_data', None)
        flash("Payment successful! Thank you for your purchase.")
        return render_template('payment_success.html', order=order, now=datetime.now())
    
    flash("Order not found.")
    return redirect(url_for('index'))

@app.route('/payment/cancel')
@login_required
def payment_cancel():
    payment_data = session.get('payment_data')
    if payment_data:
        order = Order.query.get(payment_data['order_id'])
        if order and order.user_id == current_user.id:
            for item in order.items:
                item.tank.stock += item.quantity
                db.session.delete(item)
            db.session.delete(order)
            db.session.commit()
        session.pop('payment_data', None)
    flash("Payment canceled.")
    return redirect(url_for('cart'))

# Add route to handle editing tanks
@app.route('/admin/edit_tank/<int:tank_id>', methods=['GET', 'POST'])
@login_required
def edit_tank(tank_id):
    if not current_user.is_admin:  # Ensure only admins can access
        flash("Access denied.")
        return redirect(url_for('index'))

    tank = Tank.query.get_or_404(tank_id)
    categories = TankCategory.query.all()
    nations = Nation.query.all()

    if request.method == 'POST':
        # Update tank details
        tank.name = request.form['name']
        tank.description = request.form['description']
        tank.price = float(request.form['price'])
        tank.stock = int(request.form['stock'])
        tank.category_id = int(request.form['category_id'])
        tank.nation_id = int(request.form['nation_id'])
        tank.scale = request.form['scale']

        # Handle image file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(app.root_path, filepath))
                tank.image_path = filepath

        db.session.commit()
        flash("Tank details updated successfully.")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_tank.html', tank=tank, categories=categories, nations=nations, now=datetime.now())

@app.route('/admin/delete_tank/<int:tank_id>', methods=['GET', 'POST'])
@login_required
def delete_tank(tank_id):
    if not current_user.is_admin:  # Ensure only admins can access
        flash("Access denied.")
        return redirect(url_for('index'))
    
    tank = Tank.query.get_or_404(tank_id)
    
    if request.method == 'POST':
        # Check for the confirmation
        if request.form.get('confirm') == 'yes':
            # Delete any cart items containing this tank
            CartItem.query.filter_by(tank_id=tank_id).delete()
            
            # Handle order items (optional approach - you may want to keep records)
            # This approach marks the order items but keeps the historical record
            order_items = OrderItem.query.filter_by(tank_id=tank_id).all()
            for item in order_items:
                item.tank_id = None
                
            # Delete the tank
            db.session.delete(tank)
            db.session.commit()
            flash(f"Tank '{tank.name}' has been deleted.")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Tank deletion canceled.")
            return redirect(url_for('admin_dashboard'))
            
    return render_template('admin/delete_tank.html', tank=tank, now=datetime.now())

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config.get('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata']['order_id']
        
        # Update order status
        order = Order.query.get(order_id)
        if order:
            order.status = 'paid'
            order.payment_id = payment_intent['id']
            db.session.commit()
    
    return jsonify(success=True)

@app.route('/create_checkout_session', methods=['POST'])
@login_required
def create_checkout_session():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({'error': 'Your cart is empty'}), 400
    
    # Create order
    total = sum(item.tank.price * item.quantity for item in cart_items)
    order = Order(user_id=current_user.id, total_amount=total, status='pending')
    db.session.add(order)
    db.session.flush()
    
    # Add order items
    line_items = []
    for item in cart_items:
        order_item = OrderItem(order_id=order.id, tank_id=item.tank.id, quantity=item.quantity, price=item.tank.price)
        db.session.add(order_item)
        item.tank.stock -= item.quantity
        
        # Create line item for Stripe
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item.tank.name,
                    'description': item.tank.description[:100],  # Stripe has length limits
                },
                'unit_amount': int(item.tank.price * 100),  # Stripe uses cents
            },
            'quantity': item.quantity,
        })
    
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    
    db.session.commit()
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('payment_success', _external=True) + f'?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}',
            cancel_url=url_for('payment_cancel', _external=True) + f'?order_id={order.id}',
            metadata={
                'order_id': order.id
            }
        )
        
        # Store session ID in flask session
        session['stripe_checkout_id'] = checkout_session.id
        session['payment_data'] = {'order_id': order.id, 'amount': total}
        
        return jsonify({'id': checkout_session.id, 'url': checkout_session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/order_history')
@login_required
def order_history():
    # Get all orders for the current user, ordered by most recent first
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('order_history.html', orders=orders, now=datetime.now())

if __name__ == '__main__':
    app.run(debug=True)