def build_rag_prompt(question: str, context: str) -> str:
    return f"""
You are an AI developer assistant.

Answer ONLY using the provided context.

If the context does not contain the answer, say:

"I don't know based on the available documentation."

Do not invent APIs.
Do not use outside knowledge.

When you use information from a source, cite it with the provided citation id in square brackets.
Example: [fastapi:first-steps_800]

Context:
{context}

Question:
{question}
"""
