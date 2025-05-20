from flask import Flask, request, jsonify
from flask_cors import CORS
from chat import get_gemini_response  # This should exist in main.py

app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        if not user_input:
            return jsonify({"response": "No message provided."}), 400
        ai_response = get_gemini_response(user_input)
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)