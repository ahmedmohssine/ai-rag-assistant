from ollama import chat

from src.generation.prompt_builder import build_rag_prompt


class Generator:

    def generate(self, question: str, context: str) -> str:
        
        answer = ""

        for piece in self.generate_stream(question, context):
            answer += piece 

        return answer

    def generate_stream(self, question: str, context: str):
        prompt = build_rag_prompt(question, context)

        stream = chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )

        for chunk in stream:
            yield chunk["message"]["content"]