import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload

app = Flask(__name__)
SESSION_ID = "testing"

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

    print(f"Message from {user} : {message}")

    setup = (
        "You are to help users understand the uploaded prescriptions. Answer questions based on the uploaded "
        "prescription documents. If the user asks about side effects, "
        "dosage, or interactions, provide clear and medically accurate responses "
        "from the document content.\n"
        
        "The medications you currently have on file (and thus can assist with) are: "
        "Birth control, Warfarin, Valium, and an antidepressant."
        "Prompt the user to ask a question regarding these prescriptions"
        "If prompted for the medications you have information on, or if no question is given, answer with "
        "these medications. Do not answer any questions on anything that is not included "
        "in the uploaded documents. Say that you are not sure and to consult a doctor\n"

        "The user will input their question next. Remember and follow this prompt when answering."
    )

    system_constant = (
        "Let the user know that you are an RxBot to help users understand prescriptions."
        "Prompt the user to ask a question based on the medications that you have "
        "received documentation on: Yaz (birth control), Coumadin (warfarin), "
        "Lexapro (antidepressant), Valium (Diazepam), and Respiridol (risperidone)."
        "Give them examples on what to ask about, such as its use, things to avoid, side effects, "
        "etc. Be thorough."
        "Act helpful to guide users through these prescriptions."
    )

    setup = generate(
        model="4o-mini",
        system=system_constant,
        query=setup,
        session_id=SESSION_ID,
    )

    # Generate a response using LLMProxy
    response = generate(
        model="4o-mini",
        system=system_constant,
        query=message,
        temperature=0.0,
        lastk=0,
        session_id=SESSION_ID,
        rag_usage=True,
        rag_threshold="0.8",
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