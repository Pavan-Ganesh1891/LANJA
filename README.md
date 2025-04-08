# HealthChat

A health chat application that allows users to have conversations with an AI about their health concerns, set reminders for medications and hydration, and manage their health information.

## Features

- User authentication (login/register)
- AI-powered health conversations
- Medication and hydration reminders
- Email notifications for reminders
- Conversation history

## Setup with MongoDB Database

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- MongoDB (local installation or MongoDB Atlas account)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd HealthChat
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the `.env` file with your MongoDB connection string:
     ```
     MONGO_URI=mongodb://localhost:27017/healthchat
     ```
     For MongoDB Atlas:
     ```
     MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/healthchat
     ```
   - Update other environment variables as needed

4. Initialize the database:
   ```
   python init_db.py
   ```

5. Run the application:
   ```
   python app.py
   ```

## MongoDB Setup

### Local MongoDB Setup
1. Install MongoDB from [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
2. Start the MongoDB service
3. Use the connection string: `mongodb://localhost:27017/healthchat`

### MongoDB Atlas Setup
1. Create a MongoDB Atlas account at [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (the free tier is sufficient for starting)
3. Create a database user with appropriate permissions
4. Get your connection string from the Atlas dashboard
5. Update your `.env` file with the connection string

## Environment Variables

- `MONGO_URI`: MongoDB connection string
- `EMAIL_HOST`: SMTP server hostname
- `EMAIL_PORT`: SMTP server port
- `EMAIL_USER`: Email account username
- `EMAIL_PASSWORD`: Email account password
- `EMAIL_FROM`: Sender email address
- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `FLASK_ENV`: Flask environment (development/production)

## License

[MIT License](LICENSE) 