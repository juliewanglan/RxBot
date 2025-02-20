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
    file = data.get("attachments", [{}])[0].get("file", {})

    print(data)

    # Ignore bot messages
    if data.get("bot") or not (message or file):
        return jsonify({"status": "ignored"})
    
    if file:
        file_url = file.get("url")
        file_name = file.get("name")

        if file_url and file_name:
            print(f"Processing uploaded PDF: {file_name}")

            # receive pdf
            pdf_response = requests.get(file_url)
            
            if pdf_response.status_code == 200:
                with open(file_name, "wb") as f:
                    f.write(pdf_response.content)

                # upload PDF
                pdf_upload(path=file_name, session_id=SESSION_ID, strategy="smart")

                # prompt to summarize prescription
                summary_prompt = (
                    "Summarize the uploaded prescription document. Include key details such as:\n"
                    "- Medication Name\n"
                    "- Dosage Instructions\n"
                    "- Common Side Effects\n"
                    "- Major Warnings or Interactions\n"
                    "Provide a clear, patient-friendly summary."

                    "If the uploaded document is not a prescription, do not summarize "
                    "it and ask for a prescription file instead."
                )

                summary_response = generate(
                    model="4o-mini",
                    system="Summarize the document for a general audience.",
                    query=summary_prompt,
                    session_id=SESSION_ID,
                    rag_usage=True,
                    rag_threshold="0.8",
                    rag_k=1
                )

                summary_text = summary_response["response"]

                print(summary_text)
                
                return jsonify({
                    "text": "Summary of uploaded prescription: {summary_text}"
                })

            return jsonify({"text": "Failed to download PDF. Please try again."})

    if message:
        print(f"Message from {user} : {message}")

        setup = (
            "You are an AI medical assistant. Answer questions based on the uploaded "
            "prescription and medical report PDFs. If the user asks about side effects, "
            "dosage, or interactions, provide clear and medically accurate responses "
            "from the PDF content.\n"
            
            "The medications you currently have on file (and thus can assist with) are: "
            "Birth control, Warfarin, Valium, and an antidepressant."
            "If prompted for the medications you have information on, or if no question is given, answer with "
            "these medicines. Do not answer any questions on anything that is not included "
            "in the uploaded documents. Say that you are not sure and to consult a doctor\n"

            "I will input the user's question next. Remember and follow this prompt when answering."
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