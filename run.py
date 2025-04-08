import os
from app import app, init_db_indexes, verify_mongodb_connection
from reminder_sender import start_reminder_scheduler
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Verify MongoDB connection
    if not verify_mongodb_connection():
        print("Error: Could not connect to MongoDB. Please check your connection string and try again.")
        sys.exit(1)
    
    # Initialize database indexes
    if not init_db_indexes():
        print("Error: Could not initialize database indexes. Please check your MongoDB connection and try again.")
        sys.exit(1)
    
    # Start the reminder scheduler in a background thread
    start_reminder_scheduler()
    
    # Run the Flask application
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting HealthChat with MongoDB Atlas on {host}:{port}")
    print(f"Debug mode: {'On' if debug else 'Off'}")
    
    app.run(host=host, port=port, debug=debug) 