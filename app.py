import os
import uuid
import json
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import pdfplumber

from src.process import data_load, text_split, embedding_model
from src.utils import create_vectordb, load_vectordb, VECTOR_DIR, DATA_DIR
from src.prompt_template import base_prompt
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Contract Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    
    allow_methods=["*"],   
    allow_headers=["*"],   
)

vectordb = load_vectordb()
retriever = vectordb.as_retriever(search_kwargs={"k": 4})

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

prompt = PromptTemplate(
    template=base_prompt,
    input_variables=["context", "question"]
)


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)


#pydantic
class IngestResponse(BaseModel):
    document_ids: list

class ExtractRequest(BaseModel):
    document_id: str

class AskRequest(BaseModel):
    question: str

class AuditRequest(BaseModel):
    document_id: str

#endpoints 
@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: list[UploadFile] = File(...)):
    ids = []

    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF allowed")

        name = f"{uuid.uuid4().hex}_{f.filename}"
        dest = Path(DATA_DIR) / name

        with dest.open("wb") as buffer:
            shutil.copyfileobj(f.file, buffer)

        ids.append(name)

    create_vectordb()

    return {"document_ids": ids}

@app.post("/extract")
def extract(req: ExtractRequest):
    pdf_path = Path(DATA_DIR) / req.document_id
    if not pdf_path.exists():
        raise HTTPException(404, "File not found")

    text = ""
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")

    extract_prompt = f"""
    Extract structured fields from the contract.
    
    Return STRICT JSON:
    {{
      "parties": [],
      "effective_date": "",
      "term": "",
      "governing_law": "",
      "payment_terms": "",
      "termination": "",
      "auto_renewal": "",
      "confidentiality": "",
      "indemnity": "",
      "liability_cap": "",
      "signatories": []
    }}

    Contract:
    {text[:3500]}
    """

    result_message = llm.invoke(extract_prompt)
    result_text = result_message.content  

    try:
        first_json = result_text[result_text.index("{"): result_text.rindex("}") + 1]
        parsed = json.loads(first_json)
    except:
        parsed = {"raw": result_text}

    return {"document_id": req.document_id, "extracted": parsed}

@app.post("/ask")
def ask(req: AskRequest):
    answer = rag_chain.invoke(req.question)
    return {"answer": answer}

@app.get("/ask/stream")
async def ask_stream(question: str):
    answer = rag_chain.invoke(question)

    def stream():
        for i in range(0, len(answer), 200):
            yield answer[i:i + 200]

    return StreamingResponse(stream(), media_type="text/plain")

@app.post("/audit")
def audit(req: AuditRequest):
    pdf_path = Path(DATA_DIR) / req.document_id
    if not pdf_path.exists():
        raise HTTPException(404, "File not found")

    text = ""
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")

    risk_prompt = f"""
    You are a Legal Risk Detection AI.
    Return STRICT JSON:
    {{
      "risks": [
        {{"type":"", "severity":"", "evidence":"", "explanation":""}}
      ]
    }}

    Analyze risks like:
    - Auto-renewal < 30 days
    - Unlimited liability
    - Broad indemnity
    - Ambiguous payment terms
    - Missing governing law

    Contract:
    {text[:4000]}
    """

    result_message = llm.invoke(risk_prompt)
    result_text = result_message.content  

    try:
        first_json = result_text[result_text.index("{"): result_text.rindex("}") + 1]
        parsed = json.loads(first_json)
    except:
        parsed = {"raw": result_text}

    return {"document_id": req.document_id, "risks": parsed}

@app.websocket("/ws/ask")
async def ws_ask(ws: WebSocket):
    await ws.accept()
    q = await ws.receive_text()
    ans = rag_chain.invoke(q)
    await ws.send_text(ans)
    await ws.close()
