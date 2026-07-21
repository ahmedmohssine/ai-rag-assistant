import json
import math
import re
from pathlib import Path


API_TOKENS = {
    "fastapi": "fastapi",
    "apirouter": "apirouter",
    "openapi": "openapi",
    "jsonschema": "jsonschema",
}

FIELD_WEIGHTS = {
    "title": 5,
    "filename": 5,
    "relative_path": 4,
    "content": 1,
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "with",
}

SYNONYMS = {
    "add": ["create"],
    "begin": ["start", "first", "step"],
    "build": ["create", "make", "tutorial"],
    "endpoint": ["route", "path", "operation"],
    "endpoints": ["route", "path", "operation"],
    "get": ["get"],
    "getting": ["start", "first", "step"],
    "make": ["create", "build", "tutorial"],
    "page": ["route"],
    "pages": ["route"],
    "path": ["route", "endpoint"],
    "routing": ["route"],
    "start": ["begin", "first", "step"],
    "started": ["start", "first", "step"],
    "create": ["add", "make", "build", "tutorial", "first-steps"],
}

# This is a tiny domain-specific stemmer. It keeps the project dependency-light
# while still matching common variations like "routes" -> "route".
STEM_REPLACEMENTS = {
    "apis": "api",
    "endpoints": "endpoint",
    "getting": "start",
    "operations": "operation",
    "pages": "page",
    "routes": "route",
    "routing": "route",
    "started": "start",
    "starts": "start",
    "created": "create",
    "creating": "create",
    "creates": "create",
    "models": "model",
}


class BM25Index:
    """Small BM25 index over chunk JSON data."""

    def __init__(self, chunks_path: str = "data/chunks.json", k1: float = 1.5, b: float = 0.75):
        self.chunks_path = Path(chunks_path)
        self.k1 = k1
        self.b = b
        self.chunks = self._load_chunks()
        # Pre-tokenize once at startup so each query only has to score terms.
        self.tokenized_documents = [self._tokenize_chunk(chunk) for chunk in self.chunks]
        self.average_doc_length = self._average_doc_length()
        # Document frequency tells BM25 how rare or common each term is.
        # Rare terms like "apirouter" should matter more than common terms.
        self.document_frequencies = self._document_frequencies()

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        # Expand only query terms, not document terms. This keeps the index small
        # while still making "make endpoint" match "create route".
        query_terms = self._tokenize(query, expand=True)
        scores = []

        for index, terms in enumerate(self.tokenized_documents):
            score = self._score(query_terms, terms)
            if score > 0:
                scores.append(
                    {
                        "chunk": self.chunks[index],
                        "score": score,
                    }
                )

        return sorted(scores, key=lambda result: result["score"], reverse=True)[:top_k]

    def _load_chunks(self) -> list[dict]:
        if not self.chunks_path.exists():
            return []

        with open(self.chunks_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _tokenize_chunk(self, chunk: dict) -> list[str]:
        weighted_terms = []

        for field, weight in FIELD_WEIGHTS.items():
            terms = self._tokenize(chunk.get(field, ""))
            # Repeating terms is a simple way to boost fields without changing
            # the BM25 formula itself.
            weighted_terms.extend(terms * weight)

        return weighted_terms

    def _tokenize(self, text: str, expand: bool = False) -> list[str]:
        # Split path-like and punctuation-heavy text into useful tokens:
        # "tutorial/first-steps.md" -> "tutorial", "first", "steps", "md".
        normalized_text = re.sub(r"[-_/.:]+", " ", text)
        raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9]*|[0-9]+", normalized_text)
        terms = []

        for token in raw_tokens:
            normalized = self._normalize_token(token)
            if not normalized or normalized in STOP_WORDS:
                continue

            terms.append(normalized)
            if expand:
                # Query expansion is intentionally small and domain-specific.
                # Too many synonyms would make BM25 noisy.
                terms.extend(SYNONYMS.get(normalized, []))

        return terms

    def _normalize_token(self, token: str) -> str:
        lowered = token.lower()
        # Preserve framework/API names as stable search terms.
        if lowered in API_TOKENS:
            return API_TOKENS[lowered]
        if lowered in STEM_REPLACEMENTS:
            return STEM_REPLACEMENTS[lowered]
        if len(lowered) > 4 and lowered.endswith("ing"):
            return lowered[:-3]
        if len(lowered) > 3 and lowered.endswith("ed"):
            return lowered[:-2]
        if len(lowered) > 4 and lowered.endswith("ies"):
            return f"{lowered[:-3]}y"
        if len(lowered) > 4 and lowered.endswith(("ses", "xes", "ches", "shes")):
            return lowered[:-2]
        if len(lowered) > 3 and lowered.endswith("s"):
            return lowered[:-1]

        return lowered

    def _average_doc_length(self) -> float:
        if not self.tokenized_documents:
            return 0.0

        return sum(len(document) for document in self.tokenized_documents) / len(self.tokenized_documents)

    def _document_frequencies(self) -> dict[str, int]:
        frequencies = {}
        for terms in self.tokenized_documents:
            for term in set(terms):
                frequencies[term] = frequencies.get(term, 0) + 1

        return frequencies

    def _score(self, query_terms: list[str], document_terms: list[str]) -> float:
        if not query_terms or not document_terms or self.average_doc_length == 0:
            return 0.0

        # Count term frequency inside this document/chunk.
        term_counts = {}
        for term in document_terms:
            term_counts[term] = term_counts.get(term, 0) + 1

        score = 0.0
        document_length = len(document_terms)
        total_documents = len(self.tokenized_documents)

        for term in query_terms:
            if term not in term_counts:
                continue

            document_frequency = self.document_frequencies.get(term, 0)
            # IDF rewards rare terms. If only a few chunks mention "APIRouter",
            # those chunks should jump up for APIRouter questions.
            inverse_document_frequency = math.log(
                1 + (total_documents - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            term_frequency = term_counts[term]
            # BM25 balances exact matches with document length, so a huge file
            # does not win just because it contains every word once.
            denominator = term_frequency + self.k1 * (
                1 - self.b + self.b * document_length / self.average_doc_length
            )
            score += inverse_document_frequency * (term_frequency * (self.k1 + 1)) / denominator

        return score
