from src.retrieval.bm25 import BM25Index
from src.retrieval.reranker import CrossEncoderReranker


class Retriever:
    """A class that retrieves relevant documents based on a query."""

    def __init__(
        self,
        embedder,
        store,
        bm25_index: BM25Index = None,
        reranker: CrossEncoderReranker = None,
        vector_weight: float = 0.55,
        bm25_weight: float = 0.45,
        fusion: str = "rrf",
        rrf_k: int = 60,
        min_confidence: float = 0.20,
    ):
        self.embedder = embedder
        self.store = store
        self.bm25_index = bm25_index or BM25Index()
        self.reranker = reranker
        # Weighted fusion uses these values after normalizing vector/BM25 scores.
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        # RRF is the default because it combines rankings instead of raw scores.
        # That is helpful when Chroma distances and BM25 scores are on very
        # different numeric scales.
        self.fusion = fusion if fusion in {"weighted", "rrf"} else "rrf"
        self.rrf_k = rrf_k
        self.min_confidence = min_confidence

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        vector_k: int = 40,
        bm25_k: int = 35,
        rerank: bool = True,
    ):
        # Vector search catches semantic similarity, e.g. "make an endpoint"
        # can match docs that say "create a path operation".
        query_embedding = self.embedder.embed(question)
        vector_results = self.store.search(query_embedding, vector_k)

        # BM25 catches exact names and keywords, e.g. FastAPI, APIRouter,
        # OpenAPI, first-steps, and route.
        bm25_results = self.bm25_index.search(question, bm25_k)
        candidates = self._merge_results(vector_results, bm25_results)

        # Keep more than top_k before reranking. The reranker needs a wider
        # candidate set so it can rescue good results from rank 6-15.
        ranked = sorted(candidates.values(), key=lambda item: item["hybrid_score"], reverse=True)[:15]
        if rerank and self.reranker:
            ranked = self.reranker.rerank(question, ranked, top_k)
        else:
            ranked = ranked[:top_k]

        confidence = self._confidence_score(ranked)

        return {
            "documents": [[candidate["document"] for candidate in ranked]],
            "metadatas": [[candidate["metadata"] for candidate in ranked]],
            "ids": [[candidate["id"] for candidate in ranked]],
            "scores": [[candidate["hybrid_score"] for candidate in ranked]],
            "confidence": confidence,
            "is_confident": confidence >= self.min_confidence,
        }

    def _merge_results(self, vector_results: dict, bm25_results: list[dict]) -> dict:
        # Use chunk_id as the merge key. If the same chunk appears in both
        # vector and BM25 results, we combine its signals instead of duplicating it.
        candidates = {}
        vector_scores = self._normalized_vector_scores(vector_results)
        bm25_scores = self._normalized_bm25_scores(bm25_results)
        vector_ranks = self._vector_ranks(vector_results)
        bm25_ranks = self._bm25_ranks(bm25_results)

        for index, chunk_id in enumerate(vector_results.get("ids", [[]])[0]):
            metadata = self._complete_metadata(vector_results["metadatas"][0][index], chunk_id)
            document = vector_results["documents"][0][index]
            vector_score = vector_scores.get(chunk_id, 0.0)
            # Start each vector result with only vector evidence. BM25 evidence
            # may be added below if the same chunk also appears in BM25 results.
            candidates[chunk_id] = {
                "id": chunk_id,
                "document": document,
                "metadata": metadata,
                "vector_score": vector_score,
                "bm25_score": 0.0,
                "vector_rank": vector_ranks.get(chunk_id),
                "bm25_rank": None,
                "hybrid_score": 0.0,
            }

        for result in bm25_results:
            chunk = result["chunk"]
            chunk_id = chunk["chunk_id"]
            bm25_score = bm25_scores.get(chunk_id, 0.0)

            if chunk_id not in candidates:
                # This chunk was found only by lexical search. Keep it anyway:
                # exact keyword matches often find API docs that embeddings miss.
                candidates[chunk_id] = {
                    "id": chunk_id,
                    "document": chunk["content"],
                    "metadata": self._metadata_from_chunk(chunk),
                    "vector_score": 0.0,
                    "bm25_score": bm25_score,
                    "vector_rank": None,
                    "bm25_rank": bm25_ranks.get(chunk_id),
                    "hybrid_score": 0.0,
                }
            else:
                # This chunk was found by both systems, so it gets both BM25
                # and vector evidence during fusion.
                candidates[chunk_id]["bm25_score"] = bm25_score
                candidates[chunk_id]["bm25_rank"] = bm25_ranks.get(chunk_id)

        for candidate in candidates.values():
            candidate["hybrid_score"] = self._fusion_score(candidate)

        return candidates

    def _normalized_vector_scores(self, vector_results: dict) -> dict:
        ids = vector_results.get("ids", [[]])[0]
        distances = vector_results.get("distances", [[]])[0]

        if not ids:
            return {}
        if not distances:
            return {chunk_id: 1.0 for chunk_id in ids}

        raw_scores = {}
        for chunk_id, distance in zip(ids, distances):
            # Chroma returns distance where smaller is better. Convert it into
            # a similarity-like score where larger is better.
            raw_scores[chunk_id] = 1 / (1 + float(distance))

        return self._max_normalize(raw_scores)

    def _normalized_bm25_scores(self, bm25_results: list[dict]) -> dict:
        if not bm25_results:
            return {}

        max_score = max(result["score"] for result in bm25_results) or 1.0
        return {
            result["chunk"]["chunk_id"]: result["score"] / max_score
            for result in bm25_results
        }

    def _fusion_score(self, candidate: dict) -> float:
        if self.fusion == "rrf":
            return self._rrf_score(candidate)

        # Weighted fusion compares normalized scores directly.
        # This is useful for experiments because weights are easy to tune.
        return (
            self.vector_weight * candidate["vector_score"]
            + self.bm25_weight * candidate["bm25_score"]
        )

    def _rrf_score(self, candidate: dict) -> float:
        # Reciprocal Rank Fusion cares about rank position, not score size.
        # A chunk ranked highly by both systems gets the strongest final score.
        score = 0.0
        if candidate["vector_rank"] is not None:
            score += 1 / (self.rrf_k + candidate["vector_rank"])
        if candidate["bm25_rank"] is not None:
            score += 1 / (self.rrf_k + candidate["bm25_rank"])

        return score

    def _vector_ranks(self, vector_results: dict) -> dict:
        return {
            chunk_id: rank
            for rank, chunk_id in enumerate(vector_results.get("ids", [[]])[0], start=1)
        }

    def _bm25_ranks(self, bm25_results: list[dict]) -> dict:
        return {
            result["chunk"]["chunk_id"]: rank
            for rank, result in enumerate(bm25_results, start=1)
        }

    def _max_normalize(self, scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}

        # Normalize to 0..1 so vector scores and BM25 scores can be combined
        # fairly in weighted fusion.
        max_score = max(scores.values()) or 1.0
        return {
            key: value / max_score
            for key, value in scores.items()
        }

    def _confidence_score(self, ranked: list[dict]) -> float:
        if not ranked:
            return 0.0

        # Confidence should reflect the whole top of the result list, not only
        # the first result. A strong top 3 is usually more trustworthy.
        top_scores = [candidate["hybrid_score"] for candidate in ranked[:3]]
        average_top3 = sum(top_scores) / len(top_scores)
        # The gap helps when the first result is clearly better than the second.
        gap = ranked[0]["hybrid_score"] - ranked[1]["hybrid_score"] if len(ranked) > 1 else ranked[0]["hybrid_score"]

        if self.fusion == "rrf":
            # RRF scores are small by design, so convert them to a 0..1-ish
            # confidence scale before comparing against min_confidence.
            max_rrf_score = 2 / (self.rrf_k + 1)
            average_top3 = average_top3 / max_rrf_score
            gap = gap / max_rrf_score

        return min(average_top3 + 0.25 * gap, 1.0)

    def _metadata_from_chunk(self, chunk: dict) -> dict:
        chunk_metadata = chunk.get("metadata", {})
        # BM25 reads from chunks.json, while vector search reads Chroma metadata.
        # This function makes BM25-only results look like vector results.
        return {
            "source": chunk.get("source", ""),
            "filename": chunk.get("filename", ""),
            "path": chunk.get("path", ""),
            "relative_path": chunk.get("relative_path", ""),
            "chunk_id": chunk.get("chunk_id", ""),
            "citation_id": chunk_metadata.get("citation_id", chunk.get("chunk_id", "")),
            "file_type": chunk.get("file_type", ""),
            "title": chunk.get("title", ""),
        }

    def _complete_metadata(self, metadata: dict, chunk_id: str) -> dict:
        metadata = metadata or {}
        # Older indexes may not have all metadata fields. Fill defaults so
        # search.py and citations can rely on stable keys.
        return {
            "citation_id": metadata.get("citation_id", chunk_id),
            "title": metadata.get("title", ""),
            "filename": metadata.get("filename", ""),
            "relative_path": metadata.get("relative_path", ""),
            "path": metadata.get("path", ""),
            "source": metadata.get("source", ""),
            "chunk_id": metadata.get("chunk_id", chunk_id),
            "file_type": metadata.get("file_type", ""),
        }
