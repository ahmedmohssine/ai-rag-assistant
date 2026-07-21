import os
from ollama import Client

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
client = Client(host=OLLAMA_HOST)
from src.generation.prompt_builder import build_rag_prompt


class Generator:

    def generate(self, question: str, context: str) -> str:
        
        answer = ""

        for piece in self.generate_stream(question, context):
            answer += piece 

        return answer

    def generate_stream(self, question: str, context: str):
        prompt = build_rag_prompt(question, context)

        try:
            stream = client.chat(
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
                print("OLLAMA CHUNK:", chunk)

                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception:
            import traceback
            traceback.print_exc()
            raise

    def generate_title(self, question: str) -> str:
        """Generates a concise 2-4 word conversation title from a question using LLM."""
        prompt = (
            f"You are a conversation title generator.\n"
            f"Analyze the following user question and generate a clean, concise, title for the chat room.\n"
            f"Rules:\n"
            f"- Must be between 2 to 4 words max.\n"
            f"- Do NOT wrap it in quotation marks.\n"
            f"- Do NOT include trailing punctuation like periods.\n"
            f"- Return ONLY the title text and nothing else.\n\n"
            f"User Question: {question}\n"
            f"Title:"
        )

        try:
            response = client.chat(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                stream=False,  # Title generation is short; we don't need streaming here
            )
            # Extracted output and stripped potential whitespace or weird formatting quotes
            title = response["message"]["content"].strip().replace('"', '').replace("'", "")
            return title if title else "New Conversation"
        except Exception:
            # Fallback to prevent app crashes if Ollama times out or fails
            return question if len(question) <= 40 else question[:37] + "..."
    
    def rewrite_query(self, question: str, history: list[dict] = None) -> str:
        """
        Rewrites the user's raw question to optimize it for a vector search engine (RAG).
        Resolves conversational context/pronouns using history if provided.
        """
        # Format the chat history context if any exists
        history_context = ""
        if history:
            history_context = "Recent conversation history for context:\n"
            # Take the last 3 turns to keep context brief and fast
            for msg in history[-3:]:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")
                history_context += f"- {role}: {content}\n"

        prompt = (
            f"You are an expert search query optimizer for a RAG system.\n"
            f"Your job is to rewrite the user's latest question to make it optimal for a vector database embedding search.\n\n"
            f"Rules:\n"
            f"1. Strip away conversational filler (e.g., 'please tell me', 'hello', 'can you help me with').\n"
            f"2. Fix syntax errors, typos, or unclear phrasing.\n"
            f"3. If the question uses pronouns like 'it', 'this', or 'they', use the chat history below to replace them with the concrete nouns they refer to.\n"
            f"4. Output ONLY the optimized search keywords or phrase. Do NOT add notes, preambles, or quotes.\n\n"
            f"{history_context}"
            f"Latest User Question: {question}\n"
            f"Optimized Search Query:"
        )

        try:
            response = client.chat(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                stream=False,  # No streaming needed for brief rewrites
            )
            rewritten = response["message"]["content"].strip().replace('"', '').replace("'", "")
            
            # If the LLM returns nothing or fails, safely fall back to the original question
            return rewritten if rewritten else question
        except Exception:
            return question
