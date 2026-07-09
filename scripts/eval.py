import argparse
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.evaluation.judge import LLMjudge
from src.generation.generator import Generator
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


def _normalize_dataset(dataset_path: str = "data/evaluation_dataset50.json") -> list[dict]:
    with open(dataset_path, "r", encoding="utf-8") as handle:
        dataset = json.load(handle)

    with open("data/chunks.json", "r", encoding="utf-8") as handle:
        chunks = json.load(handle)

    chunk_lookup = {
        chunk.get("chunk_id"): chunk
        for chunk in chunks
        if chunk.get("chunk_id")
    }

    normalized = []
    for sample in dataset:
        expected_documents = sample.get("expected_documents") or []
        acceptable_documents = sample.get("acceptable_documents") or []
        expected_chunk = sample.get("expected_chunk") or None
        chunk = chunk_lookup.get(expected_chunk)
        actual_path = chunk.get("path") if chunk else None

        if actual_path and expected_documents and expected_documents[0] != actual_path:
            expected_documents = [actual_path]

        if not expected_documents and actual_path:
            expected_documents = [actual_path]

        if not acceptable_documents:
            acceptable_documents = expected_documents[:]
        elif acceptable_documents == expected_documents:
            acceptable_documents = expected_documents[:]
            if actual_path and actual_path not in acceptable_documents:
                acceptable_documents.append(actual_path)

        if actual_path and actual_path not in acceptable_documents:
            acceptable_documents.append(actual_path)

        sample = dict(sample)
        sample["expected_documents"] = expected_documents
        sample["acceptable_documents"] = acceptable_documents
        normalized.append(sample)

    return normalized

from src.indexing.embedder import Embedder
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever


def _normalize_expected(sample: dict) -> tuple[list[str], list[str], str | None]:
    expected_documents = sample.get("expected_documents") or []
    if not expected_documents and sample.get("expected_document"):
        expected_documents = [sample["expected_document"]]

    acceptable_documents = sample.get("acceptable_documents") or []
    return expected_documents, acceptable_documents


def evaluate(
    retriever,
    generator,
    judge,
    dataset_path: str = "data/evaluation_dataset50.json",
    top_k: int = 5,
    verbose: bool = False,
) -> dict:
    dataset = _normalize_dataset(dataset_path)
    faithfulness_total = 0
    correctness_total = 0
    relevance_total = 0

    hallucinations = 0
    judge_samples = 0
    total = len(dataset)
    document_recall1 = document_recall3 = document_recall5 = 0
    document_mrr = 0

    for sample in dataset:
        question = sample["question"]
        expected_documents, acceptable_documents = _normalize_expected(sample)

        results = retriever.retrieve(question, top_k=top_k)
        context = []

        for metadata, document in zip(
            results["metadatas"][0],
            results["documents"][0],
        ):
            context.append(
                {
                    "content": document,
                    "metadata": metadata,
                }
            )
        expected_answer = sample.get("expected_answer", "")
        generated_answer = generator.generate(
            question,
            context,
        )     
        scores = judge.evaluate(
            question=question,
            context=context,
            expected_answer=expected_answer,
            generated_answer=generated_answer,
        )
        faithfulness_total += scores["faithfulness"]
        correctness_total += scores["correctness"]
        relevance_total += scores["relevance"]

        if scores["hallucination"]:
            hallucinations += 1

        judge_samples += 1
        judge_results = []
        judge_results.append({
            "question": question,
            "generated_answer": generated_answer,
            "scores": scores,
        })
        with open(
            r"C:\1337-Project\ai-rag-assistant\data\judge_results.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(judge_results, f, indent=2)

        result_metadatas = results.get("metadatas", [[]])[0]

        document_rank = None
        chunk_rank = None

        for index, metadata in enumerate(result_metadatas, start=1):
            path = metadata.get("path") if metadata else None
            if path and (path in expected_documents or path in acceptable_documents):
                document_rank = index
                break


        if document_rank == 1:
            document_recall1 += 1
        if document_rank is not None and document_rank <= 3:
            document_recall3 += 1
        if document_rank is not None and document_rank <= 5:
            document_recall5 += 1
        if document_rank is not None: 
            document_mrr += 1 / document_rank



    metrics = {
        "total_samples": total,
        "top_k": top_k,
        "document_recall@1": document_recall1 / total if total else 0.0,
        "document_recall@3": document_recall3 / total if total else 0.0,
        "document_recall@5": document_recall5 / total if total else 0.0,
        "document_mrr": document_mrr / total if total else 0.0,
        "faithfulness": faithfulness_total / judge_samples,
        "correctness": correctness_total / judge_samples,
        "relevance": relevance_total / judge_samples,
        "hallucination_rate": hallucinations / judge_samples,
    }
    if verbose:
        print(
            f"{question}\n"
            f"  document_rank={document_rank}\n"
            f"  chunk_rank={chunk_rank}\n"
        )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality on the FastAPI evaluation dataset")
    parser.add_argument("--dataset", default="data/evaluation_dataset50.json", help="Path to the evaluation JSON file")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieval results to consider")
    parser.add_argument("--verbose", action="store_true", help="Print per-question ranking details")
    parser.add_argument("--output", help="Optional path to save metrics as JSON")
    args = parser.parse_args()
    embedder = Embedder()
    store = VectorStore()

    retriever = Retriever(embedder, store)
    generator = Generator()
    judge = LLMjudge()    
    embedder = Embedder()
    store = VectorStore()
    retriever = Retriever(embedder, store)

    metrics = evaluate(
        retriever,
        generator,
        judge,
        dataset_path=args.dataset,
        top_k=args.top_k,
        verbose=args.verbose,
    )
    print(json.dumps(metrics, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"Saved metrics to {output_path}")



if __name__ == "__main__":
    main()