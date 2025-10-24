# ladder_calculator.py — Ladder Calculator (boxed, crisp, white outlines)

import streamlit as st

st.set_page_config(page_title="Ladder Calculator", page_icon="📊", layout="centered")

# ---------- Global CSS ----------
st.markdown("""
<style>
  * { font-family: Helvetica, Arial, sans-serif !important; }
  h1,h2,h3,h4,strong,b { font-weight: 700 !important; letter-spacing:.2px; }
  .subtitle { font-style: italic; margin-top:-6px; margin-bottom:14px; }

  /* Make all bordered containers crisp & white */
  div[data-testid="stContainer"][aria-expanded="true"],
  div[data-testid="stContainer"][class*="stContainer"][style*="border"] {
    border-color: #ffffff !important;
  }
  /* Generic border polish for st.container(border=True) */
  .st-emotion-cache-ue6h4q, .st-emotion-cache-1jicfl2, .st-emotion-cache-1r6slb0 {
    border: 1px solid #ffffff !important;
    border-radius: 14px !important;
  }

  /* Button-like radio for SL buffer */
  .slbtn [role="radiogroup"] { margin:0 !important; }
  .slbtn [role="radiogroup"] label {
    border:1px solid rgba(255,255,255,0.18);
    border-radius:999px;
    padding:6px 12px;
    margin-right:8px;
    cursor:pointer;
  }
  .slbtn [role="radiogroup"] input:checked ~ div {
    background:rgba(130,180,255,0.25);
    border-radius:999px;
    padding:6px 12px;
  }

  /* Value cards */
  .valbox { border-radius:12px; padding:12px 14px; text-align:center; font-weight:800; font-size:1.05rem; }
  .val-red   { background:#3b1d1d; color:#ff6b6b; }
  .val-green { background:#1d3b1d; color:#66ff91; }
  .val-blue  { background:#1d263b; color:#8eb8ff; }

  /* Bold inputs */
  .stNumberInput > div > div > input { font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------- Constants ----------
DEC = 4
BASE_STEP_MULT = 0.5    # base spacing = 0.5 × ATR
NUDGE_MULT = 0.25       # MACD nudge = ±0.25 × ATR
TP_MULT = 2.0           # fixed: TP = 2.0 × ATR

# ---------- Title & Slogan ----------
st.markdown("# Ladder Calculator")
st.markdown("<div class='subtitle'>Dynamic Ladder Mapping for Smarter Positioning</div>", unsafe_allow_html=True)

# ============= BOX 1: Direction =============
with st.container(border=True):
  st.markdown("### **Direction**")
  side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")

st.write("")  # tiny spacer

# ============= BOX 2: Market Structure =============
with st.container(border=True):
  st.markdown("### **Market Structure**")
  c1, c2, c3 = st.columns(3)
  with c1:
    st.markdown("**Market price**")
    market = st.number_input("Market price", min_value=0.0, format="%.4f", key="mkt", label_visibility="collapsed")
  with c2:
    st.markdown("**Upper Zone (UZ)**")
    zone_upper = st.number_input("Upper Zone", min_value=0.0, format="%.4f", key="zu", label_visibility="collapsed")
  with c3:
    st.markdown("**Lower Zone (LZ)**")
    zone_lower = st.number_input("Lower Zone", min_value=0.0, format="%.4f", key="zl", label_visibility="collapsed")

st.write("")

# ============= BOX 3: Technical Indicators =============
with st.container(border=True):
  st.markdown("### **Technical Indicators**")
  d1, d2, d3, d4 = st.columns(4)
  with d1:
    st.markdown("**ATR (4h, 14)**")
    atr = st.number_input("ATR", min_value=0.0, format="%.4f", key="atr", label_visibility="collapsed")
  with d2:
    st.markdown("**ADX (4h, 14) (optional)**")
    adx = st.number_input("ADX", min_value=0.0, value=0.0, step=0.5, format="%.2f", key="adx", label_visibility="collapsed")
  with d3:
    st.markdown("**RSI-3 trigger (optional)**")
    rsi_trigger = st.selectbox("RSI-3", ["None", "Crossed 20↑", "Crossed 50↑"], label_visibility="collapsed")
  with d4:
    st.markdown("**MACD (1h, 12-26-9)**")
    macd = st.selectbox("MACD", ["Neutral", "Bullish", "Bearish"], label_visibility="collapsed")

st.write("")

# ============= BOX 4: Stop-loss Buffer =============
with st.container(border=True):
  left, right = st.columns([0.42, 0.58])
  with left:
    st.markdown("### **Stop-loss buffer**")
  with right:
    st.markdown("<div class='slbtn'>", unsafe_allow_html=True)
    slbuf_choice = st.radio(
        "Choose SL buffer × ATR",
        ["SL buffer = 1.0 × ATR", "SL buffer = 1.5 × ATR"],
        horizontal=True, label_visibility="collapsed", index=0
    )
    st.markdown("</div>", unsafe_allow_html=True)
  sl_buf = 1.0 if "1.0" in slbuf_choice else 1.5

calc = st.button("Calculate ladders")

# ---------- Helpers ----------
def ladder_count(zone_w: float, atr_val: float, adx_val: float):
    if atr_val <= 0:
        return 2, 0.0
    k = zone_w / atr_val
    base = 2 if k < 1.2 else 3
    if adx_val >= 25:
        base = max(2, base - 1)
    return base, k

def macd_nudged_step(side: str, base_step: float, macd_state: str, atr_val: float) -> float:
    if macd_state == "Neutral":
        return base_step
    if side == "Long":
        return max(0.0, base_step - NUDGE_MULT*atr_val) if macd_state == "Bullish" else (base_step + NUDGE_MULT*atr_val)
    else:
        return max(0.0, base_step - NUDGE_MULT*atr_val) if macd_state == "Bearish" else (base_step + NUDGE_MULT*atr_val)

def clamp(x, lo, hi): return max(lo, min(hi, x))

def deltas_from_market(px: float, mkt: float, side: str):
    d = abs(px - mkt)
    pct = (d / mkt * 100) if mkt > 0 else 0.0
    where = ("below" if px < mkt else "above") if side == "Long" else ("above" if px > mkt else "below")
    return d, pct, where

# ---------- Compute & Results ----------
if calc:
    if market <= 0 or atr <= 0 or zone_upper <= 0 or zone_lower <= 0:
        st.error("Please enter positive numbers for **Market**, **ATR**, **Upper Zone**, and **Lower Zone**.")
        st.stop()
    if zone_lower >= zone_upper:
        st.error("**Lower Zone** must be less than **Upper Zone**.")
        st.stop()

    zone_w = zone_upper - zone_lower
    ladders, k = ladder_count(zone_w, atr, adx)
    base_step = BASE_STEP_MULT * atr
    step = macd_nudged_step(side, base_step, macd, atr)

    # Ladders (L0 at market)
    L = [market]
    if side == "Long":
        L1 = clamp(market - step, zone_lower, zone_upper); L.append(L1)
        if ladders == 3:
            L2 = clamp(L1 - step, zone_lower, zone_upper); L.append(L2)
    else:
        L1 = clamp(market + step, zone_lower, zone_upper); L.append(L1)
        if ladders == 3:
            L2 = clamp(L1 + step, zone_lower, zone_upper); L.append(L2)

    # Fixed TP = 2.0×ATR; SL from zone edge ± buffer×ATR
    if side == "Long":
        sl = zone_lower - sl_buf*atr
        tp = market + TP_MULT*atr
    else:
        sl = zone_upper + sl_buf*atr
        tp = market - TP_MULT*atr

    # Results
    st.markdown("## Results")

    cols = st.columns(len(L))
    for i, px in enumerate(L):
        d, pct, where = deltas_from_market(px, market, side)
        title_top = "L0" if i == 0 else f"L{i}"
        title_sub = "Market" if i == 0 else "\u00A0"
        with cols[i]:
            st.markdown(f"**{title_top}**")
            st.caption(f"**{title_sub}**")
            st.markdown(f"<div class='valbox val-blue'><strong>{px:.{DEC}f}</strong></div>", unsafe_allow_html=True)
            st.caption(f"Δ {d:.{DEC}f} ({pct:.2f}%), {where} market")
            if px == zone_lower or px == zone_upper:
                st.caption("🔒 Clipped to zone edge")

    st.divider()

    rr = ((tp - market) / max(market - sl, 1e-12)) if side == "Long" else ((market - tp) / max(sl - market, 1e-12))
    a, b, c = st.columns(3)
    with a:
        st.markdown("**Stop Loss**")
        st.markdown(f"<div class='valbox val-red'><strong>{sl:.{DEC}f}</strong></div>", unsafe_allow_html=True)
        st.caption(f"Rule: {'LZ −' if side=='Long' else 'UZ +'} {sl_buf:.1f}×ATR")
    with b:
        st.markdown("**Take Profit**")
        st.markdown(f"<div class='valbox val-green'><strong>{tp:.{DEC}f}</strong></div>", unsafe_allow_html=True)
        st.caption(f"Rule: Entry {'+' if side=='Long' else '−'} {TP_MULT:.1f}×ATR (fixed)")
    with c:
        st.markdown("**Reward : Risk**")
        st.markdown(f"<div class='valbox val-blue'><strong>{rr:.2f} : 1</strong></div>", unsafe_allow_html=True)

    st.divider()
    notes = (
        f"Zone width = {zone_w:.{DEC}f} • ATR = {atr:.{DEC}f} • "
        f"k = {k:.2f} • Ladders = {ladders} • "
        f"Base step = {base_step:.{DEC}f} • MACD step = {step:.{DEC}f}"
    )
    st.caption(notes)
