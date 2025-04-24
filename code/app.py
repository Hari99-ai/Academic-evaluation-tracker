from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect, url_for
from flask import session
from flask import Flask, render_template, request, jsonify
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import bcrypt
from flask_mail import Mail, Message
from flask import Flask, render_template, redirect, url_for, request, flash, session
# from flask_mysql_connector import MySQL
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

import mysql.connector
from mysql.connector import Error

def query_db(query, params=None, fetch_one=False):
    """
    Executes a query against the database and fetches results.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters for the SQL query. Defaults to None.
        fetch_one (bool): If True, fetch a single row. Otherwise, fetch all rows.

    Returns:
        list or dict: Query results (list of rows or a single row as a dictionary).
    """
    conn = None
    cursor = None
    try:
        # Establish database connection
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='hariom@123',  # Replace with your database password
            database='project_db'   # Replace with your database name
        )
        cursor = conn.cursor(dictionary=True)

        # Execute the query
        cursor.execute(query, params)

        # Fetch results
        if fetch_one:
            return cursor.fetchone()
        else:
            return cursor.fetchall()
    except Error as e:
        print(f"Error querying database: {e}")
        return None
    finally:
        # Ensure resources are closed
        if cursor:
            cursor.close()
        if conn:
            conn.close()



@app.route('/submit', methods=['POST'])
def submit_form():
    # Check if form data exists
    if not request.form:
        return redirect(url_for('form_page', error="Form data is missing"))

    # Store essential data only
    session['form_data'] = {key: request.form[key] for key in ['field1', 'field2']}  # Example fields

    # Redirect to success page
    return redirect(url_for('success_page'))

@app.route('/success')
def success_page():
    return "Form submitted successfully!"

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'hariom@123'
app.config['MYSQL_DB'] = 'project_db'

# Establishing connection to the MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='hariom@123',
    database='project_db'
)


cursor = conn.cursor(dictionary=True)
import mysql.connector
 # Secret key for sessions

@app.route('/', methods=['GET', 'POST'])
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    msg = ''  # Initialize the message variable for feedback
    
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'role' in request.form:
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Query to get the account details from the database based on the username
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        

        if account:
            # Compare the plain password with the one stored in the database
            if account['password'] == password:  # Plain password comparison
                # Set session variables for the logged-in user
                session['user_id'] = account['id']
                session['username'] = account['username']
                session['role'] = account['role']  # Store the user's role in the session
                
                # Role-based routing to respective dashboards
                if role == 'admin' and account['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'user' and account['role'] == 'user':
                    return redirect(url_for('user_dashboard'))
                else:
                    flash('Invalid role.', 'error')  # Invalid role selected
                    return redirect(url_for('signin'))
            else:
                flash('Invalid password!', 'error')  # Password mismatch
                return redirect(url_for('signin'))
        else:
            flash('Username not found!', 'error')  # Username not in database
            return redirect(url_for('signin'))
        
        

    return render_template('signin.html', msg=msg)

# Define the routes for the dashboards
@app.route('/admin_dashboard')
def admin_dashboard():
    username = session.get('username') 
    return render_template('admin_dashboard.html',user=username)  # Create this template
@app.route('/user_dashboard')
def user_dashboard():
    username = session.get('username') 
    email = session.get('email')
    performance=[]
    return render_template('user_dashboard.html',user=username,email=email,performance=performance)  # Create this template


@app.route('/dashboard')
def dashboard():
    # Ensure the user is signed in
    if 'signedin' not in session or not session['signedin']:
        return redirect('/signin')  # Redirect to login if not signed in

    user_id = session['id']
    email = session.get('email')  # Retrieve the email from the session

    # Fetch user details, including the password (used as roll number)
    cursor.execute('SELECT username, email, password, role FROM accounts WHERE id = %s', (user_id,))
    user_details = cursor.fetchone()

    if not user_details:
        return "Account not found", 404  # Handle missing account gracefully

    # Extract data from user details
    roll_number = user_details['password']  # Password is being used as roll number
    role = user_details['role']

    if role == 'admin':
        # Fetch all users' data for admin
        cursor.execute('SELECT * FROM accounts')
        users_data = cursor.fetchall()
        performance = []  # Replace with actual logic to fetch performance data
        return render_template(
            'admin_dashboard.html',
            user=users_data,
            performance=performance,
            email=email,
            roll_number=roll_number
        )
    elif role == 'user':
        users_data = {"username": session['username']}  # Replace with actual user-specific data logic
        performance = []  # Default empty list or fetch user-specific performance data
        return render_template(
            'user_dashboard.html',
            user=users_data,
            performance=performance,
            email=email,
            roll_number=roll_number
        )
    else:
        return "Unauthorized access", 403  # Handle unexpected roles

@app.route('/view_reports')
def view_reports():
    # Logic to retrieve reports from the database
    # For example, fetching reports from the "performance" table
    cursor.execute("SELECT * FROM performance WHERE user_id = %s", (session['user_id'],))
    reports = cursor.fetchall()
    
    # Render the reports page
    return render_template('view_reports.html', reports=reports,user=None,user_id=session['user_id'])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'role' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        session['email'] = email 
        session['username'] = username
        
        # Check if the email already exists
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        
        
        if account:
            msg = 'Account with this email already exists!'  # Error message for duplicate email
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            try:
                # Insert the new user into the database
                cursor.execute('INSERT INTO accounts (username, password, email, role) VALUES (%s, %s, %s, %s)', (username, password, email, role))
                conn.commit()
                msg = 'You have successfully registered!'
            except mysql.connector.Error as e:
                # Handle any database errors (optional)
                msg = f'An error occurred: {e}'
    
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    
    return render_template('signup.html', msg=msg)




# Establishing connection to the MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='hariom@123',
    database='project_db'
)




cursor = conn.cursor(dictionary=True)
import mysql.connector

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Example: Gmail's SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_email_password'  # Replace with your email password

mail = Mail(app)

@app.route('/t')
def t():
    return render_template('t.html')

@app.route('/send_email', methods=['GET'])
def send_email():
    email_type = request.args.get('type')
    recipient_email = "recipient_email@example.com"  # Replace with the recipient's email address

    if email_type == 'deadline':
        subject = "Reminder: Project Deadline"
        body = "Upcoming project deadline is in 2 days!"
    elif email_type == 'performance':
        subject = "Alert: Low Performance"
        body = "Low performance detected in the last evaluation."
    else:
        return "Invalid email type!", 400

    # Send email
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient_email])
        msg.body = body
        mail.send(msg)
        return f"Email sent successfully to {recipient_email}!"
    except Exception as e:
        return f"Failed to send email: {str(e)}", 500


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('signin'))


db_config = {
    'host': 'localhost',
    
    'user': 'root',
    'password': 'hariom@123',
    'database': 'project_db'
}


@app.route('/view_users')
def view_users():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch user data with role='user'
        cursor.execute("SELECT id, username, email, role, password, created_at FROM accounts WHERE role = 'user'")
        users = cursor.fetchall()
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Render HTML template
        return render_template('view_users.html', users=users)
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Route to verify password
@app.route('/verify_password', methods=['POST'])
def verify_password():
    try:
        # Get the user input
        username = request.form['username']
        plain_password = request.form['password']
        
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch hashed password for the user
        cursor.execute("SELECT password FROM accounts WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        # Close connection
        cursor.close()
        conn.close()
        
        if user and bcrypt.checkpw(plain_password.encode('utf-8'), user['password'].encode('utf-8')):
            return "Password verified successfully!"
        else:
            return "Invalid username or password."
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route('/admin/add_performance', methods=['GET', 'POST'])
def add_performance():
    msg = ''
    roll_no = None  # Initialize roll_no to avoid UnboundLocalError

    if request.method == 'POST':
        try:
            # Fetch form data
            user_id = request.form.get('user_id')
            grade = request.form.get('grade')
            marks = request.form.get('marks', 0)
            study_hours = request.form.get('study_hours', 0)
            attendance = request.form.get('attendance', 0)
            roll_no = request.form.get('roll_no')

            # Convert numeric fields to integers
            marks = int(marks) if marks else 0
            study_hours = int(study_hours) if study_hours else 0
            attendance = int(attendance) if attendance else 0

            # Check if roll_no already exists in the database
            cursor.execute('SELECT * FROM performance WHERE roll_no = %s', (roll_no,))
            existing_record = cursor.fetchone()

            if existing_record:
                msg = f'Error: Roll number {roll_no} already exists in the database!'
            else:
                # Insert performance data into the database
                cursor.execute(
                    '''
                    INSERT INTO performance (user_id, grade, marks, study_hours, attendance, roll_no)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''',
                    (user_id, grade, marks, study_hours, attendance, roll_no)
                )
                conn.commit()
                msg = 'Performance data added successfully!'
        except ValueError as ve:
            msg = f'Invalid input: {ve}'
        except Exception as e:
            conn.rollback()
            msg = f'Error adding performance data: {str(e)}'

    try:
        # Fetch all users to display in the form
        cursor.execute('SELECT id, username FROM accounts WHERE role = "user"')
        users = cursor.fetchall()
    except Exception as e:
        users = []
        msg = f'Error fetching users: {str(e)}'
 

    return render_template('add_performance.html', users=users, roll_no=roll_no or "NA", msg=msg)


    
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    feedback = request.form.get('feedback')
    user_id = session.get('user_id')  # Assuming user ID is stored in session

    if not feedback:
        flash("Feedback cannot be empty.")
        return redirect(url_for('feedback_page'))

    try:
        conn = mysql.connector.connect(
            host='localhost', user='root', password='password', database='your_db'
        )
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO feedback (user_id, feedback_text) VALUES (%s, %s)',
            (user_id, feedback)
        )
        conn.commit()
        flash("Thank you for your feedback!")
    except Exception as e:
        flash(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('feedback_page'))

@app.route('/view_feedback')
def view_feedback():
    if not session.get('is_admin'):  # Ensure only admins can access this
        return redirect(url_for('admin_dashboard'))

    try:
        conn = mysql.connector.connect(
            host='localhost', user='root', password='password', database='your_db'
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT feedback.id, users.username, feedback.feedback_text, feedback.created_at '
                       'FROM feedback JOIN users ON feedback.user_id = users.id')
        feedback_list = cursor.fetchall()
    except Exception as e:
        feedback_list = []
        flash(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

    return render_template('view_feedback.html', feedback_list=feedback_list)



@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    return render_template('feedback.html')
@app.route('/predict', methods=['POST'])
def predict():
    # Get form data
    study_hours = float(request.form['study_hours'])
    attendance = float(request.form['attendance'])
    assignments = int(request.form['assignments'])
    # Load the model and make prediction
    model = joblib.load('academic_model.pkl')
    prediction = model.predict([[study_hours, attendance, assignments]])[0]
    # Example suggestion logic
    suggestion = "Good job! Keep up the consistency." if prediction == 'Pass' else "Increase study hours or assignment completion rate."
    return render_template('result.html', prediction=prediction, suggestion=suggestion)

if __name__ == '__main__':
    # Debug mode for development
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # For production use, rely on a WSGI server like Gunicorn
    pass
