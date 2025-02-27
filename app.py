import os
import requests
from flask import Flask, request, jsonify
from llmproxy import generate

app = Flask(__name__)

RC_URL = "https://chat.genaiconnect.net/api/v1/chat.postMessage"
RC_HEADERS = {
    "Content-Type": "application/json",
    "X-Auth-Token": os.environ.get("RC_token"),
    "X-User-Id": os.environ.get("RC_userId")
}

# Define agents

def symptom_extraction_agent(message, session_id):
    """Extract symptoms from user messages."""
    symptom_prompt = (
        "Extract any symptoms from the following message. "
        "Return only the symptoms as a comma-separated list: " + message
    )
    response = generate(
        model="4o-mini",
        system="You are a medical assistant specializing in symptom extraction.",
        query=symptom_prompt,
        temperature=0.0,
        lastk=10,
        session_id=session_id
    )
    return response.get('response', '').strip()

def medical_analysis_agent(symptoms, session_id):
    """Analyze symptoms and provide a medical response."""
    analysis_prompt = (
        f"The user reported these symptoms: {symptoms}. "
        "Analyze these symptoms as a doctor would, provide medical insights, "
        "possible causes, and recommended actions."
    )
    response = generate(
        model="4o-mini",
        system="You are a virtual doctor providing medical advice based on reported symptoms.",
        query=analysis_prompt,
        temperature=0.0,
        lastk=10,
        session_id=session_id
    )
    return response.get('response', '').strip()

def send_message_to_julie(summary):
    """Send a message to Julie via Rocket.Chat."""
    payload = {
        "channel": "@julie.wang",
        "text": summary
    }
    requests.post(RC_URL, json=payload, headers=RC_HEADERS)

@app.route('/', methods=['POST'])
def main():
    data = request.get_json()
    user = data.get("user_name", "Unknown")
    message = data.get("text", "").strip()
    
    # Ignore bot messages or empty input
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    # Create session ID based on user conversation
    conversation_id = data.get("channel_id", data.get("conversation_id", data.get("chat_id", "default")))
    session_id = f"{conversation_id}_{user}"
    print(f"Processing request for session_id: '{session_id}'")
    
    # Prompt user to say "conversation done" to end
    response = generate(
        model="4o-mini",
        system="You are a virtual doctor providing helpful medical advice based on symptoms. "
               "When you feel the conversation is nearing an end, prompt the user to say 'conversation done' "
               "to summarize and finalize the interaction.",
        query=message,
        temperature=0.0,
        lastk=10,
        session_id=session_id
    )
    
    response_text = response.get('response', '')
    
    if "conversation done" in message.lower():
        symptoms = symptom_extraction_agent(message, session_id)
        if symptoms:
            analysis = medical_analysis_agent(symptoms, session_id)
            send_message_to_julie(f"User {user} has completed their conversation. Summary:\n{analysis}")
            return jsonify({"text": "A summary has been sent to Julie."})
        return jsonify({"text": "No symptoms were detected."})
    
    return jsonify({"text": response_text})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run(debug=True)