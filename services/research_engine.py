from utils.retrieval import retrieve_chunks
from services.groq_service import ask_groq

SYSTEM = """You are FINN, a careful financial research assistant. Use ONLY the supplied primary-source excerpts. Do not use outside knowledge or invent facts, figures, guidance, or dates. If the excerpts do not answer the question, say what is missing. Distinguish reported facts from interpretation. Cite every material factual claim inline as [Document, p. X]. This is research support, not investment advice."""

def answer_from_documents(pages, question, top_k=6):
    chunks = retrieve_chunks(pages, question, top_k=top_k)
    if not chunks:
        return "I couldn't find relevant text in the uploaded documents. Try a more specific question or upload a searchable PDF.", []
    context = "\n\n".join(f"SOURCE: {c['source']}, PAGE: {c['page']}\n{c['text'][:7000]}" for c in chunks)
    answer = ask_groq(SYSTEM, f"QUESTION:\n{question}\n\nPRIMARY-SOURCE EXCERPTS:\n{context}\n\nAnswer with concise headings and citations.", max_tokens=1800)
    return answer, chunks
