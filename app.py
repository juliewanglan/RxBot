import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload

app = Flask(__name__)
SESSION_ID = "testing"
USER_CONTEXT = {}  # Dictionary to store user conversation history

preloaded_pdfs = [
    "birthcontrol.pdf", # yaz (birth control)
    "warfarin.pdf", # coumadin (treat and prevent blood clots)
    "antidepressant.pdf", # lexapro (antidepressant)
    "diazepam.pdf", # valium (can treat anxiety, seizures, muscle spasms)
    "risperidone.pdf" # respiridol (antipsychotic)
]

for pdf in preloaded_pdfs:
    upload = pdf_upload(
        path = pdf,
        session_id=SESSION_ID,
        strategy = 'smart')


@app.route('/')
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    data = request.get_json() 

    # Extract relevant information
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    print(data)

    # Ignore bot messages
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})
    
    # Initialize user context if not present
    if user not in USER_CONTEXT:
        USER_CONTEXT[user] = []
        system_constant = (
                """
                Let the user know that you are an RxBot to help users understand prescriptions
                and understand symptoms that they are experiencing with their prescriptions.
                Prompt the user to ask a question and give thier experience based on the medications that you have 
                received documentation on: Yaz (birth control), Coumadin (warfarin), 
                Lexapro (antidepressant), Valium (Diazepam), and Respiridol (risperidone).
                Give them examples on what to ask about, such as its use, things to avoid, side effects, 
                etc. Be thorough.
                Prompt the user to tell you how the medication is making them feel or other symptoms.
                Act helpful to guide users through these prescriptions.
                """
            )
    else:
        system_constant = (
            """
            You are an RxBot that provides medication information. You are looking
            to see if users have any symptoms with their medication
            You should only interact with moedications that you have received
            documentation on: Yaz (birth control), Coumadin (warfarin), 
            Lexapro (antidepressant), Valium (Diazepam), and Respiridol (risperidone).
            Do not regreet the user. You guys have already spoke.
            """
        )
    print(f"Message from {user} : {message}")

    # # Limit conversation history to last 5 messages
    # USER_CONTEXT[user] = USER_CONTEXT[user][-5:]

    # Generate chatbot response with context
    context = "\n".join(USER_CONTEXT[user])
    response = generate(
        model="4o-mini",
        system=system_constant,
        query=f"Previous conversation:\n{context}\nUser: {message}",
        temperature=0.0,
        lastk=0,
        session_id=SESSION_ID,
        rag_usage=True,
        rag_threshold=0.8,
        rag_k=1
    )

    response_text = response['response']
    
    # Send response back
    print(response_text)
    # Append user message to history
    USER_CONTEXT[user].append(f"User: {message}, Response:{response_text}")

    return jsonify({"text": response_text})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()