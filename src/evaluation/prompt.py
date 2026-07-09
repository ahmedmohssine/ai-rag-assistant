def build_prompt(
    question,
    context,
    expected_answer,
    generated_answer,
):
    return f"""
You are an expert RAG evaluator.

Only use the retrieved context.
Never use outside knowledge.

Question:
{question}

Retrieved Context:
{context}

Expected Answer:
{expected_answer}

Generated Answer:
{generated_answer}

Evaluate:

Faithfulness measures whether the generated answer is supported by the retrieved context.

A score of 5 does NOT require identical wording.

Give:

Faithfulness
5 = Every important claim is supported by the retrieved context.
4 = One minor unsupported detail.
3 = Some unsupported details, but the main answer is supported.
2 = Several important claims are unsupported.
1 = Mostly unsupported.
0 = Contradicts the retrieved context.

Correctness
5 = Fully answers the question correctly.
4 = Minor mistake.
3 = Partially correct.
2 = Significant mistakes.
1 = Mostly incorrect.
0 = Completely wrong.

Relevance
5 = Directly answers the question.
4 = Mostly relevant.
3 = Somewhat relevant.
2 = Barely relevant.
1 = Mostly off-topic.
0 = Completely irrelevant.

Hallucination is TRUE only if the answer contains factual claims that cannot reasonably be inferred from the retrieved context.

General wording differences are NOT hallucinations.
Background knowledge that changes the meaning IS hallucination.

Return ONLY valid JSON.

{{
    "faithfulness": 0,
    "correctness": 0,
    "relevance": 0,
    "hallucination": false,
    "reason": "..."
}}
If the generated answer contains information that is not supported by the retrieved context, reduce the faithfulness score.

If the retrieved context is insufficient to answer the question, the correct answer is "I don't know."

Do not explain your reasoning outside the JSON.

The "reason" field is REQUIRED.
"""