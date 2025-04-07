from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import os
from ai_helper import generate_medical_response, handle_followup_question
from auth import init_user_db, authenticate_user, register_user, get_all_users
from conversation import init_conversations_db, save_conversation, get_user_conversations, get_conversation
from reminders import init_reminders_db, save_reminder, get_user_reminders, delete_reminder, get_reminder
from reminder_sender import start_reminder_scheduler
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret key in production

# Constants
ADMIN_EMAIL = 'pavan@gmail.com'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        if session.get('email') != ADMIN_EMAIL:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Authenticate user
        success, result = authenticate_user(email, password)
        
        if success:
            # Set session data for logged in user
            user = result
            session['logged_in'] = True
            session['email'] = email
            session['first_name'] = user['firstName']
            session['last_name'] = user['lastName']
            
            # If remember me is checked, make session permanent
            if remember:
                session.permanent = True
            
            return redirect(url_for('dashboard'))
        else:
            # Display error message
            return render_template('login.html', error=result)
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Register user
        success, error_message = register_user(first_name, last_name, email, password)
        
        if success:
            # Set session data
            session['logged_in'] = True
            session['email'] = email
            session['first_name'] = first_name
            session['last_name'] = last_name
            
            # Redirect to dashboard after successful signup
            return redirect(url_for('dashboard'))
        else:
            return render_template('signup.html', error=error_message)
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Clear session data
    session.clear()
    return redirect(url_for('home'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

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
    # Make sure user is logged in
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_responses = request.json
    conversation_id = user_responses.pop('conversation_id', None)
    
    try:
        # Get AI response
        ai_response = generate_medical_response(user_responses)
        
        # Prepare conversation data for storage
        conversation_data = {
            'user_responses': user_responses,
            'ai_response': ai_response,
            'messages': user_responses.get('messages', [])
        }
        
        # Save conversation
        saved_id = save_conversation(session['email'], conversation_data, conversation_id)
        
        return jsonify({
            'response': ai_response,
            'conversation_id': saved_id
        })
    except Exception as e:
        app.logger.error(f"Exception in get_ai_response: {str(e)}")
        return jsonify({
            'response': "I apologize, but I'm having trouble connecting to our AI services. Please try again later.",
            'error': str(e)
        }), 500

@app.route('/handle_followup', methods=['POST'])
def handle_followup():
    # Make sure user is logged in
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    question = data.get('question')
    previous_responses = data.get('previous_responses')
    conversation_id = data.get('conversation_id')
    
    if not question or not previous_responses:
        return jsonify({'error': 'Missing required information'}), 400
    
    try:
        # Get response from AI
        response = handle_followup_question(question, previous_responses)
        
        # Update conversation with new message
        if conversation_id:
            current_conversation = get_conversation(conversation_id)
            if current_conversation and current_conversation['user_id'] == session['email']:
                conversation_data = current_conversation['data']
                
                # Append new messages
                if 'messages' not in conversation_data:
                    conversation_data['messages'] = []
                
                conversation_data['messages'].append({
                    'user': question,
                    'ai': response,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Save updated conversation
                save_conversation(session['email'], conversation_data, conversation_id)
        
        return jsonify({'response': response, 'conversation_id': conversation_id})
    
    except Exception as e:
        app.logger.error(f"Exception in handle_followup: {str(e)}")
        return jsonify({
            'response': "I apologize, but I'm having trouble connecting to our AI services. Please try again later.",
            'error': str(e)
        }), 500

@app.route('/conversations')
def conversations():
    # Make sure user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get user's conversations
    user_conversations = get_user_conversations(session['email'])
    
    return render_template('conversations.html', conversations=user_conversations)

@app.route('/conversation/<conversation_id>')
def view_conversation(conversation_id):
    # Make sure user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get conversation
    conversation = get_conversation(conversation_id)
    
    # Check if conversation exists and belongs to the user
    if not conversation or conversation['user_id'] != session['email']:
        return redirect(url_for('conversations'))
    
    return render_template('view_conversation.html', conversation=conversation)

@app.route('/admin')
@admin_required
def admin():
    # Get all users
    users = get_all_users()
    return render_template('admin.html', users=users)

@app.route('/reminders')
@login_required
def reminders():
    # Get user's reminders
    all_reminders = get_user_reminders(session['email'])
    
    # Separate medication and hydration reminders
    medication_reminders = []
    hydration_reminders = []
    
    for reminder in all_reminders:
        reminder_type = reminder['data'].get('type')
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
        # Get reminder data from request
        reminder_data = request.json
        
        # Save reminder to database
        reminder_id = save_reminder(session['email'], reminder_data)
        
        return jsonify({'success': True, 'reminder_id': reminder_id})
    except Exception as e:
        app.logger.error(f"Exception in save_reminder: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_reminder', methods=['POST'])
@login_required
def remove_reminder():
    try:
        # Get reminder ID from request
        data = request.json
        reminder_id = data.get('reminder_id')
        
        if not reminder_id:
            return jsonify({'success': False, 'error': 'No reminder ID provided'}), 400
        
        # Delete reminder
        success = delete_reminder(reminder_id, session['email'])
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404
    except Exception as e:
        app.logger.error(f"Exception in delete_reminder: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's first name for personalized greeting
    first_name = session.get('first_name', 'User')
    
    # Check if user is admin
    is_admin = session.get('email') == ADMIN_EMAIL
    
    return render_template('dashboard.html', first_name=first_name, is_admin=is_admin)

if __name__ == '__main__':
    # Initialize databases
    init_user_db()
    init_conversations_db()
    init_reminders_db()
    
    # Start the reminder scheduler
    start_reminder_scheduler()
    
    # Run the Flask app
    app.run(debug=True)
