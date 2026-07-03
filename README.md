# AI Developer Assistant (RAG)

A Retrieval-Augmented Generation (RAG) assistant that answers questions about AI developer documentation using semantic search and a local Large Language Model (LLM).

This project is being developed as an internship project focused on building a complete RAG pipeline from document ingestion to answer generation.

---

## Features

### Document Ingestion
- Read Markdown documentation recursively
- Document metadata extraction
- Structured `Document` model

### Chunking
- Fixed-size overlapping chunking (MVP)
- Chunk metadata
- JSON dataset generation

### Embeddings
- SentenceTransformers (`all-MiniLM-L6-v2`)
- Batch embedding generation

### Vector Database
- ChromaDB persistent storage
- Automatic indexing
- Metadata stored with every chunk

### Retrieval
- Semantic similarity search
- Configurable Top-K retrieval
- Retriever abstraction

### Generation
- Local LLM using Ollama
- Context-aware answer generation
- Sources displayed with every answer

---

## Current Architecture

```
Documents (Markdown for now)
     │
     ▼
Document Reader (Select only Markdown documents)
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
Retriever
     │
     ▼
Ollama (Llama)
     │
     ▼
Generated Answer
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
├── requirements.txt (empty)
│
└── README.md

```

---

## Tech Stack

- Python
- ChromaDB
- SentenceTransformers
- Ollama
- Llama 3.2
- Markdown corpus

---

## Current Corpus

- FastAPI Documentation
- ChromaDB Documentation

Approximately:

- 155 Markdown documents
- 1910 indexed chunks

---

## Running the Project

### 1. Generate chunks

```bash
python scripts/build_chunks.py
```

### 2. Build the vector index

```bash
python scripts/build_index.py
```

### 3. Start the assistant

```bash
python scripts/search.py
```

---

## Example

```
Question:
How do I create a FastAPI route?

↓

Retriever searches ChromaDB

↓

Top relevant chunks are retrieved

↓

Ollama generates an answer using only the retrieved context

↓

Sources are displayed alongside the answer
```

---

## Roadmap

- [x] Document ingestion
- [x] MVP chunking
- [x] Embeddings
- [x] ChromaDB vector index
- [x] Semantic retrieval
- [x] Ollama integration
- [x] End-to-end RAG pipeline

### Next

- [ ] Read a heterogeneous document corpus
- [ ] Recursive/Semantic chunking
- [ ] BM25 lexical search
- [ ] Hybrid retrieval (Vector + BM25)
- [ ] Re-ranking
- [ ] Citation formatting
- [ ] FastAPI backend
- [ ] Web chat interface
- [ ] Evaluation (Recall@K, MRR, Ragas)
- [ ] Deployment

---

## Status

🚧 Work in Progress

The current version provides a fully functional MVP capable of answering questions over an indexed documentation corpus using Retrieval-Augmented Generation (RAG). Future iterations will focus on improving retrieval quality, evaluation, and user experience.