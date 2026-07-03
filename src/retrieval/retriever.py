class Retriever:
    """A class that retrieves relevant documents based on a query."""
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, top_k: int = 5):
        query_embedding = self.embedder.embed(question)
        return self.store.search(query_embedding, top_k)