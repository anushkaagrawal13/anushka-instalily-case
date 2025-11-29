# app.py

import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from appliance_agent import appliance_agent

app = Flask(__name__)
CORS(app)

sessions = {} # in memory store of session ID

# logging config
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/chat', methods=['POST'])
def chat():
    """
    main chatbot endpoint. 

    Expects JSON: {"message": "<user's question>", "session_id": "<optional>"}
    Returns JSON: {"response": "<chatbot answer>", "session_id": "<returned or existing>"}
    """
    try:
        logger.info("Received chat request")
        data = request.get_json()
        logger.debug(f"Request data: {data}")



        user_query = data.get('message', '').strip()
        if not user_query:
            logger.warning("No query provided in request")
            return jsonify({"response": "No query provided"}), 400

        logger.info(f"Processing query: {user_query}")
        response_data = appliance_agent.process_query(user_query)
        
        if isinstance(response_data, dict) and 'response' in response_data:
          response_text = response_data['response']
          response_text = response_text.replace('•', '\n--')  # convert bullets to proper Markdown
          response_data['response'] = response_text

        logger.info("Sending to frontend: %s", response_data)
        
        if isinstance(response_data, dict):
            if 'response' not in response_data:
                response_data['response'] = str(response_data)
            return jsonify(response_data)
        else:
            return jsonify({"response": str(response_data)})

    except Exception as e:
        logger.exception("Error in chat endpoint")
        error_msg = str(e)
        logger.error(f"Sending error response: {error_msg}")
        return jsonify({"response": f"Error: {error_msg}"}), 500

if __name__ == '__main__':
    # Flask dev server
    app.run(host='0.0.0.0', port=5001, debug=True)