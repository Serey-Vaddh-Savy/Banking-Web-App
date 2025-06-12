from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'



def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'bank.db')
    if not os.path.exists('database'):
        os.makedirs('database')  # Ensure the database directory exists
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (recipient_id) REFERENCES users (id)
        )
    ''')
    # Create the 'complaints' table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Create the 'purchases' table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.close()
    
   
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'bank.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows you to access rows as dictionaries
    return conn


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            # Redirect to the reset password page with the user's email
            return redirect(url_for('reset_password', email=email))
        else:
            # Show an error if the email is not found
            return render_template('forgot_password.html', error="Email not found.")
    
    return render_template('forgot_password.html')
@app.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset_password.html', email=email, error="Passwords do not match.")

        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))  # Redirect to login after successful password reset

    return render_template('reset_password.html', email=email)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not an admin
    return render_template('admin_dashboard.html')


@app.route('/investor/dashboard', methods=['GET'])
def investor_dashboard():
    if 'user_id' not in session or session.get('role') != 'investor':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not an investor
    return render_template('investor_dashboard.html')

@app.route('/customer/dashboard', methods=['GET'])
def customer_dashboard():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    return render_template('customer_dashboard.html', user=user)

@app.route('/select-role', methods=['GET'])
def select_role():
    return render_template('role_selection.html')
@app.route('/register', methods=['GET'])
def register():
    return redirect(url_for('register_select_role'))

@app.route('/register/select-role', methods=['GET'])
def register_select_role():
    return render_template('register_role_selection.html')



@app.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        role = 'customer'
        balance = round(random.uniform(100, 1000), 2)  # Generate a random balance between 100 and 1000

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            conn.close()
            return render_template('register_customer.html', error="Username or email already exists.")
        
        conn.execute('INSERT INTO users (username, email, password, role, balance) VALUES (?, ?, ?, ?, ?)', 
                     (username, email, password, role, balance))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))  # Redirect to the login page after registration
    return render_template('register_customer.html')
@app.route('/customer/personal-info', methods=['GET', 'POST'])
def personal_info():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not a customer

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        address = request.form['address']

        conn.execute('''
            UPDATE users 
            SET username = ?, email = ?, phone_number = ?, address = ? 
            WHERE id = ?
        ''', (name, email, phone_number, address, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('customer_dashboard'))  # Redirect back to the dashboard after updating

    conn.close()
    return render_template('personal_info.html', user=user)
@app.route('/customer/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not a customer

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        return render_template('personal_info.html', user=session, error="New passwords do not match.")

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # Verify the current password
    if not check_password_hash(user['password'], current_password):
        conn.close()
        return render_template('personal_info.html', user=user, error="Current password is incorrect.")

    # Update the password
    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, session['user_id']))
    conn.commit()
    conn.close()

    return redirect(url_for('customer_dashboard'))  # Redirect back to the dashboard after updating
@app.route('/customer/send-money', methods=['POST'])
def send_money():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    sender_id = session['user_id']
    recipient_email = request.form['recipient_email']
    amount = float(request.form['amount'])

    conn = get_db_connection()

    # Fetch recipient details
    recipient = conn.execute('SELECT id, balance FROM users WHERE email = ? AND role = "customer"', (recipient_email,)).fetchone()
    if not recipient:
        conn.close()
        return render_template('send_money.html', error="Recipient not found.")

    # Check if sender has enough balance
    sender = conn.execute('SELECT balance FROM users WHERE id = ?', (sender_id,)).fetchone()
    if sender['balance'] < amount:
        conn.close()
        return render_template('send_money.html', error="Insufficient balance.")

    # Update balances
    conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, sender_id))
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, recipient['id']))

    # Record the transaction
    conn.execute('INSERT INTO transfers (sender_id, recipient_id, amount, date) VALUES (?, ?, ?, datetime("now"))',
                 (sender_id, recipient['id'], amount))
    conn.commit()
    conn.close()

    return redirect(url_for('customer_dashboard'))
@app.route('/customer/invest', methods=['POST'])
def invest_money():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    user_id = session['user_id']
    stock = request.form['stock']
    amount = float(request.form['amount'])

    conn = get_db_connection()

    # Fetch user's balance
    user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['balance'] < amount:
        conn.close()
        return render_template('invest.html', error="Insufficient balance.")

    # Deduct the investment amount
    conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))

    # Record the investment
    conn.execute('INSERT INTO investments (user_id, stock, amount, date) VALUES (?, ?, ?, datetime("now"))',
                 (user_id, stock, amount))
    conn.commit()
    conn.close()

    return redirect(url_for('customer_dashboard'))
@app.route('/register/admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        role = 'admin'
        status = 'Pending'  # New admin accounts are pending approval

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            conn.close()
            return render_template('register_admin.html', error="Username or email already exists.")
        
        conn.execute('INSERT INTO users (username, email, password, role, status) VALUES (?, ?, ?, ?, ?)', 
                     (username, email, password, role, status))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))  # Redirect to the login page after registration
    return render_template('register_admin.html')
@app.route('/admin/approve-admins', methods=['GET', 'POST'])
def approve_admins():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not an admin

    conn = get_db_connection()

    if request.method == 'POST':
        admin_id = request.form['admin_id']
        conn.execute('UPDATE users SET status = "Approved" WHERE id = ?', (admin_id,))
        conn.commit()

    # Fetch all pending admin accounts
    pending_admins = conn.execute('SELECT id, username, email FROM users WHERE role = "admin" AND status = "Pending"').fetchall()
    conn.close()

    return render_template('approve_admins.html', pending_admins=pending_admins)
@app.route('/admin/decline-admins', methods=['POST'])
def decline_admins():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not an admin

    admin_id = request.form['admin_id']

    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ? AND role = "admin" AND status = "Pending"', (admin_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('approve_admins'))
@app.route('/admin/manage-users', methods=['GET', 'POST'])
def manage_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not an admin

    conn = get_db_connection()

    if request.method == 'POST':
        user_id = request.form['user_id']
        new_balance = request.form['new_balance']

        # Update the user's balance
        conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
        conn.commit()

    # Fetch all users and their balances
    users = conn.execute('SELECT id, username, email, balance FROM users WHERE role = "customer"').fetchall()
    conn.close()

    return render_template('manage_users.html', users=users)
@app.route('/admin/delete-user', methods=['POST'])
def delete_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not authenticated or not an admin

    user_id = request.form['user_id']

    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('manage_users'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            # Check if the password is correct
            if check_password_hash(user['password'], password):
                # Check if the user is an admin and their status is 'Pending'
                if user['role'] == 'admin' and user['status'] == 'Pending':
                    return render_template('login.html', error="Your account is pending approval by an existing admin.")
                
                # Log the user in
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']

                # Redirect based on the user's role
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'customer':
                    return redirect(url_for('customer_dashboard'))
            else:
                return render_template('login.html', error="Invalid email or password.")
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')
@app.route('/login/customer', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = 'customer'

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, role)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('customer_dashboard'))
        else:
            return render_template('login_customer.html', error="Invalid email or password.")
    return render_template('login_customer.html')

@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = 'admin'

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, role)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login_admin.html', error="Invalid email or password.")
    return render_template('login_admin.html')

@app.route('/balance')
def balance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('balance.html', balance=user['balance'])

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        sender_id = session['user_id']
        recipient_email = request.form['recipient']  # Use email instead of username
        amount = float(request.form['amount'])

        # Fetch sender's balance
        sender = conn.execute('SELECT * FROM users WHERE id = ?', (sender_id,)).fetchone()
        if sender['balance'] < amount:
            # Fetch transfer history before closing the connection
            transfer_history = conn.execute('''
                SELECT u1.username AS sender, u2.username AS recipient, t.amount, t.date
                FROM transfers t
                JOIN users u1 ON t.sender_id = u1.id
                JOIN users u2 ON t.recipient_id = u2.id
                WHERE t.sender_id = ? OR t.recipient_id = ?
                ORDER BY t.date DESC
            ''', (session['user_id'], session['user_id'])).fetchall()
            conn.close()
            return render_template('transfer.html', transfer_history=transfer_history, error="Insufficient balance.")

        # Fetch recipient's account using email
        recipient = conn.execute('SELECT * FROM users WHERE email = ?', (recipient_email,)).fetchone()
        if not recipient:
            # Fetch transfer history before closing the connection
            transfer_history = conn.execute('''
                SELECT u1.username AS sender, u2.username AS recipient, t.amount, t.date
                FROM transfers t
                JOIN users u1 ON t.sender_id = u1.id
                JOIN users u2 ON t.recipient_id = u2.id
                WHERE t.sender_id = ? OR t.recipient_id = ?
                ORDER BY t.date DESC
            ''', (session['user_id'], session['user_id'])).fetchall()
            conn.close()
            return render_template('transfer.html', transfer_history=transfer_history, error="Recipient not found.")

        # Update balances
        conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, sender_id))
        conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, recipient['id']))
        conn.commit()

        # Log the transfer
        conn.execute('INSERT INTO transfers (sender_id, recipient_id, amount, date) VALUES (?, ?, ?, datetime("now"))',
                     (sender_id, recipient['id'], amount))
        conn.commit()

    # Fetch transfer history
    transfer_history = conn.execute('''
        SELECT u1.username AS sender, u2.username AS recipient, t.amount, t.date
        FROM transfers t
        JOIN users u1 ON t.sender_id = u1.id
        JOIN users u2 ON t.recipient_id = u2.id
        WHERE t.sender_id = ? OR t.recipient_id = ?
        ORDER BY t.date DESC
    ''', (session['user_id'], session['user_id'])).fetchall()
    conn.close()

    return render_template('transfer.html', transfer_history=transfer_history)


@app.route('/trade', methods=['GET', 'POST'])
def trade():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    conn = get_db_connection()

    if request.method == 'POST':
        stock = request.form.get('stock')  # Stock name (e.g., TSLA)
        amount = int(request.form.get('amount', 0))  # Number of stocks
        user_id = session['user_id']
        action = request.form.get('action')  # Action: "buy", "sell", or "sell_all"

        # Fetch user's current balance
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        portfolio = conn.execute('''
            SELECT stock, SUM(amount) AS total_amount
            FROM purchases
            WHERE user_id = ? AND stock = ?
            GROUP BY stock
        ''', (user_id, stock)).fetchone()

        # Define stock price with a 65% chance of being 50.6
        stock_price = 50.6 if random.random() < 0.65 else round(random.uniform(50, 51), 1)
        total_cost = stock_price * amount

        if action == 'buy':
            # Check if the user has enough balance to purchase
            if user['balance'] < total_cost:
                conn.close()
                return render_template('trade.html', user=user, error="Insufficient balance.")
            
            # Deduct the total cost from the user's balance
            conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (total_cost, user_id))
            # Record the purchase in the purchases table
            conn.execute('INSERT INTO purchases (user_id, stock, amount, price, date) VALUES (?, ?, ?, ?, datetime("now"))',
                         (user_id, stock, amount, stock_price))

        elif action == 'sell':
            # Check if the user has enough stocks to sell
            if not portfolio or portfolio['total_amount'] < amount:
                conn.close()
                return render_template('trade.html', user=user, error="Not enough stocks to sell.")
            
            # Add the total earnings to the user's balance
            conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (total_cost, user_id))
            # Record the sale in the purchases table (negative amount indicates selling)
            conn.execute('INSERT INTO purchases (user_id, stock, amount, price, date) VALUES (?, ?, ?, ?, datetime("now"))',
                         (user_id, stock, -amount, stock_price))

        elif action == 'sell_all':
            # Sell all stocks of the given type
            if not portfolio or portfolio['total_amount'] <= 0:
                conn.close()
                return render_template('trade.html', user=user, error="You don't own any stocks to sell.")
            
            total_earnings = portfolio['total_amount'] * stock_price
            conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (total_earnings, user_id))
            conn.execute('INSERT INTO purchases (user_id, stock, amount, price, date) VALUES (?, ?, ?, ?, datetime("now"))',
                         (user_id, stock, -portfolio['total_amount'], stock_price))

        conn.commit()
        conn.close()
        return redirect(url_for('trade'))  # Redirect to refresh the page with updated data

    # Fetch the user's updated balance and portfolio
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    portfolio = conn.execute('''
        SELECT stock, SUM(amount) AS total_amount, SUM(amount * price) AS total_invested
        FROM purchases
        WHERE user_id = ?
        GROUP BY stock
    ''', (session['user_id'],)).fetchall()

    # Calculate live profit for each stock
    portfolio_data = []
    for row in portfolio:
        stock_price = 50 if row['stock'] == 'TSLA' else 53  # Example stock prices
        total_amount = row['total_amount'] if row['total_amount'] is not None else 0
        total_invested = row['total_invested'] if row['total_invested'] is not None else 0
        live_profit = (total_amount * stock_price) - total_invested
        portfolio_data.append({
            'stock': row['stock'],
            'total_amount': total_amount,
            'total_invested': total_invested,
            'live_profit': live_profit
    })
    conn.close()
    return render_template('trade.html', user=user, portfolio=portfolio_data)
    
    

@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        complaint_text = request.form['complaint']
        # Get the current date and time
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute('INSERT INTO complaints (user_id, complaint, status, date) VALUES (?, ?, ?, ?)',
                     (session['user_id'], complaint_text, 'Pending', current_date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('complaint.html')

@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session['username'])

@app.route('/admin/complaints')
def admin_complaints():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    complaints = conn.execute('SELECT * FROM complaints').fetchall()
    conn.close()

    return render_template('admin_complaints.html', complaints=complaints)
@app.route('/resolve_complaint/<int:complaint_id>', methods=['POST'])
def resolve_complaint(complaint_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('UPDATE complaints SET status = ? WHERE id = ?', ('Resolved', complaint_id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_complaints'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)


db_path = 'database/bank.db'
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:", tables)
conn.close()




@app.route('/update_balance', methods=['POST'])
def update_balance():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    new_balance = data.get('balance')

    if new_balance is None:
        return jsonify({'error': 'Invalid data'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Balance updated successfully'})