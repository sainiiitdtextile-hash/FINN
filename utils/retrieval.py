from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def _expanded_query(question):
    q = question.lower()
    terms = [question]

    if any(x in q for x in ["cash flow", "cashflow", "free cash flow", "cash conversion"]):
        terms.append(
            "consolidated statement of cash flows cash flows from operating activities "
            "net cash flows generated from operating activities cash flows generated from operations "
            "purchase of property plant and equipment purchase of intangible assets capital expenditure"
        )

    if any(x in q for x in ["ebitda", "ebit", "pbt", "pat", "profit before tax", "profit after tax"]):
        terms.append(
            "consolidated statement of profit and loss revenue from operations profit before tax "
            "profit for the year profit attributable to shareholders exceptional items "
            "depreciation and amortisation finance costs operating profit EBITDA EBIT"
        )

    if any(x in q for x in ["going concern", "audit qualification", "auditor qualification"]):
        terms.append(
            "independent auditor report opinion basis for opinion emphasis of matter "
            "material uncertainty related to going concern specific finding"
        )

    if any(x in q for x in ["segment", "vertical", "revenue mix"]):
        terms.append(
            "industry vertical segment revenue share segment performance banking financial services "
            "manufacturing consumer business communication media technology life sciences healthcare"
        )

    return " ".join(terms)


def retrieve_chunks(pages, question, top_k=9):
    if not pages:
        return []
    texts = [p.get("text", "") for p in pages]
    query = _expanded_query(question)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=40000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = scores.argsort()[::-1]
    results = []
    for i in ranked:
        if scores[i] <= 0:
            continue
        results.append(dict(pages[i], score=float(scores[i])))
        if len(results) >= top_k:
            break
    return results
