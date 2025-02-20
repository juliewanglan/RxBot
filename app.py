import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload

app = Flask(__name__)
SESSION_ID = "testing"

preloaded_pdfs = [
    "birthcontrol.pdf", 
    "warfarin.pdf",
    "clozapine.pdf", 
    "lexapro.pdf"
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

    print(f"Message from {user} : {message}")

    setup = (
        "You are an AI medical assistant. Answer questions based on the uploaded "
        "prescription and medical report PDFs. If the user asks about side effects, "
        "dosage, or interactions, provide clear and medically accurate responses "
        "from the PDF content.\n"

        "If no question is given, or something irrelevant to the pdfs are given, "
        "explain what your role is as an AI medical assistant, and list the medicines "
        "you have information on based on the uploaded PDFs. Explain to users clearly "
        "what your role is, and let them know what medications you have on file."

        "The medications you currently have on file (and thus can assist with) are: "
        "Birth control, Warfarin, Clozapine, and an antidepressant."
        "If prompted, or if no question is given, tell the user that you can answer "
        "questions on these medicines. Do not answer questions on other medicines "
        "that you have not received documents and information on."
    )

    setup = generate(
        model="4o-mini",
        system="Listen to directions to guide future conversation.",
        query=setup,
        session_id=SESSION_ID,
    )

    # Generate a response using LLMProxy
    response = generate(
        model="4o-mini",
        system="Answer medical questions as a professional assistant using the uploaded PDFs.",
        query=message,
        temperature=0.0,
        lastk=0,
        session_id=SESSION_ID,
        rag_usage=True,
        rag_threshold="0.6",
        rag_k=1
    )

    response_text = response['response']
    
    # Send response back
    print(response_text)

    return jsonify({"text": response_text})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    app.run()