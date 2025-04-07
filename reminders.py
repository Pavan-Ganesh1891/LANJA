import csv
import os
import json
from datetime import datetime
import uuid

REMINDERS_DB_FILE = 'reminders_database.csv'

def init_reminders_db():
    """Initialize the reminders database if it doesn't exist."""
    if not os.path.exists(REMINDERS_DB_FILE):
        with open(REMINDERS_DB_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'user_id', 'data'])

def save_reminder(user_id, reminder_data, reminder_id=None):
    """Save a reminder to the database.
    
    Args:
        user_id: The user's email
        reminder_data: Dictionary containing reminder data
        reminder_id: Optional ID if updating an existing reminder
    
    Returns:
        The ID of the saved reminder
    """
    # Generate a new ID if not provided
    if not reminder_id:
        reminder_id = str(uuid.uuid4())
    
    # Read existing reminders
    reminders = []
    if os.path.exists(REMINDERS_DB_FILE):
        with open(REMINDERS_DB_FILE, 'r', newline='') as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip header
            reminders = list(reader)
    
    # Find if reminder already exists
    reminder_exists = False
    for i, reminder in enumerate(reminders):
        if reminder[0] == reminder_id:
            # Update existing reminder
            reminders[i] = [reminder_id, user_id, json.dumps(reminder_data)]
            reminder_exists = True
            break
    
    # If reminder doesn't exist, add it
    if not reminder_exists:
        reminders.append([reminder_id, user_id, json.dumps(reminder_data)])
    
    # Write back to file
    with open(REMINDERS_DB_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'user_id', 'data'])
        writer.writerows(reminders)
    
    return reminder_id

def delete_reminder(reminder_id, user_id):
    """Delete a reminder from the database.
    
    Args:
        reminder_id: The ID of the reminder to delete
        user_id: The user's email (for security check)
    
    Returns:
        Boolean indicating success
    """
    if not os.path.exists(REMINDERS_DB_FILE):
        return False
    
    reminders = []
    deleted = False
    
    with open(REMINDERS_DB_FILE, 'r', newline='') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header
        for reminder in reader:
            if reminder[0] == reminder_id and reminder[1] == user_id:
                deleted = True
            else:
                reminders.append(reminder)
    
    if deleted:
        with open(REMINDERS_DB_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'user_id', 'data'])
            writer.writerows(reminders)
    
    return deleted

def get_user_reminders(user_id):
    """Get all reminders for a user.
    
    Args:
        user_id: The user's email
    
    Returns:
        List of reminder dictionaries
    """
    if not os.path.exists(REMINDERS_DB_FILE):
        return []
    
    reminders = []
    
    with open(REMINDERS_DB_FILE, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if row[1] == user_id:
                reminder = {
                    'id': row[0],
                    'data': json.loads(row[2])
                }
                reminders.append(reminder)
    
    return reminders

def get_reminder(reminder_id):
    """Get a specific reminder by ID.
    
    Args:
        reminder_id: The ID of the reminder
    
    Returns:
        Reminder dictionary or None if not found
    """
    if not os.path.exists(REMINDERS_DB_FILE):
        return None
    
    with open(REMINDERS_DB_FILE, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if row[0] == reminder_id:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'data': json.loads(row[2])
                }
    
    return None 