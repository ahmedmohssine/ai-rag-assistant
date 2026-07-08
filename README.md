# AI RAG Assistant

A local Retrieval-Augmented Generation (RAG) assistant that indexes documentation and answers questions using semantic search, BM25 lexical search, and a local LLM via Ollama.

---

## Features
### 📄 Multi-format document ingestion
 - Markdown (.md, .mdx)
 - Text (.txt)
 - reStructuredText (.rst)
 - CSV
 - JSON / JSONL
 - PDF
### ✂️ Structure-aware chunking
 - Markdown heading awareness
 - Recursive splitting
 - Overlapping chunks
 - Citation IDs
### 🧠 Embeddings
 - sentence-transformers/all-MiniLM-L6-v2
### 🗂️ Vector Database
 - ChromaDB
### 🔍 Hybrid Retrieval
 - Semantic vector search (SentenceTransformers)
 - BM25 lexical retrieval
 - FastAPI-focused document filtering and document-prior boosting
 - Hybrid fusion with document-aware reranking
 - Optional CrossEncoder reranking
### 🤖 Local LLM
 - Ollama
 - Llama 3.2
### 📚 Source citations
### 🖥️ Fully local
 - No OpenAI API
 - No cloud services
 - Offline capable
### 📊 Evaluation
 - Retrieval evaluation (Recall@1, Recall@3, Recall@5, MRR)
 - Evaluation dataset (50 FastAPI-focused questions)
 - Retrieval inspection and regression tests

---

## Current Architecture

```
Documents
(.md .mdx .txt .rst .csv .json .jsonl .pdf)
        │
        ▼
Document Reader
        │
        ▼
Structure-aware Chunker
        │
        ▼
chunks.json
        │
        ▼
SentenceTransformer
        │
        ▼
Embeddings
        │
        ▼
ChromaDB
        │
        ├───────────────┐
        ▼               ▼
 Vector Search       BM25 Search
        └──────┬────────┘
               ▼
        Hybrid Retriever
               │
               ▼
     Optional CrossEncoder
               │
               ▼
        Prompt Builder
               │
               ▼
      Ollama (Llama 3.2)
               │
               ▼
 Answer + Citation IDs
```

---

## Project Structure

```
ai-rag-assistant/

├── docs/
│
├── data/
│   ├── chunks.json
│   └── chroma/
│
├── scripts/
│   ├── build_chunks.py
│   ├── build_index.py
│   ├── eval.py
│   ├── generate_eval_chunks.py
│   ├── chat.py (empty)
│   └── search.py
│
├── tests/
│   └── test_retriever.py
│
├── src/
│   ├── chunking/
│   ├── generation/
│   ├── indexing/
│   ├── ingestion/
│   ├── models/
│   └── retrieval/
│
├── main.py (empty)
│
├── requirements.txt
│
└── README.md
```

---

## Installation

```bash
git clone https://github.com/<your-name>/ai-rag-assistant.git

cd ai-rag-assistant

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### Requirements

The runtime requirements are listed in `requirements.txt` and currently include:
 - chromadb
 - ollama
 - pypdf
 - sentence-transformers

No new runtime packages were added beyond those already required by the current pipeline.

### Install Ollama

```bash
ollama pull llama3.2:3b
```

## Build the Index
```bash
python scripts/build_chunks.py

python scripts/build_index.py
```

## Run

```bash
python scripts/search.py
```

 - Example:
```
Question:
What is OpenAPI?

Answer:
OpenAPI is the specification used to describe your API...
[fastapi:index_0]
```

## Evaluation

Run retrieval evaluation:

```bash
python scripts/eval.py
```

Run the retriever regression tests:

```bash
python -m unittest discover -s tests
```

## Current Status

### Current benchmark (FastAPI corpus, 50 questions):

 - Recall@1: 60%
 - Recall@3: 76%
 - Recall@5: 80%
 - MRR: 0.685

### Completed

- [x] Document reader
- [x] Multi-format ingestion
- [x] Structure-aware chunking
- [x] Recursive chunk splitting
- [x] Citation IDs
- [x] JSON chunk dataset
- [x] SentenceTransformer embeddings
- [x] ChromaDB indexing
- [x] Vector retrieval
- [x] BM25 retrieval
- [x] Hybrid retrieval with document-aware reranking
- [x] FastAPI-focused retrieval filtering and document-prior boosting
- [x] Optional CrossEncoder reranking
- [x] Ollama integration
- [x] Prompt builder
- [x] Retrieval evaluation framework
- [x] Evaluation dataset
- [x] End-to-end RAG pipeline
- [x] Retriever regression tests

### In Progress

- [ ] Retrieval tuning for MRR > 0.8
- [ ] Better hybrid fusion
- [ ] Better reranking
- [ ] Answer evaluation (LLM Judge / Ragas)
- [ ] Source URL citations
- [ ] FastAPI backend
- [ ] Chat UI

## Tech Stack

 - Python
 - SentenceTransformers
 - ChromaDB
 - BM25
 - Ollama
 - Llama 3.2
 - CrossEncoder (MS MARCO)
 - PyPDF
 - FastAPI (planned)

## Roadmap

 - Improve retrieval accuracy
 - Automatic retrieval tuning
 - Query rewriting
 - LLM-as-a-Judge evaluation
 - Ragas evaluation
 - Source URL citations
 - FastAPI REST API
 - Web chat interface
 - Additional document connectors