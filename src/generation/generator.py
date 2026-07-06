from ollama import chat

from src.generation.prompt_builder import build_rag_prompt


class Generator:
    def generate(self, question: str, context: str) -> str:
        prompt = build_rag_prompt(question, context)

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
