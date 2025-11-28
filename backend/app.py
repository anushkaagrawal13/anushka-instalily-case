# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from agent_manager import agent_manager

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    """
    main chatbot endpoint. 
    
    Expects JSON: {"message": "<user's question>", "session_id": "<optional>"}
    Returns JSON: {"response": "<chatbot answer>", "session_id": "<returned or existing>"}
    """
    try:
        logger.info("📥 Received chat request")
        data = request.get_json()
        logger.debug(f"Request data: {data}")

        user_query = data.get('message', '').strip()
        if not user_query:
            logger.warning("No query provided in request")
            return jsonify({"response": "No query provided"}), 400

        # Get response from agent
        logger.info(f"🤖 Processing query: {user_query}")
        response_data = agent_manager.handle_query(user_query, {})
        
        # Log the actual response being sent
        logger.info("📤 Sending to frontend: %s", response_data)
        
        # Ensure we're sending a properly formatted response
        if isinstance(response_data, dict):
            # Make sure we have the 'response' key
            if 'response' not in response_data:
                response_data['response'] = str(response_data)
            return jsonify(response_data)
        else:
            # If response_data is not a dict, wrap it
            return jsonify({"response": str(response_data)})

    except Exception as e:
        logger.exception("Error in chat endpoint")
        error_msg = str(e)
        logger.error(f"Sending error response: {error_msg}")
        return jsonify({"response": f"Error: {error_msg}"}), 500

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Flask dev server
    app.run(host='0.0.0.0', port=5001, debug=True)