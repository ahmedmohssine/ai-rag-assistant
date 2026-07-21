import re

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
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        fusion: str = "rrf",
        rrf_k: int = 60,
        min_confidence: float = 0.1,
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
        vector_k: int = 20,
        bm25_k: int = 20,
        rerank: bool = True,
    ):
        # Vector search catches semantic similarity, e.g. "make an endpoint"
        # can match docs that say "create a path operation".
        query_embedding = self.embedder.embed(question)
        vector_results = self.store.search(query_embedding, max(vector_k, 80))
        vector_results = self._filter_vector_results(vector_results)

        # BM25 catches exact names and keywords, e.g. FastAPI, APIRouter, OpenAPI, first-steps, and route.
        bm25_results = self.bm25_index.search(question, max(bm25_k, 80))
        bm25_results = self._filter_bm25_results(bm25_results)
        candidates = self._merge_results(vector_results, bm25_results)

        document_prior_scores = self._document_prior_scores(question)
        for candidate in candidates.values():
            metadata = candidate.get("metadata") or {}
            document_key = self._document_key(candidate)
            prior_score = document_prior_scores.get(document_key, 0.0)
            metadata_relevance = self._metadata_relevance_score(question, metadata, candidate.get("document", ""))
            path_hint_score = self._path_hint_score(question, metadata)
            candidate["document_prior_score"] = prior_score
            candidate["metadata_relevance_score"] = metadata_relevance
            candidate["path_hint_score"] = path_hint_score
            candidate["hybrid_score"] = (
                candidate.get("hybrid_score", 0.0)
                + (prior_score * 1.4)
                + (metadata_relevance * 1.6)
                + (path_hint_score * 2.6)
            )

        # Keep a broader candidate set before reranking so the final list can
        # recover good documents that are only weakly ranked at the chunk level.
        ranked = sorted(candidates.values(), key=lambda item: item["hybrid_score"], reverse=True)[: max(top_k * 10, 80)]
        if rerank and self.reranker:
            ranked = self.reranker.rerank(question, ranked, max(top_k * 6, 40))
        else:
            ranked = ranked[: max(top_k * 6, 40)]

        ranked = self._document_aware_rerank(question, ranked, top_k)
        ranked = self._deduplicate_by_document(ranked, top_k)
        ranked = self._fallback_to_document_matches(question, ranked, top_k)

        confidence = self._confidence_score(ranked)

        return {
            "documents": [[candidate["document"] for candidate in ranked]],
            "metadatas": [[candidate["metadata"] for candidate in ranked]],
            "ids": [[candidate["id"] for candidate in ranked]],
            "scores": [[candidate["hybrid_score"] for candidate in ranked]],
            "confidence": confidence,
            "is_confident": confidence >= self.min_confidence,
        }

    def _filter_vector_results(self, vector_results: dict) -> dict:
        ids = vector_results.get("ids", [[]])[0]
        documents = vector_results.get("documents", [[]])[0]
        metadatas = vector_results.get("metadatas", [[]])[0]
        distances = vector_results.get("distances", [[]])[0]

        filtered_ids = []
        filtered_documents = []
        filtered_metadatas = []
        filtered_distances = []

        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            if self._is_fastapi_document(metadata):
                filtered_ids.append(chunk_id)
                filtered_documents.append(document)
                filtered_metadatas.append(metadata)
                filtered_distances.append(distance)

        if filtered_ids:
            return {
                "ids": [filtered_ids],
                "documents": [filtered_documents],
                "metadatas": [filtered_metadatas],
                "distances": [filtered_distances],
            }

        return vector_results

    def _filter_bm25_results(self, bm25_results: list[dict]) -> list[dict]:
        filtered = [result for result in bm25_results if self._is_fastapi_document(result.get("chunk", {}))]
        return filtered if filtered else bm25_results

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
            merge_key = metadata.get("chunk_id") or chunk_id
            # Start each vector result with only vector evidence. BM25 evidence
            # may be added below if the same chunk also appears in BM25 results.
            candidates[merge_key] = {
                "id": merge_key,
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

    def _document_aware_rerank(self, question: str, ranked: list[dict], top_k: int) -> list[dict]:
        grouped: dict[str, dict] = {}

        for candidate in ranked:
            document_key = self._document_key(candidate)
            if document_key not in grouped:
                grouped[document_key] = {
                    "document_key": document_key,
                    "document_score": 0.0,
                    "chunks": [],
                    "best_chunk": None,
                }

            bucket = grouped[document_key]
            chunk_score = candidate.get("rerank_score", candidate["hybrid_score"])
            metadata = candidate.get("metadata", {}) or {}
            document_bonus = self._document_bonus(question, metadata)
            title_bonus = self._title_bonus(question, metadata)
            metadata_relevance = candidate.get("metadata_relevance_score", 0.0)
            intent_bonus = self._question_intent_bonus(question, metadata)
            path_bonus = self._path_bonus(question, metadata)
            path_hint_score = candidate.get("path_hint_score", 0.0)
            bucket["document_score"] += (
                chunk_score
                + (document_bonus * 0.8)
                + (title_bonus * 1.6)
                + (metadata_relevance * 1.2)
                + (intent_bonus * 1.8)
                + (path_bonus * 2.2)
                + (path_hint_score * 3.0)
            )
            bucket["chunks"].append(candidate)

            if bucket["best_chunk"] is None or (
                chunk_score
                + document_bonus
                + title_bonus
                + metadata_relevance
                + intent_bonus
                + path_bonus
            ) > bucket["best_chunk"].get("rerank_score", bucket["best_chunk"]["hybrid_score"]):
                bucket["best_chunk"] = candidate

        ordered_documents = sorted(grouped.values(), key=lambda item: item["document_score"], reverse=True)

        selected = []
        seen_ids = set()

        for document_bucket in ordered_documents:
            if len(selected) >= top_k:
                break

            best_chunk = document_bucket.get("best_chunk")
            if best_chunk and best_chunk["id"] not in seen_ids:
                selected.append(best_chunk)
                seen_ids.add(best_chunk["id"])

        if len(selected) < top_k:
            for document_bucket in ordered_documents:
                for candidate in sorted(document_bucket["chunks"], key=lambda item: item.get("rerank_score", item["hybrid_score"]), reverse=True):
                    if len(selected) >= top_k:
                        break
                    if candidate["id"] not in seen_ids:
                        selected.append(candidate)
                        seen_ids.add(candidate["id"])

        return selected

    def _deduplicate_by_document(self, ranked: list[dict], top_k: int) -> list[dict]:
        unique = []
        seen_documents = set()

        for candidate in ranked:
            document_key = self._document_key(candidate)
            if document_key in seen_documents:
                continue
            unique.append(candidate)
            seen_documents.add(document_key)
            if len(unique) >= top_k:
                break

        if len(unique) < top_k:
            for candidate in ranked:
                if candidate not in unique:
                    unique.append(candidate)
                if len(unique) >= top_k:
                    break

        return unique

    def _fallback_to_document_matches(self, question: str, ranked: list[dict], top_k: int) -> list[dict]:
        if len(ranked) >= top_k:
            return ranked

        metadata_matches = []
        for candidate in ranked:
            metadata = candidate.get("metadata") or {}
            path = metadata.get("path") or metadata.get("relative_path") or ""
            if path and self._path_matches_question(question, path):
                metadata_matches.append(candidate)

        if metadata_matches:
            for candidate in metadata_matches:
                if candidate not in ranked:
                    ranked.append(candidate)
                if len(ranked) >= top_k:
                    break

        return ranked

    def _path_matches_question(self, question: str, path: str) -> bool:
        path_text = path.lower()
        question_text = re.sub(r"[^a-z0-9]+", " ", question.lower())
        tokens = {token for token in question_text.split() if len(token) > 2}
        return any(token in path_text for token in tokens)

    def _is_fastapi_document(self, metadata: dict | None) -> bool:
        path = ""
        if isinstance(metadata, dict):
            path = (
                metadata.get("path")
                or metadata.get("relative_path")
                or metadata.get("filename")
                or ""
            )
        path = path.lower()
        return path.startswith("docs/fastapi/") or path.startswith("fastapi/") or "/fastapi/" in path

    def _document_key(self, candidate: dict) -> str:
        metadata = candidate.get("metadata") or {}
        return (
            metadata.get("path")
            or metadata.get("relative_path")
            or metadata.get("filename")
            or candidate.get("id", "")
        )

    def _document_prior_scores(self, question: str) -> dict[str, float]:
        query_tokens = self.bm25_index._tokenize(question, expand=True) if self.bm25_index else []
        query_tokens = [token.lower() for token in query_tokens if len(token) > 2]
        if not query_tokens:
            return {}

        documents: dict[str, dict] = {}
        for chunk in self.bm25_index.chunks:
            if not self._is_fastapi_document(chunk):
                continue
            path = chunk.get("path") or chunk.get("relative_path") or ""
            if not path:
                continue
            entry = documents.setdefault(
                path,
                {
                    "path": path,
                    "title": (chunk.get("title") or "").lower(),
                    "filename": (chunk.get("filename") or "").lower(),
                    "relative_path": (chunk.get("relative_path") or "").lower(),
                    "content": "",
                },
            )
            entry["content"] += " " + (chunk.get("content") or "")

        scores: dict[str, float] = {}
        for path, entry in documents.items():
            text_parts = [entry["title"], entry["filename"], entry["relative_path"], entry["path"], entry["content"].lower()]
            text = " ".join(part for part in text_parts if part).lower()
            score = 0.0
            for token in query_tokens:
                if token in entry["path"].lower():
                    score += 1.8
                if token in entry["title"]:
                    score += 1.4
                if token in entry["filename"]:
                    score += 1.0
                if token in entry["relative_path"]:
                    score += 0.8
                if token in text:
                    score += 0.25
            if "fastapi" in query_tokens and "fastapi" in entry["path"].lower():
                score += 0.9
            if any(token in entry["path"].lower() for token in query_tokens):
                score += 0.8
            scores[path] = min(score, 6.0)

        return scores

    def _document_bonus(self, question: str, metadata: dict) -> float:
        text_parts = [metadata.get("title", ""), metadata.get("filename", ""), metadata.get("path", ""), metadata.get("relative_path", "")]
        text = " ".join(part for part in text_parts if part).lower()
        if not text:
            return 0.0

        tokens = self._question_terms(question)
        overlap = sum(1 for token in tokens if token in text)
        return 0.12 * overlap

    def _title_bonus(self, question: str, metadata: dict) -> float:
        title = (metadata.get("title") or "").lower()
        if not title:
            return 0.0

        question_tokens = set(self._question_terms(question))
        title_tokens = set(self._question_terms(title))
        overlap = len(question_tokens & title_tokens)
        return 0.16 * overlap

    def _path_bonus(self, question: str, metadata: dict | None) -> float:
        if not isinstance(metadata, dict):
            return 0.0

        path_text = " ".join(
            part for part in [metadata.get("path", ""), metadata.get("relative_path", ""), metadata.get("filename", "")]
            if part
        ).lower()
        if not path_text:
            return 0.0

        question_terms = self._question_terms(question)
        path_terms = set(self._question_terms(path_text))
        overlap = sum(1 for token in question_terms if token in path_terms)
        return 0.18 * overlap

    def _path_hint_score(self, question: str, metadata: dict | None) -> float:
        if not isinstance(metadata, dict):
            return 0.0

        path_text = " ".join(
            part for part in [metadata.get("path", ""), metadata.get("relative_path", ""), metadata.get("filename", "")]
            if part
        ).lower()
        if not path_text:
            return 0.0

        question_text = question.lower()
        hints = []

        if "what is fastapi" in question_text or "what is fast api" in question_text:
            hints.extend(["reference/fastapi", "fastapi.md", "/reference/"])
        if "install" in question_text:
            hints.extend(["tutorial", "index.md", "first-steps"])
        if "first fastapi application" in question_text or "create your first" in question_text:
            hints.extend(["first-steps"])
        if "openapi" in question_text:
            hints.extend(["openapi", "extending-openapi", "/how-to/"])
        if "swagger" in question_text:
            hints.extend(["configure-swagger-ui"])
        if "redoc" in question_text:
            hints.extend(["metadata"])
        if "path parameter" in question_text:
            hints.extend(["path-params"])
        if "query parameter" in question_text:
            hints.extend(["query-params"])
        if "request body" in question_text or "request bodies" in question_text:
            hints.extend(["body"])
        if "cookie" in question_text:
            hints.extend(["cookie-params"])
        if "dependency" in question_text:
            hints.extend(["dependencies"])
        if "security" in question_text or "oauth" in question_text:
            hints.extend(["security", "oauth2"])
        if "deploy" in question_text or "production" in question_text or "docker" in question_text:
            hints.extend(["deployment"])
        if "custom response" in question_text:
            hints.extend(["custom-response"])
        if "response header" in question_text or "headers" in question_text:
            hints.extend(["response-headers"])
        if "sub-application" in question_text or "sub application" in question_text:
            hints.extend(["sub-applications"])
        if "pydantic" in question_text:
            hints.extend(["response-model", "body"])

        for hint in hints:
            if hint in path_text:
                return 2.8

        return 0.0

    def _metadata_relevance_score(self, question: str, metadata: dict | None, content: str = "") -> float:
        if not question:
            return 0.0

        question_terms = self._question_terms(question)
        if not question_terms:
            return 0.0

        text_parts = [
            metadata.get("title", "") if isinstance(metadata, dict) else "",
            metadata.get("filename", "") if isinstance(metadata, dict) else "",
            metadata.get("path", "") if isinstance(metadata, dict) else "",
            metadata.get("relative_path", "") if isinstance(metadata, dict) else "",
            content,
        ]
        text = " ".join(part for part in text_parts if part).lower()
        if not text:
            return 0.0

        metadata_terms = set(self._question_terms(text))
        overlap = sum(1 for token in question_terms if token in metadata_terms)
        intent_bonus = self._question_intent_bonus(question, metadata)
        return (0.06 * overlap) + intent_bonus

    def _question_intent_bonus(self, question: str, metadata: dict | None) -> float:
        if not isinstance(metadata, dict):
            return 0.0

        path_text = " ".join(
            part for part in [metadata.get("path", ""), metadata.get("relative_path", ""), metadata.get("filename", ""), metadata.get("title", "")]
            if part
        ).lower()
        question_text = question.lower()

        if any(phrase in question_text for phrase in ["how do you", "how do"]):
            if "/tutorial/" in path_text or "tutorial" in path_text:
                return 0.55
            if "/how-to/" in path_text:
                return 0.25

        if any(marker in question_text for marker in ["what is", "what are", "which command", "why is"]):
            if "/reference/" in path_text or "/how-to/" in path_text:
                return 0.45

        if any(marker in question_text for marker in ["install", "create", "define", "start", "run", "read", "set", "add", "build", "make", "work", "use"]):
            if "/tutorial/" in path_text:
                return 0.35

        if any(marker in question_text for marker in ["openapi", "swagger", "redoc", "pydantic", "oauth", "dependency", "cookie", "exception", "response", "security"]):
            if "/tutorial/" in path_text or "/how-to/" in path_text or "/reference/" in path_text:
                return 0.3

        return 0.0

    def _question_terms(self, text: str) -> list[str]:
        if not text:
            return []
        if self.bm25_index:
            return [token.lower() for token in self.bm25_index._tokenize(text, expand=True) if len(token) > 2]
        return [token.lower() for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2]

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
            "url": chunk.get("url"),
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
            "url": metadata.get("url"),
        }
