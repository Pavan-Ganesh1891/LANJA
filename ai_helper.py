import cohere
from typing import Dict
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Cohere client with API key
COHERE_API_KEY = os.getenv('COHERE_API_KEY', 'pGdW2vRcRYnh8PKvJoZ5Slm8j0p1ZNHHw8bYVQTo')
cohere_client = cohere.Client(COHERE_API_KEY)

def generate_medical_response(user_input):
    """
    Generate an AI response based on user input while maintaining appropriate conversation boundaries.
    """
    try:
        # Generate response using Cohere API
        response = cohere_client.chat(
            message=user_input,
            preamble="""You are a helpful AI health assistant. You provide general health information and guidance while being clear that you are not a substitute for professional medical advice. Keep your responses concise and focused.""",
            temperature=0.7,
            max_tokens=150
        )
        return response.text
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return ("I apologize, but I'm having trouble processing your request. "
                "Could you please try again or rephrase your question?")

def handle_followup_question(question, previous_responses):
    """
    Handle follow-up questions while maintaining conversation boundaries.
    """
    try:
        # Format conversation history
        conversation_history = "\n".join([f"Previous response: {resp}" for resp in previous_responses])
        
        # Generate response using Cohere API with conversation context
        response = cohere_client.chat(
            message=question,
            preamble=f"""You are a helpful AI health assistant. You provide general health information and guidance while being clear that you are not a substitute for professional medical advice. Keep your responses concise and focused.

Previous conversation:
{conversation_history}""",
            temperature=0.7,
            max_tokens=150
        )
        return response.text
    except Exception as e:
        logger.error(f"Error generating follow-up response: {str(e)}")
        return ("I apologize, but I'm having trouble processing your request. "
                "Could you please try again or rephrase your question?") 