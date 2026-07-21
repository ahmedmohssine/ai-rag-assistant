import argparse
import json
import sys
import os
import time
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.evaluation.judge import LLMjudge
from src.generation.generator import Generator
from src.indexing.embedder import Embedder
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever

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


def _normalize_expected(sample: dict) -> tuple[list[str], list[str]]:
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
) -> tuple[dict, list, list, list]:
    dataset = _normalize_dataset(dataset_path)
    faithfulness_total = 0
    correctness_total = 0
    relevance_total = 0

    hallucinations = 0
    judge_samples = 0
    total = len(dataset)
    document_recall1 = document_recall3 = document_recall5 = 0
    document_mrr = 0
    judge_results = []
    retrieval_time_total = 0
    generation_time_total = 0

    # Lists to capture failure scenarios
    retrieval_failures = []
    generation_failures = []
    all_evaluations = []

    for sample in dataset:
        question = sample["question"]
        expected_documents, acceptable_documents = _normalize_expected(sample)

        start = time.perf_counter()

        results = retriever.retrieve(question, top_k=top_k)

        retrieval_time_total += time.perf_counter() - start
        context = []


        result_metadatas = results.get("metadatas", [[]])[0]
        result_documents = results.get("documents", [[]])[0]

        for metadata, document in zip(result_metadatas, result_documents):
            context.append({
                "content": document,
                "metadata": metadata,
            })
            
        expected_answer = sample.get("expected_answer", "")
        start = time.perf_counter()

        generated_answer = generator.generate(question, context)
        generation_time_total += time.perf_counter() - start 
        
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
        
        judge_results.append({
            "question": question,
            "generated_answer": generated_answer,
            "scores": scores,
        })
        
        with open("data/judge_results.json", "w", encoding="utf-8") as f:
            json.dump(judge_results, f, indent=2, ensure_ascii=False)

        document_rank = None
        def normalize_path(path: str) -> str:
            if not path:
                return ""

            path = path.replace("\\", "/")
            path = path.lower()

            # remove duplicated docs folder
            path = path.replace("docs/fastapi/docs/", "docs/fastapi/")

            return path


        expected = {normalize_path(p) for p in expected_documents}
        acceptable = {normalize_path(p) for p in acceptable_documents}

        for index, metadata in enumerate(result_metadatas, start=1):
            path = normalize_path(metadata.get("path"))

            if path in expected or path in acceptable:
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

        # --- Track Failures ---
        record = {
            "question": question,
            "expected_documents": expected_documents,
            "acceptable_documents": acceptable_documents,
            "retrieved_documents": [meta.get("path") for meta in result_metadatas if meta],
            "expected_answer": expected_answer,
            "generated_answer": generated_answer,
            "scores": scores
        }
        
        all_evaluations.append(record)

        # Retrieval Failure: Context documents were completely missed within top_k
        if document_rank is None:
            retrieval_failures.append({
                "question": question,
                "expected_documents": expected_documents,
                "retrieved_documents": record["retrieved_documents"]
            })

        # Generation Failure: Hallucination detected, or critically low metrics
        is_low_faithfulness = scores.get("faithfulness", 5) < 3
        if scores.get("hallucination") or is_low_faithfulness:
            generation_failures.append({
                "question": question,
                "generated_answer": generated_answer,
                "scores": scores,
                "retrieved_context": context
            })

        if verbose:
            print(f"{question}\n  document_rank={document_rank}\n")

    metrics = {
        "total_samples": total,
        "top_k": top_k,
        "document_recall@1": document_recall1 / total if total else 0.0,
        "document_recall@3": document_recall3 / total if total else 0.0,
        "document_recall@5": document_recall5 / total if total else 0.0,
        "document_mrr": document_mrr / total if total else 0.0,
        "faithfulness": faithfulness_total / judge_samples if judge_samples else 0.0,
        "correctness": correctness_total / judge_samples if judge_samples else 0.0,
        "relevance": relevance_total / judge_samples if judge_samples else 0.0,
        "hallucination_rate": hallucinations / judge_samples if judge_samples else 0.0,
        "average_retrieval_time": retrieval_time_total / total if total else 0,
        "average_generation_time": generation_time_total / total if total else 0,   
    }
    
    return metrics, retrieval_failures, generation_failures, all_evaluations


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality on the FastAPI evaluation dataset")
    parser.add_argument("--dataset", default="data/evaluation_dataset50.json", help="Path to the evaluation JSON file")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieval results to consider")
    parser.add_argument("--verbose", action="store_true", help="Print per-question ranking details")
    parser.add_argument("--output", default="data/evaluation/evaluation_report.json", help="Path to save metrics as JSON")
    args = parser.parse_args()

    embedder = Embedder()
    store = VectorStore()
    retriever = Retriever(embedder, store)
    generator = Generator()
    judge = LLMjudge()    

    # Unpack updated evaluate outputs
    metrics, retrieval_failures, generation_failures, all_evaluations = evaluate(
        retriever,
        generator,
        judge,
        dataset_path=args.dataset,
        top_k=args.top_k,
        verbose=args.verbose,
    )

    # Worst Judged Answers: Sort all evaluations by the correctness score ascending
    worst_judged = sorted(all_evaluations, key=lambda x: x["scores"].get("correctness", 5))[:10]

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Save tracking JSON structures
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "summary": "RAG Evaluation Report"}, f, indent=2, ensure_ascii=False)
        
    with open("data/evaluation/retrieval_failures.json", "w", encoding="utf-8") as f:
        json.dump(retrieval_failures, f, indent=2, ensure_ascii=False)

    with open("data/evaluation/generation_failures.json", "w", encoding="utf-8") as f:
        json.dump(generation_failures, f, indent=2, ensure_ascii=False)

    with open("data/evaluation/worst_judged_answers.json", "w", encoding="utf-8") as f:
        json.dump(worst_judged, f, indent=2, ensure_ascii=False)

    
    report = f"""
    ============================================================
    AI RAG ASSISTANT - EVALUATION REPORT
    ============================================================
    Dataset size: {metrics['total_samples']} questions

    Top-K: {metrics['top_k']}Retrieval
    ------------------------------
    Recall@1 : {metrics['document_recall@1']:.2%}
    Recall@3 : {metrics['document_recall@3']:.2%}
    Recall@5 : {metrics['document_recall@5']:.2%}
    MRR       : {metrics['document_mrr']:.3f}
    
    Average Retrieval Time  : {metrics['average_retrieval_time']:.4f}s
    Average Generation Time : {metrics['average_generation_time']:.4f}s
    
    LLM Judge Metrics
    ------------------------------
    Faithfulness      : {metrics['faithfulness']:.2f}
    Correctness       : {metrics['correctness']:.2f}
    Relevance         : {metrics['relevance']:.2f}
    Hallucination Rate: {metrics['hallucination_rate']:.2%}
    
    ------------------------------
    Failure Metrics Summary
    ------------------------------
    Retrieval Failures : {len(retrieval_failures)} 
    casesGeneration Failures: {len(generation_failures)} cases
    Worst Judged Saved : {len(worst_judged)} cases
    
    All detailed reports saved successfully under the 'data/evaluation/' directory.
    ============================================================"""

    print(report)

if __name__ == "__main__":
    main()