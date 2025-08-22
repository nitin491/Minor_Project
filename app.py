from flask import Flask, render_template, request, redirect, url_for, flash, g, session
import mysql.connector

import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret_key_11'

from flask_mail import Mail, Message


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'imnitin02@gmail.com'
app.config['MAIL_PASSWORD'] = 'dadn wgjs dxpl ltxw'  # Generated using App Passwords
app.config['MAIL_DEFAULT_SENDER'] = 'imnitin02@gmail.com'
mail = Mail(app)
# MySQL connection details
DB_CONFIG = {
'user': 'root',
'password': 'root',  
'host': 'localhost',
'database': 'agri_portal'
}

def get_db():
    if not hasattr(g, 'db_conn'):
        g.db_conn = mysql.connector.connect(**DB_CONFIG)
    g.db_cursor = g.db_conn.cursor(dictionary=True)
    return g.db_conn, g.db_cursor

@app.teardown_appcontext
def close_connection(exception):
    db_conn = getattr(g, 'db_conn', None)
    db_cursor = getattr(g, 'db_cursor', None)
    if db_cursor:
        db_cursor.close()
    if db_conn:
        db_conn.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))
# ______________________________MLDecision Tree -----------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

import joblib

header = ['State_Name', 'District_Name', 'Season', 'Crop'] 

class Question:
    def __init__(self,column,value):
        self.column =column
        self.value=value
    def match(self,example):
        val = example[self.column]
        return val == self.value
    def match2(self,example):
        if example == 'True' or example == 'true' or example == '1':
            return True
        else:
            return False
    def __repr__(self):
        return "Is %s %s %s?" %(
            header[self.column],"==",str(self.value))
            
            
def class_counts(Data):
    counts= {}
    for row in Data:
        label =row[-1]
        if label not in counts:
             counts[label] = 0
        counts[label] += 1
    return counts


class Leaf:
    def __init__(self,Data):
        self.predictions = class_counts(Data)


class Decision_Node:
    def __init__(self,question,true_branch,false_branch):
        self.question=question
        self.true_branch = true_branch
        self.false_branch = false_branch


def print_tree(node,spacing=""):
    if isinstance(node,Leaf):
        print(spacing + "Predict",node.predictions)
        return
    print(spacing+str(node.question))
    print(spacing + "--> True:")
    print_tree(node.true_branch,spacing + " ")

    print(spacing + "--> False:")
    print_tree(node.false_branch,spacing + " ")


def print_leaf(counts):
    total = sum(counts.values())*1.0
    probs = {}
    for lbl in counts.keys():
        probs[lbl] =str(int(counts[lbl]/total * 100)) + "%"
    return probs


def classify(row,node):
    if isinstance(node,Leaf):
        return node.predictions
    if node.question.match(row):
        return classify(row,node.true_branch)
    else:
        return classify(row,node.false_branch)


def new(state, district, season):
    dt_model_final= joblib.load('filetest2.pkl') 

    testing_data = [[state,district,season]]

    for row in testing_data:
        #print("Actual: %s. Predicted: %s" % (row[-1],print_leaf(classify(row,dt_model_final))))
        Predict_dict = (print_leaf(classify(row,dt_model_final))).copy()


    final_crops=[]
    for key, _ in Predict_dict.items() :
        print (key, end=" ")
        final_crops.append(key)
    
    return final_crops

# ------------------------------END------------------------------

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'profile_photos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

# --- Farmer Registration and Login ---
@app.route('/farmer_register', methods=['GET', 'POST'])
def farmer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        mobile = request.form['mobile']
        address = request.form['address']
        db_conn, db_cursor = get_db()
        try:
            db_cursor.execute(
                'INSERT INTO farmers (username, password, email, full_name, mobile, address) VALUES (%s, %s, %s, %s, %s, %s)',
                (username, password, email, full_name, mobile, address)
            )
            db_conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('farmer_login'))
        except mysql.connector.IntegrityError as e:
            if "email" in str(e):
                flash('Email already exists. Please use another one.')
            else:
                flash('Username or email already exists. Please use another one.')
    return render_template('farmer_register.html')

@app.route('/farmer_login', methods=['GET', 'POST'])  
def farmer_login():
    if request.method == 'POST':
        login_input = request.form['username']  
        password = request.form['password']
        db_conn, db_cursor = get_db()
        db_cursor.execute(
            'SELECT * FROM farmers WHERE (username=%s OR email=%s) AND password=%s',
            (login_input, login_input, password)
        )
        user = db_cursor.fetchone()
        if user:
            session['farmer_id'] = user['id']
            session['farmer_username'] = user['username']
            return redirect(url_for('farmer_dashboard'))
        else:
            flash('Incorrect username/email or password.')
    return render_template('farmer_login.html')

# --- Customer Registration and Login ---
@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        address = request.form['address']
        password = request.form['password']   

        db_conn, db_cursor = get_db()
        try:
            db_cursor.execute(
                'INSERT INTO customers (username, password, email, full_name, mobile, address) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (username, password, email, full_name, mobile, address)
            )
            db_conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('customer_login'))
        except mysql.connector.IntegrityError as e:
            if "email" in str(e):
                flash('Email already exists. Please use another one.')
            else:
                flash('Username or email already exists. Please use another one.')
    return render_template('customer_register.html')

@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        login_input = request.form['username'] 
        password = request.form['password']
        db_conn, db_cursor = get_db()
        db_cursor.execute(
            'SELECT * FROM customers WHERE (username=%s OR email=%s) AND password=%s',
            (login_input, login_input, password)
        )
        user = db_cursor.fetchone()
        if user:
            session['customer_id'] = user['id']
            session['customer_username'] = user['username']
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Incorrect username/email or password.')
    return render_template('customer_login.html')

# --- Government Login  ---
@app.route('/government_login', methods=['GET', 'POST'])
def government_login():
    if request.method == 'POST':
        username = request.form['gov_id']
        password = request.form['password']
        db_conn, db_cursor = get_db()
        db_cursor.execute(
            'SELECT * FROM government WHERE username=%s AND password=%s',
            (username, password)
        )
        user = db_cursor.fetchone()
        print("Login attempt:", username, password)
        print("SQL result:", user)
        if user:
            session['gov_id'] = user['id']
            session['gov_username'] = user['username']
            return redirect(url_for('government_dashboard'))
        else:
            flash('Incorrect ID/password.')
    return render_template('government_login.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    # Check if user is logged in
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    return render_template('customer_dashboard.html')

@app.route('/farmer_dashboard')
def farmer_dashboard():
    # Check if user is logged in
    if 'farmer_id' not in session:
         return redirect(url_for('farmer_login'))
    return render_template('farmer_dashboard.html')

@app.route('/government_dashboard')
def government_dashboard():
    # Check if user is logged in and is a government official
    if 'gov_id' not in session:
         return redirect(url_for('government_login'))
    return render_template('government_dashboard.html')

####################### BUY CROPS ##########################

@app.route('/buy_crops')
def buy_crops():
    db, cur = get_db()
    crop_names = ['Rice','Maize','Moong','Bajra','Cotton','Jowar','Ragi','Gram','Wheat',
                  'Soyabean','Arhar','Barley','Jute','Lentil','Urad']
    format_strings = ','.join(['%s'] * len(crop_names))
    cur.execute(f"""SELECT crop_name, SUM(quantity) as total_stock, MIN(price_per_unit) as min_price
                    FROM crops
                    WHERE crop_name IN ({format_strings})
                    GROUP BY crop_name
                    ORDER BY crop_name""", crop_names)
    crops = cur.fetchall()
    return render_template('buy_crops.html', crops=crops)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if "customer_id" not in session:
        return redirect(url_for("login"))
    crop_name = request.form['crop_name']
    quantity = int(request.form['quantity'])
    customer_id = session['customer_id']

    db, cur = get_db()
    cur.execute("SELECT SUM(quantity) as stock FROM crops WHERE crop_name=%s", (crop_name,))
    stock = cur.fetchone()['stock'] or 0
    cart_limit = max(stock // 2, 1)

    if stock == 0:
        flash("Not available", "danger")
    elif quantity > cart_limit:
        flash(f"Not allowed more than {cart_limit} (50% of available stock).", "danger")
    else:
        # Find the cheapest crop_id with stock for this crop_name
        cur.execute("SELECT crop_id FROM crops WHERE crop_name=%s AND quantity>0 ORDER BY price_per_unit ASC LIMIT 1", (crop_name,))
        row = cur.fetchone()
        if not row:
            flash("Not available", "danger")
            return redirect(url_for("buy_crops"))
        crop_id = row['crop_id']
        # Cart logic
        cur.execute("SELECT * FROM cart WHERE customer_id=%s AND crop_id=%s", (customer_id, crop_id))
        cart_entry = cur.fetchone()
        if cart_entry:
            cur.execute("UPDATE cart SET quantity=%s WHERE customer_id=%s AND crop_id=%s", (quantity, customer_id, crop_id))
        else:
            cur.execute("INSERT INTO cart (customer_id, crop_id, quantity) VALUES (%s, %s, %s)", (customer_id, crop_id, quantity))
        db.commit()
        flash("Added to cart", "success")
    return redirect(url_for('buy_crops'))

@app.route("/cart")
def cart():
    if "customer_id" not in session:
        return redirect(url_for("login"))
    customer_id = session['customer_id']
    db, cur = get_db()
    cur.execute("""SELECT cart.cart_id, crops.crop_name, crops.price_per_unit, cart.quantity, crops.quantity as available_now, cart.crop_id
                   FROM cart JOIN crops ON cart.crop_id = crops.crop_id
                   WHERE cart.customer_id=%s""", (customer_id,))
    items = cur.fetchall()
    total = sum(i['quantity']*i['price_per_unit'] for i in items)
    return render_template('cart.html', items=items, total=total)

@app.route("/update_cart", methods=["POST"])
def update_cart():
    cart_id = int(request.form['cart_id'])
    crop_id = int(request.form['crop_id'])
    qty = int(request.form['quantity'])
    db, cur = get_db()
    cur.execute("SELECT quantity FROM crops WHERE crop_id=%s", (crop_id,))
    max_qty = cur.fetchone()['quantity']
    if qty == 0:
        cur.execute("DELETE FROM cart WHERE cart_id=%s", (cart_id,))
    elif qty > max_qty:
        flash(f"Only {max_qty} available", "danger")
        return redirect(url_for("cart"))
    else:
        cur.execute("UPDATE cart SET quantity=%s WHERE cart_id=%s", (qty, cart_id))
    db.commit()
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "customer_id" not in session:
        return redirect(url_for("login"))
    customer_id = session['customer_id']
    db, cur = get_db()
    cur.execute("""SELECT cart.cart_id, crops.crop_name, crops.price_per_unit, cart.quantity, crops.crop_id
                   FROM cart JOIN crops ON cart.crop_id = crops.crop_id
                   WHERE cart.customer_id=%s""", (customer_id,))
    items = cur.fetchall()
    total = sum(i['quantity']*i['price_per_unit'] for i in items)
    if request.method == 'POST':
        payment_id = "demo_payment"
        status = "succeeded"
        cur.execute("INSERT INTO orders (customer_id, total_price, status, payment_id) VALUES (%s, %s, %s, %s)",
                    (customer_id, total, status, payment_id))
        order_id = cur.lastrowid
        for item in items:
            cur.execute("INSERT INTO order_items (order_id, crop_id, quantity, price_at_purchase) VALUES (%s, %s, %s, %s)",
                        (order_id, item['crop_id'], item['quantity'], item['price_per_unit']))
            cur.execute("UPDATE crops SET quantity = quantity - %s WHERE crop_id = %s", (item['quantity'], item['crop_id']))
        cur.execute("DELETE FROM cart WHERE customer_id=%s", (customer_id,))
        db.commit()
    
        # Get email from customers table
        cur.execute('SELECT email FROM customers WHERE id=%s', (customer_id,))
        user = cur.fetchone()
        mailid = user['email']

        try:
            msg = Message(
                subject=f"Order Confirmation #{order_id}",
                recipients=[mailid],  # recipient list
                body=f"Thank you for your order #{order_id}! Amount paid: ₹{total:.2f}. We appreciate your purchase.",
            )
            mail.send(msg)
            flash('Order placed! Receipt sent to your email.', 'success')
        except Exception as e:
            print("Failed to send mail:", e)
            flash('Order placed, but could not send email receipt.', 'warning')
        return redirect(url_for("order_placed"))
    return render_template('checkout.html', items=items, total=total)

@app.route('/order_placed')
def order_placed():
    return render_template('order_success.html')


####################### END ################################
@app.route('/crop_predictor', methods=['GET', 'POST'])
def crop_predictor():
    result = None
    if request.method == 'POST':
        state = request.form['state']
        district = request.form['district']
        season = request.form['season'].strip()
        result = new(state, district, season)
        return render_template('crop_predictor.html', result=result)
    return render_template('crop_predictor.html')
    # return " No data found"


@app.route('/customer_profile')
def customer_profile():
    if 'customer_id' not in session:
        flash('Please log in to view your profile.')
        return redirect(url_for('customer_login'))
    customer_id = session['customer_id']
    db_conn, db_cursor = get_db()
    db_cursor.execute('SELECT * FROM customers WHERE id=%s', (customer_id,))
    user = db_cursor.fetchone()
    if not user:
        flash('Profile not found.')
        return redirect(url_for('customer_dashboard'))
    return render_template('customer_profile.html', user=user)

@app.route('/customer_profile/edit', methods=['GET', 'POST'])
def edit_customer_profile():
    if 'customer_id' not in session:
        flash('Please log in to edit your profile.')
        return redirect(url_for('customer_login'))

    customer_id = session['customer_id']
    db_conn, db_cursor = get_db()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        mobile = request.form['mobile']
        address = request.form['address']
        photo_filename = None

        file = request.files.get('profile_photo')
        if file and allowed_file(file.filename):
            filename = secure_filename(f"cust_{customer_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_filename = filename

        # Server-side validation
        if not full_name.replace(' ', '').isalpha():
            flash("Full Name must contain only letters and spaces.")
            return redirect(url_for('edit_customer_profile'))
        if not mobile.replace(' ', '').replace('+','').isdigit() or len(mobile) < 8:
            flash("Mobile number must be valid.")
            return redirect(url_for('edit_customer_profile'))

        # Update DB
        if photo_filename:
            db_cursor.execute(
                'UPDATE customers SET full_name=%s, email=%s, mobile=%s, address=%s, profile_photo=%s WHERE id=%s',
                (full_name, email, mobile, address, photo_filename, customer_id)
            )
        else:
            db_cursor.execute(
                'UPDATE customers SET full_name=%s, email=%s, mobile=%s, address=%s WHERE id=%s',
                (full_name, email, mobile, address, customer_id)
            )
        db_conn.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('customer_profile'))

    db_cursor.execute('SELECT * FROM customers WHERE id=%s', (customer_id,))
    user = db_cursor.fetchone()
    if not user:
        flash('Profile not found.')
        return redirect(url_for('customer_dashboard'))
    return render_template('edit_customer_profile.html', user=user)

@app.route('/farmer_profile')
def farmer_profile():
    if 'farmer_id' not in session:
        flash('Please log in to view your profile.')
        return redirect(url_for('farmer_login'))
    farmer_id = session['farmer_id']
    db_conn, db_cursor = get_db()
    db_cursor.execute('SELECT * FROM farmers WHERE id=%s', (farmer_id,))
    user = db_cursor.fetchone()
    if not user:
        flash('Profile not found.')
        return redirect(url_for('farmer_dashboard'))
    return render_template('farmer_profile.html', user=user)

@app.route('/farmer_profile/edit', methods=['GET', 'POST'])
def edit_farmer_profile():
    if 'farmer_id' not in session:
        flash('Please log in to edit your profile.')
        return redirect(url_for('farmer_login'))
    farmer_id = session['farmer_id']
    db_conn, db_cursor = get_db()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        mobile = request.form['mobile']
        address = request.form['address']
        photo_filename = None

        # PROFILE PHOTO HANDLING
        file = request.files.get('profile_photo')
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{farmer_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_filename = filename

        # Advanced validation (server-side)
        if not full_name.replace(' ', '').isalpha():
            flash("Full Name must contain only letters and spaces.")
            return redirect(url_for('edit_farmer_profile'))
        if not mobile.replace(' ', '').replace('+','').isdigit() or len(mobile) < 8:
            flash("Mobile number must be valid.")
            return redirect(url_for('edit_farmer_profile'))

        # Update DB
        if photo_filename:
            db_cursor.execute('UPDATE farmers SET full_name=%s, email=%s, mobile=%s, address=%s, profile_photo=%s WHERE id=%s',
                              (full_name, email, mobile, address, photo_filename, farmer_id))
        else:
            db_cursor.execute('UPDATE farmers SET full_name=%s, email=%s, mobile=%s, address=%s WHERE id=%s',
                              (full_name, email, mobile, address, farmer_id))
        db_conn.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('farmer_profile'))

    db_cursor.execute('SELECT * FROM farmers WHERE id=%s', (farmer_id,))
    user = db_cursor.fetchone()
    if not user:
        flash('Profile not found.')
        return redirect(url_for('farmer_dashboard'))
    return render_template('edit_farmer_profile.html', user=user)
##########  START #################
@app.route("/farmer/trade_history")
def farmer_trade_history():
    if "farmer_id" not in session:
        return redirect(url_for('login'))  # Secure route
    farmer_id = session['farmer_id']
    db, cur = get_db()
    cur.execute("""
        SELECT
            c.crop_name,
            oi.quantity,
            oi.price_at_purchase,
            o.placed_at,
            cu.full_name as customer_name
        FROM order_items oi
        JOIN crops c ON c.crop_id = oi.crop_id
        JOIN orders o ON o.order_id = oi.order_id
        JOIN customers cu ON cu.id = o.customer_id
        WHERE c.farmer_id = %s
        ORDER BY o.placed_at DESC
    """, (farmer_id,))
    trade_history = cur.fetchall()
    return render_template("farmer_trade_history.html", trades=trade_history)
##########  END  #################
# Current
@app.route('/farmer_crops')
def farmer_crops():
    farmer_id = session.get('farmer_id')
    if not farmer_id:
        return redirect(url_for('farmer_login'))  # Adjust route

    db_conn, db_cursor = get_db()
    db_cursor.execute("SELECT * FROM crops WHERE farmer_id=%s", (farmer_id,))
    crops = db_cursor.fetchall()
    return render_template('farmer_crops.html', crops=crops)

# Crops CREATE
@app.route('/add_crop', methods=['GET', 'POST'])
def add_crop():
    farmer_id = session.get('farmer_id')
    if not farmer_id:
        return redirect(url_for('farmer_login'))

    if request.method == 'POST':
        name = request.form['crop_name']
        crop_type = request.form['crop_type']
        quantity = request.form['quantity']
        price_per_unit = request.form['price_per_unit']
        sowing = request.form['sowing_date']
        harvesting = request.form['harvest_date']
        desc = request.form['description']
        db_conn, db_cursor = get_db()
        db_cursor.execute("""
            INSERT INTO crops (farmer_id, crop_name, crop_type, quantity, price_per_unit, sowing_date, harvest_date, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (farmer_id, name, crop_type, quantity, price_per_unit, sowing, harvesting, desc))
        db_conn.commit()
        flash('Crop added successfully.')
        return redirect(url_for('farmer_crops'))
    return render_template('add_crop.html')

# Crops UPDATE
@app.route('/edit_crop/<int:crop_id>', methods=['GET', 'POST'])
def edit_crop(crop_id):
    farmer_id = session.get('farmer_id')
    if not farmer_id:
        return redirect(url_for('farmer_login'))

    db_conn, db_cursor = get_db()
    db_cursor.execute("SELECT * FROM crops WHERE crop_id=%s AND farmer_id=%s", (crop_id, farmer_id))
    crop = db_cursor.fetchone()
    if not crop:
        flash('Crop not found.')
        return redirect(url_for('farmer_crops'))

    if request.method == 'POST':
        name = request.form['crop_name']
        crop_type = request.form['crop_type']
        quantity = request.form['quantity']
        price_per_unit = request.form['price_per_unit']
        sowing = request.form['sowing_date']
        harvesting = request.form['harvest_date']
        desc = request.form['description']
        db_cursor.execute("""
            UPDATE crops SET crop_name=%s, crop_type=%s, quantity=%s, price_per_unit=%s, sowing_date=%s, harvest_date=%s, description=%s
            WHERE crop_id=%s AND farmer_id=%s
        """, (name, crop_type, quantity, price_per_unit, sowing, harvesting, desc, crop_id, farmer_id))
        db_conn.commit()
        flash('Crop updated successfully.')
        return redirect(url_for('farmer_crops'))

    return render_template('edit_crop.html', crop=crop)

# Crops DELETE
@app.route('/farmer/crops/delete/<int:crop_id>', methods=['POST'])
def delete_crop(crop_id):
    farmer_id = session.get('farmer_id')
    if not farmer_id:
        return redirect(url_for('farmer_login'))

    db_conn, db_cursor = get_db()
    db_cursor.execute("DELETE FROM crops WHERE crop_id=%s AND farmer_id=%s", (crop_id, farmer_id))
    db_conn.commit()
    flash('Crop deleted.')
    return redirect(url_for('farmer_crops'))
# End

######### GOVERNMENT #############

######### START 1 ############
@app.route("/gov/crops_data")
def gov_crops_data():
    db, cur = get_db()
    # Get all crop records and for each crop, sum across all farmers
    cur.execute("""
        SELECT
            c.crop_id,
            c.crop_name,
            c.crop_type,
            c.quantity,
            c.price_per_unit,
            c.sowing_date,
            c.harvest_date,
            c.description,
            c.created_at,
            f.full_name AS farmer_name,
            f.id AS farmer_id
        FROM crops c
        JOIN farmers f ON c.farmer_id = f.id
        ORDER BY c.crop_name
    """)
    all_crops = cur.fetchall()

    cur.execute("""
        SELECT crop_name, SUM(quantity) as total_quantity
        FROM crops
        GROUP BY crop_name
        ORDER BY crop_name
    """)
    crop_totals = cur.fetchall()
    # Convert to a simple dict for lookup
    totals_dict = {row['crop_name']: row['total_quantity'] for row in crop_totals}

    return render_template("gov_crops_data.html", all_crops=all_crops, crop_totals=totals_dict)

########## END 1 ###########

########### START 2 ########
@app.route("/gov/transactions_history")
def gov_transactions_history():
    db, cur = get_db()
    cur.execute("""
        SELECT
            oi.order_id,
            oi.quantity,
            oi.price_at_purchase,
            o.placed_at,
            c.crop_name,
            f.full_name AS farmer_name,
            cu.full_name AS customer_name
        FROM order_items oi
        JOIN crops c ON oi.crop_id = c.crop_id
        JOIN farmers f ON c.farmer_id = f.id
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers cu ON o.customer_id = cu.id
        ORDER BY o.placed_at DESC
    """)
    transactions = cur.fetchall()
    return render_template("gov_transactions_history.html", transactions=transactions)

######### END 2 ################
@app.route('/farmers_details')
def government_farmers():
    db_conn, db_cursor = get_db()
    db_cursor.execute("SELECT * FROM farmers")
    farmers = db_cursor.fetchall()
    return render_template('farmers_details.html', module='farmers', farmers=farmers)

@app.route('/customer_details')
def government_customers():
    db_conn, db_cursor = get_db()
    db_cursor.execute("SELECT * FROM customers")
    customers = db_cursor.fetchall()
    return render_template('customer_details.html', module='customers', customers=customers)


if __name__ == '__main__':
    app.run(debug=True)
