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

Clone the repository:

```bash
git clone https://github.com/<your-username>/ai-rag-assistant.git
cd ai-rag-assistant
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
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

To prevent database update logs from triggering full server reloads, lock the uvicorn monitoring watcher scope to your source codebase folder:


```bash
python -m uvicorn src.api.app:app --reload --reload-dir src
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
- ✅ FastAPI REST API with real-time text token streaming
- ✅ Streamlit UI with typed stream renders and persistent thinking animations
- ✅ Local LLM Automatic Title Generation for chats
- ✅ Token failure logs (`retrieval_failures.json`, `generation_failures.json`, `worst_judged_answers.json`)
- ✅ Secure Token Sessions: **JWT Authentication integration**
- ✅ Secure Client Persistence: Native cross-messaging browser injection
- ✅ **Strict Per-User Data Separation & Verification Isolation**
- ✅ Configurable Sidebar UI panel: Dynamic **Top-K Context counts** and **Path Filtering keyword matchers**
---

# In Progress

- 🚧 Deployment
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

---

# Roadmap

- Google OAuth login
- Docker Multi-Container orchestration
- Per-user metadata workspace separation
- Desktop wrapper assembly
- Additional file connector parsing modules