import requests

url = "http://localhost:11434/api/chat"

questions = [
    "Who is the current president of the United States?",
    "What is the capital of the United States?",
    "Explain to me what Python is."
]

messages = [{"role": "system", "content": "You are a helpful assistant."}]

for question in questions:
    messages.append({"role": "user", "content": question})

    response = requests.post(url, json={
        "model": "qwen2.5:0.5b",
        "messages": messages,
        "stream": False
    })

    reply = response.json()["message"]["content"]
    print(f"Question: {question}")
    print("AI:", reply)
    print("-" * 40)

    messages.append({"role": "assistant", "content": reply})