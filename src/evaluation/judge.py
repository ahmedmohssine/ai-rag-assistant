import os
import json
from ollama import Client

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
client = Client(host=OLLAMA_HOST)

from src.evaluation.prompt import build_prompt



class LLMjudge:
    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model

    def evaluate(
            self,
            question: str,
            context: str,
            expected_answer: str,
            generated_answer: str,
        ) -> dict:

            prompt = build_prompt(
                question=question,
                context=context,
                expected_answer=expected_answer,
                generated_answer=generated_answer,
            )

            response = client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                format="json",
            )

            output = response["message"]["content"]

            try:
                return json.loads(output)

            except json.JSONDecodeError:
                return {
                    "faithfulness": 0,
                    "correctness": 0,
                    "relevance": 0,
                    "hallucination": True,
                    "reason": "Judge returned invalid JSON."
                }
            