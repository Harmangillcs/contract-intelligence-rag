from langchain_community.vectorstores import Chroma     
import os
from src.process import data_load, embedding_model, text_split
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

PATH_DIR=Path(__file__).resolve().parent.parent
DATA_DIR=PATH_DIR / "data"
VECTOR_DIR= PATH_DIR / "vectordb"

def create_vectordb():
    documents=data_load(str(DATA_DIR))
    chunks=text_split(documents)
    embedding = embedding_model()
    vectordb= Chroma.from_documents(
        chunks,
        embedding,
        persist_directory=str(VECTOR_DIR)
    )
    vectordb.persist()
    print("Downloaded the vectorstore")
    return vectordb

def load_vectordb():
    embedding = embedding_model()
    if VECTOR_DIR.exists() and any(VECTOR_DIR.iterdir()):
        vectordb=Chroma(
            embedding_function=embedding,
            persist_directory=str(VECTOR_DIR)
        )
        print(f"Already existed for loading...{VECTOR_DIR}")
    else:
        vectordb=create_vectordb()
        print("Creating new vectorstores...")
    return vectordb
    
if __name__=="__main__":
    create_vectordb()














