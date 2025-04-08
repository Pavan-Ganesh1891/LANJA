from database import get_database
from dotenv import load_dotenv
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def reset_password():
    try:
        # Connect to database
        db = get_database()
        users = db.users
        
        # User credentials
        email = "FWEQ@gmail.com"
        new_password = "123"
        hashed_password = hash_password(new_password)
        
        # Update user's password
        result = users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )
        
        if result.modified_count > 0:
            print(f"Successfully updated password for user: {email}")
            print(f"New password hash: {hashed_password}")
        else:
            print(f"No user found with email: {email}")
            
    except Exception as e:
        print(f"Error resetting password: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    reset_password() 