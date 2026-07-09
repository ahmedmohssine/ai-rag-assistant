from judge import LLMjudge

judge = LLMjudge()
question = "What is FastAPI and why is it used for building Python APIs?"
context = "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints. It is used because it provides automatic interactive documentation, native asynchronous support, standard validation via Pydantic, and performance on par with NodeJS and Go."
expected_answer = "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints. It is used because it provides automatic interactive documentation, native asynchronous support, standard validation via Pydantic, and performance on par with NodeJS and Go."
generated_answer = "FastAPI is a modern Python web framework for building APIs. It generates a \"schema\" with all your API using the OpenAPI standard for defining APIs. FastAPI is used for building Python APIs because it provides a simple and efficient way to create web applications with high performance and scalability."


scores = judge.evaluate(
    question,
    context,
    expected_answer,
    generated_answer,
)
print(scores)