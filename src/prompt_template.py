from langchain_core.prompts import PromptTemplate

base_prompt = """
You are a helpful contract assistant.
Answer ONLY using the context provided below.
Do not hallucinate or add extra info.

Context:
{context}

Question: {question}

Answer:
"""
