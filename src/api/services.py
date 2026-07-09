import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.indexing.embedder import Embedder
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever
from src.retrieval.reranker import CrossEncoderReranker
from src.generation.generator import Generator


class RAGService:

    def __init__(self):

        self.embedder = Embedder()
        self.store = VectorStore()
        self.generator = Generator()

        use_reranker = os.getenv("USE_RERANKER", "").lower() in {
            "1",
            "true",
            "yes",
        }

        reranker = CrossEncoderReranker() if use_reranker else None

        self.retriever = Retriever(
            self.embedder,
            self.store,
            reranker=reranker,
        )


rag = RAGService()