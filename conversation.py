import os
import csv
import json
from datetime import datetime

# File for storing conversations
CONVERSATIONS_FILE = 'conversations.csv'

def init_conversations_db():
    """Initialize the conversations database if it doesn't exist."""
    if not os.path.exists(CONVERSATIONS_FILE):
        with open(CONVERSATIONS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'timestamp', 'conversation_id', 'conversation_data'])
        print(f"Created new conversations database at {CONVERSATIONS_FILE}")

def save_conversation(user_email, conversation_data, conversation_id=None):
    """Save a conversation to the CSV file.
    
    Args:
        user_email: Email of the user (used as user_id)
        conversation_data: Dictionary containing the conversation data
        conversation_id: ID of the conversation to update, or None for a new conversation
    
    Returns:
        str: The conversation ID
    """
    # Initialize if file doesn't exist
    if not os.path.exists(CONVERSATIONS_FILE):
        init_conversations_db()
    
    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = f"{user_email}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Serialize conversation data to JSON
    conversation_json = json.dumps(conversation_data)
    
    # Get current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # If conversation exists, update it
    if conversation_id:
        # Read all conversations
        conversations = []
        found = False
        with open(CONVERSATIONS_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Skip header row
            for row in reader:
                if len(row) >= 4 and row[2] == conversation_id:
                    # Update existing conversation
                    conversations.append([user_email, timestamp, conversation_id, conversation_json])
                    found = True
                else:
                    conversations.append(row)
        
        # If conversation not found, append it
        if not found:
            conversations.append([user_email, timestamp, conversation_id, conversation_json])
        
        # Write all conversations back to file
        with open(CONVERSATIONS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'timestamp', 'conversation_id', 'conversation_data'])
            writer.writerows(conversations)
    else:
        # Append new conversation
        with open(CONVERSATIONS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([user_email, timestamp, conversation_id, conversation_json])
    
    return conversation_id

def get_user_conversations(user_email):
    """Get all conversations for a user.
    
    Args:
        user_email: Email of the user
    
    Returns:
        list: List of conversation data dictionaries with metadata
    """
    conversations = []
    
    if not os.path.exists(CONVERSATIONS_FILE):
        return conversations
    
    with open(CONVERSATIONS_FILE, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) >= 4 and row[0] == user_email:
                try:
                    conversation_data = json.loads(row[3])
                    conversations.append({
                        'conversation_id': row[2],
                        'timestamp': row[1],
                        'data': conversation_data
                    })
                except json.JSONDecodeError:
                    continue
    
    # Sort conversations by timestamp (newest first)
    conversations.sort(key=lambda x: x['timestamp'], reverse=True)
    return conversations

def get_conversation(conversation_id):
    """Get a specific conversation by ID.
    
    Args:
        conversation_id: ID of the conversation
    
    Returns:
        dict: Conversation data or None if not found
    """
    if not os.path.exists(CONVERSATIONS_FILE):
        return None
    
    with open(CONVERSATIONS_FILE, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) >= 4 and row[2] == conversation_id:
                try:
                    return {
                        'user_id': row[0],
                        'timestamp': row[1],
                        'conversation_id': row[2],
                        'data': json.loads(row[3])
                    }
                except json.JSONDecodeError:
                    return None
    
    return None 