from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, make_response
import os
from ai_helper import generate_medical_response, handle_followup_question
from database import mongo, User, Conversation, Reminder, MONGO_URI, get_direct_mongo_client, get_database
from reminder_sender import start_reminder_scheduler
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import uuid
from dotenv import load_dotenv
from bson.objectid import ObjectId
import sys
import tempfile
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')

# Session configuration
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# MongoDB configuration
app.config['MONGO_URI'] = MONGO_URI

# Initialize MongoDB
mongo.init_app(app)

# Add debug logging for session operations
@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Session: %s', dict(session))

# Constants

# Add cache control headers to prevent caching
@app.after_request
def add_header(response):
    """Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Check session before each request
@app.before_request
def before_request():
    # Skip session check for static files and certain routes
    if request.endpoint and 'static' in request.endpoint or request.endpoint in ['login', 'signup', 'home']:
        return
    
    # Check if user is logged in and verify session data is complete
    if session.get('logged_in'):
        # Verify all required session data exists
        required_fields = ['email', 'user_id', 'first_name']
        if not all(field in session for field in required_fields):
            # If any required field is missing, clear the session
            session.clear()
            return redirect(url_for('login'))
    
    # Redirect to login if trying to access protected routes while not logged in
    protected_routes = ['dashboard', 'chat', 'reminders', 'conversations', 'view_conversation']
    if not session.get('logged_in') and request.endpoint in protected_routes:
        return redirect(url_for('login'))

# Initialize database indexes
def init_db_indexes():
    """Initialize database indexes using direct MongoDB connection"""
    try:
        # Get database directly
        db = get_database()
        
        # Create indexes
        db.users.create_index("email", unique=True)
        db.conversations.create_index("conversation_id", unique=True)
        db.conversations.create_index("user_id")
        db.reminders.create_index("user_id")
        
        print("Database indexes created successfully")
        return True
    except Exception as e:
        app.logger.error(f"Error creating indexes: {str(e)}")
        print(f"Error creating indexes: {str(e)}")
        return False

# Verify MongoDB connection
def verify_mongodb_connection():
    try:
        # Try to connect directly to MongoDB
        client = get_direct_mongo_client()
        client.admin.command('ping')
        print("MongoDB connection verified successfully")
        client.close()
        return True
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_email(email):
    try:
        return User.find_by_email(email)
    except Exception as e:
        app.logger.error(f"Error finding user by email: {str(e)}")
        return None

@app.route('/')
def home():
    """Home page route"""
    # If user is logged in, redirect to chat
    if session.get('logged_in'):
        return redirect(url_for('chat'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    try:
        # Clear any existing session
        session.clear()
        app.logger.debug('Session cleared at start of login')
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember') == 'on'
            
            app.logger.debug('Login attempt for email: %s', email)
            
            if not email or not password:
                app.logger.warning('Login attempt with missing email or password')
                return render_template('login.html', error="Please provide both email and password")
            
            user = get_user_by_email(email)
            
            if not user:
                app.logger.warning('Login attempt with non-existent email: %s', email)
                return render_template('login.html', error="Invalid email or password")
            
            if user['password'] == hash_password(password):
                # Set session data
                session.clear()  # Clear again just to be safe
                session['logged_in'] = True
                session['email'] = email
                session['first_name'] = user.get('first_name', 'User')
                session['last_name'] = user.get('last_name', '')
                session['user_id'] = str(user['_id'])
                
                # Set session permanence based on remember me
                if remember:
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=7)
                else:
                    session.permanent = False
                
                app.logger.info('Successful login for user: %s', email)
                app.logger.debug('Session after login: %s', dict(session))
                
                return redirect(url_for('dashboard'))
            else:
                app.logger.warning('Login attempt with incorrect password for email: %s', email)
                return render_template('login.html', error="Invalid email or password")
        
        return render_template('login.html')
    except Exception as e:
        app.logger.error('Login error: %s', str(e), exc_info=True)
        return render_template('login.html', error="An error occurred during login. Please try again.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if get_user_by_email(email):
            return render_template('signup.html', error="Email already registered")
        
        try:
            user = User.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=hash_password(password)
            )
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('signup.html', error="An error occurred during registration")
    
    return render_template('signup.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle signup requests"""
    try:
        if request.method == 'POST':
            first_name = request.form.get('firstName', '').strip()
            last_name = request.form.get('lastName', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            # Validate input
            if not all([first_name, last_name, email, password]):
                return render_template('signup.html', error="All fields are required")
            
            # Check if email already exists
            if get_user_by_email(email):
                return render_template('signup.html', error="Email already registered")
            
            try:
                # Create new user
                user = User.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=hash_password(password)
                )
                
                if user:
                    # Redirect to login page with success message
                    return render_template('login.html', success="Registration successful! Please login.")
                else:
                    return render_template('signup.html', error="Failed to create user. Please try again.")
                    
            except Exception as e:
                app.logger.error(f"User creation error: {str(e)}")
                return render_template('signup.html', error="An error occurred during registration")
        
        return render_template('signup.html')
        
    except Exception as e:
        app.logger.error(f"Signup error: {str(e)}")
        return render_template('signup.html', error="An error occurred. Please try again.")

@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    
    # Create response with redirect and no-cache headers
    response = make_response(redirect(url_for('home')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/chat')
@login_required
def chat():
    current_time = datetime.now().strftime('%I:%M %p')
    return render_template('chat.html', current_time=current_time)

@app.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    return render_template('appointment.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Here you would handle the form submission
        # For example, sending an email or saving to database
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Add your form processing logic here
        # For now, just redirect back to the contact page
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/appointment/confirmation', methods=['GET', 'POST'])
@login_required
def appointment_confirmation():
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        time = request.form.get('time')
        timezone = request.form.get('timezone')
        
        # Store in session
        session['appointment'] = {
            'date': date,
            'time': time,
            'timezone': timezone
        }
        return redirect(url_for('slot_confirmation'))
    return redirect(url_for('appointment'))

@app.route('/slot-confirmation')
@login_required
def slot_confirmation():
    # Check if we have appointment details in session or query parameters
    # This handles both direct form submissions and redirects from getform.io
    appointment = session.get('appointment')
    
    # For getform.io redirects, the parameters will be in the URL
    if not appointment and (
        request.args.get('appointment_date') or 
        request.args.get('appointment_time') or 
        request.args.get('appointment_timezone')
    ):
        # Create appointment object from query parameters
        appointment = {
            'date': request.args.get('appointment_date'),
            'time': request.args.get('appointment_time'),
            'timezone': request.args.get('appointment_timezone')
        }
        
    # If we still don't have appointment details, redirect to appointment page
    if not appointment:
        return redirect(url_for('appointment'))
        
    return render_template('slot_confirmation.html', appointment=appointment)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/get_ai_response', methods=['POST'])
def get_ai_response():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    try:
        ai_response = generate_medical_response(user_message)
        
        # Create a new conversation if no conversation_id was provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Save the conversation to the database
        conversation_data = {
            'messages': [
                {
                    'user': user_message,
                    'ai': ai_response,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        }
        
        # Check if the conversation already exists
        existing_conversation = Conversation.find_by_conversation_id(conversation_id)
        
        if existing_conversation:
            # Update the existing conversation by appending the new message
            existing_messages = existing_conversation.get('conversation_data', {}).get('messages', [])
            conversation_data['messages'] = existing_messages + conversation_data['messages']
            
            mongo.db.conversations.update_one(
                {'conversation_id': conversation_id},
                {'$set': {'conversation_data': conversation_data}}
            )
        else:
            # Create a new conversation
            Conversation.create(
                conversation_id=conversation_id,
                user_id=session.get('user_id'),
                conversation_data=conversation_data
            )
        
        return jsonify({
            'response': ai_response,
            'conversation_id': conversation_id
        })
    except Exception as e:
        app.logger.error(f"Error generating AI response: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/handle_followup', methods=['POST'])
def handle_followup():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    question = data.get('question')
    previous_responses = data.get('previous_responses')
    conversation_id = data.get('conversation_id')
    
    if not question or not previous_responses:
        return jsonify({'error': 'Missing required information'}), 400
    
    try:
        response = handle_followup_question(question, previous_responses)
        
        if conversation_id:
            user = get_user_by_email(session['email'])
            conversation = Conversation.find_by_conversation_id(conversation_id)
            
            if conversation:
                conversation_data = conversation['conversation_data']
                
                if 'messages' not in conversation_data:
                    conversation_data['messages'] = []
                
                conversation_data['messages'].append({
                    'user': question,
                    'ai': response,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                conversation_data['messages'] = conversation_data['messages'][-10:]  # Limit to 10 messages
                
                mongo.db.conversations.update_one(
                    {'conversation_id': conversation_id},
                    {'$set': {'conversation_data': conversation_data}}
                )
        
        return jsonify({'response': response, 'conversation_id': conversation_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/conversations')
@login_required
def conversations():
    user = get_user_by_email(session['email'])
    user_conversations = [conv for conv in Conversation.find_all_by_user_id(user['_id'])]
    return render_template('conversations.html', conversations=user_conversations)

@app.route('/conversation/<conversation_id>')
@login_required
def view_conversation(conversation_id):
    user = get_user_by_email(session['email'])
    conversation = Conversation.find_by_conversation_id(conversation_id)
    
    if not conversation:
        return redirect(url_for('conversations'))
    
    return render_template('view_conversation.html', conversation=conversation)

@app.route('/reminders')
@login_required
def reminders():
    user = get_user_by_email(session['email'])
    all_reminders = [reminder for reminder in Reminder.find_all_by_user_id(user['_id'])]
    
    medication_reminders = []
    hydration_reminders = []
    
    for reminder in all_reminders:
        reminder_type = reminder['reminder_data'].get('type')
        if reminder_type == 'medication':
            medication_reminders.append(reminder)
        elif reminder_type == 'hydration':
            hydration_reminders.append(reminder)
    
    return render_template('reminders.html', 
                         medication_reminders=medication_reminders,
                         hydration_reminders=hydration_reminders)

@app.route('/save_reminder', methods=['POST'])
@login_required
def add_reminder():
    try:
        reminder_data = request.json
        user = get_user_by_email(session['email'])
        
        # Create a new reminder
        reminder = Reminder.create(
            reminder_id=str(uuid.uuid4()),
            user_id=user['_id'],
            reminder_data=reminder_data
        )
        
        return jsonify({'success': True, 'reminder_id': str(reminder['_id'])})
    except Exception as e:
        app.logger.error(f"Error saving reminder: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_reminder', methods=['POST'])
@login_required
def remove_reminder():
    try:
        data = request.json
        reminder_id = data.get('reminder_id')
        
        if not reminder_id:
            return jsonify({'success': False, 'error': 'No reminder ID provided'}), 400
        
        user = get_user_by_email(session['email'])
        reminder = Reminder.find_by_id(reminder_id)
        
        if reminder and str(reminder['user_id']) == str(user['_id']):
            Reminder.delete(reminder)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Reminder not found or unauthorized'}), 404
    except Exception as e:
        app.logger.error(f"Error deleting reminder: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's first name for personalized greeting
    first_name = session.get('first_name', 'User')
    
    return render_template('dashboard.html', first_name=first_name)

if __name__ == '__main__':
    # Initialize database indexes
    init_db_indexes()
    
    # Start the reminder scheduler
    start_reminder_scheduler()
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        # Production settings
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.run(host='0.0.0.0', port=port)
