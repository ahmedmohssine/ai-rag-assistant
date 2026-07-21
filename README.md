# AI RAG Assistant

A fully local Retrieval-Augmented Generation (RAG) assistant that indexes technical documentation and answers questions using hybrid retrieval, local embeddings, and a local LLM through Ollama.

The project is designed as a production-style RAG pipeline with evaluation tools, a REST API, and a web chat interface.

---

# Features

## 📄 Multi-format document ingestion

- Markdown (.md, .mdx)
- Text (.txt)
- reStructuredText (.rst)
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

## 🔍 Hybrid Retrieval & UI Controls

- Semantic vector search
- BM25 lexical retrieval
- Hybrid fusion
- FastAPI-specific document boosting
- Metadata-aware reranking
- Optional CrossEncoder reranking
- Confidence scoring
- URL-aware source metadata
- **Configurable Context Count (Top-K)** adjustable straight from the sidebar
- **Post-Retrieval Document Filtering** to match specific document path scopes

---

## 🤖 Local LLM & Streaming

- Ollama
- Llama 3.2
- **Automatic Conversation Titles** generated using the local LLM instead of character truncation
- **Real-time token streaming** with custom typewriter animations via Streamlit and FastAPI `StreamingResponse`

---

## 🌐 REST API

Built with FastAPI.

Endpoints include:

- Chat (with full metadata and streaming capabilities)
- Conversation history
- Conversation management
- Conversation deletion (Isolated per user)
- User registration
- User login (JWT authentication)
- Feedback submission (Isolated per user)

---

## 💬 Web Interface

Built with Streamlit.

Features:

- Modern chat interface with custom styling
- Multiple conversations with an LLM title engine
- **Persistent browser login sessions** synced via native JavaScript browser storage and URL tracking
- Active "Thinking Phase" loaders during initial RAG pipeline operations
- Confidence score expanders
- Clickable documentation sources
- Feedback system (thumbs up/down + text area comments)
- Conversation deletion
- User authentication
- Login & registration
- Fully local execution

## 📚 Source Citations

Every answer includes:

- Retrieved source documents
- Direct links to the original documentation (when available)
- Clickable references from the chat interface
---

## 💾 Local Storage

SQLite is used to store:

- User accounts
- Password hashes (bcrypt)
- Conversation history
- Chat messages
- Confidence scores
- Source metadata
- User feedback tracking
---

## 📊 Evaluation & Failure Reporting

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

### Failure Tracking Reports

Automated logging saves granular execution context blocks directly under the `data/` directory for analytical debugging:
- **`evaluation_report.json`**: Broad automated matrix summary metrics.
- **`retrieval_failures.json`**: Isolated records where documents were missed within Top-K.
- **`generation_failures.json`**: Tracks LLM judge hallucinations or critically low metric drops.
- **`worst_judged_answers.json`**: Sorts and slices the bottom-10 lowest-scoring generation answers.

---

## 🔐 Authentication & Session Security

The assistant includes a cryptographically secure, isolated authentication system.

Features:

- Email/password registration
- Secure password hashing using `bcrypt`
- Secure cryptographic session signing using **JSON Web Tokens (JWT)** via `pyjwt`
- **Strict Per-User Conversation Isolation**: Access control layers check ownership before returning histories, processing deletions, or appending metrics to feedback rows.

---

## 🖥️ Fully Local

- No OpenAI API
- No cloud services
- Offline capable

---

## 🐳 Docker Support

The application can be run either natively or through Docker Compose.

Containers include:

- FastAPI backend
- Streamlit frontend
- Shared persistent ChromaDB storage
- Connects to a local Ollama instance running on the host machine

---

# Architecture

```text
                  Documents
 (.md .pdf .json .txt .rst ...)
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
          Ollama (Host Machine)
                     │
                     ▼
              Generated Answer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
        FastAPI            Streamlit
          │                     │
          └──────────┬──────────┘
                     ▼
             Docker Compose
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
│   ├── evaluation_report.json     # Saved evaluation metrics
│   ├── retrieval_failures.json     # Tracks search issues
│   ├── generation_failures.json    # Tracks low faithfulness/hallucinations
│   ├── worst_judged_answers.json   # Slices bottom 10 low-quality logs
│   ├── chroma/
│   └── evaluation_dataset50.json
│
├── docs/ (where you put your documents)
│
├── scripts/
│   ├── build_chunks.py
│   ├── build_index.py
│   ├── eval.py                     # Generates comprehensive evaluation reports
│   ├── search.py
│   └── tune_retrieval.py (for tuning)
│
├── src/
│   ├── api/
│   │   ├── app.py
│   │   ├── auth_utils.py           # JWT encoder/decoder helpers
│   │   ├── database.py
│   │   ├── models.py
│   │   └── services.py
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

# Before Installation

The repository includes the FastAPI and ChromaDB documentation corpora used for development and evaluation.

If you want to use your own knowledge base:

1. Remove the sample documentation under `docs/`.
2. Add your own documentation (Markdown, PDF, JSON, TXT, RST, etc.).
3. Rebuild the chunks and vector index before starting the application.

Example:

```text
Remove

docs/FastAPI/
docs/ChromaDB/

Add

docs/my_docs/
docs/product_docs/
docs/company_docs/
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/ai-rag-assistant.git
cd ai-rag-assistant
```

---

# Install Ollama

Install Ollama from https://ollama.com/download

Then download the model used by the project:

```bash
ollama pull llama3.2:3b
```

Verify it is available:

```bash
ollama list
```

---

# Docker (Recommended)

Build the application:

```bash
docker compose build
```

Start all services:

```bash
docker compose up
```

Or run in detached mode:

```bash
docker compose up -d
```

The Docker setup starts:

- FastAPI backend
- Streamlit frontend

Ollama runs on the host machine and is accessed from the containers through `host.docker.internal`.

---

# Build the Index

Whenever you change the documentation corpus, rebuild the chunks and embeddings.

Inside the backend container:

```bash
docker compose exec backend python scripts/build_chunks.py
docker compose exec backend python scripts/build_index.py
```

---

# CLI Search (Optional)

```bash
docker compose exec backend python scripts/search.py
```

---

# API

FastAPI Swagger UI:

```
http://localhost:8000/docs
```

---

# Web Interface

Streamlit:

```
http://localhost:8501
```

---

# Evaluation

Run the complete retrieval and generation benchmark:

```bash
docker compose exec backend python scripts/eval.py
```

The evaluation automatically generates:

- `evaluation_report.json`
- `retrieval_failures.json`
- `generation_failures.json`
- `worst_judged_answers.json`

---

# Unit Tests

```bash
docker compose exec backend python -m unittest discover -s tests
```

---

# Running Without Docker (Optional)

If you prefer running everything locally:

Create a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python -m uvicorn src.api.app:app --reload --reload-dir src
```

Start the frontend:

```bash
streamlit run ui/app.py
```

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
- ✅ FastAPI REST API with real-time text token streaming
- ✅ Streamlit UI with typed stream renders and persistent thinking animations
- ✅ Local LLM Automatic Title Generation for chats
- ✅ Token failure logs (`retrieval_failures.json`, `generation_failures.json`, `worst_judged_answers.json`)
- ✅ Secure Token Sessions: **JWT Authentication integration**
- ✅ Secure Client Persistence: Native cross-messaging browser injection
- ✅ **Strict Per-User Data Separation & Verification Isolation**
- ✅ Configurable Sidebar UI panel: Dynamic **Top-K Context counts** and **Path Filtering keyword matchers**
- ✅ Dockerized backend
- ✅ Dockerized Streamlit frontend
- ✅ Docker Compose orchestration
- ✅ Local Ollama integration from Docker containers
---

# Tech Stack

- Python
- FastAPI
- Streamlit
- SQLite
- PyJWT
- bcrypt
- ChromaDB
- SentenceTransformers
- BM25
- CrossEncoder
- Ollama
- Llama 3.2
- PyPDF
- Docker
- Docker Compose

---

# Roadmap

## User Experience
- Automatic Ollama installation detection
- Automatic model detection (`llama3.2:3b`)
- One-click model download if missing
- Automatic Docker startup verification
- Automatic browser launch after startup
- Native desktop launcher (Windows)

## Deployment
- Docker multi-container orchestration
- One-click installer (Windows)
- Standalone desktop application
- Automatic application updates

## Authentication & Users
- Google OAuth login
- Per-user metadata workspace separation
- User roles & administration panel

## Document Support
- Additional file connector parsing modules
- Microsoft Office documents (.docx, .pptx, .xlsx)
- HTML website ingestion
- ZIP archive ingestion

## Monitoring & Evaluation
- Evaluation dashboard
- Retrieval performance visualization
- Feedback analytics
- Conversation analytics
- Exportable evaluation reports
