import unittest

from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever


class RetrieverTests(unittest.TestCase):
    def test_document_bonus_uses_metadata_tokens(self):
        retriever = Retriever(embedder=None, store=None)
        metadata = {
            "title": "First Steps",
            "filename": "first-steps.md",
            "path": "docs/fastapi/tutorial/first-steps.md",
            "relative_path": "fastapi/tutorial/first-steps.md",
        }

        bonus = retriever._document_bonus("How do I create a FastAPI app?", metadata)

        self.assertGreater(bonus, 0.0)

    def test_document_key_prefers_path_metadata(self):
        retriever = Retriever(embedder=None, store=None)
        candidate = {"id": "chunk-1", "metadata": {"path": "docs/fastapi/tutorial/first-steps.md"}}

        self.assertEqual(retriever._document_key(candidate), "docs/fastapi/tutorial/first-steps.md")

    def test_path_matches_question_with_key_terms(self):
        retriever = Retriever(embedder=None, store=None)

        self.assertTrue(retriever._path_matches_question("How do I install FastAPI?", "docs/fastapi/tutorial/index.md"))

    def test_metadata_relevance_prefers_tutorial_for_how_to_questions(self):
        retriever = Retriever(embedder=None, store=None)
        metadata = {"path": "docs/fastapi/tutorial/index.md", "title": "Tutorial", "filename": "index.md"}

        score = retriever._metadata_relevance_score("How do you install FastAPI in a Python environment?", metadata)

        self.assertGreater(score, 0.0)

    def test_embedding_text_includes_title_and_path(self):
        store = VectorStore.__new__(VectorStore)
        chunk = {
            "title": "FastAPI",
            "content": "A modern web framework for building APIs.",
            "path": "docs/fastapi/reference/fastapi.md",
            "filename": "fastapi.md",
        }

        embedding_text = store._document_text_for_chunk(chunk)

        self.assertIn("FastAPI", embedding_text)
        self.assertIn("docs/fastapi/reference/fastapi.md", embedding_text)


if __name__ == "__main__":
    unittest.main()
