from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def retrieve_chunks(pages, question, top_k=5):
    if not pages: return []
    texts = [p["text"] for p in pages]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=30000)
    matrix = vectorizer.fit_transform(texts + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = scores.argsort()[::-1][:top_k]
    return [dict(pages[i], score=float(scores[i])) for i in ranked if scores[i] > 0]
