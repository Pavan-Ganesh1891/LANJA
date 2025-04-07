import os
import csv
import hashlib

# Set up the CSV file path for user data
USER_DB_FILE = 'user_database.csv'

# Create users CSV file if it doesn't exist
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        # Create CSV with user columns
        with open(USER_DB_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['firstName', 'lastName', 'email', 'password'])
        print(f"Created new user database at {USER_DB_FILE}")

# Hash password for secure storage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Find user by email
def find_user_by_email(email):
    if not os.path.exists(USER_DB_FILE):
        return None
    
    with open(USER_DB_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for user in reader:
            if user['email'] == email:
                return user
    return None

# Register a new user
def register_user(first_name, last_name, email, password):
    # Check if email already exists
    if find_user_by_email(email):
        return False, "Email already registered"
    
    try:
        # Hash password for storage
        hashed_password = hash_password(password)
        
        # Add new user to CSV
        with open(USER_DB_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([first_name, last_name, email, hashed_password])
        
        return True, None
    except Exception as e:
        print(f"Registration error: {e}")
        return False, "An error occurred during registration"

# Authenticate user
def authenticate_user(email, password):
    try:
        user = find_user_by_email(email)
        
        if user and user['password'] == hash_password(password):
            return True, user
        else:
            return False, "Invalid email or password"
    except Exception as e:
        print(f"Authentication error: {e}")
        return False, "An error occurred during authentication"

# Get all users (for admin)
def get_all_users():
    users = []
    
    if not os.path.exists(USER_DB_FILE):
        return users
    
    with open(USER_DB_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for user in reader:
            # Create a copy without the password
            safe_user = {
                'firstName': user['firstName'],
                'lastName': user['lastName'],
                'email': user['email']
            }
            users.append(safe_user)
    
    return users

# Get user by email (for reminders)
def get_user_by_email(email):
    # Reuse the find_user_by_email function but return a safe user (no password)
    user = find_user_by_email(email)
    if user:
        return {
            'firstName': user['firstName'],
            'lastName': user['lastName'],
            'email': user['email']
        }
    return None 