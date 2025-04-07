import cohere
from typing import Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use the API key directly
cohere_client = cohere.Client('pGdW2vRcRYnh8PKvJoZ5Slm8j0p1ZNHHw8bYVQTo')
max_response_tokens = 150  # Adjust for shorter or longer responses

def generate_medical_response(user_responses: Dict[str, str]) -> str:
    # Create a structured prompt from user responses
    prompt = f"""
Based on the following patient information:
- Symptoms: {user_responses.get('symptoms', 'Not provided')}
- Recent Medicines: {user_responses.get('recent-medicines', 'None')}
- Long-term Conditions: {user_responses.get('long-term-conditions', 'No')}
{f"- Condition Details: {user_responses.get('conditions-details')}" if user_responses.get('conditions-details') else ''}

Please provide a concise medical analysis with:
1. Brief assessment of symptoms
2. Whether immediate medical attention is needed
3. General recommendations

Answer (concise):
"""

    try:
        logger.info("Sending request to Cohere generate API")
        result = cohere_client.generate(
            model='command',
            prompt=prompt,
            max_tokens=max_response_tokens,
            temperature=0.3,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE'
        )
        logger.info("Successfully received response from Cohere API")
        return result.generations[0].text.strip()
    except Exception as e:
        logger.error(f"Error calling Cohere API: {str(e)}")
        return f"I apologize, but I'm unable to provide a response at the moment. Please consult with a healthcare provider for medical advice." 

def handle_followup_question(question: str, previous_responses: Dict[str, str]) -> str:
    prompt = f"""
Context - Patient with following information:
- Symptoms: {previous_responses.get('symptoms', 'Not provided')}
- Recent Medicines: {previous_responses.get('recent-medicines', 'None')}
- Long-term Conditions: {previous_responses.get('long-term-conditions', 'No')}
{f"- Condition Details: {previous_responses.get('conditions-details')}" if previous_responses.get('conditions-details') else ''}

Question: {question}

Provide a concise and helpful answer based on the medical context above:
"""

    try:
        logger.info("Sending follow-up request to Cohere generate API")
        result = cohere_client.generate(
            model='command',
            prompt=prompt,
            max_tokens=max_response_tokens,
            temperature=0.3,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE'
        )
        logger.info("Successfully received follow-up response from Cohere API")
        return result.generations[0].text.strip()
    except Exception as e:
        logger.error(f"Error calling Cohere API for follow-up: {str(e)}")
        return f"I apologize, but I'm unable to provide a response at the moment. Please consult with a healthcare provider for medical advice." 