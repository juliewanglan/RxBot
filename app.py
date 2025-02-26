import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from agent_tools import send_email

app = Flask(__name__)
SESSION_ID = "testing"
USER_CONTEXT = {}  # Dictionary to store user conversation history
USER_SYMPTOMS = {}  # Dictionary to track symptoms per user

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
        USER_SYMPTOMS[user] = None
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
            You have already spoke with this user. Take note of the context in
            the query.
            Prompt the user to type "conversation done" if they are finished.
            """
        )
    print(f"Message from {user} : {message}")

    USER_CONTEXT[user].append(f"User: {message}")
    USER_CONTEXT[user] = USER_CONTEXT[user][-5:]

    # Generate chatbot response with context
    context = "\n".join(USER_CONTEXT[user])

    if "conversation done" in message.lower():
        symptom_response = generate(
            model="4o-mini",
            system= (
                """
                You are an assistant that drafts symptom report emails based on user conversations.
                Identify the user's symptoms, link them to medications, and format the response as a clear, concise email.
                Only respond with the email body, without extra commentary.
                """
            ),
            query=f"Analyze the following conversation, extract possible symptoms, and generate an email:\n{context}",
            temperature=0.0,
            lastk=0,
            session_id="symptoms"
        )
        
        symptom_text = symptom_response['response']
        if symptom_text and symptom_text.strip():
            USER_SYMPTOMS[user] = symptom_text
            return jsonify({"text": "Would you like to send the following symptom report to your doctor? Reply 'yes' to confirm.\n\n" + symptom_text})
        else:
            return jsonify({"text": "No symptoms were detected."})
        
    response = generate(
        model="4o-mini",
        system=system_constant,
        query=f"Previous conversation:\n{context}User: {message}",
        temperature=0.0,
        lastk=0,
        session_id=SESSION_ID,
        rag_usage=True,
        rag_threshold=0.8,
        rag_k=1
    )
    response_text = response['response']
    USER_CONTEXT[user].append(f"RxBot Response:{response_text}")


    if "yes" in message.lower() and user in USER_SYMPTOMS and USER_SYMPTOMS[user]:
        doctor_email = "juliewanglan@gmail.com"  # Replace with actual doctor email
        send_email("juliewanglan@gmail.com", doctor_email, "Patient Symptom Report", USER_SYMPTOMS[user])
        USER_SYMPTOMS[user] = None
        return jsonify({"text": "Your symptoms have been sent to your doctor."})

    return jsonify({"text": response_text})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()