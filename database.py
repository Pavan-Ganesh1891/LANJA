from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
import certifi
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize PyMongo (will be configured with the app later)
mongo = PyMongo()

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

def get_direct_mongo_client():
    """Get a direct MongoDB client connection"""
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        # Test the connection
        client.admin.command('ping')
        logger.debug("MongoDB client connection successful")
        return client
    except Exception as e:
        logger.error(f"Error creating MongoDB client: {str(e)}")
        raise

def get_database():
    """Get the MongoDB database instance"""
    try:
        client = get_direct_mongo_client()
        # Extract database name from URI
        db_name = MONGO_URI.split('/')[-1].split('?')[0]
        if not db_name:
            db_name = 'healthchat'  # fallback database name
        logger.debug(f"Using database: {db_name}")
        return client[db_name]
    except Exception as e:
        logger.error(f"Error getting database: {str(e)}")
        raise

class User:
    @staticmethod
    def find_by_email(email):
        """Find a user by email"""
        try:
            db = get_database()
            return db.users.find_one({'email': email})
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None
    
    @staticmethod
    def find_by_id(user_id):
        """Find a user by ID"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            db = get_database()
            return db.users.find_one({"_id": user_id})
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
    
    @staticmethod
    def create(first_name, last_name, email, password):
        """Create a new user"""
        try:
            db = get_database()
            user = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'created_at': datetime.now()
            }
            result = db.users.insert_one(user)
            user['_id'] = result.inserted_id
            logger.info(f"Created new user with email: {email}")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None

class Conversation:
    @staticmethod
    def create(conversation_id, user_id, conversation_data):
        """Create a new conversation"""
        try:
            db = get_database()
            conversation = {
                'conversation_id': conversation_id,
                'user_id': ObjectId(user_id),
                'conversation_data': conversation_data,
                'created_at': datetime.now()
            }
            result = db.conversations.insert_one(conversation)
            conversation['_id'] = result.inserted_id
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return None

    @staticmethod
    def find_by_conversation_id(conversation_id):
        """Find a conversation by its ID"""
        try:
            db = get_database()
            return db.conversations.find_one({'conversation_id': conversation_id})
        except Exception as e:
            logger.error(f"Error finding conversation: {str(e)}")
            return None

    @staticmethod
    def find_all_by_user_id(user_id):
        """Find all conversations for a user"""
        try:
            db = get_database()
            return db.conversations.find({'user_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error finding conversations: {str(e)}")
            return []

class Reminder:
    @staticmethod
    def create(reminder_id, user_id, reminder_data):
        """Create a new reminder"""
        try:
            db = get_database()
            reminder = {
                'reminder_id': reminder_id,
                'user_id': ObjectId(user_id),
                'reminder_data': reminder_data,
                'created_at': datetime.now()
            }
            result = db.reminders.insert_one(reminder)
            reminder['_id'] = result.inserted_id
            return reminder
        except Exception as e:
            logger.error(f"Error creating reminder: {str(e)}")
            return None

    @staticmethod
    def find_by_id(reminder_id):
        """Find a reminder by its ID"""
        try:
            db = get_database()
            return db.reminders.find_one({'_id': ObjectId(reminder_id)})
        except Exception as e:
            logger.error(f"Error finding reminder: {str(e)}")
            return None

    @staticmethod
    def find_all_by_user_id(user_id):
        """Find all reminders for a user"""
        try:
            db = get_database()
            return db.reminders.find({'user_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error finding reminders: {str(e)}")
            return []

    @staticmethod
    def delete(reminder):
        """Delete a reminder"""
        try:
            db = get_database()
            return db.reminders.delete_one({'_id': reminder['_id']})
        except Exception as e:
            logger.error(f"Error deleting reminder: {str(e)}")
            return None

    @staticmethod
    def to_dict(reminder):
        return {
            "id": str(reminder["_id"]),  # Convert _id to string
            "data": reminder["reminder_data"]
        } 