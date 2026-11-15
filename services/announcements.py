from pathlib import Path
import pandas as pd

CATEGORIES = ["results", "M&A", "fund_raise", "management_change", "litigation", "insider_trading",
              "earnings_call", "investor_meetings", "credit_rating", "dividend", "bonus_split", "capex",
              "press_release", "postal_ballot", "agm_egm", "pledging", "unclassified"]
REQUIRED = ["date", "symbol", "headline", "details", "source_url"]

def load_announcements(uploaded_file=None, csv_path="data/announcements.csv"):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        source = "Uploaded CSV"
    elif Path(csv_path).exists():
        df = pd.read_csv(csv_path)
        source = "Local CSV"
    else:
        return pd.DataFrame(columns=REQUIRED + ["category", "priority"]), "No filing data loaded"
    for col in REQUIRED:
        if col not in df.columns:
            df[col] = ""
    if "category" not in df.columns: df["category"] = "unclassified"
    if "priority" not in df.columns: df["priority"] = "Medium"
    df["date"] = df["date"].astype(str)
    return df, source

def classify_fallback(headline, details=""):
    text = f"{headline} {details}".lower()
    rules = {
        "results": ["quarterly result", "financial result", "audited result", "unaudited result"],
        "M&A": ["acquisition", "merger", "demerger", "joint venture"],
        "management_change": ["resign", "appointed", "appointment", "ceo", "cfo", "managing director"],
        "dividend": ["dividend", "record date"], "capex": ["capital expenditure", "new plant", "capacity expansion"],
        "litigation": ["court", "tribunal", "penalty", "fine", "regulatory order"],
        "earnings_call": ["earnings call", "concall", "investor call"],
        "fund_raise": ["qip", "rights issue", "preferential allotment", "commercial paper", "buyback"]
    }
    for category, terms in rules.items():
        if any(t in text for t in terms): return category
    return "press_release"
