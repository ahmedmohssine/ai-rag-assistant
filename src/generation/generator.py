from ollama import chat


class Generator:
    def generate(self, question: str, context: str) -> str:

        prompt = f"""
You are an AI Developer Assistant.

Answer ONLY using the documentation below.

If the documentation doesn't contain the answer, reply:

"I don't know based on the provided documentation."

Documentation:
{context}

Question:
{question}

Answer:
"""

        response = chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response["message"]["content"]