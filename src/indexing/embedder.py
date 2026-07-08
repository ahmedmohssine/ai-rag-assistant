from sentence_transformers import SentenceTransformer


class Embedder:
    """Generates embeddings for text."""

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", cache_folder=None):
        self.model = SentenceTransformer(model_name, cache_folder=cache_folder)

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return self.model.encode(
            texts,
            convert_to_numpy=True
        ).tolist()