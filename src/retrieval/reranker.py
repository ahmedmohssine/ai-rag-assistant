class CrossEncoderReranker:
    """Optional cross-encoder reranker for final candidate ordering."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None

        try:
            from sentence_transformers import CrossEncoder

            # A cross-encoder reads the question and candidate chunk together.
            # It is slower than vector search, but usually better at final ranking.
            self.model = CrossEncoder(model_name)
        except Exception:
            # Keep reranking optional. If the model cannot load, retrieval still
            # works with hybrid BM25 + vector search.
            self.model = None

    def rerank(self, question: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        if not self.model or not candidates:
            return candidates[:top_k]

        # Each pair asks: "How relevant is this chunk to this exact question?"
        pairs = [(
                    question,
                    f"""
                        Title:
                        {candidate["metadata"].get("title","")}

                        Filename:
                        {candidate["metadata"].get("filename","")}

                        Document:
                        {candidate["document"]}
                    """
                ) for candidate in candidates
            ]
        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        return sorted(candidates, key=lambda candidate: candidate["rerank_score"], reverse=True)[:top_k]
