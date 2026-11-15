import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from config.portfolio import PORTFOLIO
from services.market_data import get_market_data, detect_alerts
from services.announcements import load_announcements, classify_fallback, CATEGORIES
from services.groq_service import ask_groq, get_api_key
from services.research_engine import answer_from_documents
from utils.pdf_loader import extract_pdf_pages

st.set_page_config(
    page_title="FINN | Investment Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background: radial-gradient(circle at 10% 0%, #17283b 0, #0b1220 35%, #080d17 100%); color:#e7edf6;}
section[data-testid="stSidebar"] {background:#0b1422; border-right:1px solid #1e2b3e;}
h1,h2,h3 {font-family:'Manrope',sans-serif; letter-spacing:-.03em;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#142238,#101a2a); border:1px solid #24354b; padding:16px 18px; border-radius:14px;}
[data-testid="stMetricLabel"] {color:#9aabc1;}
[data-testid="stMetricValue"] {color:#f4f7fb;}
div[data-testid="stTabs"] button {font-weight:600;}
div.stButton>button {border-radius:10px; border:1px solid #31445e; background:#172941; color:#eef5ff;}
div.stButton>button:hover {border-color:#62b6a5; color:white;}
.finn-kicker {color:#69d6bd; font-size:12px; letter-spacing:.16em; font-weight:700; text-transform:uppercase;}
.finn-card {background:linear-gradient(145deg,rgba(23,39,60,.95),rgba(14,24,39,.95)); border:1px solid #263a53; padding:18px; border-radius:16px;}
.muted {color:#94a7bf;}
</style>
""", unsafe_allow_html=True)

if "research_pages" not in st.session_state:
    st.session_state.research_pages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.markdown("# ◈ FINN")
    st.caption("FINANCIAL INVESTMENT INTELLIGENCE")
    section = st.radio(
        "WORKSPACE",
        ["Today", "Intelligence", "Research"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**SYSTEM STATUS**")
    st.markdown("🟢 Market data connector · yfinance")
    st.markdown("🟢 Groq API configured" if get_api_key() else "🟡 Groq API key missing")
    st.caption("Prototype · End-of-day data · Not investment advice")
    st.divider()
    st.caption("FINN v0.1 · Built for the ENAM AI Engineer Build Challenge")

symbols = list(PORTFOLIO.keys())
with st.spinner("Loading end-of-day market data…"):
    market_df, histories, market_errors = get_market_data(symbols)

st.markdown('<div class="finn-kicker">Your investment intelligence desk</div>', unsafe_allow_html=True)
st.title({
    "Today": "See what matters.",
    "Intelligence": "Signals, not noise.",
    "Research": "Go beyond the headline.",
}[section])
st.markdown(
    '<div class="muted">A focused view of portfolio movements, company disclosures and primary-source research.</div>',
    unsafe_allow_html=True,
)
st.write("")

if section == "Today":
    if market_df.empty:
        st.warning(
            "Live market data could not be retrieved. Check your internet connection or try again later. "
            "No fabricated market prices are shown."
        )
        st.info("The dashboard will populate automatically when Yahoo Finance returns data.")
    else:
        avg_move = float(market_df["Change %"].mean())
        adv = int((market_df["Change %"] > 0).sum())
        decl = int((market_df["Change %"] < 0).sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tracked companies", f"{len(market_df)} / 18")
        c2.metric("Average daily move", f"{avg_move:+.2f}%")
        c3.metric("Advancers", adv)
        c4.metric("Decliners", decl)

        left, right = st.columns([1.55, 1])
        with left:
            st.subheader("Portfolio watchlist")
            view = market_df.copy()
            view["Company"] = view["Symbol"].map(PORTFOLIO)
            view = view[["Symbol", "Company", "Price", "Change %", "Volume / Avg"]].sort_values(
                "Change %", ascending=False
            )
            st.dataframe(
                view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn(format="₹ %.2f"),
                    "Change %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Volume / Avg": st.column_config.NumberColumn(format="%.2f×"),
                },
            )
        with right:
            st.subheader("Market pulse")
            fig = px.bar(
                market_df.sort_values("Change %"),
                x="Change %",
                y="Symbol",
                orientation="h",
                color="Change %",
                color_continuous_scale=["#e16b72", "#53647a", "#54c7a5"],
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=430,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("What deserves attention")
        alerts = detect_alerts(market_df, 3.0, 2.0)
        if alerts:
            for alert in alerts:
                st.warning(
                    f"**{alert['symbol']}** · ₹{alert['price']:,.2f} · {alert['change']:+.2f}% — "
                    + "; ".join(alert["reasons"])
                )
        else:
            st.success("No stocks crossed the default alert thresholds today.")
        st.caption(
            "Price and volume indicators use the latest available daily candle. "
            "This is not a real-time portfolio valuation; equal weighting is not assumed."
        )

    with st.expander("Configure unusual-movement thresholds"):
        price_threshold = st.slider("Absolute daily price move (%)", 1.0, 10.0, 3.0, 0.5)
        volume_threshold = st.slider("Volume vs 20-day average (×)", 1.0, 5.0, 2.0, 0.25)
        if not market_df.empty:
            custom_alerts = detect_alerts(market_df, price_threshold, volume_threshold)
            st.write(f"{len(custom_alerts)} alert(s) at your selected thresholds.")

elif section == "Intelligence":
    st.markdown("Monitor corporate disclosures and identify events that may deserve investor attention.")
    uploaded = st.file_uploader(
        "Upload an announcements CSV",
        type=["csv"],
        help="Expected columns: date, symbol, headline, details, source_url. Optional: category, priority.",
    )
    ann, source = load_announcements(uploaded)
    st.caption(
        f"Filing data source: {source}. Local sample rows, if present, are explicitly illustrative—not live exchange filings."
    )

    if not ann.empty:
        ann["category"] = ann.apply(
            lambda row: row["category"]
            if str(row["category"]).strip() not in ["", "nan", "None"]
            else classify_fallback(row["headline"], row["details"]),
            axis=1,
        )
        ann["priority"] = ann["priority"].fillna("Medium")

        f1, f2, f3 = st.columns(3)
        category_filter = f1.selectbox("Announcement category", ["All"] + CATEGORIES)
        priority_filter = f2.selectbox("Priority", ["All", "High", "Medium", "Low"])
        symbol_filter = f3.selectbox(
            "Company",
            ["All"] + sorted(ann.symbol.dropna().astype(str).unique().tolist()),
        )

        filtered = ann.copy()
        if category_filter != "All":
            filtered = filtered[filtered.category == category_filter]
        if priority_filter != "All":
            filtered = filtered[filtered.priority.str.lower() == priority_filter.lower()]
        if symbol_filter != "All":
            filtered = filtered[filtered.symbol == symbol_filter]

        for _, row in filtered.iterrows():
            priority = str(row.get("priority", "Medium")).lower()
            color = "🔴" if priority == "high" else "🟡" if priority == "medium" else "⚪"
            with st.container(border=True):
                st.markdown(
                    f"{color} **{row['symbol']}** · `{row['category']}` · {row['date']}"
                )
                st.markdown(f"#### {row['headline']}")
                st.write(row["details"])
                source_url = str(row.get("source_url", "")).strip()
                if source_url and source_url.lower() != "nan":
                    st.link_button("Open original filing", source_url)
                if st.button("Generate AI investor brief", key=f"brief_{row.name}"):
                    try:
                        brief = ask_groq(
                            "You are FINN, an investment intelligence analyst. Do not invent facts. "
                            "Distinguish filing facts from possible implications. Do not give buy/sell advice.",
                            f"Company: {row['symbol']}\nHeadline: {row['headline']}\n"
                            f"Filing details: {row['details']}\nCategory: {row['category']}\n\n"
                            "Return: 1) What happened 2) Why an investor may care 3) What to verify next. "
                            "If information is insufficient, say so.",
                            max_tokens=700,
                        )
                        st.markdown(brief)
                    except Exception as exc:
                        st.error(str(exc))
    else:
        st.info("No announcements loaded yet. Upload an exchange export or your own CSV to activate this feed.")

    st.divider()
    st.subheader("How this ingestion works")
    st.write(
        "The MVP accepts a standardised CSV so that the classification and prioritisation workflow can be tested "
        "reliably. A production NSE/BSE connector requires a stable, permitted exchange data-access method; "
        "the app does not pretend that the sample fixture is a live feed."
    )

else:
    st.markdown("Research a company using its annual reports, investor presentations and earnings-call transcripts.")
    with st.expander(
        "1 · Add primary-source documents",
        expanded=not bool(st.session_state.research_pages),
    ):
        uploaded_pdfs = st.file_uploader(
            "Upload searchable PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
        )
        if st.button("Process documents", type="primary", disabled=not uploaded_pdfs):
            pages = []
            with st.spinner("Extracting text and page references…"):
                for pdf_file in uploaded_pdfs:
                    try:
                        pages.extend(extract_pdf_pages(pdf_file.getvalue(), pdf_file.name))
                    except Exception as exc:
                        st.error(f"Could not read {pdf_file.name}: {exc}")
            st.session_state.research_pages = pages
            st.session_state.chat_history = []
            st.success(
                f"Processed {len(pages)} text-bearing pages from {len(uploaded_pdfs)} document(s)."
            )

    pages = st.session_state.research_pages
    if pages:
        document_names = sorted({page["source"] for page in pages})
        st.success(
            f"Research library ready · {len(document_names)} document(s) · "
            f"{len(pages)} pages with extractable text"
        )
        st.caption("Only uploaded document excerpts are passed to the model. Citations refer to PDF page numbers.")

        suggested_questions = [
            "Summarise the company's business segments and revenue mix.",
            "What are the latest reported revenue, EBITDA and PAT figures? Cite the source pages.",
            "What does management say about growth, margins and capex guidance?",
            "Compare management's stated expectations with reported outcomes in the uploaded documents.",
            "Assess cash generation, debt and working-capital risks using the documents.",
        ]
        for index, prompt in enumerate(suggested_questions):
            if st.button(prompt, key=f"suggested_question_{index}"):
                st.session_state.pending_question = prompt

        question = st.chat_input("Ask about the uploaded company documents…")
        if "pending_question" in st.session_state:
            question = st.session_state.pop("pending_question")

        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.spinner("Retrieving relevant pages and analysing with Groq…"):
                try:
                    answer, used_sources = answer_from_documents(pages, question)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer, "sources": used_sources}
                    )
                except Exception as exc:
                    st.error(str(exc))

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("sources"):
                    with st.expander("Retrieved source pages"):
                        for source in message["sources"]:
                            st.caption(
                                f"{source['source']} · p. {source['page']} · "
                                f"retrieval score {source['score']:.3f}"
                            )
    else:
        st.info(
            "Upload at least one searchable annual report or earnings-call transcript PDF to start research. "
            "Scanned/image-only PDFs may need OCR and are not yet supported in this MVP."
        )

st.divider()
st.caption(
    f"FINN · Data timestamp: {datetime.now().strftime('%d %b %Y, %H:%M')} · "
    "Market data may be delayed · For research and demonstration only, not investment advice."
)
