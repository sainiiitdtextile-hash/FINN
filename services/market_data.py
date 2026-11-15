import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=900, show_spinner=False)
def get_market_data(symbols):
    rows, histories, errors = [], {}, []
    for symbol in symbols:
        ticker = f"{symbol}.NS"
        try:
            hist = yf.Ticker(ticker).history(period="3mo", auto_adjust=True)
            if hist.empty or len(hist) < 2:
                errors.append(symbol)
                continue
            hist = hist.dropna(subset=["Close"])
            last, prev = float(hist.Close.iloc[-1]), float(hist.Close.iloc[-2])
            avg_vol = float(hist.Volume.iloc[:-1].tail(20).mean()) if len(hist) > 2 else 0
            volume = float(hist.Volume.iloc[-1]) if pd.notna(hist.Volume.iloc[-1]) else 0
            rows.append({"Symbol": symbol, "Price": last, "Change %": ((last/prev)-1)*100,
                         "Volume": volume, "20D Avg Volume": avg_vol,
                         "Volume / Avg": volume/avg_vol if avg_vol else 0})
            histories[symbol] = hist
        except Exception:
            errors.append(symbol)
    return pd.DataFrame(rows), histories, errors

def detect_alerts(df, price_threshold=3.0, volume_multiple=2.0):
    alerts = []
    if df is None or df.empty:
        return alerts
    for _, r in df.iterrows():
        reasons = []
        if abs(float(r["Change %"])) >= price_threshold:
            reasons.append(f"Price moved {r['Change %']:+.2f}%")
        if float(r["Volume / Avg"]) >= volume_multiple:
            reasons.append(f"Volume is {r['Volume / Avg']:.1f}× the 20-day average")
        if reasons:
            alerts.append({"symbol": r["Symbol"], "price": r["Price"], "change": r["Change %"], "reasons": reasons})
    return alerts
