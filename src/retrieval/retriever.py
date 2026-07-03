class Retriever:
    """A class that retrieves relevant documents based on a query."""
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question, top_k=5):
        query = self.embedder.embed(question)
        return self.store.search(query, top_k)