# AI RAG Assistant

A fully local Retrieval-Augmented Generation (RAG) assistant that indexes technical documentation and answers questions using hybrid retrieval, local embeddings, and a local LLM through Ollama.

The project is designed as a production-style RAG pipeline with evaluation tools, a REST API, and a web chat interface.

---

# Features

## 📄 Multi-format document ingestion

- Markdown (.md, .mdx)
- Text (.txt)
- reStructuredText (.rst)
- CSV
- JSON / JSONL
- PDF

---

## ✂️ Structure-aware chunking

- Markdown heading awareness
- Recursive splitting
- Overlapping chunks
- Citation IDs
- Metadata preservation

---

## 🧠 Embeddings

- sentence-transformers/all-MiniLM-L6-v2

---

## 🗂️ Vector Database

- ChromaDB

---

## 🔍 Hybrid Retrieval

- Semantic vector search
- BM25 lexical retrieval
- Hybrid fusion
- FastAPI-specific document boosting
- Metadata-aware reranking
- Optional CrossEncoder reranking
- Confidence scoring
- URL-aware source metadata

---

## 🤖 Local LLM

- Ollama
- Llama 3.2

---

## 🌐 REST API

Built with FastAPI.

Endpoints include:

- Chat
- Streaming chat (experimental)
- Conversation history
- Conversation management
- Conversation deletion
- Feedback submission

---

## 💬 Web Interface

Built with Streamlit.

Features:

- Modern chat interface
- Multiple conversations
- Persistent chat history
- Confidence score
- Clickable documentation sources
- Feedback system (thumbs up/down + comments)
- Conversation deletion
- Fully local execution
---

## 📚 Source Citations

Every answer includes:

- Retrieved source documents
- Direct links to the original documentation (when available)
- Clickable references from the chat interface
---

## 💾 Local Storage

SQLite is used to store:

- Conversation history
- Chat messages
- User feedback
- Confidence scores
---

## 📊 Evaluation

### Retrieval Evaluation

- Recall@1
- Recall@3
- Recall@5
- MRR

### Generation Evaluation

LLM-as-a-Judge scoring using Ollama.

Evaluates:

- Faithfulness
- Correctness
- Relevance
- Hallucination rate

---

## 🖥️ Fully Local

- No OpenAI API
- No cloud services
- Offline capable

---

# Architecture

```text
                  Documents
 (.md .pdf .json .csv .txt .rst ...)
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
          Sentence Transformers
                     │
                     ▼
                Embeddings
                     │
                     ▼
                 ChromaDB
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     Vector Search         BM25 Search
          └──────────┬──────────┘
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
              Generated Answer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     FastAPI API          Streamlit UI
```

---

# Project Structure

```text
ai-rag-assistant/

├── data/
│   ├── chat_history.db
│   ├── chunks.json
│   ├── judge_results.json
│   ├── results.csv
│   ├── chroma/
│   └── evaluation_dataset50.json
│
├── docs/ (where you put your documents)
│
├── scripts/
│   ├── build_chunks.py
│   ├── build_index.py
│   ├── eval.py
│   ├── search.py
│   └── tune_retreval.py (for tunning)
│
├── src/
│   ├── api/
│   ├── chunking/
│   ├── evaluation/
│   ├── generation/
│   ├── indexing/
│   ├── ingestion/
│   ├── retrieval/
│   └── models/
│
├── ui/
│   └── app.py
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

## Before Installation

Important: The repository includes the FastAPI documentation corpus used for development and evaluation.

Before building the index, delete everything inside the docs/ folder and add your own documentation files (Markdown, PDF, JSON, TXT, etc.).

Example:
```
Delete

docs/fastapi/

docs/chromadb/

Add your own corpus

docs/my_docs/

docs/product_docs/

docs/company_docs/

Then run the indexing pipeline normally.
```
# Installation

```bash
git clone https://github.com/<your-name>/ai-rag-assistant.git

cd ai-rag-assistant

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

---

# Install Ollama

```bash
ollama pull llama3.2:3b
```

---

# Build the Index

```bash
python scripts/build_chunks.py

python scripts/build_index.py
```

---

# Run CLI Search (optional)

```bash
python scripts/search.py
```

---

# Run FastAPI

```bash
python -m uvicorn src.api.app:app --reload
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

---

# Run Streamlit

```bash
streamlit run ui/app.py
```

---

# Evaluation (takes about 20-30 min related to your Q/A)

Run retrieval + generation evaluation:

```bash
python scripts/eval.py
```

Run retriever tests:

```bash
python -m unittest discover -s tests
```

---

# Current Results

## Retrieval (50-question benchmark)

| Metric | Score |
|---------|-------|
| Recall@1 | **64%** |
| Recall@3 | **92%** |
| Recall@5 | **98%** |
| MRR | **0.782** |

---

## LLM-as-a-Judge

| Metric | Score |
|---------|-------|
| Faithfulness | **3.88 / 5** |
| Correctness | **4.34 / 5** |
| Relevance | **4.74 / 5** |
| Hallucination Rate | **0%** |

---

# Completed

- ✅ Multi-format ingestion
- ✅ Structure-aware chunking
- ✅ Citation IDs
- ✅ URL extraction from documentation
- ✅ ChromaDB indexing
- ✅ SentenceTransformer embeddings
- ✅ BM25 retrieval
- ✅ Hybrid retrieval
- ✅ Confidence scoring
- ✅ CrossEncoder reranking
- ✅ Ollama integration
- ✅ Prompt builder
- ✅ Retrieval evaluation
- ✅ LLM-as-a-Judge evaluation
- ✅ FastAPI REST API
- ✅ Streamlit UI
- ✅ Conversation history
- ✅ Multiple conversations
- ✅ Delete conversations
- ✅ Source citations
- ✅ Clickable documentation links
- ✅ SQLite chat history
- ✅ User feedback collection (👍 / 👎 + comments)
---

# In Progress

- 🚧 Streaming responses
- 🚧 Automatic chat titles
- 🚧 Evaluation report command
- 🚧 Query rewriting
- 🚧 Authentication
- 🚧 Deployment
---

# Tech Stack

- Python
- FastAPI
- Streamlit
- SQLite
- ChromaDB
- SentenceTransformers
- BM25
- CrossEncoder
- Ollama
- Llama 3.2
- PyPDFPDF

---

# Roadmap

- Authentication
- Deployment
- Desktop application
- Automatic conversation titles
- Streaming chat responses
- Query rewriting
- Evaluation report generation
- Improved hybrid search
- Additional document connectors
- Docker support