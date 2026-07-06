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
 - Semantic vector search
 - BM25 lexical search
 - Hybrid score fusion
### 🤖 Local LLM
 - Ollama
 - Llama 3.2
### 📚 Source citations
### 🖥️ Fully local
 - No OpenAI API
 - No cloud services
 - Offline capable

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
Chunker
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
        ▼
Hybrid Retriever
(Vector + BM25)
        │
        ▼
(Optional Reranker)
        │
        ▼
Prompt Builder
        │
        ▼
Ollama (Llama)
        │
        ▼
Answer + Citations
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
│   ├── chat.py (empty)
│   └── search.py
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

## Current Status

### Completed

- [x] Document reader
- [x] Multi-format ingestion
- [x] Structure-aware chunking
- [x] JSON chunk dataset
- [x] SentenceTransformer embeddings
- [x] ChromaDB indexing
- [x] Vector search
- [x] BM25 retrieval
- [x] Hybrid retrieval
- [x] Ollama integration
- [x] End-to-end RAG pipeline
- [x] Citation IDs

### In Progress

- [ ] Retrieval quality improvements
- [ ] Better hybrid score fusion
- [ ] Reranking improvements
- [ ] Evaluation framework
- [ ] FastAPI backend
- [ ] Chat UI

## Tech Stack

 - Python
 - SentenceTransformers
 - ChromaDB
 - Ollama
 - Llama 3.2
 - BM25
 - PyPDF
 - FastAPI (planned)

## Roadmap

 - Improve retrieval accuracy
 - Add evaluation metrics
 - Better reranking
 - Source URL citations
 - FastAPI backend
 - Web chat interface
 - Additional document connectors