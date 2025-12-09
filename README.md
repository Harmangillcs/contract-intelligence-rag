# Contract Intelligence API

A FastAPI-based application to ingest contracts (PDFs), extract structured data, answer questions, and perform legal risk analysis using OpenAI's GPT models and LangChain RAG pipelines.

## Features
- **Ingest PDFs**: Upload contracts to store in a local `data/` directory and vector database.
- **Extract structured fields**: Extract parties, effective date, term, payment terms, governing law, etc.
- **Ask questions**: Ask questions about contracts using a Retrieval-Augmented Generation (RAG) pipeline.
- **Audit contracts**: Detect potential risks like auto-renewal, broad indemnity, unlimited liability, and ambiguous payment terms.
- **WebSocket support**: Stream answers in real-time using `/ws/ask`.
- **Dockerized**: Run easily in Docker without additional setup.

Set environment variable:
```bash
export OPENAI_API_KEY=your_openai_api_key
```

## Local Setup
Create a virtual environment and install dependencies:
```bash
python -m venv bot
# On Windows: bot\Scripts\activate
pip install -r requirements.txt
```

Run locally:
```bash
uvicorn app:app --reload
```

## Docker Setup
Pull the image:
```bash
docker pull harmangal/contract
```

Run the container:
```bash
docker run -d \
  -p 8080:8080 \
  --env OPENAI_API_KEY=your_key_here \
  -v /data:/app/data \
  harmangal/contract
```

Access docs:
```
http://localhost:8080/docs
```

## API Endpoints

### 1. Health Check
```
GET /healthz
```
**Response:**
```json
{"status": "ok"}
```

### 2. Ingest PDFs
```
POST /ingest
```
**Request:** Upload PDF(s)
```bash
curl -X POST "http://localhost:8080/ingest" \
  -F "files=@contract1.pdf"
```
**Response:** (Success message or file ID)

### 3. Extract Contract Fields
```
POST /extract
```
**Request:**
```bash
curl -X POST 'http://localhost:8080/extract' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": "a9154f269ee8471b8b7e0395a77bdbb4_contract1.pdf"
  }'
```
**Response:** Structured fields (JSON)

### 4. Ask Questions
```
POST /ask
```
**Request:**
```bash
curl -X POST 'http://localhost:8080/ask' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What is the payment term?"
  }'
```
**Response:**
```json
{"answer": "Client will pay Provider $5000 per month within 15 days of invoice."}
```

### 5. Streamed Answers
```
GET /ask/stream
```
**Request:** (Query params for question)

### 6. Audit Contract Risks
```
POST /audit
```
**Request:**
```bash
curl -X POST 'http://localhost:8080/audit' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": "a9154f269ee8471b8b7e0395a77bdbb4_contract1.pdf"
  }'
```
**Response:** Risk analysis (JSON)