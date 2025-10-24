# ladder_calculator.py — Ladder Calculator (boxed layout, Helvetica, polished UI)
# - Title: "Ladder Calculator" + italic slogan under it
# - Helvetica everywhere; bold labels
# - Grouped input "boxes" (cards) for clarity
# - SL buffer selector (1.0× / 1.5×) tight to heading
# - Fixed TP = 2.0 × ATR (no input)
# - MACD label: "MACD (1h, 12-26-9)"
# - L0 shows “Market”; L1/L2 bold; crisp value cards; no sidebar/forms

import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Ladder Calculator", page_icon="📊", layout="centered")

# ---------------- Global style ----------------
st.markdown("""
<style>
  :root { --border: rgba(255,255,255,0.14); --muted: rgba(255,255,255,0.7); }
  * { font-family: Helvetica, Arial, sans-serif !important; }
  h1,h2,h3,h4,strong,b { font-weight: 700 !important; letter-spacing:.2px; }
  .input-box {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      margin: 14px 0;
      background: rgba(255,255,255,0.02);
  }
  .input-box h3 { margin: 0 0 10px 0; font-size: 1.05rem; }
  .tight-label { margin-bottom: -6px; }
  .badge {
      display:inline-block; padding:6px 10px; border-radius:999px;
      border:1px solid var(--border); margin-right:8px; font-size:.92rem; color:var(--muted);
  }
  .valbox { border-radius:12px; padding:12px 14px; text-align:center; font-weight:800; font-size:1.05rem; }
  .val-red   { background:#3b1d1d; color:#ff6b6b; }
  .val-green { background:#1d3b1d; color:#66ff91; }
  .val-blue  { background:#1d263b; color:#8eb8ff; }

  /* Button-like radio for SL buffer, tight to heading */
  .slbuf-row { display:flex; align-items:center; gap:.6rem; }
  .slbuf-row .label { font-weight: 700; }
  .slbtn [role="radiogroup"] { margin:0 !important; }
  .slbtn [role="radiogroup"] label {
    border:1px solid var(--border);
    border-radius:999px;
    padding:6px 12px;
    margin-right:8px;
    cursor:pointer;
  }
  .slbtn [role="radiogroup"] label:hover { background:rgba(255,255,255,0.06); }
  .slbtn [role="radiogroup"] input:checked ~ div {
    background:rgba(130,180,255,0.25);
    border-radius:999px;
    padding:6px 12px;
  }

  /* Compact bold inputs */
  .stNumberInput > div > div > input { font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------------- Constants ----------------
DEC = 4
BASE_STEP_MULT = 0.5   # base spacing = 0.5 × ATR
NUDGE_MULT = 0.25      # MACD nudge = ±0.25 × ATR
TP_MULT = 2.0          # Fixed TP = 2.0 × ATR

# ---------------- Title + Slogan ----------------
st.markdown("# Ladder Calculator")
st.markdown("_Dynamic Ladder Mapping for Smarter Positioning_")

# ---------------- Section 1: Direction ----------------
st.markdown("<div class='input-box'>", unsafe_allow_html=True)
st.markdown("### **Direction**")
side = st.radio("Direction", ["Long", "Short"], horizontal=True, label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Section 2: Market Structure ----------------
st.markdown("<div class='input-box'>", unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Section 3: Indicators ----------------
st.markdown("<div class='input-box'>", unsafe_allow_html=True)
st.markdown("### **Indicators**")
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
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Section 4: Risk Parameters (SL buffer) ----------------
st.markdown("<div class='input-box'>", unsafe_allow_html=True)
st.markdown("<div class='slbuf-row'><span class='label'>**Stop-loss buffer**</span>", unsafe_allow_html=True)
st.markdown("<span class='slbtn'>", unsafe_allow_html=True)
slbuf_choice = st.radio(
    "Choose SL buffer × ATR",
    ["SL buffer = 1.0 × ATR", "SL buffer = 1.5 × ATR"],
    horizontal=True, label_visibility="collapsed", index=0
)
st.markdown("</span></div>", unsafe_allow_html=True)
sl_buf = 1.0 if "1.0" in slbuf_choice else 1.5
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Action ----------------
calc = st.button("Calculate ladders")

# ---------------- Helpers ----------------
def ladder_count(zone_w: float, atr_val: float, adx_val: float):
    if atr_val <= 0:
        return 2, 0.0
    k = zone_w / atr_val
    base = 2 if k < 1.2 else 3
    if adx_val >= 25:
        base = max(2, base - 1)  # trending → fewer rungs
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

# ---------------- Compute + Results ----------------
if calc:
    # Validate basics
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

    # Build ladders (L0 at market)
    L = [market]
    if side == "Long":
        L1 = clamp(market - step, zone_lower, zone_upper); L.append(L1)
        if ladders == 3:
            L2 = clamp(L1 - step, zone_lower, zone_upper); L.append(L2)
    else:
        L1 = clamp(market + step, zone_lower, zone_upper); L.append(L1)
        if ladders == 3:
            L2 = clamp(L1 + step, zone_lower, zone_upper); L.append(L2)

    # Fixed TP = 2.0 × ATR
    if side == "Long":
        sl = zone_lower - sl_buf*atr
        tp = market + TP_MULT*atr
    else:
        sl = zone_upper + sl_buf*atr
        tp = market - TP_MULT*atr

    # ------- Results -------
    st.markdown("## Results")

    # Ladders row
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

    # SL / TP / RR (bold values)
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

    # Notes (chips)
    st.markdown("### Notes")
    st.markdown(
        f"<span class='badge'>Zone width: {zone_w:.{DEC}f}</span>"
        f"<span class='badge'>ATR: {atr:.{DEC}f}</span>"
        f"<span class='badge'>k = width/ATR: {k:.2f}</span>"
        f"<span class='badge'>Ladders: {ladders}</span>"
        f"<span class='badge'>Base step: {base_step:.{DEC}f}</span>"
        f"<span class='badge'>MACD step: {step:.{DEC}f}</span>",
        unsafe_allow_html=True
    )
    tips = []
    if adx >= 25: tips.append("ADX≥25 → reduced ladder count (trend).")
    if rsi_trigger != "None": tips.append(f"RSI rule noted: {rsi_trigger}.")
    if macd != "Neutral": tips.append(f"MACD bias applied: {macd}.")
    if tips: st.caption(" • ".join(tips))

else:
    st.info("Enter values and press **Calculate ladders** to generate entries.", icon="ℹ️")
