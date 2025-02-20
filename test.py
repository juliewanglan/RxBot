import requests

response_main = requests.get("https://colossal-auroora-juliewang-983c2b9b.koyeb.app/")
print('Web Application Response:\n', response_main.text, '\n\n')


data = {"text":"tell me about tufts"}
response_llmproxy = requests.post("https://colossal-auroora-juliewang-983c2b9b.koyeb.app/query", json=data)
print('LLMProxy Response:\n', response_llmproxy.text)
