import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import threading
import schedule
import logging
import os
from database import mongo, User, Reminder
from bson.objectid import ObjectId

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Email configuration
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', 'healthchat.noreply@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'HealthChat <healthchat.noreply@gmail.com>')

def send_email(to_email, subject, html_content):
    """Send an email using the configured SMTP server."""
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = EMAIL_FROM
        message['To'] = to_email
        
        message.attach(MIMEText(html_content, 'html'))
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(message)
            
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_medication_reminder(reminder_id):
    """Send a medication reminder email based on reminder ID."""
    try:
        reminder = Reminder.find_by_id(reminder_id)
        if not reminder:
            logger.warning(f"Reminder not found: {reminder_id}")
            return
        
        user = User.find_by_id(reminder['user_id'])
        if not user:
            logger.warning(f"User not found: {reminder['user_id']}")
            return
            
        # Extract reminder data
        reminder_data = reminder['reminder_data']
        medication_name = reminder_data.get('name', 'your medication')
        dosage = reminder_data.get('dosage', '')
        
        # Create email content
        subject = f"Medication Reminder: {medication_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #4287f5;">Medication Reminder</h2>
                <p>Hello {user['first_name']},</p>
                <p>This is a reminder to take your medication.</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #4287f5; margin: 15px 0;">
                    <h3 style="margin-top: 0;">Time to take your medication</h3>
                    <p><strong>Medication:</strong> {medication_name}</p>
                    <p><strong>Dosage:</strong> {dosage}</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%I:%M %p')}</p>
                </div>
                <p>Stay healthy!</p>
                <p style="margin-top: 30px; font-size: 0.9em; color: #777;">
                    This is an automated message from HealthChat. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        send_email(user['email'], subject, html_content)
        
    except Exception as e:
        logger.error(f"Error in send_medication_reminder: {str(e)}")

def send_hydration_reminder(reminder_id):
    """Send a hydration reminder email based on reminder ID."""
    try:
        reminder = Reminder.find_by_id(reminder_id)
        if not reminder:
            logger.warning(f"Reminder not found: {reminder_id}")
            return
        
        user = User.find_by_id(reminder['user_id'])
        if not user:
            logger.warning(f"User not found: {reminder['user_id']}")
            return
            
        # Extract reminder data
        reminder_data = reminder['reminder_data']
        amount = reminder_data.get('amount', '250ml')
        
        # Create email content
        subject = "Hydration Reminder: Time to drink water"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #42c3f5;">Hydration Reminder</h2>
                <p>Hello {user['first_name']},</p>
                <p>This is a reminder to stay hydrated!</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #42c3f5; margin: 15px 0;">
                    <h3 style="margin-top: 0;">Time to drink water</h3>
                    <p><strong>Recommended amount:</strong> {amount}ml</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%I:%M %p')}</p>
                </div>
                <p>Staying hydrated is essential for your health and wellbeing.</p>
                <p>Stay healthy!</p>
                <p style="margin-top: 30px; font-size: 0.9em; color: #777;">
                    This is an automated message from HealthChat. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        send_email(user['email'], subject, html_content)
        
    except Exception as e:
        logger.error(f"Error in send_hydration_reminder: {str(e)}")

def check_reminders():
    """Check for reminders that need to be sent."""
    logger.info("Checking reminders...")
    current_time = datetime.now()
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # Only process reminders during reasonable hours (8 AM - 9 PM)
    if current_hour < 8 or current_hour > 21:
        return
    
    # Get all reminders
    all_reminders = Reminder.find_all()
    
    for reminder in all_reminders:
        user_id = reminder['user_id']
        user = User.find_by_id(user_id)
        
        if not user:
            continue
            
        reminder_data = reminder['reminder_data']
        reminder_type = reminder_data.get('type')
        
        # Process medication reminders
        if reminder_type == 'medication':
            reminder_time = reminder_data.get('time', '')
            
            # Parse time string (HH:MM format)
            if reminder_time:
                try:
                    hour, minute = map(int, reminder_time.split(':'))
                    
                    # Check if it's time to send the reminder (within a 5-minute window)
                    if (hour == current_hour and 
                        abs(minute - current_minute) <= 5):
                        
                        # Send medication reminder
                        send_medication_reminder(reminder['_id'])
                except Exception as e:
                    logger.error(f"Error processing medication time: {str(e)}")
        
        # Process hydration reminders
        elif reminder_type == 'hydration':
            start_time = reminder_data.get('start_time', '08:00')
            end_time = reminder_data.get('end_time', '20:00')
            frequency = int(reminder_data.get('frequency', 2))  # Hours
            
            try:
                # Parse start and end times
                start_hour, start_minute = map(int, start_time.split(':'))
                end_hour, end_minute = map(int, end_time.split(':'))
                
                # Create datetime objects for start and end
                start_dt = current_time.replace(hour=start_hour, minute=start_minute)
                end_dt = current_time.replace(hour=end_hour, minute=end_minute)
                
                # Check if current time is within active hours
                if start_dt <= current_time <= end_dt:
                    # Check if it's on a frequency interval (accounting for start time)
                    hours_since_start = (current_time - start_dt).total_seconds() / 3600
                    
                    # If we're at a frequency interval (within 5 minutes)
                    if hours_since_start > 0 and abs(hours_since_start % frequency) <= 0.083:  # 0.083 is 5 minutes in hours
                        # Send hydration reminder
                        send_hydration_reminder(reminder['_id'])
            except Exception as e:
                logger.error(f"Error processing hydration time: {str(e)}")

def run_scheduler():
    """Run the scheduler in a loop."""
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_reminder_scheduler():
    """Start the scheduler to periodically check for reminders."""
    logger.info("Starting reminder scheduler...")
    
    # Schedule checks every 5 minutes
    schedule.every(5).minutes.do(check_reminders)
    
    # Run in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    logger.info("Reminder scheduler started")

if __name__ == "__main__":
    # This allows running the scheduler directly for testing
    start_reminder_scheduler()
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Reminder scheduler stopped") 