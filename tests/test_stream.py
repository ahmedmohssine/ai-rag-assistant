from ollama import chat

stream = chat(
    model="llama3.2:3b",
    messages=[
        {
            "role": "user",
            "content": "Count from 1 to 20 slowly.",
        }
    ],
    stream=True,
)

for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)